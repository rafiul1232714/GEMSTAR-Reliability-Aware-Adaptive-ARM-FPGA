import os
import csv
import math
import struct
import bisect
from osi3 import osi_groundtruth_pb2

INPUT = os.environ["C02_KF_INPUT"]
GT_PATH = os.environ["C02_GT_INPUT"]
OUTPUT = os.environ["C02_EVAL_OUTPUT"]

EGO_ID = 71238
TARGET_ID = 71240

with open(INPUT, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise RuntimeError("Empty Kalman CSV")

gt_samples = []
gt_frames = 0

with open(GT_PATH, "rb") as f:
    while True:
        header = f.read(4)
        if not header:
            break
        if len(header) != 4:
            raise RuntimeError("Truncated GT header")

        size = struct.unpack("<I", header)[0]
        if not 0 < size <= 100_000_000:
            raise RuntimeError("Invalid GT record length")

        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Truncated GT message")

        gt = osi_groundtruth_pb2.GroundTruth()
        gt.ParseFromString(payload)
        gt_frames += 1

        t = gt.timestamp.seconds + gt.timestamp.nanos / 1e9

        if t > 29:
            break

        objects = {int(o.id.value): o for o in gt.moving_object}

        if EGO_ID not in objects or TARGET_ID not in objects:
            continue

        ego = objects[EGO_ID].base.position
        target = objects[TARGET_ID].base.position

        radial = math.hypot(
            target.x - ego.x,
            target.y - ego.y
        )

        gt_samples.append((t, radial))

if not gt_samples:
    raise RuntimeError("No matched GT ego/target records")

times = [sample[0] for sample in gt_samples]

def closest_gt(t):
    index = bisect.bisect_left(times, t)
    candidates = [
        gt_samples[i]
        for i in (index - 1, index)
        if 0 <= i < len(gt_samples)
    ]
    return min(candidates, key=lambda v: abs(v[0] - t))

def optional_float(value):
    return float(value) if str(value).strip() else None

result = []

for row in rows:
    t = float(row["sensor_time_s"])
    gt_t, gt_distance = closest_gt(t)

    if abs(gt_t - t) > 0.1:
        raise RuntimeError(
            f"GT timestamp mismatch at {t}: {gt_t}"
        )

    mx = optional_float(row["measurement_x_m"])
    my = optional_float(row["measurement_y_m"])

    raw_distance = (
        math.hypot(mx, my)
        if mx is not None and my is not None
        else None
    )

    kf_distance = math.hypot(
        float(row["kalman_x_m"]),
        float(row["kalman_y_m"])
    )

    result.append({
        "requested_time_s": row["requested_time_s"],
        "sensor_time_s": t,
        "gt_time_s": gt_t,
        "gt_time_difference_s": abs(gt_t - t),
        "status": row["kalman_status"],
        "gt_center_radial_m": gt_distance,
        "raw_lidar_radial_m": raw_distance,
        "kalman_radial_m": kf_distance,
        "raw_change_error_m": None,
        "kalman_change_error_m": None,
        "diagnostic_target_purity":
            row["diagnostic_target_purity"]
    })

first = result[0]

if first["raw_lidar_radial_m"] is None:
    raise RuntimeError("Initial LiDAR measurement unavailable")

gt_initial = first["gt_center_radial_m"]
raw_initial = first["raw_lidar_radial_m"]
kf_initial = first["kalman_radial_m"]

for r in result:
    gt_change = r["gt_center_radial_m"] - gt_initial

    if r["raw_lidar_radial_m"] is not None:
        raw_change = r["raw_lidar_radial_m"] - raw_initial
        r["raw_change_error_m"] = raw_change - gt_change

    kf_change = r["kalman_radial_m"] - kf_initial
    r["kalman_change_error_m"] = kf_change - gt_change

def rmse(values):
    values = list(values)
    if not values:
        return None
    return math.sqrt(sum(v*v for v in values)/len(values))

paired = [
    r for r in result
    if r["raw_change_error_m"] is not None
]

raw_rmse = rmse(r["raw_change_error_m"] for r in paired)
kf_paired_rmse = rmse(
    r["kalman_change_error_m"] for r in paired
)
kf_full_rmse = rmse(
    r["kalman_change_error_m"] for r in result
)

prediction_only = [
    r for r in result
    if r["status"] == "PREDICTED_ONLY"
]

prediction_rmse = rmse(
    r["kalman_change_error_m"] for r in prediction_only
)

fields = list(result[0].keys())

with open(OUTPUT, "x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for r in result:
        writer.writerow({
            key: "" if value is None else value
            for key, value in r.items()
        })

print("GT_FRAMES_READ=", gt_frames)
print("GT_MATCHED_SAMPLES=", len(result))
print("PAIRED_MEASUREMENT_SAMPLES=", len(paired))
print("PREDICTION_ONLY_SAMPLES=", len(prediction_only))

print("\n=== RADIAL CHANGE RMSE ===")
print("RAW_LIDAR_RMSE_M=", round(raw_rmse, 5))
print("KALMAN_PAIRED_RMSE_M=", round(kf_paired_rmse, 5))
print("KALMAN_FULL_SEQUENCE_RMSE_M=", round(kf_full_rmse, 5))
print("KALMAN_PREDICTION_ONLY_RMSE_M=",
      round(prediction_rmse, 5)
      if prediction_rmse is not None else "NONE")

print("\n=== SELECTED SAMPLES ===")
for r in result:
    if float(r["requested_time_s"]) in (
        2, 5, 7, 10, 15, 20, 25, 26, 26.5, 27, 28
    ):
        print(
            "TIME=", r["requested_time_s"],
            "GT_RADIAL_M=", round(r["gt_center_radial_m"], 3),
            "RAW_CHANGE_ERROR_M=",
            round(r["raw_change_error_m"], 3)
            if r["raw_change_error_m"] is not None else "MISSING",
            "KF_CHANGE_ERROR_M=",
            round(r["kalman_change_error_m"], 3),
            "STATUS=", r["status"]
        )

print("\nMETRIC=INITIAL_DISTANCE_ALIGNED_RADIAL_CHANGE")
print("NOT_FULL_2D_POSITION_RMSE=YES")
print("GROUND_TRUTH_USED_BY_FILTER=NO")
print("GROUND_TRUTH_USED_FOR_EVALUATION=YES")
print("NOISE_PARAMETERS_CALIBRATED=NO")
print("OUTPUT_CSV=", OUTPUT)
print("TASK24_05_05A_KALMAN_GT_EVALUATION_COMPLETE")
