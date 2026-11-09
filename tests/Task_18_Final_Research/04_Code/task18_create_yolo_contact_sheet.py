from pathlib import Path
from PIL import Image, ImageDraw
import csv
import math

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

IMAGE_DIR = BASE / "08_Extracted_Images" / "YOLO_Detections"
CSV_FILE = BASE / "02_CSV_Data" / "task18_yolo_frame_summary.csv"

OUTPUT = (
    BASE / "01_Graphs" /
    "task18_yolo_detection_contact_sheet.png"
)

with CSV_FILE.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

columns = 3
tile_w = 480
tile_h = 400
image_h = 360
row_count = math.ceil(len(rows) / columns)

sheet = Image.new(
    "RGB",
    (columns * tile_w, row_count * tile_h),
    "white"
)

draw = ImageDraw.Draw(sheet)

for index, row in enumerate(rows):
    frame = int(row["Frame"])

    image_path = IMAGE_DIR / f"task18_yolo_frame_{frame:03d}.png"

    if not image_path.exists():
        raise FileNotFoundError(image_path)

    with Image.open(image_path) as source:
        image = source.convert("RGB")
        image.thumbnail((tile_w - 12, image_h))

    col = index % columns
    line = index // columns

    x = col * tile_w + (tile_w - image.width) // 2
    y = line * tile_h + 5

    sheet.paste(image, (x, y))

    label = (
        f'Frame {frame} | '
        f'Objects: {row["ObjectsDetected"]} | '
        f'Vehicles: {row["VehiclesDetected"]}'
    )

    draw.text(
        (col * tile_w + 10, line * tile_h + 368),
        label,
        fill="black"
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
sheet.save(OUTPUT)

print("\n=== TASK 18.6E DETECTION CONTACT SHEET ===")
print("Frames included:", len(rows))
print("Contact sheet saved:", OUTPUT.exists())
print("Sheet resolution:", sheet.size)
print("Output:", OUTPUT)
