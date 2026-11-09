import json
import struct
from pathlib import Path

from osi3 import osi_groundtruth_pb2
from google.protobuf.json_format import MessageToDict

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_gt_380_X_466_GEMSTAR.osi"
)

target_frame = 150
target_ids = {83181, 83183, 83185, 83265}

assert source.is_file(), f"Ground-truth file missing: {source}"

def get_object_id(obj):
    if hasattr(obj, "id") and obj.HasField("id"):
        return int(obj.id.value)
    return None

with source.open("rb") as f:
    gt = None

    for frame in range(target_frame + 1):
        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError(f"Missing header at frame {frame}")

        length = struct.unpack("<I", header)[0]

        if not (0 < length < 100_000_000):
            raise RuntimeError(f"Invalid record length: {length}")

        if frame != target_frame:
            f.seek(length, 1)
            continue

        payload = f.read(length)

        if len(payload) != length:
            raise RuntimeError("Truncated ground-truth frame")

        gt = osi_groundtruth_pb2.GroundTruth()
        gt.ParseFromString(payload)

assert gt is not None

print("\n=== TASK 19.8D GROUND TRUTH INSPECTION ===")
print("Frame:", target_frame)

collections = [
    "moving_object",
    "stationary_object",
    "traffic_sign",
    "traffic_light"
]

matched = []
counts = {}

for name in collections:
    if not hasattr(gt, name):
        continue

    objects = getattr(gt, name)
    counts[name] = len(objects)

    print(f"{name}: {len(objects)} entries")

    for obj in objects:
        oid = get_object_id(obj)

        if oid in target_ids:
            item = {
                "id": oid,
                "collection": name,
                "data": MessageToDict(
                    obj,
                    preserving_proto_field_name=True
                )
            }

            matched.append(item)

            print(f"\nMATCH: ID {oid}, collection={name}")
            print(json.dumps(item, indent=2)[:2500])

found_ids = {item["id"] for item in matched}
missing_ids = sorted(target_ids - found_ids)

report = {
    "scenario": "fog_mor100",
    "frame": target_frame,
    "target_ids": sorted(target_ids),
    "matched_ids": sorted(found_ids),
    "unmatched_ids": missing_ids,
    "collection_counts": counts,
    "matches": matched
}

output = (
    base / "05_Raw_Data_References"
    / "task19_8d_frame150_ground_truth_id_matching.json"
)

output.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 19.8D COMPLETE ===")
print("Target IDs:", sorted(target_ids))
print("Matched IDs:", sorted(found_ids))
print("Unmatched IDs:", missing_ids)
print("JSON saved:", output.is_file())
