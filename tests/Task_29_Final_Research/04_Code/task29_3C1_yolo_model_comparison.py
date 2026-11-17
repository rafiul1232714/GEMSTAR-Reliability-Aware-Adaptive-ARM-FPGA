import csv
import hashlib
import json
import platform
import statistics
import time
from collections import defaultdict
from pathlib import Path

import cv2
import torch
import ultralytics
from ultralytics import YOLO

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
OUT = TASK / "02_CSV_Data"

MODELS = ROOT / "tests" / "Task_18_Final_Research" / "03_Configurations" / "Models"
MANIFEST = ROOT / "tests" / "Task_28_Final_Research" / "02_CSV_Data" / "task28_3D4B2_camera_image_manifest.csv"

RAW_OUT = OUT / "task29_3C1_yolo_comparison_raw.csv"
SUMMARY_OUT = OUT / "task29_3C1_yolo_comparison_summary.csv"
REPORT_OUT = TASK / "06_Research_Findings" / "task29_3C1_yolo_comparison_report.json"

EXPECTED_S_HASH = "85A76FE86DD8AFE384648546B56A7A78580C7CB7B404FC595F97969322D502D5"

REPEATS = 10
WARMUPS = 3
IMAGE_SIZE = 640
CONF = 0.15
IOU = 0.70

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def percentile(values, p):
    a = sorted(values)
    pos = (len(a) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(a) - 1)
    return a[lo] + (a[hi] - a[lo]) * (pos - lo)

def save_csv(path, rows, fields):
    with open(path, "x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def main():
    for path in (RAW_OUT, SUMMARY_OUT, REPORT_OUT):
        if path.exists():
            raise FileExistsError("Existing research output preserved: " + str(path))

    model_paths = {
        "yolo11n": MODELS / "yolo11n.pt",
        "yolo11s": MODELS / "yolo11s.pt",
    }

    for path in model_paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    model_hashes = {
        name: sha256(path)
        for name, path in model_paths.items()
    }

    if model_hashes["yolo11s"] != EXPECTED_S_HASH:
        raise RuntimeError("YOLO11s weight hash mismatch")

    with MANIFEST.open("r", newline="", encoding="utf-8-sig") as f:
        manifest = list(csv.DictReader(f))

    if len(manifest) != 20:
        raise RuntimeError("Expected exactly 20 images")

    images = []

    for item in manifest:
        path = Path(item["OutputPNG"])

        if not path.is_file():
            raise FileNotFoundError(path)

        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None or image.shape[:2] != (480, 640):
            raise RuntimeError("Invalid image: " + str(path))

        # PNG was written from the recorded RGB byte array.
        # Verify decoded pixels match its source payload hash.
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        digest = hashlib.sha256(rgb.tobytes()).hexdigest()

        if digest.lower() != item["ImageSHA256"].lower():
            raise RuntimeError("Source image hash mismatch: " + str(path))

        images.append((item, image))

    torch.set_num_threads(4)
    cv2.setNumThreads(1)

    print("=== TASK 29.3C.1: CONTROLLED YOLO BENCHMARK ===")
    print("Images verified:", len(images))
    print("Model hashes:", model_hashes)
    print("PyTorch:", torch.__version__)
    print("Ultralytics:", ultralytics.__version__)

    models = {
        name: YOLO(str(path))
        for name, path in model_paths.items()
    }

    def predict(model, image):
        result = model.predict(
            source=image,
            device="cpu",
            imgsz=IMAGE_SIZE,
            conf=CONF,
            iou=IOU,
            agnostic_nms=True,
            verbose=False,
            save=False,
        )
        if len(result) != 1:
            raise RuntimeError("Expected one prediction")
        return result[0]

    for name, model in models.items():
        for _ in range(WARMUPS):
            predict(model, images[0][1])
        print("Warm-up complete:", name)

    raw = []

    # Alternate model execution order between repetitions.
    for index, (item, image) in enumerate(images):

        scenario = item["Scenario"]
        frame = int(item["Frame"])

        for repeat in range(1, REPEATS + 1):
            order = ["yolo11n", "yolo11s"]

            if (index + repeat) % 2 == 0:
                order.reverse()

            for model_name in order:
                start = time.perf_counter_ns()
                result = predict(models[model_name], image)
                elapsed = (time.perf_counter_ns() - start) / 1e6

                raw.append({
                    "Scenario": scenario,
                    "Frame": frame,
                    "Model": model_name,
                    "Repeat": repeat,
                    "Detections": len(result.boxes),
                    "ElapsedMs": round(elapsed, 6),
                })

        print(
            "Completed image {}/20: {} frame {}".format(
                index + 1, scenario, frame
            )
        )

    if len(raw) != 400:
        raise RuntimeError("Expected 400 timing rows")

    groups = defaultdict(list)

    for row in raw:
        groups[(row["Scenario"], row["Frame"], row["Model"])].append(row)

    summary = []

    for (scenario, frame, model_name), rows in sorted(groups.items()):
        times = [r["ElapsedMs"] for r in rows]
        counts = [r["Detections"] for r in rows]

        if len(times) != REPEATS:
            raise RuntimeError("Incorrect repeat count")

        if len(set(counts)) != 1:
            raise RuntimeError(
                "Inconsistent detections: {} {} {}".format(
                    scenario, frame, model_name
                )
            )

        summary.append({
            "Scenario": scenario,
            "Frame": frame,
            "Model": model_name,
            "Repetitions": len(times),
            "Detections": counts[0],
            "MedianMs": round(statistics.median(times), 6),
            "P95Ms": round(percentile(times, 0.95), 6),
            "P99Ms": round(percentile(times, 0.99), 6),
            "MeanMs": round(statistics.mean(times), 6),
            "MinMs": round(min(times), 6),
            "MaxMs": round(max(times), 6),
        })

    if len(summary) != 40:
        raise RuntimeError("Expected 40 frame/model summaries")

    OUT.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)

    save_csv(
        RAW_OUT, raw,
        ["Scenario", "Frame", "Model", "Repeat", "Detections", "ElapsedMs"]
    )

    save_csv(
        SUMMARY_OUT, summary,
        ["Scenario", "Frame", "Model", "Repetitions", "Detections",
         "MedianMs", "P95Ms", "P99Ms", "MeanMs", "MinMs", "MaxMs"]
    )

    report = {
        "task": "29.3C.1",
        "images": len(images),
        "models": list(models),
        "weight_sha256": model_hashes,
        "source_manifest": str(MANIFEST),
        "source_image_hashes_verified": True,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "ultralytics_version": ultralytics.__version__,
        "device": "cpu",
        "torch_threads": 4,
        "imgsz": IMAGE_SIZE,
        "confidence": CONF,
        "iou": IOU,
        "agnostic_nms": True,
        "warmups_per_model": WARMUPS,
        "repeats_per_image_per_model": REPEATS,
        "timing_records": len(raw),
        "frame_model_summaries": len(summary),
        "timing_definition": "wall_time_model_predict_preprocess_inference_postprocess",
        "model_loading_timed": False,
        "disk_read_timed": False,
        "energy_measured": False,
        "independent_detection_accuracy_measured": False,
    }

    with REPORT_OUT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=== FINAL SUMMARY ===")

    for model_name in models:
        rows = [r for r in summary if r["Model"] == model_name]
        medians = [r["MedianMs"] for r in rows]
        print(
            "{} | images={} | median_of_image_medians={:.4f} ms".format(
                model_name, len(rows), statistics.median(medians)
            )
        )

    print("Raw timing rows:", len(raw))
    print("Frame-model summary rows:", len(summary))
    print("Report saved:", REPORT_OUT)
    print("\nTASK 29.3C.1: PASS")

if __name__ == "__main__":
    main()
