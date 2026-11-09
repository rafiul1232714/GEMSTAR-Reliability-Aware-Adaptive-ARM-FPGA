from pathlib import Path
import csv
import hashlib

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

SOURCE = BASE / "02_CSV_Data" / "task18_selected_camera_frames.csv"
IMAGE_DIR = BASE / "08_Extracted_Images" / "Selected_Frames"

LABEL_DIR = BASE / "09_GroundTruth_Annotations"
OUTPUT = BASE / "02_CSV_Data" / "task18_annotation_manifest.csv"

LABEL_DIR.mkdir(parents=True, exist_ok=True)

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    frames = list(csv.DictReader(f))

rows = []

for row in frames:
    image = IMAGE_DIR / row["ImageFile"]

    if not image.exists():
        raise FileNotFoundError(image)

    sha256 = hashlib.sha256(image.read_bytes()).hexdigest()

    rows.append({
        "Frame": row["Frame"],
        "TimestampSeconds": row["TimestampSeconds"],
        "ImageFile": row["ImageFile"],
        "ImageSHA256": sha256,
        "AnnotationStatus": "NOT_ANNOTATED",
        "AnnotationSource": "PENDING_MANUAL_REVIEW",
        "Notes": ""
    })

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 18.7D ANNOTATION PREPARATION ===")
print("Images registered:", len(rows))
print("All images hashed:", all(r["ImageSHA256"] for r in rows))
print("Annotation folder created:", LABEL_DIR.exists())
print("Annotation manifest saved:", OUTPUT.exists())
print("Output:", OUTPUT)
