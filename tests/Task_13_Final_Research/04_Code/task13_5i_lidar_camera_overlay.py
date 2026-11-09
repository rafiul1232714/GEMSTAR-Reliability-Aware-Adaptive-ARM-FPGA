
# TASK 13.5I - LIDAR TO CAMERA OVERLAY
# GEMSTAR MOR100, frame 150
#
# Compare two provisional camera projection models.
# Do not overwrite any earlier research files.

from pathlib import Path
import csv
import math

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"

IMAGE = TASK / "01_Graphs" / "task13_5e_camera_frame150_rgb.png"
LIDAR = (
    ROOT / "tests" / "Task_11_Final_Research" /
    "02_CSV_Data" / "task11_lidar_frame150_geometry.csv"
)
OUT = TASK / "01_Graphs"
OUT.mkdir(parents=True, exist_ok=True)

# Both positions are relative to the vehicle actor.
LIDAR_MOUNT = np.array([2.60, 0.0, 0.70])
CAMERA_MOUNT = np.array([0.70, 0.0, 1.60])

# Camera-to-LiDAR mounting translation in the same
# ego coordinate frame; zero relative rotation.
SHIFT = LIDAR_MOUNT - CAMERA_MOUNT

image = Image.open(IMAGE).convert("RGB")
width, height = image.size

points = []

with LIDAR.open(newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        x = float(row["x_ego_m"])
        y = float(row["y_ego_m"])
        z = float(row["z_ego_m"])

        # Existing CSV coordinates are ego-relative.
        # Do not add LiDAR mounting translation again.
        points.append((x, y, z))

print("\n===== TASK 13.5I - LIDAR CAMERA OVERLAY =====")
print("Camera size:", width, height)
print("LiDAR points:", len(points))

# Correct conversion from ego frame to camera frame:
# camera frame origin is CAMERA_MOUNT.
#
# Unreal: +X forward, +Y right, +Z up.
# OSI: +X forward, -Y right, +Z up.
#
# Image: +u right, +v down.
#
# Therefore u = cx - fx*(Y/X)
#           v = cy - fy*(Z/X)

def make_overlay(name, fx, fy):
    output = image.copy()
    draw = ImageDraw.Draw(output)

    total_front = 0
    visible = 0

    for x, y, z in points:
        xc = x - CAMERA_MOUNT[0]
        yc = y - CAMERA_MOUNT[1]
        zc = z - CAMERA_MOUNT[2]

        if xc <= 0.05:
            continue

        total_front += 1

        u = width / 2 - fx * (yc / xc)
        v = height / 2 - fy * (zc / xc)

        if 0 <= u < width and 0 <= v < height:
            visible += 1

            u = int(round(u))
            v = int(round(v))

            draw.ellipse(
                (u-2, v-2, u+2, v+2),
                fill=(255, 0, 0)
            )

    path = OUT / f"task13_5i_{name}.png"
    output.save(path)

    print(f"\n{name}")
    print("Points in front:", total_front)
    print("Projected inside image:", visible)
    print("Saved:", path)


# Model A: camera's nominal 90-degree horizontal FOV,
# and conventional square-pixel perspective projection.
fx_a = width / (2 * math.tan(math.radians(90) / 2))
fy_a = fx_a

# Model B: use both 90-degree FOV values literally.
fx_b = width / (2 * math.tan(math.radians(90) / 2))
fy_b = height / (2 * math.tan(math.radians(90) / 2))

make_overlay("square_pixel_projection", fx_a, fy_a)
make_overlay("dual_90deg_projection", fx_b, fy_b)

print("\nTASK 13.5I COMPLETED")
