
# TASK 11.8E.2 - YOLO VEHICLE DETECTION
# GEMSTAR MOR100 - Camera Frame 150

from pathlib import Path
import csv
import time
import cv2
import torch
from ultralytics import YOLO

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")

ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"
GRAPH_DIR = ARCHIVE / "01_Graphs"
CSV_DIR = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

for folder in [GRAPH_DIR, CSV_DIR, FINDINGS]:
    folder.mkdir(parents=True, exist_ok=True)

IMAGE = GRAPH_DIR / "task11_mor100_frame0150_camera_0.ppm"

assert IMAGE.is_file(), f"Camera image missing: {IMAGE}"

print("\nTASK 11.8E.2 - YOLO VEHICLE DETECTION")
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

# Start with CPU for a reproducible baseline.
device = "cpu"

# Download pretrained weights automatically on first use.
model = YOLO("yolo11n.pt")

image = cv2.imread(str(IMAGE))
assert image is not None, "Cannot read camera image."

# COCO vehicle classes:
# 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
vehicle_classes = [2, 3, 5, 7]

# Warm-up run, excluded from measured inference
model.predict(
    source=image,
    device=device,
    imgsz=640,
    verbose=False
)

start = time.perf_counter()

results = model.predict(
    source=image,
    device=device,
    imgsz=640,
    conf=0.25,
    classes=vehicle_classes,
    verbose=False
)

elapsed_ms = (time.perf_counter() - start) * 1000

result = results[0]

detections = []

for box in result.boxes:

    class_id = int(box.cls.item())
    confidence = float(box.conf.item())

    x1, y1, x2, y2 = box.xyxy[0].tolist()

    detections.append({
        "frame": 150,
        "class_id": class_id,
        "class_name": model.names[class_id],
        "confidence": confidence,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2
    })

output_csv = CSV_DIR / "task11_camera_yolo_detections_frame150.csv"

with output_csv.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "frame", "class_id", "class_name",
        "confidence", "x1", "y1", "x2", "y2"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(detections)

# Save image with bounding boxes.
annotated = result.plot()

output_image = GRAPH_DIR / "task11_camera_yolo_frame150.png"

cv2.imwrite(str(output_image), annotated)

report = [
    "TASK 11.8E.2 - CAMERA VEHICLE DETECTION",
    "Frame: 150",
    "Model: yolo11n.pt",
    f"Device: {device}",
    f"Vehicle detections: {len(detections)}",
    f"Wall-clock prediction time: {elapsed_ms:.3f} ms",
    "Model download and warm-up excluded.",
    "This is a single-run latency measurement.",
    "Camera detections are not yet associated with LiDAR/Radar."
]

report_path = FINDINGS / "task11_camera_yolo_frame150_findings.txt"
report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

print("\n===== DETECTIONS =====")
for d in detections:
    print(
        f"{d['class_name']} | "
        f"Confidence: {d['confidence']:.3f} | "
        f"Box: ({d['x1']:.0f}, {d['y1']:.0f}, "
        f"{d['x2']:.0f}, {d['y2']:.0f})"
    )

print("\nVehicles detected:", len(detections))
print(f"Prediction time: {elapsed_ms:.3f} ms")
print("Saved image:", output_image)
print("Saved CSV:", output_csv)
print("TASK 11.8E.2 COMPLETED")
