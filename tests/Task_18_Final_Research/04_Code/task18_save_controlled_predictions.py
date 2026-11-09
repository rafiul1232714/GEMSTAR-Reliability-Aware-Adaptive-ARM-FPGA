from pathlib import Path
import csv
import statistics
from ultralytics import YOLO

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

IMAGES = BASE / "08_Extracted_Images" / "Selected_Frames"
MODELS = BASE / "03_Configurations" / "Models"
CSV_DIR = BASE / "02_CSV_Data"

images = sorted(IMAGES.glob("task18_camera_frame_*.png"))

if len(images) != 12:
    raise RuntimeError(f"Expected 12 images, found {len(images)}")

settings = {
    "device": "cpu",
    "imgsz": 640,
    "conf": 0.25,
    "iou": 0.70,
    "agnostic_nms": True,
    "verbose": False,
}

detections = []
summaries = []

for model_name in ["yolo11n", "yolo11s"]:

    model = YOLO(str(MODELS / f"{model_name}.pt"))

    # Warm up the model.
    for _ in range(3):
        model.predict(str(images[0]), **settings)

    for path in images:
        frame = int(path.stem.rsplit("_", 1)[-1])

        result = model.predict(str(path), **settings)[0]

        for box in result.boxes:
            cls = int(box.cls.item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "Model": model_name,
                "Frame": frame,
                "ClassName": model.names[cls],
                "Confidence": float(box.conf.item()),
                "X1": x1,
                "Y1": y1,
                "X2": x2,
                "Y2": y2
            })

        summaries.append({
            "Model": model_name,
            "Frame": frame,
            "ObjectsDetected": len(result.boxes),
            "InferenceMs": result.speed["inference"]
        })

def save_csv(path, rows, headers):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

prediction_file = CSV_DIR / "task18_controlled_predictions.csv"
summary_file = CSV_DIR / "task18_controlled_inference_summary.csv"

save_csv(
    prediction_file,
    detections,
    ["Model", "Frame", "ClassName", "Confidence",
     "X1", "Y1", "X2", "Y2"]
)

save_csv(
    summary_file,
    summaries,
    ["Model", "Frame", "ObjectsDetected", "InferenceMs"]
)

print("\n=== TASK 18.7K CONTROLLED PREDICTIONS ===")

for name in ["yolo11n", "yolo11s"]:
    model_rows = [r for r in summaries if r["Model"] == name]
    prediction_rows = [r for r in detections if r["Model"] == name]

    print(
        f"{name}: "
        f"frames={len(model_rows)}, "
        f"predictions={len(prediction_rows)}, "
        f"median_inference_ms="
        f"{statistics.median(r['InferenceMs'] for r in model_rows):.3f}"
    )

print("Prediction CSV saved:", prediction_file.exists())
print("Inference CSV saved:", summary_file.exists())
