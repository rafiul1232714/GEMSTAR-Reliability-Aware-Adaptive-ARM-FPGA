
from pathlib import Path
import csv
import math
from collections import defaultdict

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

DATA = (
    ROOT / "tests" / "Task_11_Final_Research"
    / "02_CSV_Data"
)

SOURCE = DATA / "task11_lidar_measurements.csv"
OUTPUT = DATA / "task11_geometric_frame_candidates.csv"

# Confirmed GEMSTAR LiDAR configuration
H_RAYS = 251
V_RAYS = 21

H_FOV = math.radians(90)
V_FOV = math.radians(20)

# Mounting position
MOUNT_X = 2.6
MOUNT_Y = 0.0
MOUNT_Z = 0.7

# Process all frames, using object IDs only as
# diagnostic grouping labels, not vehicle labels.
groups = defaultdict(list)

print("TASK 11.5I - FIND GEOMETRIC OBJECT CANDIDATES")

with SOURCE.open(newline="", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        distance = float(row["range_m"])

        if not (0.1 <= distance <= 20.1):
            continue

        frame = int(row["frame"])
        ray = int(row["ray_index"])

        object_id = row["object_id_diagnostic"]

        h = ray % H_RAYS
        v = ray // H_RAYS

        theta = -H_FOV/2 + H_FOV*h/(H_RAYS-1)
        phi = -V_FOV/2 + V_FOV*v/(V_RAYS-1)

        x = MOUNT_X + distance * math.cos(phi) * math.cos(theta)
        y = MOUNT_Y - distance * math.cos(phi) * math.sin(theta)
        z = MOUNT_Z + distance * math.sin(phi)

        groups[(frame, object_id)].append((x, y, z))

rows = []

for (frame, object_id), points in groups.items():

    if len(points) < 20:
        continue

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]

    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    dz = max(zs) - min(zs)

    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    cz = sum(zs) / len(zs)

    # Exploratory compact-shape filter.
    # Not a vehicle classifier.
    compact = (
        0.3 <= dx <= 6.0
        and 0.3 <= dy <= 4.0
        and dz >= 0.2
    )

    rows.append([
        frame,
        object_id,
        len(points),
        cx, cy, cz,
        dx, dy, dz,
        int(compact)
    ])

rows.sort(
    key=lambda r: (r[-1], r[2]),
    reverse=True
)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
        "frame",
        "diagnostic_object_id",
        "point_count",
        "center_x_m",
        "center_y_m",
        "center_z_m",
        "x_extent_m",
        "y_extent_m",
        "z_extent_m",
        "compact_candidate"
    ])

    writer.writerows(rows)

print("\nTop 15 candidates:")

for row in rows[:15]:
    print(
        f"Frame {row[0]} | "
        f"ID {row[1]} | "
        f"Points {row[2]} | "
        f"Size ({row[6]:.2f}, "
        f"{row[7]:.2f}, {row[8]:.2f}) m | "
        f"Compact {row[9]}"
    )

print("\nTotal grouped objects:", len(rows))
print("Compact candidates:", sum(r[-1] for r in rows))
print("Saved:", OUTPUT)
print("\nTASK 11.5I COMPLETED")
