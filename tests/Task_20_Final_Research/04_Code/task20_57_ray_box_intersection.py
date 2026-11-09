import csv
import json
import math
import struct
from pathlib import Path
from collections import Counter

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_20_Final_Research")
OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")
SV = OUTPUT / "20261102T180104Z_sv_380_X_806_GEMSTAR.osi"
GT = OUTPUT / "20261102T180104Z_gt_380_X_806_GEMSTAR.osi"

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"
DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

FRAMES = set(range(95, 100))
TARGET_ID = 76765
TRACE_RANGE = 50.0
C = 299705543.0

def read_frames(path, cls):
    with path.open("rb") as f:
        for i in range(100):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete OSI header")
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI record size")
            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated OSI record")
            if i in FRAMES:
                msg = cls()
                msg.ParseFromString(payload)
                yield i, msg

def rotate(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return c*x-s*y, s*x+c*y

def ray_box(origin, direction, centre, yaw, dimensions):
    # Convert ray origin and direction into target-box axes.
    ox, oy = rotate(
        origin[0]-centre[0],
        origin[1]-centre[1], -yaw
    )
    oz = origin[2]-centre[2]
    dx, dy = rotate(direction[0], direction[1], -yaw)
    dz = direction[2]

    half = [d/2 for d in dimensions]
    tmin, tmax = 0.0, TRACE_RANGE

    for p, v, h in zip(
        [ox, oy, oz], [dx, dy, dz], half
    ):
        if abs(v) < 1e-12:
            if abs(p) > h:
                return None
            continue

        a = (-h-p)/v
        b = (h-p)/v

        if a > b:
            a, b = b, a

        tmin = max(tmin, a)
        tmax = min(tmax, b)

        if tmin > tmax:
            return None

    return tmin

sv_data = dict(read_frames(SV, SensorView))
gt_data = dict(read_frames(GT, GroundTruth))

results = []
print("\n=== TASK 20.57 RADAR RAY-BOX INTERSECTION ===")

for frame in sorted(FRAMES):
    sv = sv_data.get(frame)
    gt = gt_data.get(frame)

    if sv is None or gt is None:
        print(f"Frame {frame}: missing recording")
        continue

    target = next(
        (o for o in gt.moving_object
         if int(o.id.value) == TARGET_ID),
        None
    )

    if target is None:
        print(f"Frame {frame}: target missing")
        continue

    nested = sv.global_ground_truth
    host_id = int(nested.host_vehicle_id.value)
    hosts = [
        o for o in nested.moving_object
        if int(o.id.value) == host_id
    ]

    if not hosts:
        print(f"Frame {frame}: host pose missing")
        continue

    hp = hosts[0].base.position
    ho = hosts[0].base.orientation
    bp = target.base.position
    bo = target.base.orientation
    dim = target.base.dimension

    if max(abs(ho.pitch), abs(ho.roll),
           abs(bo.pitch), abs(bo.roll)) > 1e-6:
        print(f"Frame {frame}: unsupported pitch/roll")
        continue

    centre = (bp.x, bp.y, bp.z)
    dimensions = (dim.length, dim.width, dim.height)

    for radar_index, view in enumerate(sv.radar_sensor_view):
        cfg = view.view_configuration
        mp = cfg.mounting_position.position
        mo = cfg.mounting_position.orientation

        if max(abs(mo.yaw), abs(mo.pitch),
               abs(mo.roll)) > 1e-6:
            print(f"Frame {frame}: unsupported radar mount")
            continue

        mx, my = rotate(mp.x, mp.y, ho.yaw)
        origin = (hp.x+mx, hp.y+my, hp.z+mp.z)

        count_recorded = 0
        count_doubled = 0
        ray54_recorded = False
        ray54_doubled = False

        for index, ref in enumerate(view.reflection):
            az = float(ref.source_horizontal_angle)
            el = float(ref.source_vertical_angle)

            # Unreal local Y -> OSI Y conversion.
            lx = math.cos(el)*math.cos(az)
            ly = -math.cos(el)*math.sin(az)
            lz = math.sin(el)

            wx, wy = rotate(lx, ly, ho.yaw)
            direction = (wx, wy, lz)

            hit_recorded = ray_box(
                origin, direction, centre,
                bo.yaw, dimensions
            )
            hit_doubled = ray_box(
                origin, direction, centre,
                bo.yaw, tuple(2*d for d in dimensions)
            )

            valid = (
                math.isfinite(ref.time_of_flight)
                and math.isfinite(ref.signal_strength)
                and ref.time_of_flight > 0
                and ref.signal_strength > 0
            )

            measured = (
                ref.time_of_flight*C/2
                if valid else None
            )

            if hit_recorded is not None:
                count_recorded += 1
            if hit_doubled is not None:
                count_doubled += 1

            if index == 54:
                ray54_recorded = hit_recorded is not None
                ray54_doubled = hit_doubled is not None

            if (hit_recorded is not None
                    or hit_doubled is not None
                    or index == 54):
                results.append({
                    "Frame": frame,
                    "RadarIndex": radar_index,
                    "RayIndex": index,
                    "IntersectsRecordedBox":
                        hit_recorded is not None,
                    "IntersectsDoubledBox":
                        hit_doubled is not None,
                    "RecordedBoxEntryM":
                        hit_recorded if hit_recorded is not None else "",
                    "DoubledBoxEntryM":
                        hit_doubled if hit_doubled is not None else "",
                    "MeasuredReturnM":
                        measured if measured is not None else "",
                    "PositiveReturn": valid,
                    "Model": target.model_reference
                })

        print(
            f"Frame={frame} | "
            f"RecordedBoxRays={count_recorded} | "
            f"DoubledBoxRays={count_doubled} | "
            f"Ray54Recorded={ray54_recorded} | "
            f"Ray54Doubled={ray54_doubled}"
        )

csv_path = DATA / "task20_57_ray_box_intersections.csv"
json_path = FINDINGS / "task20_57_ray_box_audit.json"

columns = [
    "Frame", "RadarIndex", "RayIndex",
    "IntersectsRecordedBox", "IntersectsDoubledBox",
    "RecordedBoxEntryM", "DoubledBoxEntryM",
    "MeasuredReturnM", "PositiveReturn", "Model"
]

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(results)

json_path.write_text(
    json.dumps({
        "Task": "20.57",
        "TargetID": TARGET_ID,
        "Results": results,
        "Assumptions": [
            "Zero host and mount pitch/roll",
            "Zero radar mounting yaw",
            "OSI world-coordinate yaw",
            "Recorded and doubled GT box dimensions",
            "50 m maximum trace distance",
            "Identical frame indices used",
            "Pose sampling-time offset unresolved"
        ],
        "CollisionMeshIntersectionVerified": False,
        "RadarDetectionAccuracyValidated": False,
        "HardwareEnergyMeasured": False
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.57 COMPLETE ===")
print("Diagnostic ray records:", len(results))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Real collision mesh verified:", False)
print("Detection accuracy validated:", False)
