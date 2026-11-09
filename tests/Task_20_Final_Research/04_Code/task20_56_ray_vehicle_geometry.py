import csv
import json
import math
import struct
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_20_Final_Research"
)

GT = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261102T180104Z_gt_380_X_806_GEMSTAR.osi"
)

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

TARGET_ID = 76765
FRAMES = set(range(95, 100))

with (DATA / "task20_55_ray_alignment.csv").open(
    encoding="utf-8-sig", newline=""
) as f:
    alignment = {
        int(row["Frame"]): row
        for row in csv.DictReader(f)
    }

records = []

print("\n=== TASK 20.56 RAY / VEHICLE GEOMETRY ===")

with GT.open("rb") as f:
    for frame in range(100):
        header = f.read(4)
        if not header:
            break
        if len(header) != 4:
            raise ValueError("Invalid OSI header")

        size = struct.unpack("<I", header)[0]
        if not 0 < size < 100_000_000:
            raise ValueError("Invalid message length")

        payload = f.read(size)
        if len(payload) != size:
            raise ValueError("Incomplete message")

        if frame not in FRAMES:
            continue

        gt = GroundTruth()
        gt.ParseFromString(payload)

        matches = [
            obj for obj in gt.moving_object
            if int(obj.id.value) == TARGET_ID
        ]

        if frame not in alignment or not matches:
            print(f"Frame {frame}: target/alignment missing")
            continue

        obj = matches[0]
        row = alignment[frame]

        distance = float(row["TargetCenterRangeM"])
        angle_deg = float(row["AngularSeparationDeg"])
        angle_rad = math.radians(angle_deg)

        # Perpendicular distance from target centre
        # to infinite nearest-ray line, assuming the
        # recorded relative angular separation.
        perpendicular = distance * math.sin(angle_rad)

        dimension = obj.base.dimension
        orientation = obj.base.orientation

        result = {
            "Frame": frame,
            "ObjectID": TARGET_ID,
            "Model": obj.model_reference,
            "CenterRangeM": distance,
            "AngularGapDeg": angle_deg,
            "PerpendicularRayGapM": perpendicular,
            "GTLengthM": float(dimension.length),
            "GTWidthM": float(dimension.width),
            "GTHeightM": float(dimension.height),
            "GTYawRad": float(orientation.yaw),
            "NearestRayIndex": int(row["NearestRayIndex"]),
            "NearestRayPositiveReturn":
                row["NearestRayPositiveReturn"],
            "ObjectIntersectionValidated": False
        }

        records.append(result)

        print(
            f"Frame={frame} | "
            f"RayGap={perpendicular:.3f}m | "
            f"GT Length={dimension.length:.3f}m | "
            f"Width={dimension.width:.3f}m | "
            f"Height={dimension.height:.3f}m"
        )

csv_path = DATA / "task20_56_ray_vehicle_geometry.csv"
json_path = FINDINGS / "task20_56_ray_vehicle_geometry.json"

columns = [
    "Frame", "ObjectID", "Model",
    "CenterRangeM", "AngularGapDeg",
    "PerpendicularRayGapM",
    "GTLengthM", "GTWidthM", "GTHeightM",
    "GTYawRad", "NearestRayIndex",
    "NearestRayPositiveReturn",
    "ObjectIntersectionValidated"
]

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(records)

json_path.write_text(
    json.dumps({
        "Task": "20.56",
        "TargetID": TARGET_ID,
        "Results": records,
        "Limitations": [
            "Angular gap is centre-to-ray only",
            "GT dimensions may differ from collision extents",
            "GEMSTAR GT export may use Unreal half-extents",
            "Object yaw not yet used for box intersection",
            "No raycast hit actor ID available in OSI",
            "No independent detection accuracy measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.56 COMPLETE ===")
print("Observations:", len(records))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Ray-box intersection validated:", False)
print("Radar detection accuracy validated:", False)
