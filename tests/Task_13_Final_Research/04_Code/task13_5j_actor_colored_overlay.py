
# TASK 13.5J - ACTOR-COLOURED LIDAR CAMERA OVERLAY

from pathlib import Path
import csv
import math
from collections import Counter
from PIL import Image, ImageDraw

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

TASK = ROOT / "tests" / "Task_13_Final_Research"

IMAGE = TASK / "01_Graphs" / "task13_5e_camera_frame150_rgb.png"

CSV = (
    ROOT / "tests" / "Task_11_Final_Research" /
    "02_CSV_Data" / "task11_lidar_frame150_geometry.csv"
)

OUT = TASK / "01_Graphs"

CAMERA_X = 0.70
CAMERA_Y = 0.0
CAMERA_Z = 1.60

COLORS = {
    "83185": (255, 0, 0),
    "83181": (0, 255, 0),
    "83265": (0, 80, 255),
    "83183": (255, 165, 0),
}

with CSV.open(newline="", encoding="utf-8-sig") as f:
    points = list(csv.DictReader(f))

print("\n===== TASK 13.5J - ACTOR OVERLAY =====")
print("Total valid LiDAR points:", len(points))
print("Actor counts:", dict(Counter(
    r["object_id_diagnostic"] for r in points
)))


def create_overlay(name, fy):
    image = Image.open(IMAGE).convert("RGB")
    draw = ImageDraw.Draw(image)

    width, height = image.size
    fx = width / 2

    visible = Counter()

    for row in points:
        actor = row["object_id_diagnostic"]

        x = float(row["x_ego_m"]) - CAMERA_X
        y = float(row["y_ego_m"]) - CAMERA_Y
        z = float(row["z_ego_m"]) - CAMERA_Z

        if x <= 0.05:
            continue

        u = width / 2 - fx * y / x
        v = height / 2 - fy * z / x

        if not (0 <= u < width and 0 <= v < height):
            continue

        color = COLORS.get(actor, (255, 165, 0))

        draw.ellipse(
            (u-2, v-2, u+2, v+2),
            fill=color
        )

        visible[actor] += 1

    output = OUT / f"task13_5j_{name}.png"
    image.save(output)

    print(f"\n{name}")
    print("Visible actor counts:", dict(visible))
    print("Saved:", output)


# Model A: square-pixel camera model.
create_overlay("square_pixel_actors", 320.0)

# Model B: independent 90-degree vertical FOV.
create_overlay("dual_90deg_actors", 240.0)

print("\nTASK 13.5J COMPLETED")
