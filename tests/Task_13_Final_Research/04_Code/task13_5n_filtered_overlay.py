
# TASK 13.5N - FILTERED LIDAR CAMERA OVERLAY
# MOR100, frame 150
#
# Diagnostic visualization only.
# Excluding an actor does NOT establish object identity.

from pathlib import Path
from collections import Counter
import csv

from PIL import Image, ImageDraw

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"

IMAGE_FILE = (
    TASK / "01_Graphs" /
    "task13_5e_camera_frame150_rgb.png"
)

LIDAR_FILE = (
    ROOT / "tests" / "Task_11_Final_Research" /
    "02_CSV_Data" /
    "task11_lidar_frame150_geometry.csv"
)

OUT = TASK / "01_Graphs"
OUT.mkdir(parents=True, exist_ok=True)

CAMERA = (0.70, 0.0, 1.60)

COLORS = {
    "83265": (0, 100, 255),
    "83181": (0, 220, 0),
    "83183": (255, 165, 0)
}

with LIDAR_FILE.open(
    newline="", encoding="utf-8-sig"
) as f:
    points = list(csv.DictReader(f))

image = Image.open(IMAGE_FILE).convert("RGB")
width, height = image.size

# Using the square-pixel model for this diagnostic.
fx = width / 2
fy = fx

print("\n===== TASK 13.5N - FILTERED OVERLAY =====")

filtered = [
    p for p in points
    if p["object_id_diagnostic"] != "83185"
]

print("Original LiDAR points:", len(points))
print("Remaining after exclusion:", len(filtered))

print("Remaining actor counts:")
for actor, count in Counter(
    p["object_id_diagnostic"]
    for p in filtered
).items():
    print(f"  Actor {actor}: {count}")


def overlay(name, selected):
    output = image.copy()
    draw = ImageDraw.Draw(output)

    drawn = 0

    for row in selected:
        actor = row["object_id_diagnostic"]

        x = float(row["x_ego_m"]) - CAMERA[0]
        y = float(row["y_ego_m"]) - CAMERA[1]
        z = float(row["z_ego_m"]) - CAMERA[2]

        if x <= 0:
            continue

        u = width/2 - fx*y/x
        v = height/2 - fy*z/x

        if not (0 <= u < width and 0 <= v < height):
            continue

        color = COLORS.get(actor, (255, 255, 0))

        draw.ellipse(
            (u-3, v-3, u+3, v+3),
            fill=color
        )
        drawn += 1

    path = OUT / f"task13_5n_{name}.png"
    output.save(path)

    print(f"\n{name}")
    print("Projected points:", drawn)
    print("Saved:", path)


# Overlay 1: all actors except the flat-ground candidate.
overlay("non_ground_candidates", filtered)

# Overlay 2: only vertical-like actor.
overlay(
    "vertical_surface_only",
    [
        p for p in filtered
        if p["object_id_diagnostic"] == "83265"
    ]
)

# Overlay 3: only other horizontal-like surfaces.
overlay(
    "other_horizontal_surfaces",
    [
        p for p in filtered
        if p["object_id_diagnostic"] in ("83181", "83183")
    ]
)

print("\nTASK 13.5N COMPLETED")
