import csv
import math
import struct
import sys
from pathlib import Path
from statistics import mean, median

from osi3.osi_groundtruth_pb2 import GroundTruth

gt_path = Path(sys.argv[1])
comparison_path = Path(sys.argv[2])
output_path = Path(sys.argv[3])

TARGET_ID = 76897
TOTAL_FRAMES = 2122

with comparison_path.open(newline="", encoding="utf-8-sig") as f:
    comparisons = list(csv.DictReader(f))

if len(comparisons) != 23:
    raise RuntimeError("Expected 23 GT center-reference rows")

by_frame = {int(r["frame"]): r for r in comparisons}
if len(by_frame) != len(comparisons):
    raise RuntimeError("Duplicate comparison frame")

gt_objects = {}

with gt_path.open("rb") as f:
    for frame in range(TOTAL_FRAMES):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Incomplete GT header")

        size = struct.unpack("<I", header)[0]
        if not (0 < size < 100_000_000):
            raise RuntimeError("Invalid GT message size")

        if frame not in by_frame:
            f.seek(size, 1)
            continue

        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Incomplete GT payload")

        gt = GroundTruth()
        gt.ParseFromString(payload)

        objects = [
            obj for obj in gt.moving_object
            if int(obj.id.value) == TARGET_ID
        ]

        if len(objects) != 1:
            raise RuntimeError(
                f"Unexpected target count at frame {frame}"
            )

        gt_objects[frame] = objects[0]

    if f.read(1):
        raise RuntimeError("Unexpected trailing GT data")

if set(gt_objects) != set(by_frame):
    raise RuntimeError("Missing GT evaluation frames")

results = []
missing_dimensions = []

for frame in sorted(by_frame):
    r = by_frame[frame]
    obj = gt_objects[frame]
    dimensions = obj.base.dimension

    length = float(dimensions.length)
    width = float(dimensions.width)
    target_yaw = float(obj.base.orientation.yaw)
    ego_yaw = float(r["ego_yaw_rad"])

    if not (
        math.isfinite(length)
        and math.isfinite(width)
        and 0.5 <= length <= 30.0
        and 0.3 <= width <= 10.0
    ):
        missing_dimensions.append(frame)
        continue

    relative_yaw = math.atan2(
        math.sin(target_yaw - ego_yaw),
        math.cos(target_yaw - ego_yaw)
    )

    gt_x = float(r["gt_center_x_ego_m"])
    gt_y = float(r["gt_center_y_ego_m"])

    # Rear-face center, assuming object length is along its
    # longitudinal heading. This is an approximation only.
    rear_x = gt_x - 0.5 * length * math.cos(relative_yaw)
    rear_y = gt_y - 0.5 * length * math.sin(relative_yaw)

    # The facing direction matters: rear face may not be
    # the actual LiDAR-visible surface in every frame.
    estimator_positions = {
        name: (
            gt_x + float(r[f"{name}_x_error_m"]),
            gt_y + float(r[f"{name}_y_error_m"])
        )
        for name in ("lidar", "radar", "camera")
    }

    out = {
        "frame": frame,
        "target_id_evaluation_only": TARGET_ID,
        "gt_length_m": length,
        "gt_width_m": width,
        "relative_yaw_deg": math.degrees(relative_yaw),
        "gt_center_x_m": gt_x,
        "gt_center_y_m": gt_y,
        "approx_rear_face_x_m": rear_x,
        "approx_rear_face_y_m": rear_y,
        "reference_type": "APPROXIMATE_GT_REAR_FACE",
    }

    for name, (x, y) in estimator_positions.items():
        out[f"{name}_center_error_m"] = math.hypot(
            x - gt_x, y - gt_y
        )
        out[f"{name}_rear_face_error_m"] = math.hypot(
            x - rear_x, y - rear_y
        )

    results.append(out)

if not results:
    raise RuntimeError(
        "GT target dimensions unavailable; cannot test offset"
    )

with output_path.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

print("=== TASK 24.10.3B RESULTS ===")
print("EVALUATION_FRAMES=", len(comparisons))
print("DIMENSION_VALID_FRAMES=", len(results))
print("DIMENSION_MISSING_FRAMES=", missing_dimensions)

print("GT_LENGTH_RANGE_M=", (
    round(min(r["gt_length_m"] for r in results), 4),
    round(max(r["gt_length_m"] for r in results), 4)
))

print("GT_WIDTH_RANGE_M=", (
    round(min(r["gt_width_m"] for r in results), 4),
    round(max(r["gt_width_m"] for r in results), 4)
))

print("RELATIVE_YAW_RANGE_DEG=", (
    round(min(r["relative_yaw_deg"] for r in results), 3),
    round(max(r["relative_yaw_deg"] for r in results), 3)
))

for name in ("lidar", "radar", "camera"):
    center = [r[f"{name}_center_error_m"] for r in results]
    rear = [r[f"{name}_rear_face_error_m"] for r in results]

    print()
    print("ESTIMATOR=", name.upper())
    print("MEAN_CENTER_ERROR_M=", round(mean(center), 6))
    print("MEAN_APPROX_REAR_FACE_ERROR_M=", round(mean(rear), 6))
    print("MEDIAN_APPROX_REAR_FACE_ERROR_M=",
          round(median(rear), 6))

print()
print("=== SELECTED FRAME COMPARISONS ===")

for r in results:
    if r["frame"] in (245, 530, 816, 938):
        print(
            f"FRAME={r['frame']} "
            f"LENGTH={r['gt_length_m']:.3f} "
            f"YAW_DIFF_DEG={r['relative_yaw_deg']:.3f} "
            f"RADAR_CENTER_ERROR={r['radar_center_error_m']:.3f} "
            f"RADAR_REAR_FACE_ERROR={r['radar_rear_face_error_m']:.3f}"
        )

print()
print("OUTPUT=", output_path)
print("GROUND_TRUTH_USED_FOR_TRACKING=NO")
print("EKF_STATES_MODIFIED=NO")
print("REAR_FACE_IS_APPROXIMATION=YES")
print("RESULT_IS_NOT_INDEPENDENT_TRACKER_IMPROVEMENT=YES")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_10_03B_SURFACE_DIAGNOSTIC_COMPLETE")