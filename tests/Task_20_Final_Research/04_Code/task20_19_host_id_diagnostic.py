import json
import struct
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
OUT = ROOT / "tests" / "Task_20_Final_Research" / "06_Research_Findings"
OUT.mkdir(parents=True, exist_ok=True)

def read_frames(path, cls, limit=10):
    with path.open("rb") as f:
        for frame in range(limit):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete header")
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid size")
            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Incomplete payload")
            msg = cls()
            msg.ParseFromString(payload)
            yield frame, msg

def timestamp(msg):
    return (
        int(msg.timestamp.seconds) * 1_000_000_000
        + int(msg.timestamp.nanos)
    )

def position(obj):
    p = obj.base.position
    return [round(p.x, 5), round(p.y, 5), round(p.z, 5)]

results = []

print("\n=== TASK 20.19 HOST ID DIAGNOSTIC ===")

for folder in sorted(RAW.iterdir()):
    if not folder.is_dir():
        continue

    sv_files = list(folder.glob("*_sv_*.osi"))
    gt_files = list(folder.glob("*_gt_*.osi"))

    if len(sv_files) != 1:
        continue

    gt_by_timestamp = {}
    if len(gt_files) == 1:
        gt_by_timestamp = {
            timestamp(msg): msg
            for _, msg in read_frames(gt_files[0], GroundTruth)
        }

    printed = 0

    for frame, sv in read_frames(sv_files[0], SensorView):
        if not sv.HasField("global_ground_truth"):
            continue

        ngt = sv.global_ground_truth
        has_host = ngt.HasField("host_vehicle_id")

        nested = [
            {
                "id": int(o.id.value),
                "xyz": position(o),
            }
            for o in ngt.moving_object
        ]

        gt = gt_by_timestamp.get(timestamp(sv))

        global_objects = (
            [
                {
                    "id": int(o.id.value),
                    "xyz": position(o),
                    "model": o.model_reference,
                }
                for o in gt.moving_object
            ]
            if gt is not None else []
        )

        record = {
            "recording": folder.name,
            "frame": frame,
            "timestamp_ns": timestamp(sv),
            "nested_host_id": (
                int(ngt.host_vehicle_id.value)
                if has_host else None
            ),
            "nested_objects": nested,
            "standalone_gt_objects": global_objects,
        }

        results.append(record)

        print("\nRecording:", folder.name, "Frame:", frame)
        print("Nested host ID:", record["nested_host_id"])
        print("Nested objects:", nested)
        print("Standalone GT objects:", global_objects)

        printed += 1
        if printed >= 3:
            break

path = OUT / "task20_19_host_id_diagnostic.json"
path.write_text(json.dumps(results, indent=2), encoding="utf-8")

print("\n=== TASK 20.19 COMPLETE ===")
print("Frames inspected:", len(results))
print("Report saved:", path.is_file())
print("Report:", path)
print("Ego identity verified:", False)
