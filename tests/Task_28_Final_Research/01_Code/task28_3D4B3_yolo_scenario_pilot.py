import csv
import hashlib
import json
import math
import statistics
import time
from collections import defaultdict
from pathlib import Path

import cv2
import torch
import ultralytics
from ultralytics import YOLO

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests/Task_28_Final_Research"
DATA = TASK / "02_CSV_Data"
PLOTS = TASK / "04_Plots/Camera_YOLO_Comparison"
FINDINGS = TASK / "06_Research_Findings"

MODEL = (
    ROOT / "tests/Task_18_Final_Research"
    / "03_Configurations/Models/yolo11s.pt"
)

EXPECTED_MODEL_HASH = (
    "85A76FE86DD8AFE384648546B56A7A78580C7CB7B404FC595F97969322D502D5"
)

MANIFEST = DATA / "task28_3D4B2_camera_image_manifest.csv"

TIMING_CSV = DATA / "task28_3D4B3_yolo_cpu_timing.csv"
DETECTION_CSV = DATA / "task28_3D4B3_yolo_detections.csv"
FRAME_CSV = DATA / "task28_3D4B3_yolo_frame_summary.csv"
SCENARIO_CSV = DATA / "task28_3D4B3_yolo_scenario_summary.csv"
REPORT = FINDINGS / "task28_3D4B3_yolo_pilot_report.json"
ANNOTATED = PLOTS / "YOLO_Annotated"

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_mor100",
    "fog_postfix_validation",
]

TIMED_REPEATS = 10
WARMUPS = 3
CONFIDENCE = 0.15
IMAGE_SIZE = 640

TIMING_FIELDS = [
    "Scenario", "Frame", "Repeat",
    "Detections", "Elapsed_ms",
]

DETECTION_FIELDS = [
    "Scenario", "Frame", "ClassID",
    "ClassName", "Confidence",
    "X1", "Y1", "X2", "Y2",
]

FRAME_FIELDS = [
    "Scenario", "Frame", "Image",
    "Detections", "MeanConfidence",
    "MedianLatency_ms", "P95Latency_ms",
    "P99Latency_ms", "MinLatency_ms",
    "MaxLatency_ms",
]

SCENARIO_FIELDS = [
    "Scenario", "Images",
    "ImagesWithDetections",
    "TotalDetections",
    "MeanDetectionsPerImage",
    "MedianImageLatency_ms",
    "P95ImageLatency_ms",
    "P99ImageLatency_ms",
]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()


def percentile(values, p):
    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * p
    low = math.floor(pos)
    high = math.ceil(pos)
    return (
        sorted_values[low]
        + (sorted_values[high] - sorted_values[low])
        * (pos - low)
    )


def load_manifest():
    if not MANIFEST.is_file():
        raise RuntimeError("Image manifest missing")

    with MANIFEST.open(
        "r", newline="", encoding="utf-8-sig"
    ) as f:
        entries = list(csv.DictReader(f))

    if len(entries) != 20:
        raise RuntimeError(
            f"Expected 20 images; found {len(entries)}"
        )

    counts = {
        scenario: 0 for scenario in SCENARIOS
    }

    for entry in entries:
        scenario = entry["Scenario"]

        if scenario not in counts:
            raise RuntimeError(
                f"Unexpected scenario: {scenario}"
            )

        counts[scenario] += 1

        path = Path(entry["OutputPNG"])

        if (
            not path.is_file()
            or not path.resolve().is_relative_to(
                (PLOTS / "Inputs").resolve()
            )
        ):
            # Python 3.11 supports Path.is_relative_to.
            raise RuntimeError(
                f"Missing/invalid image path: {path}"
            )

        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None:
            raise RuntimeError(f"Cannot decode {path}")

        if image.shape[:2] != (480, 640):
            raise RuntimeError(
                f"Incorrect image dimensions: {path}"
            )

        # Verify that the extracted PNG has the same pixel
        # bytes as the original OSI payload under the Task24
        # RGB convention.
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pixel_hash = hashlib.sha256(
            rgb.tobytes()
        ).hexdigest()

        if pixel_hash.lower() != entry["ImageSHA256"].lower():
            raise RuntimeError(
                f"Camera pixel hash mismatch: {path}"
            )

        entry["_image"] = image
        entry["_path"] = path

    if any(value != 5 for value in counts.values()):
        raise RuntimeError(
            f"Unexpected images per scenario: {counts}"
        )

    return entries


def infer(model, image):
    result = model.predict(
        source=image,
        imgsz=IMAGE_SIZE,
        conf=CONFIDENCE,
        device="cpu",
        verbose=False,
        save=False,
    )

    if len(result) != 1:
        raise RuntimeError("Expected one YOLO result")

    return result[0]


def main():
    outputs = [
        TIMING_CSV,
        DETECTION_CSV,
        FRAME_CSV,
        SCENARIO_CSV,
        REPORT,
    ]

    if any(path.exists() for path in outputs):
        raise RuntimeError(
            "Output already exists; prior research preserved"
        )

    if ANNOTATED.exists():
        raise RuntimeError(
            "Annotated output directory already exists"
        )

    if not MODEL.is_file():
        raise RuntimeError("YOLO model missing")

    model_hash = sha256(MODEL)

    if model_hash != EXPECTED_MODEL_HASH:
        raise RuntimeError(
            "YOLO model differs from Task 26"
        )

    entries = load_manifest()

    torch.set_num_threads(4)
    cv2.setNumThreads(1)

    print("\n=== TASK 28.3D.4B.3 YOLO PILOT ===")
    print(f"Model: {MODEL.name}")
    print("Model SHA256 verified: YES")
    print(f"Ultralytics: {ultralytics.__version__}")
    print(f"PyTorch: {torch.__version__}")
    print("Device: CPU")
    print(f"Images: {len(entries)}")
    print(f"Warmups per image: {WARMUPS}")
    print(f"Timed repeats per image: {TIMED_REPEATS}")

    model = YOLO(str(MODEL))

    ANNOTATED.mkdir(parents=True, exist_ok=False)

    timing_rows = []
    detection_rows = []
    frame_rows = []

    for index, entry in enumerate(entries, 1):
        scenario = entry["Scenario"]
        frame = int(entry["Frame"])
        image = entry["_image"]

        for _ in range(WARMUPS):
            infer(model, image)

        durations = []
        counts = []

        for repeat in range(1, TIMED_REPEATS + 1):
            start = time.perf_counter_ns()
            result = infer(model, image)

            duration = (
                time.perf_counter_ns() - start
            ) / 1e6

            count = len(result.boxes)

            durations.append(duration)
            counts.append(count)

            timing_rows.append({
                "Scenario": scenario,
                "Frame": frame,
                "Repeat": repeat,
                "Detections": count,
                "Elapsed_ms": round(duration, 6),
            })

        # Reuse the last timed result to avoid an
        # additional inference run.
        confidence_values = []

        for box in result.boxes:
            cls = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            coords = [
                float(v) for v in box.xyxy[0].tolist()
            ]

            confidence_values.append(confidence)

            detection_rows.append({
                "Scenario": scenario,
                "Frame": frame,
                "ClassID": cls,
                "ClassName": result.names[cls],
                "Confidence": round(confidence, 6),
                "X1": round(coords[0], 4),
                "Y1": round(coords[1], 4),
                "X2": round(coords[2], 4),
                "Y2": round(coords[3], 4),
            })

        annotated = result.plot()

        annotated_path = ANNOTATED / (
            f"task28_3D4B3_{scenario}_"
            f"frame{frame:05d}_yolo.png"
        )

        if not cv2.imwrite(
            str(annotated_path), annotated
        ):
            raise RuntimeError(
                f"Could not save {annotated_path}"
            )

        frame_rows.append({
            "Scenario": scenario,
            "Frame": frame,
            "Image": entry["_path"].name,
            "Detections": len(result.boxes),
            "MeanConfidence": (
                round(statistics.mean(confidence_values), 6)
                if confidence_values else ""
            ),
            "MedianLatency_ms": round(
                statistics.median(durations), 6
            ),
            "P95Latency_ms": round(
                percentile(durations, 0.95), 6
            ),
            "P99Latency_ms": round(
                percentile(durations, 0.99), 6
            ),
            "MinLatency_ms": round(min(durations), 6),
            "MaxLatency_ms": round(max(durations), 6),
        })

        if len(set(counts)) > 1:
            print(
                "WARNING: Detection count varied across "
                f"repeats for {scenario} frame {frame}"
            )

        print(
            f"[{index:02d}/20] "
            f"{scenario} frame={frame} "
            f"detections={len(result.boxes)} "
            f"median={statistics.median(durations):.3f} ms",
            flush=True,
        )

    scenario_rows = []

    for scenario in SCENARIOS:
        selected_frames = [
            r for r in frame_rows
            if r["Scenario"] == scenario
        ]

        selected_times = [
            r["Elapsed_ms"] for r in timing_rows
            if r["Scenario"] == scenario
        ]

        scenario_rows.append({
            "Scenario": scenario,
            "Images": len(selected_frames),
            "ImagesWithDetections": sum(
                r["Detections"] > 0
                for r in selected_frames
            ),
            "TotalDetections": sum(
                r["Detections"] for r in selected_frames
            ),
            "MeanDetectionsPerImage": round(
                statistics.mean(
                    r["Detections"] for r in selected_frames
                ), 4
            ),
            "MedianImageLatency_ms": round(
                statistics.median(selected_times), 5
            ),
            "P95ImageLatency_ms": round(
                percentile(selected_times, 0.95), 5
            ),
            "P99ImageLatency_ms": round(
                percentile(selected_times, 0.99), 5
            ),
        })

    for path, fields, rows in [
        (TIMING_CSV, TIMING_FIELDS, timing_rows),
        (DETECTION_CSV, DETECTION_FIELDS, detection_rows),
        (FRAME_CSV, FRAME_FIELDS, frame_rows),
        (SCENARIO_CSV, SCENARIO_FIELDS, scenario_rows),
    ]:
        with path.open(
            "x", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=fields
            )
            writer.writeheader()
            writer.writerows(rows)

    report = {
        "task": "28.3D.4B.3",
        "model": str(MODEL),
        "model_sha256": model_hash,
        "ultralytics_version": ultralytics.__version__,
        "torch_version": torch.__version__,
        "opencv_version": cv2.__version__,
        "device": "cpu",
        "torch_threads": 4,
        "image_size": IMAGE_SIZE,
        "confidence_threshold": CONFIDENCE,
        "warmups_per_image": WARMUPS,
        "timed_repeats_per_image": TIMED_REPEATS,
        "images_tested": len(entries),
        "timing_observations": len(timing_rows),
        "detections_reported": len(detection_rows),
        "image_encoding_convention":
            "Task24_RGB_assumption_not_source_verified",
        "image_bytes_verified_against_manifest": True,
        "model_load_excluded_from_timing": True,
        "disk_read_excluded_from_timing": True,
        "prediction_preprocess_inference_postprocess_timed": True,
        "recordings_matched_by_scene": False,
        "ground_truth_detection_accuracy_validated": False,
        "hardware_energy_measured": False,
        "scenario_summary": scenario_rows,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=== FOUR-SCENARIO YOLO RESULTS ===")

    for r in scenario_rows:
        print(f"\nScenario: {r['Scenario']}")
        print(f"Images tested: {r['Images']}")
        print(
            f"Images with detections: "
            f"{r['ImagesWithDetections']}"
        )
        print(f"Total detected boxes: {r['TotalDetections']}")
        print(
            f"Median CPU latency: "
            f"{r['MedianImageLatency_ms']:.3f} ms"
        )
        print(
            f"P99 CPU latency: "
            f"{r['P99ImageLatency_ms']:.3f} ms"
        )

    print(f"\nTotal timed observations: {len(timing_rows)}")
    print(f"Annotated images: {len(frame_rows)}")
    print(f"Detection CSV: {DETECTION_CSV}")
    print(f"Frame summary: {FRAME_CSV}")
    print(f"Scenario summary: {SCENARIO_CSV}")
    print(f"Research report: {REPORT}")
    print("ORIGINAL_OSI_MODIFIED: NO")
    print("DETECTION_ACCURACY_VALIDATED: NO")
    print("STATUS: TASK 28.3D.4B.3 SUCCESS")


if __name__ == "__main__":
    main()
