import csv
import math
import struct
import statistics
from pathlib import Path

from osi3 import osi_sensorview_pb2

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi"
)

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

OUTPUT = (
    TASK / "02_CSV_Data"
    / "task23_11D_clear_lidar_frame_metrics.csv"
)

C = 299792458.0
MIN_RANGE = 0.05
MAX_RANGE = 200.0

rows = []
previous_time = None

with SOURCE.open("rb") as file:

    frame = 0

    while True:
        header = file.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI frame header")

        size = struct.unpack("<I", header)[0]

        if size <= 0 or size > 100_000_000:
            raise RuntimeError("Invalid frame payload size")

        payload = file.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI frame payload")

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        if not message.HasField("timestamp"):
            raise RuntimeError("Missing observation timestamp")

        frame += 1

        timestamp_ns = (
            message.timestamp.seconds * 1_000_000_000
            + message.timestamp.nanos
        )

        interval_ms = (
            (timestamp_ns - previous_time) / 1_000_000
            if previous_time is not None
            else ""
        )

        if previous_time is not None and timestamp_ns <= previous_time:
            raise RuntimeError("Non-monotonic timestamp")

        previous_time = timestamp_ns

        ray_slots = 0
        positive = 0
        ranges = []

        for lidar in message.lidar_sensor_view:

            for reflection in lidar.reflection:

                ray_slots += 1

                tof = float(reflection.time_of_flight)
                strength = float(reflection.signal_strength)

                finite = (
                    math.isfinite(tof)
                    and math.isfinite(strength)
                )

                valid_positive = (
                    finite
                    and tof > 0
                    and strength > 0
                )

                if valid_positive:
                    positive += 1

                    distance = C * tof / 2.0

                    if MIN_RANGE <= distance <= MAX_RANGE:
                        ranges.append(distance)

        accepted = len(ranges)

        rows.append({
            "Frame": frame,
            "TimestampNS": timestamp_ns,
            "IntervalMS": interval_ms,
            "RaySlots": ray_slots,
            "PositiveReturns": positive,
            "ScreenedReturns": accepted,
            "CoveragePct": (
                100 * accepted / ray_slots
                if ray_slots else 0
            ),
            "MinRangeM": min(ranges) if ranges else "",
            "MedianRangeM": (
                statistics.median(ranges)
                if ranges else ""
            ),
            "MeanRangeM": (
                statistics.mean(ranges)
                if ranges else ""
            ),
            "MaxRangeM": max(ranges) if ranges else "",
        })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=list(rows[0].keys())
    )

    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 23.11.D CLEAR BASELINE ===")
print("Frames processed:", len(rows))
print("Total ray slots:", sum(r["RaySlots"] for r in rows))
print("Positive returns:", sum(r["PositiveReturns"] for r in rows))
print("Screened returns:", sum(r["ScreenedReturns"] for r in rows))
print(
    "Mean coverage:",
    round(statistics.mean(r["CoveragePct"] for r in rows), 4),
    "%"
)
print("First frame coverage:", round(rows[0]["CoveragePct"], 4), "%")
print("Last frame coverage:", round(rows[-1]["CoveragePct"], 4), "%")
print("CSV:", OUTPUT)
