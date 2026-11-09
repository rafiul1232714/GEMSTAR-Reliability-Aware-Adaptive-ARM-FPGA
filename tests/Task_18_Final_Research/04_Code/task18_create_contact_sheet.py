from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import csv
import math

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

IMAGE_DIR = BASE / "08_Extracted_Images" / "Selected_Frames"

CSV = BASE / "02_CSV_Data" / "task18_selected_camera_frames.csv"

OUTPUT = (
    BASE / "01_Graphs" /
    "task18_selected_camera_contact_sheet.png"
)

with CSV.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

columns = 3
tile_width = 480
tile_height = 390
image_height = 360
rows_count = math.ceil(len(rows) / columns)

sheet = Image.new(
    "RGB",
    (columns * tile_width, rows_count * tile_height),
    "white"
)

draw = ImageDraw.Draw(sheet)

for index, row in enumerate(rows):

    path = IMAGE_DIR / row["ImageFile"]

    with Image.open(path) as source:
        image = source.convert("RGB")
        image.thumbnail((tile_width - 12, image_height))

    col = index % columns
    line = index // columns

    x = col * tile_width + (tile_width - image.width) // 2
    y = line * tile_height + 4

    sheet.paste(image, (x, y))

    label = (
        f'Frame {row["Frame"]} | '
        f'{float(row["TimestampSeconds"]):.3f} s | '
        f'{row["TimingRegime"]}'
    )

    draw.text(
        (col * tile_width + 10, line * tile_height + 365),
        label,
        fill="black"
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
sheet.save(OUTPUT)

print("\n=== TASK 18.5B CAMERA CONTACT SHEET ===")
print("Images included:", len(rows))
print("Sheet resolution:", sheet.size)
print("Contact sheet saved:", OUTPUT.exists())
print("Output:", OUTPUT)
