import sys
import json
import time
import hashlib
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TESTS = ROOT / "tests"

TASK23_CODE = TESTS / "Task_23_Final_Research" / "01_Code"
sys.path.insert(0, str(TASK23_CODE))

from task23_15_camera_adapter import process_camera

import cv2
import torch
from ultralytics import YOLO

IMAGE = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
    / "Camera_NoVisualizer_V2_2122"
    / "clean_camera_02_frame00530.png"
)

MODEL = (
    TESTS / "Task_18_Final_Research"
    / "03_Configurations"
    / "Models"
    / "yolo11s.pt"
)

OUTPUT = (
    TESTS / "Task_29_Final_Research"
    / "06_Research_Findings"
    / "task29_4B8C_camera_ai_cpu_execution.json"
)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)

    for path in (IMAGE, MODEL):
        if not path.is_file():
            raise FileNotFoundError(path)

    cv2.setNumThreads(1)
    torch.set_num_threads(4)

    image = cv2.imread(str(IMAGE), cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError("Camera image cannot be decoded")

    height, width = image.shape[:2]

    timestamp_ns = 1_000_000_000

    start = time.perf_counter_ns()

    camera = process_camera(
        image,
        timestamp_ns=timestamp_ns,
        roi=None
    )

    preprocessing_end = time.perf_counter_ns()

    if camera.status != "VALID":
        raise RuntimeError(
            f"Camera preprocessing status: {camera.status}"
        )

    model = YOLO(str(MODEL))

    # Warm-up is not included in the measured run.
    for _ in range(3):
        model.predict(
            source=image,
            imgsz=640,
            conf=0.15,
            device="cpu",
            verbose=False,
            save=False
        )

    inference_start = time.perf_counter_ns()

    predictions = model.predict(
        source=image,
        imgsz=640,
        conf=0.15,
        device="cpu",
        verbose=False,
        save=False
    )

    inference_end = time.perf_counter_ns()

    if len(predictions) != 1:
        raise RuntimeError("Expected exactly one prediction result")

    result = predictions[0]
    detections = len(result.boxes)

    if detections < 0:
        raise RuntimeError("Invalid detection count")

    record = {
        "task": "29.4B.8C",
        "status": "PASS",
        "data_type": "REAL_GEMSTAR_CAMERA_IMAGE",
        "frame": 530,
        "image_path": str(IMAGE),
        "image_sha256": sha256(IMAGE),
        "model_path": str(MODEL),
        "model_sha256": sha256(MODEL),
        "image_width": width,
        "image_height": height,
        "camera_status": camera.status,
        "camera_quality_fields": list(camera.quality.keys()),
        "yolo_model": "yolo11s",
        "yolo_confidence": 0.15,
        "detections": detections,
        "camera_preprocessing_ms": (
            preprocessing_end - start
        ) / 1e6,
        "yolo_inference_ms": (
            inference_end - inference_start
        ) / 1e6,
        "execution": "WORKSTATION_CPU",
        "timestamp_is_synthetic_test_metadata": True,
        "independent_sensor_sync_verified": False,
        "model_loading_timed": False,
        "disk_read_timed": False,
        "benchmark_repeat_count": 1,
        "accuracy_validated": False,
        "fusion_included": False,
        "energy_measured": False
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("x", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    print("CAMERA_FRAME: 530", flush=True)
    print("IMAGE_SIZE:", width, "x", height, flush=True)
    print("CAMERA_STATUS:", camera.status, flush=True)
    print("YOLO_MODEL: yolo11s", flush=True)
    print("DETECTIONS:", detections, flush=True)
    print(
        "CAMERA_PREPROCESSING_MS:",
        round(record["camera_preprocessing_ms"], 6),
        flush=True
    )
    print(
        "YOLO_INFERENCE_MS:",
        round(record["yolo_inference_ms"], 6),
        flush=True
    )
    print("TASK 29.4B.8C: PASS", flush=True)

if __name__ == "__main__":
    main()
