import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw
from osi3.osi_sensorview_pb2 import SensorView

recording = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

image_path = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\Camera_NoVisualizer_V2_2122\clean_camera_02_frame00530.png"
)

output_path = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_V2_Frame0530_LiDAR_Projection_NOMINAL.png"
)

TARGET_FRAME = 530
C = 299792458.0

# Nominal mount locations in Unreal coordinates, meters.
CAMERA = (0.70, 0.0, 1.60)
LIDAR = (2.60, 0.0, 0.70)

with recording.open("rb") as f:
    for frame in range(TARGET_FRAME + 1):
        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]

        if size <= 0:
            raise RuntimeError("Invalid OSI message size")

        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

    sv = SensorView()
    sv.ParseFromString(payload)

if len(sv.lidar_sensor_view) != 1:
    raise RuntimeError("Expected one LiDAR view")

if len(sv.camera_sensor_view) != 1:
    raise RuntimeError("Expected one Camera view")

view = sv.lidar_sensor_view[0]
cfg = view.view_configuration

nh = int(cfg.number_of_rays_horizontal)
nv = int(cfg.number_of_rays_vertical)

if (nh, nv) != (251, 21):
    raise RuntimeError("Unexpected LiDAR grid")

if len(view.reflection) != nh * nv:
    raise RuntimeError("Unexpected reflection count")

image = Image.open(image_path).convert("RGB")

width, height = image.size

if (width, height) != (640, 480):
    raise RuntimeError("Unexpected Camera dimensions")

hfov_camera = math.radians(90.0)

fx = width / (2 * math.tan(hfov_camera / 2))
fy = fx

cx = width / 2
cy = height / 2

hfov = float(cfg.field_of_view_horizontal)
vfov = float(cfg.field_of_view_vertical)

points = []

valid_ranges = 0
positive_depth = 0

for index, reflection in enumerate(view.reflection):

    tof = float(reflection.time_of_flight)

    if not math.isfinite(tof) or tof <= 0:
        continue

    distance = C * tof / 2

    if not math.isfinite(distance) or distance <= 0.01:
        continue

    valid_ranges += 1

    hi = index % nh
    vi = index // nh

    yaw = -hfov / 2 + hi * hfov / (nh - 1)
    pitch = -vfov / 2 + vi * vfov / (nv - 1)

    # LiDAR-local coordinates, Unreal X-forward, Y-right, Z-up.
    lx = distance * math.cos(pitch) * math.cos(yaw)
    ly = distance * math.cos(pitch) * math.sin(yaw)
    lz = distance * math.sin(pitch)

    # Convert to Camera-relative coordinates.
    x = lx + LIDAR[0] - CAMERA[0]
    y = ly + LIDAR[1] - CAMERA[1]
    z = lz + LIDAR[2] - CAMERA[2]

    if x <= 0:
        continue

    positive_depth += 1

    # Perspective projection: X forward, Y right, Z up.
    u = cx + fx * (y / x)
    v = cy - fy * (z / x)

    if 0 <= u < width and 0 <= v < height:
        points.append((u, v))

# Save a separate visualization; do not overwrite the camera image.
overlay = image.copy()
draw = ImageDraw.Draw(overlay)

# Limit visual clutter while retaining points across the image.
step = max(1, math.ceil(len(points) / 700))

for u, v in points[::step]:
    draw.ellipse(
        (u - 1.5, v - 1.5, u + 1.5, v + 1.5),
        fill=(0, 255, 255)
    )

overlay.save(output_path)

print("=== TASK 24.7.9 RESULTS ===")
print("FRAME=", TARGET_FRAME)
print("IMAGE_RESOLUTION=", image.size)
print("LIDAR_REFLECTIONS=", len(view.reflection))
print("VALID_RANGE_REFLECTIONS=", valid_ranges)
print("POSITIVE_CAMERA_DEPTH=", positive_depth)
print("POINTS_INSIDE_IMAGE=", len(points))
print("DRAWN_POINTS=", len(points[::step]))
print("FX_PX=", fx)
print("FY_PX=", fy)
print("PROJECTION_MODEL=NOMINAL_UNCALIBRATED")
print("OUTPUT=", output_path)
print("ORIGINAL_IMAGE_MODIFIED=NO")
print("OSI_MODIFIED=NO")
print("TASK24_07_09_PROJECTION_COMPLETE")