from pathlib import Path
import struct
from osi3.osi_groundtruth_pb2 import GroundTruth

path = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211140Z_gt_380_X_2122_GEMSTAR.osi"
)

count = 0
moving_frames = 0
stationary_frames = 0
timestamps = []
max_moving = 0
max_stationary = 0

with path.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete Ground Truth header")

        length = struct.unpack("<I", header)[0]

        if length == 0:
            raise ValueError("Empty Ground Truth message")

        payload = f.read(length)

        if len(payload) != length:
            raise ValueError("Incomplete Ground Truth payload")

        gt = GroundTruth()
        gt.ParseFromString(payload)

        count += 1

        moving = len(gt.moving_object)
        stationary = len(gt.stationary_object)

        moving_frames += moving > 0
        stationary_frames += stationary > 0

        max_moving = max(max_moving, moving)
        max_stationary = max(max_stationary, stationary)

        if gt.HasField("timestamp"):
            t = gt.timestamp.seconds + gt.timestamp.nanos / 1e9
            timestamps.append(t)

        if count <= 3:
            print(
                f"GT_MESSAGE={count} "
                f"MOVING={moving} "
                f"STATIONARY={stationary}"
            )

monotonic = all(
    b >= a for a, b in zip(timestamps, timestamps[1:])
)

strictly_increasing = all(
    b > a for a, b in zip(timestamps, timestamps[1:])
)

print("\n=== GROUND TRUTH RESULTS ===")
print("TOTAL_GT_MESSAGES=", count)
print("TIMESTAMPED_MESSAGES=", len(timestamps))
print("TIMESTAMPS_MONOTONIC=", monotonic)
print("TIMESTAMPS_STRICTLY_INCREASING=", strictly_increasing)
print("FRAMES_WITH_MOVING_OBJECTS=", moving_frames)
print("FRAMES_WITH_STATIONARY_OBJECTS=", stationary_frames)
print("MAX_MOVING_OBJECTS=", max_moving)
print("MAX_STATIONARY_OBJECTS=", max_stationary)

if timestamps:
    print("FIRST_TIMESTAMP_SECONDS=", timestamps[0])
    print("LAST_TIMESTAMP_SECONDS=", timestamps[-1])
    print("GT_DURATION_SECONDS=", timestamps[-1] - timestamps[0])

print("GT_FILE_MODIFIED=NO")

if count > 0 and len(timestamps) == count and monotonic:
    print("TASK24_06_04AR1_GT_INTEGRITY_PASS")
else:
    print("TASK24_06_04AR1_GT_INTEGRITY_REVIEW_REQUIRED")