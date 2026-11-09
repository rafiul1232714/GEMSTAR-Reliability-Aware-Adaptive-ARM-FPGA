import csv
import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

targets = {0, 50, 100, 150, 200, 250, 350, 450}

assert source.is_file(), f"Recording missing: {source}"

rows = []
frame_index = 0

print("\n=== TASK 19.10A MULTI-FRAME LIDAR AUDIT ===")

with source.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete record header")

        length = struct.unpack("<I", header)[0]

        if not 0 < length < 100_000_000:
            raise RuntimeError(
                f"Invalid record length at frame {frame_index}"
            )

        if frame_index not in targets:
            f.seek(length, 1)
            frame_index += 1
            continue

        payload = f.read(length)

        if len(payload) != length:
            raise RuntimeError("Truncated SensorView message")

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(payload)

        lidar_count = len(sv.lidar_sensor_view)

        for sensor_index, lidar in enumerate(sv.lidar_sensor_view):

            repeated_fields = []

            for descriptor, value in lidar.ListFields():
                if descriptor.is_repeated:
                    repeated_fields.append(
                        f"{descriptor.name}:{len(value)}"
                    )

            row = {
                "FrameIndex": frame_index,
                "SensorIndex": sensor_index,
                "SensorCountInFrame": lidar_count,
                "RecordBytes": length,
                "RepeatedFields": "; ".join(repeated_fields),
            }

            rows.append(row)

            print(
                f"Frame {frame_index:3d}: "
                f"LiDAR sensor {sensor_index}, "
                f"record bytes {length:,}, "
                f"fields {row['RepeatedFields']}"
            )

        if lidar_count == 0:
            print(f"Frame {frame_index}: NO LIDAR SENSOR VIEW")

        frame_index += 1

output = (
    base / "02_CSV_Data"
    / "task19_10a_multiframe_lidar_audit.csv"
)

output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "FrameIndex",
            "SensorIndex",
            "SensorCountInFrame",
            "RecordBytes",
            "RepeatedFields",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 19.10A COMPLETE ===")
print("Total SensorView records:", frame_index)
print("Selected frame records with LiDAR:", len(rows))
print("CSV saved:", output.is_file())
