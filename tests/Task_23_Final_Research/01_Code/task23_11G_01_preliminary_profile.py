import csv
import statistics
import struct
import sys
import time
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView
from task23_11F_lidar_reliability import score_lidar_frame

task = Path(sys.argv[1])
output = Path(r"E:\GEMSTAR_Project\gemstar\Output")

datasets = [
    ("Clear", "20261105T213845Z_sv_380_X_13819_T23_11E_CLEAR.osi"),
    ("Fog100", "20261105T220440Z_sv_380_X_12386_T23_11E_FOG100.osi"),
    ("Fog20", "20261105T215332Z_sv_380_X_14597_T23_11E_FOG20.osi"),
]

result_csv = task / "02_CSV_Data" / "task23_11G_01_preliminary_timing.csv"

if result_csv.exists():
    raise RuntimeError("Timing CSV already exists")

repetitions = 200
warmups = 30

def percentile(values, percent):
    values = sorted(values)
    position = (len(values) - 1) * percent / 100
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)

rows = []

for weather, filename in datasets:
    path = output / filename

    with path.open("rb") as stream:
        header = stream.read(4)
        if len(header) != 4:
            raise RuntimeError(f"{weather}: missing header")

        length = struct.unpack("<I", header)[0]
        if length <= 0:
            raise RuntimeError(f"{weather}: invalid length")

        payload = stream.read(length)
        if len(payload) != length:
            raise RuntimeError(f"{weather}: incomplete payload")

    frame = SensorView()
    frame.ParseFromString(payload)

    if len(frame.lidar_sensor_view) != 1:
        raise RuntimeError(f"{weather}: unexpected LiDAR view count")

    lidar = frame.lidar_sensor_view[0]
    timestamp = frame.timestamp.seconds + frame.timestamp.nanos / 1e9

    for _ in range(warmups):
        score_lidar_frame(lidar, timestamp)

    durations_us = []

    for _ in range(repetitions):
        start = time.perf_counter_ns()
        result = score_lidar_frame(lidar, timestamp)
        end = time.perf_counter_ns()

        durations_us.append((end - start) / 1000)

    if result.total_reflections != 5271:
        raise RuntimeError(f"{weather}: unexpected reflection count")

    mean_us = statistics.mean(durations_us)
    p50_us = statistics.median(durations_us)
    p95_us = percentile(durations_us, 95)
    p99_us = percentile(durations_us, 99)

    rows.append([
        weather, repetitions, result.total_reflections,
        result.positive_returns, result.status,
        f"{mean_us:.3f}", f"{p50_us:.3f}",
        f"{p95_us:.3f}", f"{p99_us:.3f}"
    ])

    print(
        f"{weather}: "
        f"MEAN_US={mean_us:.3f} "
        f"P50_US={p50_us:.3f} "
        f"P95_US={p95_us:.3f} "
        f"P99_US={p99_us:.3f}"
    )

with result_csv.open("x", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "weather", "repetitions", "reflection_slots",
        "positive_returns", "status",
        "mean_us", "p50_us", "p95_us", "p99_us"
    ])
    writer.writerows(rows)

print(f"RESULT_CSV={result_csv}")
print("TASK23_11G_01_PRELIMINARY_PROFILE_PASS")
