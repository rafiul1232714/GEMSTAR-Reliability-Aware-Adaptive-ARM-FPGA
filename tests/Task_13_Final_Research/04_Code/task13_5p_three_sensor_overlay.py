
# TASK 13.5P - THREE-SENSOR OVERLAY
# GEMSTAR MOR100, frame 150
#
# Camera + LiDAR + Radar visualization.
# Provisional pinhole camera projection.
# No claim of validated object association.

from pathlib import Path
import csv
import math
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"

IMAGE_FILE = (
    TASK / "01_Graphs" /
    "task13_5e_camera_frame150_rgb.png"
)

SOURCE = (
    ROOT / "tests" / "Task_11_Final_Research" /
    "02_CSV_Data"
)

LIDAR_FILE = SOURCE / "task11_lidar_frame150_geometry.csv"
RADAR_FILE = SOURCE / "task11_radar_measurements.csv"

OUT = TASK / "01_Graphs"
OUT.mkdir(parents=True, exist_ok=True)

FRAME = 150

# All coordinates use the vehicle-relative OSI convention:
# +X forward, +Y left, +Z up.
CAMERA_MOUNT = (0.70, 0.0, 1.60)
RADAR_MOUNT = (2.00, 0.0, 0.80)

image = Image.open(IMAGE_FILE).convert("RGB")
width, height = image.size

# Provisional Unreal perspective-camera model.
fx = width / 2.0
fy = fx
cx = width / 2.0
cy = height / 2.0


def project(x, y, z):
    """Project ego-relative OSI point into image pixels."""
    x -= CAMERA_MOUNT[0]
    y -= CAMERA_MOUNT[1]
    z -= CAMERA_MOUNT[2]

    if x <= 0.05:
        return None

    u = cx - fx * y / x
    v = cy - fy * z / x

    if not (0 <= u < width and 0 <= v < height):
        return None

    return int(round(u)), int(round(v))


with LIDAR_FILE.open(newline="", encoding="utf-8-sig") as f:
    lidar = list(csv.DictReader(f))

with RADAR_FILE.open(newline="", encoding="utf-8-sig") as f:
    radar = [
        row for row in csv.DictReader(f)
        if int(row["frame"]) == FRAME
        and float(row["range_m"]) > 0.1
        and float(row["signal_strength"]) > 0
    ]

# Filter the flat-surface candidate.
lidar_filtered = [
    row for row in lidar
    if row["object_id_diagnostic"] != "83185"
]

print("\n===== TASK 13.5P - THREE-SENSOR OVERLAY =====")
print("Frame:", FRAME)
print("LiDAR original:", len(lidar))
print("LiDAR filtered:", len(lidar_filtered))
print("Radar candidates:", len(radar))

canvas = image.copy()
draw = ImageDraw.Draw(canvas)

lidar_projected = 0
radar_projected = 0

# LiDAR in green.
for row in lidar_filtered:
    point = project(
        float(row["x_ego_m"]),
        float(row["y_ego_m"]),
        float(row["z_ego_m"])
    )

    if point is None:
        continue

    u, v = point
    draw.ellipse(
        (u-2, v-2, u+2, v+2),
        fill=(0, 230, 40)
    )
    lidar_projected += 1

# Radar in magenta.
for row in radar:
    rng = float(row["range_m"])
    az = float(row["horizontal_angle_rad"])
    el = float(row["vertical_angle_rad"])

    # Unreal forward direction represented in OSI:
    # invert Y sign.
    dx = math.cos(el) * math.cos(az)
    dy = -math.cos(el) * math.sin(az)
    dz = math.sin(el)

    # Transform from radar-local to ego-relative coordinates.
    x = RADAR_MOUNT[0] + rng * dx
    y = RADAR_MOUNT[1] + rng * dy
    z = RADAR_MOUNT[2] + rng * dz

    point = project(x, y, z)

    if point is None:
        continue

    u, v = point
    draw.ellipse(
        (u-5, v-5, u+5, v+5),
        outline=(255, 0, 220),
        width=2
    )
    radar_projected += 1

output = OUT / "task13_5p_camera_lidar_radar_overlay.png"
canvas.save(output)

print("LiDAR projected:", lidar_projected)
print("Radar projected:", radar_projected)
print("Saved:", output)
print("TASK 13.5P COMPLETED")
