
# TASK 11.5W - LIDAR VEHICLE VISIBILITY DIAGNOSTIC
# Frame 150, Ground Truth candidate 76865
# No third-party packages required.

import csv
import math
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"
DATA = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

SOURCE = DATA / "task11_lidar_frame150_geometry.csv"

# Provisional GT ego-relative vehicle center
TARGET_X = 5.48
TARGET_Y = 2.18

# Recorded LiDAR mount
LIDAR_X = 2.6
LIDAR_Y = 0.0
LIDAR_Z = 0.7

H_RAYS = 251
H_STEP_DEG = 90.0 / 250.0

dx = TARGET_X - LIDAR_X
dy = TARGET_Y - LIDAR_Y

expected_distance = math.hypot(dx, dy)

# Test both possible lateral-axis conventions.
angle_positive = math.degrees(math.atan2(dy, dx))
angle_negative = -angle_positive

points = []

with SOURCE.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        points.append({
            "ray": int(row["ray_index"]),
            "range": float(row["range_m"]),
            "x": float(row["x_ego_m"]),
            "y": float(row["y_ego_m"]),
            "z": float(row["z_ego_m"]),
            "id": row["object_id_diagnostic"]
        })

def inspect_direction(target_angle):
    selected = []

    for p in points:
        h = p["ray"] % H_RAYS
        angle = -45.0 + h * H_STEP_DEG

        if abs(angle - target_angle) <= 10.0:
            selected.append(p)

    selected.sort(key=lambda p: p["range"])

    return selected

report = [
    "TASK 11.5W - LIDAR VISIBILITY",
    "Frame: 150",
    "GT candidate: 76865",
    "GT position: provisional",
    "",
    f"LiDAR mount X: {LIDAR_X:.2f} m",
    f"Vehicle center X: {TARGET_X:.2f} m",
    f"Vehicle center Y: {TARGET_Y:.2f} m",
    f"Expected horizontal distance from LiDAR: "
    f"{expected_distance:.3f} m",
    f"Expected +Y bearing: {angle_positive:.2f} deg",
    f"Expected -Y bearing: {angle_negative:.2f} deg",
    "",
    "Measured LiDAR minimum range: "
    f"{min(p['range'] for p in points):.3f} m",
    ""
]

for title, angle in [
    ("POSITIVE-Y DIRECTION", angle_positive),
    ("MIRRORED-Y DIRECTION", angle_negative)
]:
    selected = inspect_direction(angle)

    report.append(title)
    report.append(f"Points in +/-10 deg: {len(selected)}")

    if selected:
        report.append(
            f"Minimum return range: "
            f"{selected[0]['range']:.3f} m"
        )

        report.append("Nearest 10 returns:")

        for p in selected[:10]:
            report.append(
                f"Ray {p['ray']} | "
                f"range {p['range']:.2f} m | "
                f"X {p['x']:.2f} | "
                f"Y {p['y']:.2f} | "
                f"Z {p['z']:.2f} | "
                f"diagnostic ID {p['id']}"
            )

    report.append("")

report.extend([
    "IMPORTANT:",
    "This is a preliminary bearing/range diagnostic.",
    "GT yaw, coordinate axes and vehicle visibility",
    "are not yet independently validated.",
    "Sensor mounting rotation and object geometry",
    "must also be considered before conclusions."
])

text = "\n".join(report)

print("\n" + text)

FINDINGS.mkdir(parents=True, exist_ok=True)

output = FINDINGS / "task11_frame150_visibility_diagnostic.txt"
output.write_text(text + "\n", encoding="utf-8")

print("\nSaved:", output)
print("TASK 11.5W COMPLETED")
