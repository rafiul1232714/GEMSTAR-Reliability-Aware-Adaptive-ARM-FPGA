
from pathlib import Path
import csv
import math

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

DATA = (
    ROOT / "tests" / "Task_11_Final_Research"
    / "02_CSV_Data"
)

SOURCE = DATA / "task11_lidar_measurements.csv"
OUTPUT = DATA / "task11_lidar_frame431_geometry.csv"

FRAME = 431
DIAGNOSTIC_ID = "83391"

H_RAYS = 251
V_RAYS = 21

H_FOV = math.radians(90)
V_FOV = math.radians(20)

rows = []

with SOURCE.open(newline="", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        if int(row["frame"]) != FRAME:
            continue

        distance = float(row["range_m"])

        if not math.isfinite(distance) or distance < 0.1:
            continue

        ray = int(row["ray_index"])

        h = ray % H_RAYS
        v = ray // H_RAYS

        if not (0 <= v < V_RAYS):
            continue

        theta = -H_FOV / 2 + H_FOV * h / (H_RAYS - 1)
        phi = -V_FOV / 2 + V_FOV * v / (V_RAYS - 1)

        mx = float(row["mount_x"])
        my = float(row["mount_y"])
        mz = float(row["mount_z"])

        x = mx + distance * math.cos(phi) * math.cos(theta)
        y = my - distance * math.cos(phi) * math.sin(theta)
        z = mz + distance * math.sin(phi)

        object_id = row["object_id_diagnostic"]

        diagnostic_match = int(object_id == DIAGNOSTIC_ID)

        rows.append([
            FRAME,
            ray,
            distance,
            x,
            y,
            z,
            float(row["signal_strength"]),
            object_id,
            diagnostic_match
        ])

with OUTPUT.open("w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
        "frame",
        "ray_index",
        "range_m",
        "x_ego_m",
        "y_ego_m",
        "z_ego_m",
        "signal_strength",
        "diagnostic_object_id",
        "diagnostic_match"
    ])

    writer.writerows(rows)

print("\nTASK 11.5J - FRAME 431 GEOMETRY")
print("All valid LiDAR points:", len(rows))

selected = [r for r in rows if r[-1] == 1]

print("Diagnostic object points:", len(selected))

if selected:
    print("X extent:", round(
        max(r[3] for r in selected) -
        min(r[3] for r in selected), 3
    ))

    print("Y extent:", round(
        max(r[4] for r in selected) -
        min(r[4] for r in selected), 3
    ))

    print("Z extent:", round(
        max(r[5] for r in selected) -
        min(r[5] for r in selected), 3
    ))

print("Saved:", OUTPUT)
print("TASK 11.5J PYTHON EXTRACTION COMPLETED")
