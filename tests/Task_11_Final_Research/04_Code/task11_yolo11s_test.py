
# TASK 11.8E.4 - YOLO11s VEHICLE DETECTION
# GEMSTAR MOR100 - Frame 150

from pathlib import Path
import csv
import time

import cv2
from ultralytics import YOLO

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"

GRAPH_DIR = ARCHIVE / "01_Graphs"
CSV_DIR = ARCHIVE / "02_CSV_Data"
FINDINGS_DIR = ARCHIVE / "06_Research_Findings"

for folder in [GRAPH_DIR, CSV_DIR, FINDINGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

IMAGE = GRAPH_DIR / "task11_mor100_frame0150_camera_0.ppm"
assert IMAGE.is_file(), f"Missing camera image: {IMAGE}"

image = cv2.imread(str(IMAGE))
assert image is not None, "Cannot read camera image."

print("\nTASK 11.8E.4 - YOLO11s TEST")
print("Frame: 150")

# Larger model than YOLO11n.
# First run downloads the model weights.
model = YOLO("yolo11s.pt")

# Warm up.
model.predict(
    source=image,
    device="cpu",
    imgsz=640,
    conf=0.05,
    verbose=False
)

start = time.perf_counter()

result = model.predict(
    source=image,
    device="cpu",
    imgsz=640,
    conf=0.05,
    verbose=False
)[0]

elapsed_ms = (time.perf_counter() - start) * 1000

vehicle_classes = {2, 3, 5, 7}
rows = []

print("\n===== ALL DETECTIONS =====")

for box in result.boxes:

    class_id = int(box.cls.item())
    class_name = model.names[class_id]
    confidence = float(box.conf.item())

    x1, y1, x2, y2 = box.xyxy[0].tolist()

    is_vehicle = class_id in vehicle_classes

    print(
        f"{class_name} | "
        f"confidence={confidence:.3f} | "
        f"vehicle={is_vehicle}"
    )

    rows.append({
        "frame": 150,
        "model": "yolo11s.pt",
        "class_id": class_id,
        "class_name": class_name,
        "confidence": confidence,
        "is_vehicle": int(is_vehicle),
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2
    })

vehicle_count = sum(r["is_vehicle"] for r in rows)

csv_file = CSV_DIR / "task11_yolo11s_frame150.csv"

fields = [
    "frame", "model", "class_id", "class_name",
    "confidence", "is_vehicle",
    "x1", "y1", "x2", "y2"
]

with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

annotated_file = GRAPH_DIR / "task11_yolo11s_frame150.png"
cv2.imwrite(str(annotated_file), result.plot())

report = [
    "TASK 11.8E.4 - YOLO11s TEST",
    "Frame: 150",
    "Model: yolo11s.pt",
    "Device: CPU",
    "Confidence threshold: 0.05",
    f"Total detections: {len(rows)}",
    f"Vehicle detections: {vehicle_count}",
    f"Wall-clock prediction time: {elapsed_ms:.3f} ms",
    "Single-run timing, after warm-up.",
    "No cross-sensor object association performed."
]

(FINDINGS_DIR / "task11_yolo11s_findings.txt").write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)

print("\n===== FINAL SUMMARY =====")
print("All detections:", len(rows))
print("Vehicle detections:", vehicle_count)
print(f"Prediction time: {elapsed_ms:.3f} ms")
print("Saved:", annotated_file)
print("Saved:", csv_file)
print("TASK 11.8E.4 COMPLETED")
