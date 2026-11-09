from pathlib import Path
import struct
from statistics import mean
from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

SV = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)
GT = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211140Z_gt_380_X_2122_GEMSTAR.osi"
)

def read_timestamps(path, message_class):
    timestamps = []
    missing = 0

    with path.open("rb") as f:
        while True:
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError(f"Incomplete header: {path}")

            size = struct.unpack("<I", header)[0]

            if size == 0:
                raise ValueError(f"Empty message: {path}")

            data = f.read(size)

            if len(data) != size:
                raise ValueError(f"Incomplete payload: {path}")

            message = message_class()
            message.ParseFromString(data)

            if message.HasField("timestamp"):
                timestamp = (
                    message.timestamp.seconds +
                    message.timestamp.nanos / 1e9
                )
                timestamps.append(timestamp)
            else:
                missing += 1
                timestamps.append(None)

    return timestamps, missing

sv_times, sv_missing = read_timestamps(SV, SensorView)
gt_times, gt_missing = read_timestamps(GT, GroundTruth)

def strictly_increasing(values):
    if any(t is None for t in values):
        return False
    return all(b > a for a, b in zip(values, values[1:]))

matched = [
    (s, g)
    for s, g in zip(sv_times, gt_times)
    if s is not None and g is not None
]

offsets_ms = [
    (s - g) * 1000.0
    for s, g in matched
]

abs_offsets_ms = sorted(abs(x) for x in offsets_ms)

def percentile(values, p):
    if not values:
        return None

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower

    return values[lower] * (1 - weight) + values[upper] * weight

print("\n=== SYNCHRONIZATION RESULTS ===")
print("SV_MESSAGES=", len(sv_times))
print("GT_MESSAGES=", len(gt_times))
print("SV_MISSING_TIMESTAMPS=", sv_missing)
print("GT_MISSING_TIMESTAMPS=", gt_missing)
print("SV_STRICTLY_INCREASING=", strictly_increasing(sv_times))
print("GT_STRICTLY_INCREASING=", strictly_increasing(gt_times))
print("MATCHED_INDEX_PAIRS=", len(matched))

if offsets_ms:
    print("MEAN_SIGNED_OFFSET_MS=", round(mean(offsets_ms), 6))
    print("MAX_ABSOLUTE_OFFSET_MS=", round(max(abs_offsets_ms), 6))
    print("MEDIAN_ABSOLUTE_OFFSET_MS=", round(percentile(abs_offsets_ms, 0.5), 6))
    print("P99_ABSOLUTE_OFFSET_MS=", round(percentile(abs_offsets_ms, 0.99), 6))

for i in [0, 530, 1060, 1591, 2121]:
    if i < len(sv_times) and i < len(gt_times):
        s = sv_times[i]
        g = gt_times[i]

        if s is not None and g is not None:
            print(
                f"FRAME={i} "
                f"SV={s:.9f} "
                f"GT={g:.9f} "
                f"DIFF_MS={(s-g)*1000:.6f}"
            )

print("FILES_MODIFIED=NO")

if (
    len(sv_times) == len(gt_times) == 2122
    and sv_missing == 0
    and gt_missing == 0
    and strictly_increasing(sv_times)
    and strictly_increasing(gt_times)
):
    print("TASK24_06_04AR2_TIMESTAMP_INTEGRITY_PASS")
else:
    print("TASK24_06_04AR2_REVIEW_REQUIRED")