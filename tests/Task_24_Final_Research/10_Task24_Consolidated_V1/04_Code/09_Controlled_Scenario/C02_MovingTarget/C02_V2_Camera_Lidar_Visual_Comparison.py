from pathlib import Path
from PIL import Image, ImageDraw

base = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

camera = Image.open(
    base / "C02_V2_YOLO_Frame0530.png"
).convert("RGB")

lidar = Image.open(
    base / "C02_V2_Frame0530_LiDAR_Projection_NOMINAL.png"
).convert("RGB")

if camera.size != lidar.size:
    raise RuntimeError("Image resolution mismatch")

width, height = camera.size

canvas = Image.new(
    "RGB",
    (width * 2, height + 40),
    (255, 255, 255)
)

canvas.paste(camera, (0, 40))
canvas.paste(lidar, (width, 40))

draw = ImageDraw.Draw(canvas)

draw.text(
    (10, 12),
    "CAMERA - YOLO DETECTIONS",
    fill=(0, 0, 0)
)

draw.text(
    (width + 10, 12),
    "LIDAR - NOMINAL PROJECTION",
    fill=(0, 0, 0)
)

output = base / "C02_V2_Camera_Lidar_SideBySide_Frame0530.png"

canvas.save(output)

print("CAMERA_RESOLUTION=", camera.size)
print("LIDAR_RESOLUTION=", lidar.size)
print("OUTPUT=", output)
print("ORIGINAL_IMAGES_MODIFIED=NO")
print("TASK24_07_15_VISUAL_COMPARISON_COMPLETE")