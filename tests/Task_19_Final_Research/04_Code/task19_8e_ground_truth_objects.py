import csv
import struct
from pathlib import Path

from osi3 import osi_groundtruth_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_gt_380_X_466_GEMSTAR.osi"
)

target_frame = 150

with source.open("rb") as f:
    for frame in range(target_frame + 1):
        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Missing frame header")

        length = struct.unpack("<I", header)[0]

        if frame == target_frame:
            payload = f.read(length)

            if len(payload) != length:
                raise RuntimeError("Truncated frame")

            gt = osi_groundtruth_pb2.GroundTruth()
            gt.ParseFromString(payload)
        else:
            f.seek(length, 1)

rows = []

print("\n=== TASK 19.8E GROUND TRUTH OBJECTS ===")
print("Frame:", target_frame)
print("Moving objects:", len(gt.moving_object))

for obj in gt.moving_object:
    oid = int(obj.id.value)

    base_obj = obj.base
    pos = base_obj.position
    dim = base_obj.dimension

    row = {
        "ObjectID": oid,
        "TypeCode": int(obj.type),
        "X": float(pos.x),
        "Y": float(pos.y),
        "Z": float(pos.z),
        "Length": float(dim.length),
        "Width": float(dim.width),
        "Height": float(dim.height),
    }

    rows.append(row)

    print(
        f"ID={oid} | "
        f"type={obj.type} | "
        f"position=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}) | "
        f"dimensions=({dim.length:.2f}, "
        f"{dim.width:.2f}, {dim.height:.2f})"
    )

out = (
    base / "02_CSV_Data"
    / "task19_8e_gt_frame150_objects.csv"
)

with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "ObjectID","TypeCode","X","Y","Z",
        "Length","Width","Height"
    ])
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 19.8E COMPLETE ===")
print("Objects exported:", len(rows))
print("CSV saved:", out.is_file())
