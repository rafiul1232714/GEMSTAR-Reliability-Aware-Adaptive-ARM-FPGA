from pathlib import Path
import struct
import sys
import csv

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"
OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")

FILE = OUTPUT / "20261103T152603Z_sv_380_X_1534_GEMSTARADAR.osi"

# Locate existing generated OSI protobuf modules.
module_dirs = []

for module in ROOT.rglob("osi_sensorview_pb2.py"):
    module_dirs.append(module.parent)

for directory in module_dirs:
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

try:
    import osi_sensorview_pb2
except ImportError as exc:
    raise RuntimeError(
        "Generated OSI protobuf modules could not be imported"
    ) from exc

if not FILE.exists():
    raise FileNotFoundError(FILE)

records = []
frames = 0
radar_frames = 0
radar_views = 0
configurations = set()
reflection_counts = []

with FILE.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete message header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise ValueError("Truncated protobuf payload")

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        frames += 1

        radar = list(message.radar_sensor_view)

        if radar:
            radar_frames += 1

        radar_views += len(radar)

        for sensor in radar:
            count = len(sensor.reflection)
            reflection_counts.append(count)

            records.append({
                "Frame": frames,
                "TimestampSeconds": message.timestamp.seconds,
                "TimestampNanos": message.timestamp.nanos,
                "RadarReflections": count
            })

        for cfg in message.radar_sensor_view_configuration:
            configurations.add(str(cfg))

csv_path = TASK / "02_CSV_Data" / "task23_07s_radar_frames.csv"

csv_path.parent.mkdir(parents=True, exist_ok=True)

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Frame",
            "TimestampSeconds",
            "TimestampNanos",
            "RadarReflections"
        ]
    )

    writer.writeheader()
    writer.writerows(records)

print("\n=== TASK 23.7S — RADAR PROTOBUF VALIDATION ===")
print("Total OSI frames:", frames)
print("Frames containing Radar:", radar_frames)
print("Total Radar views:", radar_views)
print("Total Radar reflections:", sum(reflection_counts))
print("Unique Radar configurations:", len(configurations))

for config in sorted(configurations):
    print("\nRADAR CONFIGURATION:")
    print(config[:2000])

print("\nCSV saved:", csv_path)
print("=== TASK 23.7S FINISHED ===")
