import json
import struct
from collections import Counter
from pathlib import Path

from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

assert source.is_file(), f"Missing OSI recording: {source}"

selected = {0, 50, 100, 150, 200, 250, 300,
            350, 400, 423, 424, 450}

def describe(message, depth=0):
    results = []
    for field, value in message.ListFields():
        item = {
            "name": field.name,
            "type": field.type,
            "repeated": field.is_repeated
        }

        if field.is_repeated:
            item["count"] = len(value)
            if len(value) and field.message_type and depth < 3:
                item["first_item_fields"] = describe(value[0], depth + 1)
        elif field.message_type and depth < 3:
            item["fields"] = describe(value, depth + 1)
        elif field.type == field.TYPE_BYTES:
            item["bytes_length"] = len(value)
        else:
            item["value"] = str(value)[:120]

        results.append(item)

    return results

frames = []
payload_counts = Counter()
total_messages = 0

with source.open("rb") as stream:
    while True:
        header = stream.read(4)
        if not header:
            break
        if len(header) != 4:
            raise ValueError("Incomplete OSI record header")

        length = struct.unpack("<I", header)[0]
        if length <= 0 or length > 250_000_000:
            raise ValueError(f"Unexpected record length: {length}")

        data = stream.read(length)
        if len(data) != length:
            raise ValueError("Truncated OSI record")

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(data)

        lidar_views = list(getattr(sv, "lidar_sensor_view", []))
        payload_counts[len(lidar_views)] += 1

        if total_messages in selected:
            entry = {
                "frame": total_messages,
                "lidar_sensor_views": len(lidar_views),
                "fields": [
                    describe(view) for view in lidar_views[:2]
                ]
            }
            frames.append(entry)

            print(
                f"Frame {total_messages}: "
                f"{len(lidar_views)} LiDAR sensor views"
            )

        total_messages += 1

report = {
    "source": str(source),
    "source_bytes": source.stat().st_size,
    "total_sensorview_messages": total_messages,
    "lidar_views_per_message": dict(payload_counts),
    "selected_frame_inspection": frames
}

output = (
    base / "05_Raw_Data_References"
    / "task19_1_lidar_payload_audit.json"
)

output.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 19.1A LIDAR AUDIT ===")
print("Total messages:", total_messages)
print("LiDAR view distribution:", dict(payload_counts))
print("Selected frames inspected:", len(frames))
print("Audit JSON saved:", output.is_file())

if frames:
    print("\nFirst selected frame LiDAR field structure:")
    print(json.dumps(frames[0]["fields"], indent=2)[:6000])
