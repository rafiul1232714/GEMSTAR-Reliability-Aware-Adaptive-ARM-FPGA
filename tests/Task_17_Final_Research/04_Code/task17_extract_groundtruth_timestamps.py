from pathlib import Path
import csv
import struct

from osi3 import osi_groundtruth_pb2

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

SOURCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\data\raw\fog_mor100"
    r"\20261027T224313Z_gt_380_X_466_GEMSTAR.osi"
)

OUTPUT = BASE / "02_CSV_Data" / "task17_groundtruth_timestamps.csv"

rows = []
previous_time = None

with SOURCE.open("rb") as f:
    frame = 0

    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete GT length header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete GT payload")

        gt = osi_groundtruth_pb2.GroundTruth()
        gt.ParseFromString(payload)

        if not gt.HasField("timestamp"):
            raise RuntimeError(
                f"Missing GT timestamp at frame {frame}"
            )

        timestamp = (
            gt.timestamp.seconds
            + gt.timestamp.nanos / 1_000_000_000
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
            "MovingObjects": len(gt.moving_object),
            "StationaryObjects": len(gt.stationary_object),
            "MessageBytes": size,
        })

        previous_time = timestamp
        frame += 1

if not rows:
    raise RuntimeError("No GroundTruth messages found")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

intervals = [
    float(row["IntervalSeconds"])
    for row in rows
    if row["IntervalSeconds"]
]

print("\n=== TASK 17.4A GROUNDTRUTH TIMESTAMPS ===")
print("GT frames parsed:", len(rows))
print("First GT timestamp:", rows[0]["TimestampSeconds"])
print("Last GT timestamp:", rows[-1]["TimestampSeconds"])
print("Minimum GT interval:", min(intervals) if intervals else "N/A")
print("Maximum GT interval:", max(intervals) if intervals else "N/A")
print("Non-positive GT intervals:", sum(x <= 0 for x in intervals))
print("CSV saved:", OUTPUT)
