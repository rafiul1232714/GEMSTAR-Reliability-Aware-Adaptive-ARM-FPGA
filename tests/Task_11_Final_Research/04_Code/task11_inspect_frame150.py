
# TASK 11.5T - RECONSTRUCT LIDAR FRAME 150
# Uses existing MOR100 LiDAR measurements.
# No simulation rerun required.

import csv
import math
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"
DATA = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

SOURCE = DATA / "task11_lidar_measurements.csv"
OUTPUT = DATA / "task11_lidar_frame150_geometry.csv"

FRAME = 150

H_RAYS = 251
V_RAYS = 21

H_FOV = math.radians(90)
V_FOV = math.radians(20)

# GEMSTAR LiDAR mounting, meters
MOUNT_X = 2.6
MOUNT_Y = 0.0
MOUNT_Z = 0.7

# Predicted vehicle center from provisional GT transform.
TARGET_X = 5.48
TARGET_Y = 2.18

points = []
invalid = 0

assert SOURCE.is_file(), f"Missing input file: {SOURCE}"

with SOURCE.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if int(row["frame"]) != FRAME:
            continue

        r = float(row["range_m"])
        ray = int(row["ray_index"])

        if not math.isfinite(r) or r < 0.1:
            invalid += 1
            continue

        h = ray % H_RAYS
        v = ray // H_RAYS

        if not (0 <= v < V_RAYS):
            invalid += 1
            continue

        theta = -H_FOV / 2 + h * H_FOV / (H_RAYS - 1)
        phi = -V_FOV / 2 + v * V_FOV / (V_RAYS - 1)

        # Reuse the provisional convention from Task 11.
        x = MOUNT_X + r * math.cos(phi) * math.cos(theta)
        y = MOUNT_Y - r * math.cos(phi) * math.sin(theta)
        z = MOUNT_Z + r * math.sin(phi)

        points.append({
            "frame": FRAME,
            "ray_index": ray,
            "range_m": r,
            "x_ego_m": x,
            "y_ego_m": y,
            "z_ego_m": z,
            "signal_strength": row["signal_strength"],
            "object_id_diagnostic": row["object_id_diagnostic"]
        })

assert points, "No valid LiDAR points found in frame 150."

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(points[0].keys())
    )
    writer.writeheader()
    writer.writerows(points)

# Preliminary spatial search only.
# An actual detection must not use the object IDs.

def nearby_count(y_target):
    return sum(
        abs(p["x_ego_m"] - TARGET_X) <= 2.5
        and abs(p["y_ego_m"] - y_target) <= 2.0
        for p in points
    )

positive_y = nearby_count(TARGET_Y)
negative_y = nearby_count(-TARGET_Y)

lines = [
    "TASK 11.5T - FRAME 150 LIDAR INSPECTION",
    f"Valid points: {len(points)}",
    f"Rejected points: {invalid}",
    f"X range: {min(p['x_ego_m'] for p in points):.3f} "
    f"to {max(p['x_ego_m'] for p in points):.3f} m",
    f"Y range: {min(p['y_ego_m'] for p in points):.3f} "
    f"to {max(p['y_ego_m'] for p in points):.3f} m",
    "",
    "Provisional GT vehicle 76865:",
    f"X = {TARGET_X:.2f} m",
    f"Y = {TARGET_Y:.2f} m",
    "",
    "Nearby LiDAR point counts (rectangular XY search):",
    f"At predicted Y = +2.18 m: {positive_y}",
    f"At mirrored Y  = -2.18 m: {negative_y}",
    "",
    "Counts include road and background reflections.",
    "They are not vehicle detections.",
    "Coordinate signs and yaw conventions remain provisional."
]

report = "\n".join(lines)

print("\n" + report)

report_path = FINDINGS / "task11_frame150_initial_inspection.txt"
report_path.write_text(report + "\n", encoding="utf-8")

print("\nSaved:", OUTPUT)
print("Saved:", report_path)
print("TASK 11.5T COMPLETED")
