import csv
import math
from pathlib import Path
from statistics import mean, median

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

def load(name):
    with (DIR / name).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

center = load("gt_center_comparison_track2_v1.csv")
surface = load("gt_surface_offset_diagnostic_v1.csv")
baseline = load("lidar_radar_ekf_track2_v1.csv")

if len(center) != 23 or len(surface) != 23 or len(baseline) != 24:
    raise RuntimeError("Unexpected input row counts")

def keyed(rows):
    result = {}
    for row in rows:
        frame = int(row["frame"])
        if frame in result:
            raise RuntimeError(f"Duplicate frame {frame}")
        result[frame] = row
    return result

surfaces = keyed(surface)
ekf = keyed(baseline)
centers = keyed(center)

if set(centers) != set(surfaces):
    raise RuntimeError("Center and surface frames do not match")

def percentile(values, percentage):
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentage / 100
    lo = math.floor(index)
    hi = math.ceil(index)
    return (
        ordered[lo] * (hi - index)
        + ordered[hi] * (index - lo)
        if lo != hi else ordered[lo]
    )

rows = []

for frame in sorted(centers):
    c = centers[frame]
    s = surfaces[frame]
    e = ekf[frame]

    lidar = float(c["lidar_center_error_m"])
    radar = float(c["radar_center_error_m"])
    camera = float(c["camera_center_error_m"])

    result = {
        "frame": frame,
        "time_s": c["time_s"],
        "phase": (
            "BEFORE_CAMERA" if frame < 530
            else "CAMERA_FRAME" if frame == 530
            else "AFTER_CAMERA"
        ),
        "radar_update_status": e["radar_status"],
        "lidar_center_error_m": lidar,
        "radar_center_error_m": radar,
        "camera_center_error_m": camera,
        "radar_improvement_vs_lidar_m": lidar - radar,
        "camera_improvement_vs_radar_m": radar - camera,
        "radar_rear_face_error_m":
            float(s["radar_rear_face_error_m"]),
        "gt_length_m": float(s["gt_length_m"]),
        "gt_width_m": float(s["gt_width_m"]),
        "relative_yaw_deg": float(s["relative_yaw_deg"]),
        "radar_x_error_m": float(c["radar_x_error_m"]),
        "radar_y_error_m": float(c["radar_y_error_m"])
    }
    rows.append(result)

with (DIR / "gt_robustness_per_frame_v1.csv").open(
    "x", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

def summarize(group, title):
    if not group:
        return [f"{title}: NO_FRAMES"]

    improvement = [
        r["radar_improvement_vs_lidar_m"] for r in group
    ]
    camera_delta = [
        r["camera_improvement_vs_radar_m"] for r in group
    ]

    return [
        title,
        f"  Frames: {len(group)}",
        f"  Mean Radar improvement (m): {mean(improvement):.7f}",
        f"  Median Radar improvement (m): {median(improvement):.7f}",
        f"  Radar improved frames: {sum(v > 1e-6 for v in improvement)}",
        f"  Radar worsened frames: {sum(v < -1e-6 for v in improvement)}",
        f"  Radar approximately unchanged: {sum(abs(v) <= 1e-6 for v in improvement)}",
        f"  Mean Camera improvement (m): {mean(camera_delta):.7f}",
        ""
    ]

lidar_errors = [r["lidar_center_error_m"] for r in rows]
radar_errors = [r["radar_center_error_m"] for r in rows]
camera_errors = [r["camera_center_error_m"] for r in rows]
rear_errors = [r["radar_rear_face_error_m"] for r in rows]

lines = [
    "TASK 24.10.4 - ROBUSTNESS AND ERROR DISTRIBUTION",
    "=" * 58,
    f"Evaluated frames: {len(rows)}",
    "Reference: Ground Truth object center in ego frame",
    "Ego-unavailable frame 0 excluded",
    "",
    "CENTER ERROR DISTRIBUTION"
]

for label, errors in (
    ("LiDAR-only", lidar_errors),
    ("LiDAR-Radar", radar_errors),
    ("Three-sensor", camera_errors)
):
    lines.extend([
        label,
        f"  Mean (m): {mean(errors):.6f}",
        f"  Median (m): {median(errors):.6f}",
        f"  P95 (m): {percentile(errors,95):.6f}",
        f"  Maximum (m): {max(errors):.6f}",
        ""
    ])

lines.extend(summarize(rows, "ALL EVALUATED FRAMES"))
lines.extend(summarize(
    [r for r in rows if r["frame"] < 530],
    "BEFORE CAMERA"
))
lines.extend(summarize(
    [r for r in rows if r["frame"] >= 530],
    "CAMERA FRAME AND AFTER"
))
lines.extend(summarize(
    [r for r in rows if r["radar_update_status"] == "ACCEPTED"],
    "FRAMES WITH ACCEPTED RADAR UPDATES"
))

lengths = [r["gt_length_m"] for r in rows]
widths = [r["gt_width_m"] for r in rows]
yaws = [r["relative_yaw_deg"] for r in rows]

lines.extend([
    "GROUND TRUTH GEOMETRY",
    f"  Length min/max (m): {min(lengths):.5f} / {max(lengths):.5f}",
    f"  Width min/max (m): {min(widths):.5f} / {max(widths):.5f}",
    f"  Relative yaw min/max (deg): {min(yaws):.3f} / {max(yaws):.3f}",
    f"  Mean approximate rear-face error (m): {mean(rear_errors):.6f}",
    "",
    "INTERPRETATION LIMITATIONS",
    "Rear-face comparison is not a calibrated surface-accuracy metric.",
    "Recorded dimensions vary and need source-level explanation.",
    "Only one recording and one provisional target track were evaluated.",
    "The 23 samples are temporally correlated, not independent trials.",
    "Noise covariance assumptions are uncalibrated.",
    "No full covariance consistency test (NEES) is performed.",
    "No velocity Ground Truth accuracy test is performed.",
    "No full-rate tracking or independent scenario replication.",
    "No energy or hardware measurements are part of this task.",
    "",
    "TASK24_10_04_ROBUSTNESS_COMPLETE"
])

report = DIR / "gt_robustness_summary_v1.txt"
with report.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("=== TASK 24.10.4 RESULTS ===")
print("EVALUATED_FRAMES=", len(rows))
print("RADAR_IMPROVED_FRAMES=", sum(
    r["radar_improvement_vs_lidar_m"] > 1e-6 for r in rows
))
print("RADAR_WORSENED_FRAMES=", sum(
    r["radar_improvement_vs_lidar_m"] < -1e-6 for r in rows
))
print("RADAR_UNCHANGED_FRAMES=", sum(
    abs(r["radar_improvement_vs_lidar_m"]) <= 1e-6 for r in rows
))

print("RADAR_MEAN_IMPROVEMENT_M=", round(
    mean(r["radar_improvement_vs_lidar_m"] for r in rows), 7
))
print("CAMERA_MEAN_IMPROVEMENT_M=", round(
    mean(r["camera_improvement_vs_radar_m"] for r in rows), 7
))
print("RADAR_CENTER_ERROR_P95_M=", round(
    percentile(radar_errors, 95), 6
))
print("RADAR_CENTER_ERROR_MAX_M=", round(max(radar_errors), 6))
print("RADAR_REAR_FACE_ERROR_MEAN_M=", round(
    mean(rear_errors), 6
))
print("GT_LENGTH_VARIATION_M=", round(max(lengths)-min(lengths), 6))
print("GT_WIDTH_VARIATION_M=", round(max(widths)-min(widths), 6))

print("\n=== RADAR IMPROVEMENT BY PHASE ===")
for label, group in (
    ("BEFORE_CAMERA", [r for r in rows if r["frame"] < 530]),
    ("CAMERA_ONWARD", [r for r in rows if r["frame"] >= 530])
):
    print(
        f"{label}: FRAMES={len(group)} "
        f"MEAN_IMPROVEMENT_M="
        f"{mean(r['radar_improvement_vs_lidar_m'] for r in group):.7f}"
    )

print("\n=== ACCEPTED RADAR FRAMES ===")
for r in rows:
    if r["radar_update_status"] == "ACCEPTED":
        print(
            f"FRAME={r['frame']} "
            f"IMPROVEMENT_M={r['radar_improvement_vs_lidar_m']:.6f}"
        )

print("OUTPUT_CSV=", DIR / "gt_robustness_per_frame_v1.csv")
print("REPORT=", report)
print("RESULT_STATUS=DESCRIPTIVE_SINGLE_SEQUENCE_ONLY")
print("GROUND_TRUTH_USED_FOR_FILTER_UPDATE=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_10_04_ROBUSTNESS_COMPLETE")