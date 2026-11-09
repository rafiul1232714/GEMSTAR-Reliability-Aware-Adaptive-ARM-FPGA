from pathlib import Path
import csv
import time
import cv2
import torch
from ultralytics import YOLO

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

IMAGE_DIR = BASE / "08_Extracted_Images" / "Selected_Frames"
MODEL = BASE / "03_Configurations" / "Models" / "yolo11n.pt"

OUT = BASE / "08_Extracted_Images" / "YOLO_Detections"
CSV_DIR = BASE / "02_CSV_Data"

OUT.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

model = YOLO(str(MODEL))

images = sorted(IMAGE_DIR.glob("task18_camera_frame_*.png"))

if len(images) != 12:
    raise RuntimeError(f"Expected 12 images, found {len(images)}")

# Warm-up is separate from the measured frames.
model.predict(
    source=str(images[0]),
    device="cpu",
    imgsz=640,
    conf=0.25,
    verbose=False
)

detections = []
summary = []

VEHICLE_CLASSES = {2, 3, 5, 7}

print("\n=== TASK 18.6D YOLO OBJECT DETECTION ===")

for image_path in images:

    frame = int(image_path.stem.rsplit("_", 1)[-1])

    start = time.perf_counter()

    results = model.predict(
        source=str(image_path),
        device="cpu",
        imgsz=640,
        conf=0.25,
        verbose=False
    )

    wall_ms = (time.perf_counter() - start) * 1000

    result = results[0]
    annotated = result.plot()

    output_image = OUT / f"task18_yolo_frame_{frame:03d}.png"
    cv2.imwrite(str(output_image), annotated)

    object_count = 0
    vehicle_count = 0

    for box in result.boxes:

        cls = int(box.cls.item())
        confidence = float(box.conf.item())

        x1, y1, x2, y2 = [
            float(v) for v in box.xyxy[0].tolist()
        ]

        object_count += 1

        if cls in VEHICLE_CLASSES:
            vehicle_count += 1

        detections.append({
            "Frame": frame,
            "ClassID": cls,
            "ClassName": model.names[cls],
            "Confidence": confidence,
            "X1": x1,
            "Y1": y1,
            "X2": x2,
            "Y2": y2
        })

    speed = result.speed or {}

    summary.append({
        "Frame": frame,
        "ObjectsDetected": object_count,
        "VehiclesDetected": vehicle_count,
        "PreprocessMs": speed.get("preprocess", 0),
        "InferenceMs": speed.get("inference", 0),
        "PostprocessMs": speed.get("postprocess", 0),
        "TotalWallMs": wall_ms
    })

    print(
        f"Frame {frame:3d} | "
        f"Objects={object_count:2d} | "
        f"Vehicles={vehicle_count:2d} | "
        f"Inference={speed.get('inference', 0):.2f} ms | "
        f"Wall={wall_ms:.2f} ms"
    )

def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

write_csv(
    CSV_DIR / "task18_yolo_detections.csv",
    detections,
    ["Frame", "ClassID", "ClassName", "Confidence",
     "X1", "Y1", "X2", "Y2"]
)

write_csv(
    CSV_DIR / "task18_yolo_frame_summary.csv",
    summary,
    ["Frame", "ObjectsDetected", "VehiclesDetected",
     "PreprocessMs", "InferenceMs", "PostprocessMs",
     "TotalWallMs"]
)

print("\n=== TASK 18.6D SUMMARY ===")
print("Frames processed:", len(summary))
print("Total detections:", len(detections))
print("Total vehicle detections:",
      sum(r["VehiclesDetected"] for r in summary))
print("Detection CSV saved:",
      (CSV_DIR / "task18_yolo_detections.csv").exists())
print("Summary CSV saved:",
      (CSV_DIR / "task18_yolo_frame_summary.csv").exists())
print("Annotated images saved:", len(list(OUT.glob("*.png"))))
print("Output folder:", OUT)
