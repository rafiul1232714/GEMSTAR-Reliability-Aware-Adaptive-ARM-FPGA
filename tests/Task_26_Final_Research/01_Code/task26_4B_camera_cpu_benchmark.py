from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import math
import statistics
import time

import cv2
import numpy as np

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
TASK23 = ROOT / "Task_23_Final_Research"
TASK26 = ROOT / "Task_26_Final_Research"

SOURCE = TASK23 / "01_Code" / "task23_12C_06_camera_cpu_preprocessing.py"

IMAGE_DIR = (
    TASK23 / "08_Processed_Data"
    / "Camera_Weather_Comparison"
)

IMAGES = {
    "CLEAR": "CLEAR_t0200ms.png",
    "FOG100": "FOG100_t0200ms.png",
    "FOG20": "FOG20_t0200ms.png",
}

CSV_OUT = TASK26 / "02_CSV_Data" / "task26_4B_camera_cpu_timing.csv"
SUMMARY_OUT = TASK26 / "02_CSV_Data" / "task26_4B_camera_cpu_summary.csv"
REPORT_OUT = TASK26 / "06_Research_Findings" / "task26_4B_camera_cpu_report.json"

WARMUP = 20
REPEATS = 100

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def percentile(values, p):
    v = sorted(values)
    pos = (len(v)-1)*p/100
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return v[lo] + (v[hi]-v[lo])*(pos-lo)

def load_processor():
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    spec = importlib.util.spec_from_file_location(
        "task26_camera_reference", SOURCE
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Camera processor import failed")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.preprocess_camera

def main():
    if any(p.exists() for p in (CSV_OUT, SUMMARY_OUT, REPORT_OUT)):
        raise FileExistsError(
            "Existing Task 26.4B results detected; no files overwritten."
        )

    # Fixed OpenCV threading policy for reproducibility.
    cv2.setNumThreads(1)
    process = load_processor()

    raw_rows = []
    summary_rows = []
    image_manifest = []

    for weather, filename in IMAGES.items():
        path = IMAGE_DIR / filename
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None:
            raise RuntimeError(f"Cannot read image: {path}")

        height, width = image.shape[:2]

        # Centered ROI, only when image dimensions permit.
        roi_w, roi_h = 384, 288
        options = [("FULL", None)]

        if width >= roi_w and height >= roi_h:
            roi_x = (width - roi_w) // 2
            roi_y = (height - roi_h) // 2
            options.append(
                ("ROI", (roi_x, roi_y, roi_w, roi_h))
            )

        image_manifest.append({
            "weather": weather,
            "path": str(path),
            "sha256": sha256(path),
            "width": width,
            "height": height,
        })

        for mode, roi in options:

            reference = process(image, roi=roi)
            if reference["status"] != "VALID":
                raise RuntimeError(
                    f"Unexpected result: {weather}/{mode}"
                )

            # Warm-up runs are not recorded.
            for _ in range(WARMUP):
                process(image, roi=roi)

            times = []

            for run in range(1, REPEATS + 1):
                start = time.perf_counter_ns()
                result = process(image, roi=roi)
                elapsed = time.perf_counter_ns() - start

                if result["status"] != "VALID":
                    raise RuntimeError("Invalid timed output")

                duration_ms = elapsed / 1e6
                times.append(duration_ms)

                raw_rows.append({
                    "weather": weather,
                    "mode": mode,
                    "repeat": run,
                    "image_width": width,
                    "image_height": height,
                    "processed_pixels": result["grayscale"].size,
                    "elapsed_ms": duration_ms
                })

            quality = reference["features"]

            summary_rows.append({
                "weather": weather,
                "mode": mode,
                "processed_pixels": reference["grayscale"].size,
                "mean_ms": statistics.mean(times),
                "median_ms": statistics.median(times),
                "p95_ms": percentile(times, 95),
                "p99_ms": percentile(times, 99),
                "min_ms": min(times),
                "max_ms": max(times),
                "edge_density": quality["edge_density"],
                "contrast_std": quality["contrast_std"],
                "mean_luminance": quality["mean_luminance"],
                "laplacian_variance": quality["laplacian_variance"],
                "mean_saturation": quality["mean_saturation"]
            })

            print(
                f"{weather} {mode}: "
                f"pixels={reference['grayscale'].size} "
                f"median={statistics.median(times):.4f}ms "
                f"p95={percentile(times,95):.4f}ms "
                f"p99={percentile(times,99):.4f}ms"
            )

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)

    for path, rows in (
        (CSV_OUT, raw_rows),
        (SUMMARY_OUT, summary_rows)
    ):
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(rows[0].keys())
            )
            writer.writeheader()
            writer.writerows(rows)

    report = {
        "task": "26.4B",
        "scope": "Camera preprocessing only",
        "source_script": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "opencv_threads": cv2.getNumThreads(),
        "warmup_runs": WARMUP,
        "timed_runs_per_configuration": REPEATS,
        "image_manifest": image_manifest,
        "summary": summary_rows,
        "osi_parsing_timed": False,
        "yolo_timed": False,
        "adapter_loading_timed": False,
        "energy_measured": False,
        "quality_coverage": "Three sampled weather images only"
    }

    with REPORT_OUT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print("=== TASK 26.4B CAMERA BENCHMARK ===")
    print("CONFIGURATIONS:", len(summary_rows))
    print("TIMED_RUNS:", len(raw_rows))
    print("PROCESSING_ONLY: YES")
    print("YOLO_INCLUDED: NO")
    print("ENERGY_MEASURED: NO")
    print("TASK26_4B_CAMERA_CPU_BENCHMARK_PASS")
    print("CSV:", CSV_OUT)
    print("SUMMARY:", SUMMARY_OUT)
    print("REPORT:", REPORT_OUT)

if __name__ == "__main__":
    main()
