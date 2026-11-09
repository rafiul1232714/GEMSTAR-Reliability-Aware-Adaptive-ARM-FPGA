import csv
import math
import struct
import sys
from pathlib import Path
from statistics import mean, median

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

sv_path = Path(sys.argv[1])
gt_path = Path(sys.argv[2])
comparison_path = Path(sys.argv[3])
output_path = Path(sys.argv[4])
report_path = Path(sys.argv[5])

TARGET_ID = 76897
EXPECTED_HOST_ID = 76894
EXPECTED_FRAMES = 2122

with comparison_path.open(newline="", encoding="utf-8-sig") as f:
    estimates = list(csv.DictReader(f))

if len(estimates) != 24:
    raise RuntimeError("Expected 24 matched estimator observations")

by_frame = {}
for row in estimates:
    frame = int(row["frame"])
    if frame in by_frame:
        raise RuntimeError(f"Duplicate estimator frame {frame}")
    by_frame[frame] = row

wanted = set(by_frame)

def read_selected(path, cls):
    result = {}
    with path.open("rb") as f:
        for frame in range(EXPECTED_FRAMES):
            header = f.read(4)
            if len(header) != 4:
                raise RuntimeError(f"Incomplete header: frame {frame}")

            size = struct.unpack("<I", header)[0]
            if not (0 < size < 100_000_000):
                raise RuntimeError(f"Invalid message size: frame {frame}")

            if frame not in wanted:
                f.seek(size, 1)
                continue

            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError(f"Incomplete payload: frame {frame}")

            message = cls()
            message.ParseFromString(payload)
            result[frame] = message

        if f.read(1):
            raise RuntimeError("Unexpected data beyond 2122 frames")

    if set(result) != wanted:
        raise RuntimeError("Not all estimator frames were found")

    return result

sv_data = read_selected(sv_path, SensorView)
gt_data = read_selected(gt_path, GroundTruth)

results = []
skipped = []

for frame in sorted(wanted):
    row = by_frame[frame]
    sv = sv_data[frame]
    gt = gt_data[frame]

    t = float(row["time_s"])
    sv_t = sv.timestamp.seconds + sv.timestamp.nanos * 1e-9
    gt_t = gt.timestamp.seconds + gt.timestamp.nanos * 1e-9

    if abs(sv_t - t) > 1e-6 or abs(gt_t - t) > 1e-6:
        raise RuntimeError(f"Timestamp mismatch at frame {frame}")

    embedded = sv.global_ground_truth
    host_id = int(embedded.host_vehicle_id.value)

    host = [
        o for o in embedded.moving_object
        if int(o.id.value) == host_id
    ]

    target = [
        o for o in gt.moving_object
        if int(o.id.value) == TARGET_ID
    ]

    if host_id != EXPECTED_HOST_ID or not host or len(target) != 1:
        skipped.append((frame, "HOST_OR_TARGET_UNAVAILABLE"))
        continue

    ego = host[0].base

    # Ensure duplicated ego observations agree within this frame.
    if not all(
        abs(h.base.position.x - ego.position.x) < 1e-6
        and abs(h.base.position.y - ego.position.y) < 1e-6
        and abs(h.base.orientation.yaw - ego.orientation.yaw) < 1e-6
        for h in host
    ):
        raise RuntimeError(f"Inconsistent ego pose: frame {frame}")

    p = target[0].base.position
    dx = p.x - ego.position.x
    dy = p.y - ego.position.y
    yaw = ego.orientation.yaw

    gx = math.cos(yaw) * dx + math.sin(yaw) * dy
    gy = -math.sin(yaw) * dx + math.cos(yaw) * dy

    out = {
        "frame": frame,
        "time_s": t,
        "eval_target_id": TARGET_ID,
        "ego_id": host_id,
        "gt_center_x_ego_m": gx,
        "gt_center_y_ego_m": gy,
        "ego_yaw_rad": yaw,
        "comparison_reference": "GT_OBJECT_CENTER",
    }

    estimators = {
        "lidar": ("lidar_only_x_m", "lidar_only_y_m"),
        "radar": ("lidar_radar_x_m", "lidar_radar_y_m"),
        "camera": ("three_sensor_x_m", "three_sensor_y_m"),
    }

    for name, (xc, yc) in estimators.items():
        x = float(row[xc])
        y = float(row[yc])

        ex = x - gx
        ey = y - gy

        out[f"{name}_x_error_m"] = ex
        out[f"{name}_y_error_m"] = ey
        out[f"{name}_center_error_m"] = math.hypot(ex, ey)

    out["camera_minus_radar_center_error_m"] = (
        out["camera_center_error_m"]
        - out["radar_center_error_m"]
    )

    results.append(out)

if not results:
    raise RuntimeError("No valid GT comparisons")

with output_path.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

lines = [
    "TASK 24.10.3A — GT CENTER REFERENCE COMPARISON",
    "=" * 55,
    f"Matched estimator observations: {len(estimates)}",
    f"Evaluated GT frames: {len(results)}",
    f"Skipped frames: {skipped}",
    f"Evaluation target ID: {TARGET_ID}",
    "Reference: GT object center transformed to ego frame",
    "",
]

print("=== TASK 24.10.3A RESULTS ===")
print("ESTIMATOR_OBSERVATIONS=", len(estimates))
print("GT_FRAMES_EVALUATED=", len(results))
print("SKIPPED_FRAMES=", skipped)

for name in ("lidar", "radar", "camera"):
    errors = [r[f"{name}_center_error_m"] for r in results]
    x_errors = [r[f"{name}_x_error_m"] for r in results]
    y_errors = [r[f"{name}_y_error_m"] for r in results]

    lines.extend([
        f"{name.upper()} ESTIMATOR",
        f"Mean center error (m): {mean(errors):.6f}",
        f"Median center error (m): {median(errors):.6f}",
        f"Maximum center error (m): {max(errors):.6f}",
        f"Final center error (m): {errors[-1]:.6f}",
        f"Mean signed X error (m): {mean(x_errors):.6f}",
        f"Mean signed Y error (m): {mean(y_errors):.6f}",
        "",
    ])

    print()
    print("ESTIMATOR=", name.upper())
    print("MEAN_GT_CENTER_ERROR_M=", round(mean(errors), 6))
    print("MEDIAN_GT_CENTER_ERROR_M=", round(median(errors), 6))
    print("MAX_GT_CENTER_ERROR_M=", round(max(errors), 6))
    print("FINAL_GT_CENTER_ERROR_M=", round(errors[-1], 6))
    print("MEAN_SIGNED_X_ERROR_M=", round(mean(x_errors), 6))
    print("MEAN_SIGNED_Y_ERROR_M=", round(mean(y_errors), 6))

camera_rows = [r for r in results if r["frame"] == 530]
if len(camera_rows) != 1:
    raise RuntimeError("Missing frame 530 comparison")

change = camera_rows[0]["camera_minus_radar_center_error_m"]

print()
print("FRAME530_CAMERA_MINUS_RADAR_ERROR_M=", round(change, 8))
print("FRAME530_CAMERA_ERROR_DIRECTION=",
      "LOWER" if change < 0 else
      "HIGHER" if change > 0 else "UNCHANGED")

print("\n=== SELECTED FRAME ERRORS ===")
for r in results:
    if r["frame"] in (245, 530, 816, 938):
        print(
            f"FRAME={r['frame']} "
            f"GT_CENTER=({r['gt_center_x_ego_m']:.3f},"
            f"{r['gt_center_y_ego_m']:.3f}) "
            f"LIDAR_ERR={r['lidar_center_error_m']:.3f} "
            f"RADAR_ERR={r['radar_center_error_m']:.3f} "
            f"CAMERA_ERR={r['camera_center_error_m']:.3f}"
        )

lines.extend([
    "IMPORTANT LIMITATIONS",
    "Errors are relative to the GT object center.",
    "LiDAR clusters may represent visible object surfaces.",
    "A systematic surface-to-center offset is not corrected.",
    "Evaluation object ID was chosen for diagnostic comparison.",
    "Correspondence requires independent validation.",
    "No GT information was used to alter EKF estimates.",
    "No velocity accuracy was evaluated.",
    "Camera calibration and noise are not validated.",
    "",
    "NEXT: validate target correspondence and surface bias",
    "before interpreting these values as tracker accuracy.",
])

with report_path.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print()
print("OUTPUT_CSV=", output_path)
print("REPORT=", report_path)
print("GT_USED_TO_UPDATE_FILTER=NO")
print("OBJECT_CENTER_BIAS_CORRECTED=NO")
print("VELOCITY_ACCURACY_EVALUATED=NO")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_10_03A_CENTER_COMPARISON_COMPLETE")