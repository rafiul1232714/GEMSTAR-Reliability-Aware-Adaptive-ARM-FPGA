import csv
import random
import statistics
import struct
import sys
import time
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView
from task23_11F_lidar_reliability import score_lidar_frame

task = Path(sys.argv[1])
source_dir = Path(r"E:\GEMSTAR_Project\gemstar\Output")

output = (
    task / "02_CSV_Data" /
    "task23_11G_02A_raw_timing_distribution.csv"
)

if output.exists():
    raise RuntimeError("Raw timing CSV already exists")

datasets = [
    ("Clear", "20261105T213845Z_sv_380_X_13819_T23_11E_CLEAR.osi"),
    ("Fog100", "20261105T220440Z_sv_380_X_12386_T23_11E_FOG100.osi"),
    ("Fog20", "20261105T215332Z_sv_380_X_14597_T23_11E_FOG20.osi"),
]

frames = {}

for weather, filename in datasets:
    with (source_dir / filename).open("rb") as stream:
        header = stream.read(4)

        if len(header) != 4:
            raise RuntimeError(f"{weather}: invalid header")

        length = struct.unpack("<I", header)[0]

        if length <= 0:
            raise RuntimeError(f"{weather}: invalid frame length")

        payload = stream.read(length)

        if len(payload) != length:
            raise RuntimeError(f"{weather}: truncated frame")

    frame = SensorView()
    frame.ParseFromString(payload)

    if len(frame.lidar_sensor_view) != 1:
        raise RuntimeError(f"{weather}: expected one LiDAR view")

    lidar = frame.lidar_sensor_view[0]
    timestamp = frame.timestamp.seconds + frame.timestamp.nanos / 1e9

    frames[weather] = (lidar, timestamp)

rng = random.Random(23011)
records = []
rounds = 3
repetitions = 200

for round_number in range(1, rounds + 1):
    order = list(frames)
    rng.shuffle(order)

    print(f"ROUND={round_number} ORDER={','.join(order)}")

    for weather in order:
        lidar, timestamp = frames[weather]

        for _ in range(30):
            score_lidar_frame(lidar, timestamp)

        durations = []

        for repetition in range(1, repetitions + 1):
            start = time.perf_counter_ns()

            result = score_lidar_frame(lidar, timestamp)

            elapsed = time.perf_counter_ns() - start
            duration_us = elapsed / 1000.0

            if result.total_reflections != 5271:
                raise RuntimeError("Reflection count mismatch")

            if result.availability_score is None:
                raise RuntimeError("Unexpected undefined score")

            durations.append(duration_us)

            records.append([
                round_number,
                weather,
                repetition,
                f"{duration_us:.3f}",
                result.status
            ])

        print(
            f"{weather} ROUND={round_number} "
            f"MEAN_US={statistics.mean(durations):.3f} "
            f"MEDIAN_US={statistics.median(durations):.3f}"
        )

expected_count = rounds * repetitions * len(datasets)

if len(records) != expected_count:
    raise RuntimeError("Unexpected measurement count")

with output.open("x", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "round",
        "weather",
        "repetition",
        "duration_us",
        "status"
    ])

    writer.writerows(records)

print(f"TOTAL_MEASUREMENTS={len(records)}")
print(f"RAW_TIMING_CSV={output}")
print("TASK23_11G_02A_TIMING_DISTRIBUTION_PASS")
