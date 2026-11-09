
# TASK 11.8E.3 - YOLO MISSED-DETECTION DIAGNOSTIC
# GEMSTAR MOR100 Camera Frame 150
# CPU baseline, no CUDA required

from pathlib import Path
import csv
import cv2
import torch
from ultralytics import YOLO

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"

GRAPHS = ARCHIVE / "01_Graphs"
DATA = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

for folder in [GRAPHS, DATA, FINDINGS]:
    folder.mkdir(parents=True, exist_ok=True)

IMAGE = GRAPHS / "task11_mor100_frame0150_camera_0.ppm"

assert IMAGE.is_file(), f"Missing image: {IMAGE}"

print("\nTASK 11.8E.3 - YOLO DIAGNOSTIC")
print("PyTorch:", torch.__version__)
print("Device: CPU")

image = cv2.imread(str(IMAGE))
assert image is not None, "Unable to read image."

model = YOLO("yolo11n.pt")

# Test A: OpenCV's normal BGR interpretation
# Test B: Swap R and B channels
tests = {
    "original": image,
    "swapped_rb": cv2.cvtColor(
        image, cv2.COLOR_BGR2RGB
    )
}

rows = []
summary = []

vehicle_ids = {2, 3, 5, 7}

for test_name, img in tests.items():

    print(f"\n===== TEST: {test_name} =====")

    result = model.predict(
        source=img,
        device="cpu",
        conf=0.05,
        imgsz=640,
        verbose=False
    )[0]

    boxes = result.boxes
    vehicle_count = 0

    for box in boxes:

        cls_id = int(box.cls.item())
        cls_name = model.names[cls_id]
        confidence = float(box.conf.item())

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        is_vehicle = cls_id in vehicle_ids

        if is_vehicle:
            vehicle_count += 1

        print(
            f"{cls_name} | "
            f"confidence={confidence:.3f} | "
            f"vehicle={is_vehicle} | "
            f"box=({x1:.0f},{y1:.0f},"
            f"{x2:.0f},{y2:.0f})"
        )

        rows.append({
            "frame": 150,
            "test": test_name,
            "class_id": cls_id,
            "class_name": cls_name,
            "confidence": confidence,
            "is_vehicle": int(is_vehicle),
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        })

    total_count = len(boxes)

    print("All detections:", total_count)
    print("Vehicle detections:", vehicle_count)

    summary.append({
        "test": test_name,
        "all_detections": total_count,
        "vehicle_detections": vehicle_count
    })

    annotated = result.plot()

    output = GRAPHS / (
        f"task11_frame150_yolo_{test_name}_lowconf.png"
    )

    cv2.imwrite(str(output), annotated)

    print("Saved:", output)

# Save detection CSV even if nothing was detected
output_csv = DATA / "task11_yolo_diagnostic_frame150.csv"

fields = [
    "frame", "test", "class_id", "class_name",
    "confidence", "is_vehicle",
    "x1", "y1", "x2", "y2"
]

with output_csv.open(
    "w", newline="", encoding="utf-8"
) as f:

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

summary_file = DATA / "task11_yolo_diagnostic_summary.csv"

with summary_file.open(
    "w", newline="", encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "test",
            "all_detections",
            "vehicle_detections"
        ]
    )

    writer.writeheader()
    writer.writerows(summary)

report = [
    "TASK 11.8E.3 - YOLO MISSED DETECTION",
    "Frame: 150",
    "Model: yolo11n.pt",
    "Confidence threshold: 0.05",
    "Image size: 640",
    "Device: CPU",
    "",
]

for item in summary:
    report.append(
        f"{item['test']}: "
        f"{item['all_detections']} total, "
        f"{item['vehicle_detections']} vehicles"
    )

report.extend([
    "",
    "This is a diagnostic test, not final evaluation.",
    "Lower confidence can increase false positives.",
    "Color channel ordering remains to be verified.",
    "No camera-to-LiDAR object association performed."
])

report_file = FINDINGS / (
    "task11_yolo_missed_detection_diagnostic.txt"
)

report_file.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)

print("\n===== FINAL SUMMARY =====")

for item in summary:
    print(
        f"{item['test']}: "
        f"{item['all_detections']} detections, "
        f"{item['vehicle_detections']} vehicles"
    )

print("\nCSV:", output_csv)
print("TASK 11.8E.3 COMPLETED")
