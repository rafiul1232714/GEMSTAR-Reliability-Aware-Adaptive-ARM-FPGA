from pathlib import Path
import csv
import struct

from osi3 import osi_sensorview_pb2

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

SOURCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\data\raw\fog_mor100"
    r"\20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUTPUT = BASE / "02_CSV_Data" / "task17_sensor_timestamps.csv"

rows = []
previous_time = None

with SOURCE.open("rb") as f:
    frame = 0

    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI length header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI message payload")

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(payload)

        timestamp = (
            sv.timestamp.seconds
            + sv.timestamp.nanos / 1_000_000_000
        )

        interval = (
            timestamp - previous_time
            if previous_time is not None
            else None
        )

        rows.append({
            "Frame": frame,
            "TimestampSeconds": f"{timestamp:.9f}",
            "IntervalSeconds": (
                f"{interval:.9f}" if interval is not None else ""
            ),
            "CameraEntries": len(sv.camera_sensor_view),
            "LiDAREntries": len(sv.lidar_sensor_view),
            "RadarEntries": len(sv.radar_sensor_view),
            "MessageBytes": size
        })

        previous_time = timestamp
        frame += 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

intervals = [
    float(row["IntervalSeconds"])
    for row in rows
    if row["IntervalSeconds"]
]

print("\n=== TASK 17.3A TIMESTAMP EXTRACTION ===")
print("Frames parsed:", len(rows))
print("First timestamp:", rows[0]["TimestampSeconds"])
print("Last timestamp:", rows[-1]["TimestampSeconds"])
print("Minimum interval:", min(intervals))
print("Maximum interval:", max(intervals))
print("Average interval:", sum(intervals) / len(intervals))
print("Non-positive intervals:", sum(x <= 0 for x in intervals))
print("CSV saved:", OUTPUT)
