import csv
import json
import math
import struct
from pathlib import Path
from statistics import median

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

def read_frames(path, limit=100):
    with path.open("rb") as f:
        for i in range(limit):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete OSI header")
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid record size")
            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated OSI record")
            msg = SensorView()
            msg.ParseFromString(payload)
            yield i, msg

def rotate_xy(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return c*x-s*y, s*x+c*y

def host_origin(sv):
    if not sv.HasField("global_ground_truth"):
        return None
    ngt = sv.global_ground_truth
    if not ngt.HasField("host_vehicle_id"):
        return None

    host_id = int(ngt.host_vehicle_id.value)
    hosts = [
        obj for obj in ngt.moving_object
        if int(obj.id.value) == host_id
    ]
    if not hosts:
        return None

    first = hosts[0]
    p = first.base.position
    o = first.base.orientation

    # Reject inconsistent duplicate copies.
    for other in hosts[1:]:
        q = other.base.position
        r = other.base.orientation
        if max(
            abs(q.x-p.x), abs(q.y-p.y), abs(q.z-p.z),
            abs(r.yaw-o.yaw), abs(r.pitch-o.pitch),
            abs(r.roll-o.roll)
        ) > 1e-6:
            return None

    if abs(o.pitch) > 1e-6 or abs(o.roll) > 1e-6:
        return None

    return (
        host_id,
        float(p.x), float(p.y), float(p.z),
        float(o.yaw)
    )

points_file = DATA / "task20_28_radar_world_points.csv"
gt_file = DATA / "task20_14_gt_classified_objects.csv"

with points_file.open(
    newline="", encoding="utf-8-sig"
) as f:
    points = list(csv.DictReader(f))

with gt_file.open(
    newline="", encoding="utf-8-sig"
) as f:
    gt_objects = list(csv.DictReader(f))

gt_by_frame = {}
for obj in gt_objects:
    key = (obj["Recording"], int(obj["Frame"]))
    gt_by_frame.setdefault(key, []).append(obj)

points_by_frame = {}
for row in points:
    key = (
        row["Recording"],
        int(row["FrameIndex"])
    )
    points_by_frame.setdefault(key, []).append(row)

details = []
summary = []

print("\n=== TASK 20.30 RADAR GEOMETRY DIAGNOSTICS ===")

for path in sorted(RAW.rglob("*_sv_*.osi")):
    scenario = path.parent.name
    errors = []
    evaluated = 0
    host_nearest = 0
    helper_nearest = 0
    other_nearest = 0

    for frame, sv in read_frames(path):
        key = (scenario, frame)
        frame_points = points_by_frame.get(key, [])
        if not frame_points:
            continue

        host = host_origin(sv)
        if host is None:
            continue

        host_id, hx, hy, hz, yaw = host

        for radar_index, view in enumerate(
            sv.radar_sensor_view
        ):
            if not view.HasField("view_configuration"):
                continue

            cfg = view.view_configuration
            if not cfg.HasField("mounting_position"):
                continue

            m = cfg.mounting_position.position

            ox, oy = rotate_xy(
                float(m.x), float(m.y), yaw
            )
            ox += hx
            oy += hy
            oz = hz + float(m.z)

            for point in frame_points:
                if int(point["RadarIndex"]) != radar_index:
                    continue

                x = float(point["WorldX"])
                y = float(point["WorldY"])
                z = float(point["WorldZ"])
                measured = float(point["RangeM"])

                reconstructed = math.sqrt(
                    (x-ox)**2 + (y-oy)**2 + (z-oz)**2
                )
                error = abs(reconstructed-measured)
                errors.append(error)
                evaluated += 1

                nearest_id = ""
                nearest_distance = float("inf")
                nearest_kind = ""

                for obj in gt_by_frame.get(key, []):
                    if obj["Kind"] != "MOVING":
                        continue

                    d = math.hypot(
                        x-float(obj["X"]),
                        y-float(obj["Y"])
                    )

                    if d < nearest_distance:
                        nearest_distance = d
                        nearest_id = obj["ID"]
                        nearest_kind = obj["ObjectType"]

                if nearest_id:
                    if nearest_id == str(host_id):
                        host_nearest += 1
                    else:
                        helper_nearest += 1
                else:
                    other_nearest += 1

                details.append({
                    "Recording": scenario,
                    "Frame": frame,
                    "HostID": host_id,
                    "RadarIndex": radar_index,
                    "SensorOriginX": ox,
                    "SensorOriginY": oy,
                    "SensorOriginZ": oz,
                    "RadarWorldX": x,
                    "RadarWorldY": y,
                    "RadarWorldZ": z,
                    "MeasuredRangeM": measured,
                    "ReconstructedDistanceM":
                        reconstructed,
                    "RangeResidualM": error,
                    "NearestMovingObjectID":
                        nearest_id,
                    "NearestMovingObjectType":
                        nearest_kind,
                    "NearestCentreDistanceXYM": (
                        nearest_distance
                        if math.isfinite(nearest_distance)
                        else ""
                    )
                })

    item = {
        "Recording": scenario,
        "PointsEvaluated": evaluated,
        "MedianRangeResidualM": (
            median(errors) if errors else None
        ),
        "MaximumRangeResidualM": (
            max(errors) if errors else None
        ),
        "HostNearestCount": host_nearest,
        "OtherMovingObjectNearestCount":
            helper_nearest,
        "NoMovingObjectCount": other_nearest,
    }

    summary.append(item)

    print(
        f"{scenario:28s}"
        f" | Points={evaluated:5d}"
        f" | MedianResidual="
        f"{item['MedianRangeResidualM']}"
        f" | HostNearest={host_nearest}"
        f" | OtherNearest={helper_nearest}"
    )

def save_csv(path, rows):
    if not rows:
        return
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

detail_path = (
    DATA / "task20_30_radar_geometry_details.csv"
)
summary_path = (
    DATA / "task20_30_radar_geometry_summary.csv"
)
report_path = (
    FINDINGS / "task20_30_geometry_diagnostics.json"
)

save_csv(detail_path, details)
save_csv(summary_path, summary)

report_path.write_text(
    json.dumps({
        "Task": "20.30",
        "Summary": summary,
        "Limitation": (
            "Geometric self-consistency only; "
            "not radar detection accuracy."
        ),
        "DetectionAccuracyValidated": False,
        "EnergyMeasured": False
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.30 COMPLETE ===")
print("Points evaluated:", len(details))
print("Details saved:", detail_path.is_file())
print("Summary saved:", summary_path.is_file())
print("JSON saved:", report_path.is_file())
print("Radar accuracy validated:", False)
print("Energy measured:", False)
