import csv
import json
import math
import struct
from pathlib import Path
from collections import Counter
from statistics import median

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests/Task_20_Final_Research"
SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261102T180104Z_sv_380_X_806_GEMSTAR.osi"
)

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"
DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

C = 299705543.0
MAX_RANGE = 50.0
PROXIMITY = 3.0

def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

targets = load_csv(DATA / "task20_52_external_gt_50m.csv")

by_frame = {}
for item in targets:
    frame = int(item["Frame"])
    by_frame.setdefault(frame, []).append(item)

def rotate(x, y, angle):
    c, s = math.cos(angle), math.sin(angle)
    return c*x-s*y, s*x+c*y

def read_sv(path, limit=100):
    with path.open("rb") as f:
        for index in range(limit):
            header = f.read(4)
            if not header:
                break
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI record size")
            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Incomplete OSI record")
            msg = SensorView()
            msg.ParseFromString(payload)
            yield index, msg

def host_pose(sv):
    if not sv.HasField("global_ground_truth"):
        return None

    gt = sv.global_ground_truth
    if not gt.HasField("host_vehicle_id"):
        return None

    host_id = gt.host_vehicle_id.value
    matches = [
        obj for obj in gt.moving_object
        if obj.id.value == host_id
        and obj.base.HasField("position")
        and obj.base.HasField("orientation")
    ]

    if not matches:
        return None

    p = matches[0].base.position
    o = matches[0].base.orientation

    values = (
        float(p.x), float(p.y), float(p.z),
        float(o.yaw), float(o.pitch), float(o.roll)
    )

    if not all(math.isfinite(v) for v in values):
        return None

    if abs(o.pitch) > 1e-6 or abs(o.roll) > 1e-6:
        return None

    for other in matches[1:]:
        q, a = other.base.position, other.base.orientation
        test = (
            float(q.x), float(q.y), float(q.z),
            float(a.yaw), float(a.pitch), float(a.roll)
        )
        if max(abs(x-y) for x,y in zip(values,test)) > 1e-6:
            return None

    return values

rows = []
stats = Counter()

print("\n=== TASK 20.53 EXTERNAL VEHICLE PROXIMITY ===")

for frame, sv in read_sv(SOURCE):
    if frame == 0:
        continue

    frame_targets = by_frame.get(frame, [])
    if not frame_targets:
        continue

    host = host_pose(sv)
    if host is None:
        stats["MissingHostFrames"] += 1
        continue

    hx,hy,hz,yaw,_,_ = host

    for radar_index, view in enumerate(sv.radar_sensor_view):
        if not view.HasField("view_configuration"):
            continue

        cfg = view.view_configuration
        if not cfg.HasField("mounting_position"):
            continue

        mount = cfg.mounting_position
        mp, mo = mount.position, mount.orientation

        if abs(mo.pitch) > 1e-6 or abs(mo.roll) > 1e-6:
            stats["UnsupportedMountViews"] += 1
            continue

        ox,oy = rotate(mp.x,mp.y,yaw)
        sx,sy,sz = hx+ox,hy+oy,hz+mp.z
        sensor_yaw = yaw+mo.yaw

        hfov = float(cfg.field_of_view_horizontal)
        vfov = float(cfg.field_of_view_vertical)

        if not (0 < hfov <= 2*math.pi
                and 0 < vfov <= math.pi):
            continue

        points = []

        for ref in view.reflection:
            tof = float(ref.time_of_flight)
            strength = float(ref.signal_strength)

            if not (
                math.isfinite(tof) and math.isfinite(strength)
                and tof > 0 and strength > 0
            ):
                continue

            r = tof*C/2

            # Skip near-zero initialization artifacts.
            if not 0.001 <= r <= MAX_RANGE+0.01:
                continue

            az = float(ref.source_horizontal_angle)
            el = float(ref.source_vertical_angle)

            # GEMSTAR Unreal local axes -> OSI local axes.
            lx = r*math.cos(el)*math.cos(az)
            ly = -r*math.cos(el)*math.sin(az)
            lz = r*math.sin(el)

            # Mount orientation is zero in the
            # inspected configuration; avoid a
            # silently incorrect rotated-mount model.
            if abs(mo.yaw) > 1e-6:
                points = []
                stats["UnsupportedMountYawViews"] += 1
                break

            px,py = rotate(
                float(mp.x)+lx, float(mp.y)+ly, yaw
            )
            points.append((
                hx+px, hy+py, hz+mp.z+lz
            ))

        if abs(mo.yaw) > 1e-6:
            continue

        for obj in frame_targets:
            tx,ty,tz = (
                float(obj[k]) for k in ("X","Y","Z")
            )

            dx,dy,dz = tx-sx,ty-sy,tz-sz
            distance = math.sqrt(dx*dx+dy*dy+dz*dz)

            azimuth = math.atan2(
                math.sin(math.atan2(dy,dx)-sensor_yaw),
                math.cos(math.atan2(dy,dx)-sensor_yaw)
            )
            elevation = math.atan2(
                dz, math.hypot(dx,dy)
            )

            inside = (
                distance <= MAX_RANGE
                and abs(azimuth) <= hfov/2
                and abs(elevation) <= vfov/2
            )

            nearest = (
                min(
                    math.dist((tx,ty,tz), p)
                    for p in points
                )
                if points else None
            )

            close = (
                nearest is not None
                and nearest <= PROXIMITY
            )

            stats["Targets"] += 1
            stats["CenterEligible"] += int(inside)
            stats["Within3m"] += int(close)
            stats["EligibleWithin3m"] += int(
                inside and close
            )

            rows.append({
                "Frame":frame,
                "ObjectID":obj["ObjectID"],
                "ModelReference":obj["ModelReference"],
                "RadarIndex":radar_index,
                "CenterRangeM":round(distance,5),
                "CenterInsideRangeFoV":inside,
                "RadarPointsInFrame":len(points),
                "NearestRadarPointDistanceM": (
                    round(nearest,5)
                    if nearest is not None else ""
                ),
                "PointWithin3mOfCenter":close,
                "Interpretation":"Exploratory proximity only"
            })

distances = [
    float(r["NearestRadarPointDistanceM"])
    for r in rows
    if r["NearestRadarPointDistanceM"] != ""
]

csv_path = DATA / "task20_53_vehicle_radar_proximity.csv"
json_path = FINDINGS / "task20_53_vehicle_proximity_audit.json"

fields = [
    "Frame","ObjectID","ModelReference","RadarIndex",
    "CenterRangeM","CenterInsideRangeFoV",
    "RadarPointsInFrame","NearestRadarPointDistanceM",
    "PointWithin3mOfCenter","Interpretation"
]

with csv_path.open(
    "w",newline="",encoding="utf-8"
) as f:
    writer = csv.DictWriter(f,fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

summary = {
    "Task":"20.53",
    "TargetObservationsEvaluated":len(rows),
    "CenterInside50mAndFoV":stats["CenterEligible"],
    "RadarPointWithin3mOfCenter":stats["Within3m"],
    "EligibleAndWithin3m":stats["EligibleWithin3m"],
    "MedianNearestPointDistanceM":(
        median(distances) if distances else None
    ),
    "MissingHostFrames":stats["MissingHostFrames"],
    "IndependentDetectionAccuracyValidated":False,
    "RangeLimitSource":"Verified runtime 50m",
    "Limitations":[
        "Centre proximity is not object association",
        "Surface geometry and occlusion not evaluated",
        "Pose/GT sampling offset unresolved",
        "World transform requires independent validation",
        "Only first 100 recorded frames evaluated",
        "No hardware energy measured"
    ]
}

json_path.write_text(
    json.dumps(summary,indent=2),
    encoding="utf-8"
)

print("GT observations evaluated:",len(rows))
print("Centres inside 50 m and FoV:",
      stats["CenterEligible"])
print("Radar point within 3 m:",
      stats["Within3m"])
print("Eligible centres with nearby point:",
      stats["EligibleWithin3m"])
print("Median nearest-point distance:",
      summary["MedianNearestPointDistanceM"])
print("Missing host frames:",
      stats["MissingHostFrames"])

print("\n=== TASK 20.53 COMPLETE ===")
print("CSV saved:",csv_path.is_file())
print("JSON saved:",json_path.is_file())
print("Detection accuracy validated:",False)
print("Energy measured:",False)
