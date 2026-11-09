from pathlib import Path
from PIL import Image, ImageDraw
import json
import csv
import math

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

IMAGE_DIR = BASE / "08_Extracted_Images" / "Selected_Frames"
LABEL_DIR = BASE / "09_GroundTruth_Annotations"
MANIFEST = BASE / "02_CSV_Data" / "task18_annotation_manifest.csv"
OUTPUT = BASE / "01_Graphs" / "task18_manual_annotation_contact_sheet.png"

with MANIFEST.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

columns = 3
tile_w = 480
tile_h = 390
img_h = 360

sheet = Image.new(
    "RGB",
    (columns * tile_w, math.ceil(len(rows)/columns) * tile_h),
    "white"
)

draw = ImageDraw.Draw(sheet)

for index, row in enumerate(rows):

    frame = int(row["Frame"])

    image_path = IMAGE_DIR / row["ImageFile"]
    label_path = LABEL_DIR / f"task18_labels_frame_{frame:03d}.json"

    with Image.open(image_path) as source:
        image = source.convert("RGB")

    annotations = json.loads(
        label_path.read_text(encoding="utf-8")
    )

    image_draw = ImageDraw.Draw(image)

    for obj in annotations["objects"]:
        x1, y1, x2, y2 = (
            obj["x1"], obj["y1"], obj["x2"], obj["y2"]
        )

        image_draw.rectangle(
            [x1, y1, x2, y2],
            outline="lime",
            width=3
        )

        image_draw.text(
            (x1, max(0, y1-15)),
            obj["class"],
            fill="lime"
        )

    image.thumbnail((tile_w - 12, img_h))

    col = index % columns
    line = index // columns

    x = col * tile_w + (tile_w - image.width)//2
    y = line * tile_h + 3

    sheet.paste(image, (x, y))

    draw.text(
        (col * tile_w + 10, line * tile_h + 365),
        f"Frame {frame} | Manual objects: {len(annotations['objects'])}",
        fill="black"
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
sheet.save(OUTPUT)

print("\n=== TASK 18.7H ANNOTATION CONTACT SHEET ===")
print("Images included:", len(rows))
print("Contact sheet saved:", OUTPUT.exists())
print("Output:", OUTPUT)
