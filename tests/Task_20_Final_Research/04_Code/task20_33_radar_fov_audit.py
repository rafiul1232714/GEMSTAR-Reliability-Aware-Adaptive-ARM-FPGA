import csv
import json
import math
import struct
from pathlib import Path
from collections import Counter, defaultdict

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_20_Final_Research"
RAW = ROOT / "data" / "raw"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

targets_path = DATA / "task20_31_external_moving_candidates.csv"

with targets_path.open(encoding="utf-8-sig", newline="") as f:
    targets = list(csv.DictReader(f))

by_frame = defaultdict(list)
for obj in targets:
    by_frame[(obj["Recording"], int(obj["Frame"]))].append(obj)

def has(message, field):
    return field in {f.name for f, _ in message.ListFields()}

def frames(path):
    with path.open("rb") as f:
        for index in range(100):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI size")

            data = f.read(size)
            if len(data) != size:
                raise ValueError("Truncated OSI message")

            sv = SensorView()
            sv.ParseFromString(data)
            yield index, sv

def host_pose(sv):
    if not has(sv, "global_ground_truth"):
        return None

    gt = sv.global_ground_truth
    if not has(gt, "host_vehicle_id"):
        return None

    host_id = int(gt.host_vehicle_id.value)

    hosts = [
        obj for obj in gt.moving_object
        if int(obj.id.value) == host_id
        and has(obj.base, "position")
        and has(obj.base, "orientation")
    ]

    if not hosts:
        return None

    def values(obj):
        p, o = obj.base.position, obj.base.orientation
        return (
            float(p.x), float(p.y), float(p.z),
            float(o.yaw), float(o.pitch), float(o.roll)
        )

    first = values(hosts[0])
    if not all(math.isfinite(v) for v in first):
        return None

    if abs(first[4]) > 1e-6 or abs(first[5]) > 1e-6:
        return None

    for obj in hosts[1:]:
        other = values(obj)
        if max(abs(a-b) for a,b in zip(first,other)) > 1e-6:
            return None

    return first

def rotate(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return c*x-s*y, s*x+c*y

rows = []
summaries = []

print("\n=== TASK 20.33 CORRECTED FOV AUDIT ===")

for path in sorted(RAW.rglob("*_sv_*.osi")):
    scenario = path.parent.name
    counts = Counter()
    configurations = set()

    for frame, sv in frames(path):
        objects = by_frame.get((scenario, frame), [])
        if not objects:
            continue

        host = host_pose(sv)
        if host is None:
            counts["NO_HOST_POSE"] += len(objects)
            continue

        hx, hy, hz, yaw, _, _ = host

        if not sv.radar_sensor_view:
            counts["NO_RADAR_VIEW"] += len(objects)
            continue

        for index, view in enumerate(sv.radar_sensor_view):
            if not has(view, "view_configuration"):
                counts["NO_CONFIG"] += len(objects)
                continue

            cfg = view.view_configuration

            if not has(cfg, "mounting_position"):
                counts["NO_MOUNT"] += len(objects)
                continue

            mounting = cfg.mounting_position
            if not (has(mounting, "position")
                    and has(mounting, "orientation")):
                counts["NO_MOUNT"] += len(objects)
                continue

            mp = mounting.position
            mo = mounting.orientation

            if abs(mo.pitch) > 1e-6 or abs(mo.roll) > 1e-6:
                counts["UNSUPPORTED_ROTATION"] += len(objects)
                continue

            # Range is deliberately not read:
            # RadarSensorViewConfiguration has no range field.
            hfov = float(cfg.field_of_view_horizontal)
            vfov = float(cfg.field_of_view_vertical)

            config_valid = (
                has(cfg, "field_of_view_horizontal")
                and has(cfg, "field_of_view_vertical")
                and math.isfinite(hfov)
                and math.isfinite(vfov)
                and 0 < hfov <= 2*math.pi
                and 0 < vfov <= math.pi
            )

            if config_valid:
                configurations.add((
                    round(math.degrees(hfov), 3),
                    round(math.degrees(vfov), 3)
                ))

            mx, my = rotate(mp.x, mp.y, yaw)
            sx, sy, sz = hx+mx, hy+my, hz+mp.z
            sensor_yaw = yaw+mo.yaw

            for obj in objects:
                tx, ty, tz = (
                    float(obj[k]) for k in ("X", "Y", "Z")
                )

                dx, dy, dz = tx-sx, ty-sy, tz-sz
                distance = math.sqrt(dx*dx+dy*dy+dz*dz)

                azimuth = math.atan2(
                    math.sin(math.atan2(dy,dx)-sensor_yaw),
                    math.cos(math.atan2(dy,dx)-sensor_yaw)
                )
                elevation = math.atan2(dz, math.hypot(dx,dy))

                if not config_valid:
                    status = "CONFIG_UNAVAILABLE"
                elif (
                    abs(azimuth) <= hfov/2
                    and abs(elevation) <= vfov/2
                ):
                    status = "CENTER_INSIDE_FOV"
                else:
                    status = "CENTER_OUTSIDE_FOV"

                counts[status] += 1

                rows.append({
                    "Recording": scenario,
                    "Frame": frame,
                    "ObjectID": obj["ID"],
                    "RadarIndex": index,
                    "CenterDistanceM": round(distance, 6),
                    "AzimuthDeg": round(math.degrees(azimuth), 4),
                    "ElevationDeg": round(math.degrees(elevation), 4),
                    "HorizontalFoVDeg": (
                        round(math.degrees(hfov), 4)
                        if config_valid else ""
                    ),
                    "VerticalFoVDeg": (
                        round(math.degrees(vfov), 4)
                        if config_valid else ""
                    ),
                    "RangeEligibility": "UNKNOWN",
                    "Status": status
                })

    summaries.append({
        "Recording": scenario,
        "InsideFOV": counts["CENTER_INSIDE_FOV"],
        "OutsideFOV": counts["CENTER_OUTSIDE_FOV"],
        "ConfigUnavailable": counts["CONFIG_UNAVAILABLE"],
        "NoHostPose": counts["NO_HOST_POSE"],
        "RecordedFoVDeg": sorted(configurations)
    })

    print(
        f"{scenario:28s}"
        f" | Inside={counts['CENTER_INSIDE_FOV']:3d}"
        f" | Outside={counts['CENTER_OUTSIDE_FOV']:3d}"
        f" | ConfigMissing={counts['CONFIG_UNAVAILABLE']:3d}"
        f" | NoHost={counts['NO_HOST_POSE']:3d}"
    )
    if configurations:
        print("  Recorded FoV (H°, V°):",
              sorted(configurations))

csv_path = DATA / "task20_33_radar_fov_eligibility.csv"
json_path = FINDINGS / "task20_33_radar_fov_audit.json"

columns = [
    "Recording", "Frame", "ObjectID", "RadarIndex",
    "CenterDistanceM", "AzimuthDeg", "ElevationDeg",
    "HorizontalFoVDeg", "VerticalFoVDeg",
    "RangeEligibility", "Status"
]

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

json_path.write_text(
    json.dumps({
        "Task": "20.33",
        "Summary": summaries,
        "RangeLimitKnown": False,
        "ObjectCenterOnly": True,
        "OcclusionValidated": False,
        "PoseTimingValidated": False,
        "RadarAccuracyValidated": False,
        "EnergyMeasured": False
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.33 COMPLETE ===")
print("Object/radar observations evaluated:", len(rows))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Range eligibility established:", False)
print("Radar accuracy validated:", False)
