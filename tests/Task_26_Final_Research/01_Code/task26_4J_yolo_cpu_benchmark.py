from pathlib import Path
import csv
import hashlib
import json
import math
import platform
import statistics
import time

import cv2
import numpy as np
import torch
import ultralytics
from ultralytics import YOLO

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
TASK26 = TESTS / "Task_26_Final_Research"

MODEL = (
    TESTS / "Task_18_Final_Research"
    / "03_Configurations" / "Models" / "yolo11s.pt"
)

IMAGE_DIR = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario" / "C02_MovingTarget"
    / "Camera_NoVisualizer_V2_2122"
)

IMAGES = [
    (0, "clean_camera_01_frame00000.png"),
    (530, "clean_camera_02_frame00530.png"),
    (1060, "clean_camera_03_frame01060.png"),
    (1591, "clean_camera_04_frame01591.png"),
    (2121, "clean_camera_05_frame02121.png"),
]

TIMING = TASK26 / "02_CSV_Data" / "task26_4J_yolo_cpu_timing.csv"
SUMMARY = TASK26 / "02_CSV_Data" / "task26_4J_yolo_cpu_summary.csv"
REPORT = TASK26 / "06_Research_Findings" / "task26_4J_yolo_cpu_report.json"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def percentile(values, p):
    v = sorted(values)
    pos = (len(v) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)

def predict(model, image):
    results = model.predict(
        source=image,
        imgsz=640,
        conf=0.15,
        device="cpu",
        verbose=False,
        save=False,
    )
    if len(results) != 1:
        raise RuntimeError("Expected one YOLO result")
    return results[0]

def main():
    for path in (TIMING, SUMMARY, REPORT):
        if path.exists():
            raise FileExistsError(f"Existing output preserved: {path}")

    if not MODEL.is_file():
        raise FileNotFoundError(MODEL)

    torch.set_num_threads(4)
    cv2.setNumThreads(1)

    frames = []
    for frame, filename in IMAGES:
        path = IMAGE_DIR / filename
        image = cv2.imread(str(path))
        if image is None:
            raise RuntimeError(f"Cannot read image: {path}")
        frames.append((frame, filename, path, image))

    start = time.perf_counter_ns()
    model = YOLO(str(MODEL))
    model_load_ms = (time.perf_counter_ns() - start) / 1e6

    raw = []
    summaries = []

    for frame, filename, path, image in frames:
        for _ in range(3):
            predict(model, image)

        durations = []
        counts = []

        for repeat in range(1, 11):
            start = time.perf_counter_ns()
            result = predict(model, image)
            duration = (time.perf_counter_ns() - start) / 1e6

            count = len(result.boxes)
            durations.append(duration)
            counts.append(count)

            raw.append({
                "frame": frame,
                "filename": filename,
                "repeat": repeat,
                "detections": count,
                "elapsed_ms": duration,
            })

        summaries.append({
            "frame": frame,
            "filename": filename,
            "detections": counts[-1],
            "median_ms": statistics.median(durations),
            "p95_ms": percentile(durations, 0.95),
            "p99_ms": percentile(durations, 0.99),
            "mean_ms": statistics.mean(durations),
        })

        print(
            f"FRAME={frame} "
            f"DETECTIONS={counts[-1]} "
            f"MEDIAN_MS={statistics.median(durations):.4f} "
            f"P99_MS={percentile(durations, 0.99):.4f}"
        )

    TIMING.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    for path, rows in ((TIMING, raw), (SUMMARY, summaries)):
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    report = {
        "task": "26.4J",
        "model_sha256": sha256(MODEL),
        "model_load_ms": model_load_ms,
        "torch_version": torch.__version__,
        "ultralytics_version": ultralytics.__version__,
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "python_version": platform.python_version(),
        "device": "cpu",
        "cpu_threads": 4,
        "warmup_per_image": 3,
        "timed_runs_per_image": 10,
        "image_hashes": {
            filename: sha256(path)
            for _, filename, path, _ in frames
        },
        "summary": summaries,
        "disk_read_timed": False,
        "model_load_included_in_timing": False,
        "prediction_preprocessing_timed": True,
        "prediction_inference_timed": True,
        "prediction_postprocessing_timed": True,
        "energy_measured": False,
        "accuracy_validated": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print("=== TASK 26.4J YOLO CPU BENCHMARK ===")
    print("IMAGES_TESTED:", len(frames))
    print("TIMING_ROWS:", len(raw))
    print("MODEL_LOAD_MS:", round(model_load_ms, 3))
    print("CPU_INFERENCE: YES")
    print("END_TO_END_GEMSTAR: NO")
    print("ENERGY_MEASURED: NO")
    print("TASK26_4J_YOLO_CPU_BENCHMARK_PASS")

if __name__ == "__main__":
    main()
