from pathlib import Path
import csv
import statistics
from ultralytics import YOLO

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research")
IMAGES = BASE / "08_Extracted_Images" / "Selected_Frames"
MODELS = BASE / "03_Configurations" / "Models"
OUTPUT = BASE / "02_CSV_Data" / "task18_controlled_model_comparison.csv"

images = sorted(IMAGES.glob("task18_camera_frame_*.png"))

if len(images) != 12:
    raise RuntimeError(f"Expected 12 images, found {len(images)}")

rows = []
vehicle_classes = {2, 3, 5, 7}

for model_name in ["yolo11n", "yolo11s"]:
    model = YOLO(str(MODELS / f"{model_name}.pt"))

    settings = dict(
        device="cpu",
        imgsz=640,
        conf=0.25,
        iou=0.7,
        agnostic_nms=True,
        verbose=False
    )

    # Warm up each model.
    for _ in range(3):
        model.predict(str(images[0]), **settings)

    for path in images:
        frame = int(path.stem.rsplit("_", 1)[-1])
        result = model.predict(str(path), **settings)[0]

        classes = [
            int(box.cls.item())
            for box in result.boxes
        ]

        names = [
            model.names[cls]
            for cls in classes
        ]

        rows.append({
            "Model": model_name,
            "Frame": frame,
            "Detections": len(classes),
            "VehicleDetections": sum(
                cls in vehicle_classes for cls in classes
            ),
            "Classes": ";".join(names),
            "InferenceMs": float(result.speed["inference"])
        })

        print(
            f"{model_name} | Frame {frame:3d} | "
            f"Objects={len(classes)} | "
            f"Classes={names} | "
            f"Inference={result.speed['inference']:.2f} ms"
        )

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 18.7C CONTROLLED COMPARISON ===")

for name in ["yolo11n", "yolo11s"]:
    selected = [r for r in rows if r["Model"] == name]
    print(
        f"{name}: "
        f"frames={len(selected)}, "
        f"detections={sum(r['Detections'] for r in selected)}, "
        f"median_inference_ms="
        f"{statistics.median(r['InferenceMs'] for r in selected):.3f}"
    )

print("Comparison CSV saved:", OUTPUT.exists())
