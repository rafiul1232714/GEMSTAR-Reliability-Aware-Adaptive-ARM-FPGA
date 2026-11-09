from pathlib import Path
import csv
import statistics
import numpy as np
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
    raise RuntimeError("Expected 12 Camera images")

REPEATS = 5

settings = dict(
    device="cpu",
    imgsz=640,
    conf=0.25,
    iou=0.70,
    agnostic_nms=True,
    verbose=False
)

measurements = []
summaries = []

print("\n=== TASK 18.9A REPEATED CPU BENCHMARK ===")

for model_name in ["yolo11n", "yolo11s"]:

    model = YOLO(str(MODELS / f"{model_name}.pt"))

    print("\nBenchmarking:", model_name)

    # Warm up inference.
    for _ in range(5):
        model.predict(str(images[0]), **settings)

    times = []

    for image_path in images:
        frame = int(image_path.stem.rsplit("_", 1)[-1])

        for repetition in range(1, REPEATS + 1):

            result = model.predict(
                str(image_path), **settings
            )[0]

            inference_ms = float(
                result.speed["inference"]
            )

            times.append(inference_ms)

            measurements.append({
                "Model": model_name,
                "Frame": frame,
                "Repeat": repetition,
                "InferenceMs": inference_ms,
                "Detections": len(result.boxes)
            })

        print(f"Frame {frame}: completed {REPEATS} repetitions")

    summaries.append({
        "Model": model_name,
        "Measurements": len(times),
        "MeanMs": statistics.mean(times),
        "MedianMs": statistics.median(times),
        "StdDevMs": statistics.stdev(times),
        "P95Ms": float(np.percentile(times, 95)),
        "MinMs": min(times),
        "MaxMs": max(times)
    })

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

DETAIL = CSV_DIR / "task18_repeated_cpu_benchmark.csv"
SUMMARY = CSV_DIR / "task18_repeated_cpu_summary.csv"

write_csv(DETAIL, measurements)
write_csv(SUMMARY, summaries)

print("\n=== TASK 18.9A BENCHMARK RESULTS ===")

for row in summaries:
    print(
        f'{row["Model"]}: '
        f'measurements={row["Measurements"]}, '
        f'median={row["MedianMs"]:.3f} ms, '
        f'mean={row["MeanMs"]:.3f} ms, '
        f'p95={row["P95Ms"]:.3f} ms, '
        f'std={row["StdDevMs"]:.3f} ms'
    )

print("\nMeasurement CSV saved:", DETAIL.exists())
print("Summary CSV saved:", SUMMARY.exists())
