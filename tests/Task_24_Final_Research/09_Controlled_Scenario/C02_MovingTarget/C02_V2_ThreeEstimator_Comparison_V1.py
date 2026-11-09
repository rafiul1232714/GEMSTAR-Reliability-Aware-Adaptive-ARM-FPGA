import csv
import math
from pathlib import Path
from statistics import mean
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

CAMERA_FRAME = 530

def load(name):
    with (DIR / name).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

baseline = load("lidar_radar_ekf_track2_v1.csv")
fusion = load("lidar_radar_camera_ekf_track2_v1.csv")

if len(baseline) != 24 or len(fusion) != 24:
    raise RuntimeError("Expected 24 matched observations")

def distance(x1, y1, x2, y2):
    return math.hypot(x1-x2, y1-y2)

rows = []

for a, b in zip(baseline, fusion):
    frame = int(a["frame"])

    if frame != int(b["frame"]):
        raise RuntimeError("Frame mismatch")

    if abs(float(a["time_s"]) - float(b["time_s"])) > 1e-6:
        raise RuntimeError("Timestamp mismatch")

    ax = float(a["lidar_only_x_m"])
    ay = float(a["lidar_only_y_m"])

    bx = float(a["radar_ekf_x_m"])
    by = float(a["radar_ekf_y_m"])

    cx = float(b["camera_aided_x_m"])
    cy = float(b["camera_aided_y_m"])

    ab = distance(ax, ay, bx, by)
    bc = distance(bx, by, cx, cy)
    ac = distance(ax, ay, cx, cy)

    if frame < CAMERA_FRAME and bc > 1e-6:
        raise RuntimeError(
            "Camera changed estimator before Camera update"
        )

    rows.append({
        "frame": frame,
        "time_s": float(a["time_s"]),
        "lidar_only_x_m": ax,
        "lidar_only_y_m": ay,
        "lidar_radar_x_m": bx,
        "lidar_radar_y_m": by,
        "three_sensor_x_m": cx,
        "three_sensor_y_m": cy,
        "lidar_vs_radar_difference_m": ab,
        "radar_vs_camera_aided_difference_m": bc,
        "lidar_vs_camera_aided_difference_m": ac,
        "radar_status": a["radar_status"],
        "camera_status": b["camera_status"],
        "phase": (
            "BEFORE_CAMERA"
            if frame < CAMERA_FRAME else
            "CAMERA_UPDATE"
            if frame == CAMERA_FRAME else
            "AFTER_CAMERA"
        ),
        "ground_truth_error_available": "NO"
    })

if not any(r["frame"] == CAMERA_FRAME for r in rows):
    raise RuntimeError("Camera update frame missing")

pre = [r for r in rows if r["frame"] < CAMERA_FRAME]
post = [r for r in rows if r["frame"] >= CAMERA_FRAME]

if not pre or not post:
    raise RuntimeError("Invalid before/after grouping")

metrics = [
    ("LiDAR vs LiDAR-Radar",
     "lidar_vs_radar_difference_m"),
    ("LiDAR-Radar vs three-sensor",
     "radar_vs_camera_aided_difference_m"),
    ("LiDAR vs three-sensor",
     "lidar_vs_camera_aided_difference_m")
]

print("=== TASK 24.9.7 RESULTS ===")
print("MATCHED_OBSERVATIONS=", len(rows))
print("BEFORE_CAMERA_OBSERVATIONS=", len(pre))
print("FROM_CAMERA_ONWARD_OBSERVATIONS=", len(post))
print("CAMERA_FRAME=", CAMERA_FRAME)

for name, key in metrics:
    values = [r[key] for r in rows]

    print()
    print("COMPARISON=", name)
    print("MEAN_DIFFERENCE_M=", round(mean(values), 7))
    print("MAX_DIFFERENCE_M=", round(max(values), 7))
    print("FINAL_DIFFERENCE_M=", round(values[-1], 7))

print()
print("=== CAMERA EFFECT ===")
print("BEFORE_CAMERA_MAX_DIFFERENCE_M=", round(
    max(r["radar_vs_camera_aided_difference_m"] for r in pre),
    9
))
print("FROM_CAMERA_MAX_DIFFERENCE_M=", round(
    max(r["radar_vs_camera_aided_difference_m"] for r in post),
    7
))

print("CAMERA_UPDATE_FRAME_DIFFERENCE_M=", round(
    next(
        r["radar_vs_camera_aided_difference_m"]
        for r in rows if r["frame"] == CAMERA_FRAME
    ), 7
))

print("RADAR_ACCEPTED_FRAMES=", sum(
    r["radar_status"] == "ACCEPTED" for r in rows
))

print("CAMERA_ACCEPTED_FRAMES=", sum(
    r["camera_status"] == "EXPERIMENTAL_ACCEPTED"
    for r in rows
))

output = DIR / "three_estimator_matched_comparison_v1.csv"

with output.open("x", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

times = [r["time_s"] for r in rows]

fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    times,
    [100 * r["lidar_vs_radar_difference_m"] for r in rows],
    label="LiDAR-only vs LiDAR-Radar",
    marker="o",
    markersize=3
)
ax.plot(
    times,
    [100 * r["radar_vs_camera_aided_difference_m"] for r in rows],
    label="LiDAR-Radar vs Camera-aided",
    marker="s",
    markersize=3
)

camera_time = next(
    r["time_s"] for r in rows if r["frame"] == CAMERA_FRAME
)

ax.axvline(
    camera_time,
    linestyle="--",
    label="Camera update (frame 530)"
)

ax.set_xlabel("Recording time (s)")
ax.set_ylabel("Difference between position estimates (cm)")
ax.set_title("C02 V2: Matched EKF estimator differences")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

plot = DIR / "three_estimator_position_differences_v1.png"
fig.savefig(plot, dpi=180)
plt.close(fig)

report_lines = [
    "TASK 24.9.7 - MATCHED THREE-ESTIMATOR COMPARISON",
    "=" * 58,
    "Recording: clean V2",
    "Track: provisional LiDAR Track 2",
    f"Matched observations: {len(rows)}",
    f"Camera update frame: {CAMERA_FRAME}",
    "",
]

for name, key in metrics:
    values = [r[key] for r in rows]
    report_lines.extend([
        name,
        f"  Mean difference (m): {mean(values):.8f}",
        f"  Maximum difference (m): {max(values):.8f}",
        f"  Final difference (m): {values[-1]:.8f}",
        ""
    ])

report_lines.extend([
    "Radar updates accepted: " + str(sum(
        r["radar_status"] == "ACCEPTED" for r in rows
    )),
    "Camera updates accepted: " + str(sum(
        r["camera_status"] == "EXPERIMENTAL_ACCEPTED"
        for r in rows
    )),
    "",
    "INTERPRETATION",
    "These values measure disagreement between estimators.",
    "They do not measure accuracy against Ground Truth.",
    "Camera detector confidence is low and class is ambiguous.",
    "Camera calibration and noise remain unvalidated.",
    "Radar-LiDAR associations are provisional.",
    "The comparison uses the same 24 observations.",
    "No energy, latency or FPGA measurements are included.",
    "",
    "NEXT: TASK 24.10",
    "Use Ground Truth exclusively for independent evaluation.",
    "Check ego-motion and coordinate alignment.",
    "Evaluate position/velocity error and track association.",
    "Determine if Radar or Camera improves true accuracy.",
    "Validate assumptions and uncertainty.",
])

report = DIR / "three_estimator_comparison_report_v1.txt"

with report.open("x", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print()
print("COMPARISON_CSV=", output)
print("COMPARISON_PLOT=", plot)
print("REPORT=", report)
print("GROUND_TRUTH_ACCURACY_EVALUATED=NO")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_09_07_COMPARISON_COMPLETE")