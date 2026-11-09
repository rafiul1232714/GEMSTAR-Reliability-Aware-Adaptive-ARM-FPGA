import csv
import math
import struct
import sys
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView
from task23_11F_lidar_reliability import score_lidar_frame

TASK = Path(sys.argv[1])
OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")
CSV_DIR = TASK / "02_CSV_Data"

DATASETS = [
    ("Clear", "20261105T213845Z_sv_380_X_13819_T23_11E_CLEAR.osi",
     13819, 5090, "VALID"),
    ("Fog100", "20261105T220440Z_sv_380_X_12386_T23_11E_FOG100.osi",
     12386, 5090, "VALID"),
    ("Fog20", "20261105T215332Z_sv_380_X_14597_T23_11E_FOG20.osi",
     14597, 0, "NO_RETURNS"),
]

DETAIL = CSV_DIR / "task23_11F_04B_frame_reliability.csv"
SUMMARY = CSV_DIR / "task23_11F_04B_reliability_summary.csv"

for path in (DETAIL, SUMMARY):
    if path.exists():
        raise RuntimeError(f"Output already exists: {path}")

for _, name, _, _, _ in DATASETS:
    if not (OUTPUT / name).is_file():
        raise RuntimeError(f"Source recording missing: {name}")

tmp_detail = DETAIL.with_suffix(".csv.partial")
tmp_summary = SUMMARY.with_suffix(".csv.partial")

for path in (tmp_detail, tmp_summary):
    if path.exists():
        raise RuntimeError(f"Partial output already exists: {path}")

summary_rows = []
total_processed = 0

try:
    with tmp_detail.open("w", encoding="utf-8", newline="") as output_csv:
        writer = csv.writer(output_csv)
        writer.writerow([
            "weather",
            "frame_index",
            "timestamp_seconds",
            "status",
            "positive_returns",
            "total_reflections",
            "availability_score"
        ])

        for weather, filename, expected_frames, expected_positive, expected_status in DATASETS:
            source = OUTPUT / filename
            count = 0
            previous_timestamp = None
            score_sum = 0.0
            minimum_score = math.inf
            maximum_score = -math.inf

            print(f"\nSTART={weather}", flush=True)

            with source.open("rb") as stream:
                while True:
                    header = stream.read(4)

                    if not header:
                        break

                    if len(header) != 4:
                        raise RuntimeError(f"{weather}: incomplete frame header")

                    length = struct.unpack("<I", header)[0]

                    if length <= 0:
                        raise RuntimeError(f"{weather}: invalid frame length")

                    payload = stream.read(length)

                    if len(payload) != length:
                        raise RuntimeError(f"{weather}: truncated frame")

                    frame = SensorView()
                    frame.ParseFromString(payload)

                    timestamp = (
                        frame.timestamp.seconds
                        + frame.timestamp.nanos / 1_000_000_000
                    )

                    if len(frame.lidar_sensor_view) != 1:
                        raise RuntimeError(
                            f"{weather} frame {count}: expected one LiDAR view"
                        )

                    result = score_lidar_frame(
                        frame.lidar_sensor_view[0],
                        timestamp,
                        previous_timestamp
                    )

                    if result.status != expected_status:
                        raise RuntimeError(
                            f"{weather} frame {count}: status {result.status}"
                        )

                    if result.positive_returns != expected_positive:
                        raise RuntimeError(
                            f"{weather} frame {count}: unexpected positive count"
                        )

                    if result.total_reflections != 5271:
                        raise RuntimeError(
                            f"{weather} frame {count}: reflection count mismatch"
                        )

                    score = result.availability_score

                    if score is None or not math.isfinite(score):
                        raise RuntimeError(
                            f"{weather} frame {count}: undefined score"
                        )

                    expected_score = expected_positive / 5271

                    if abs(score - expected_score) > 1e-12:
                        raise RuntimeError(
                            f"{weather} frame {count}: score mismatch"
                        )

                    writer.writerow([
                        weather,
                        count,
                        f"{timestamp:.9f}",
                        result.status,
                        result.positive_returns,
                        result.total_reflections,
                        f"{score:.12f}"
                    ])

                    score_sum += score
                    minimum_score = min(minimum_score, score)
                    maximum_score = max(maximum_score, score)

                    previous_timestamp = timestamp
                    count += 1

                    if count % 2000 == 0:
                        print(
                            f"{weather}_PROCESSED={count}",
                            flush=True
                        )

            if count != expected_frames:
                raise RuntimeError(
                    f"{weather}: expected {expected_frames}, found {count}"
                )

            mean_score = score_sum / count

            summary_rows.append([
                weather,
                count,
                expected_positive,
                5271,
                expected_status,
                f"{minimum_score:.12f}",
                f"{mean_score:.12f}",
                f"{maximum_score:.12f}"
            ])

            total_processed += count

            print(f"{weather}_FRAMES={count}")
            print(f"{weather}_MEAN_SCORE={mean_score:.9f}")
            print(f"{weather}_PASS", flush=True)

    if total_processed != 40802:
        raise RuntimeError(
            f"Unexpected total frame count: {total_processed}"
        )

    with tmp_summary.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "weather",
            "frames",
            "positive_returns_per_frame",
            "reflection_slots_per_frame",
            "status",
            "min_score",
            "mean_score",
            "max_score"
        ])
        writer.writerows(summary_rows)

    # Publish final files only after all validations pass.
    # Refuse replacement even if another process created an output.
    for path in (DETAIL, SUMMARY):
        if path.exists():
            raise RuntimeError(f"Output appeared during processing: {path}")

    tmp_detail.rename(DETAIL)
    tmp_summary.rename(SUMMARY)

except Exception:
    for path in (tmp_detail, tmp_summary):
        if path.exists():
            path.unlink()
    raise

print(f"\nTOTAL_PROCESSED_FRAMES={total_processed}")
print(f"FRAME_CSV={DETAIL}")
print(f"SUMMARY_CSV={SUMMARY}")
print("TASK23_11F_04B_FULL_RELIABILITY_PASS")
