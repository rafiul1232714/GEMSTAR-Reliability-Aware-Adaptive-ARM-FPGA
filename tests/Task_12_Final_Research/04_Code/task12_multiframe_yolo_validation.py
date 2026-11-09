
# TASK 12.6C - MULTI-FRAME YOLO11s / GROUND TRUTH
# GEMSTAR MOR100 - 8 candidate camera frames
# Geometric association is provisional, not confirmed.

from pathlib import Path
import csv
import time
import math
import shutil

import cv2
import torch
from ultralytics import YOLO

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
TASK = ROOT / "tests" / "Task_12_Final_Research"

DATA = TASK / "02_CSV_Data"
GRAPHS = TASK / "01_Graphs"
CODE = TASK / "04_Code"
FINDINGS = TASK / "06_Research_Findings"

IMAGE_DIR = (
    ROOT / "results" / "figures" / "fog_mor100_camera"
)

INPUT = DATA / "task12_6_camera_gt_visibility_candidates.csv"

for folder in [DATA, GRAPHS, CODE, FINDINGS]:
    folder.mkdir(parents=True, exist_ok=True)

assert INPUT.is_file(), f"Missing CSV: {INPUT}"

with INPUT.open(newline="", encoding="utf-8-sig") as f:
    candidates = [
        row for row in csv.DictReader(f)
        if int(row["center_in_image"]) == 1
    ]

print("\n===== TASK 12.6C - MULTI-FRAME YOLO =====")
print("Candidate frames:", len(candidates))
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

MODEL_NAME = "yolo11s.pt"
DEVICE = "cpu"
CONF = 0.05
IMGSZ = 640

model = YOLO(MODEL_NAME)

# COCO vehicle categories
VEHICLE_CLASSES = {2, 3, 5, 7}

# Warm up without including first-use overhead in timing.
first_image = IMAGE_DIR / candidates[0]["image_filename"]
warmup_image = cv2.imread(str(first_image))

assert warmup_image is not None, "First Camera image missing."

model.predict(
    source=warmup_image,
    device=DEVICE,
    imgsz=IMGSZ,
    conf=CONF,
    verbose=False
)

records = []
all_detections = []

for row in candidates:

    frame = int(row["frame"])
    image_path = IMAGE_DIR / row["image_filename"]

    img = cv2.imread(str(image_path))

    if img is None:
        print(f"Frame {frame}: IMAGE UNAVAILABLE")
        continue

    gt_u = float(row["projected_u_px"])
    gt_v = float(row["projected_v_px"])

    start = time.perf_counter()

    result = model.predict(
        source=img,
        device=DEVICE,
        imgsz=IMGSZ,
        conf=CONF,
        verbose=False
    )[0]

    elapsed_ms = (time.perf_counter() - start) * 1000

    height, width = img.shape[:2]

    vehicle_detections = []

    for box in result.boxes:

        class_id = int(box.cls.item())

        if class_id not in VEHICLE_CLASSES:
            continue

        confidence = float(box.conf.item())

        x1, y1, x2, y2 = [
            float(v) for v in box.xyxy[0].tolist()
        ]

        center_u = (x1 + x2) / 2
        center_v = (y1 + y2) / 2

        center_error = math.hypot(
            center_u - gt_u,
            center_v - gt_v
        )

        gt_inside = (
            x1 <= gt_u <= x2 and
            y1 <= gt_v <= y2
        )

        detection = {
            "frame": frame,
            "class_name": model.names[class_id],
            "confidence": confidence,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "bbox_center_u": center_u,
            "bbox_center_v": center_v,
            "gt_center_error_px": center_error,
            "gt_center_inside_bbox": int(gt_inside),
        }

        vehicle_detections.append(detection)
        all_detections.append(detection)

    # Candidate assignment only:
    # prefer a vehicle box containing the projected GT center.
    containing = [
        d for d in vehicle_detections
        if d["gt_center_inside_bbox"]
    ]

    if containing:
        best = min(
            containing,
            key=lambda d: d["gt_center_error_px"]
        )
        status = "PROVISIONAL_GT_CENTER_OVERLAP"
    elif vehicle_detections:
        best = min(
            vehicle_detections,
            key=lambda d: d["gt_center_error_px"]
        )
        status = "VEHICLE_DETECTED_NO_GT_OVERLAP"
    else:
        best = None
        status = "NO_VEHICLE_DETECTION"

    # Annotate image
    annotated = result.plot()
    point = (round(gt_u), round(gt_v))

    cv2.drawMarker(
        annotated,
        point,
        (0, 255, 255),
        cv2.MARKER_CROSS,
        18,
        2
    )

    cv2.putText(
        annotated,
        "Projected GT 76865 (provisional)",
        (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2
    )

    output_image = GRAPHS / (
        f"task12_6_yolo_frame_{frame:04d}.png"
    )

    cv2.imwrite(str(output_image), annotated)

    record = {
        "frame": frame,
        "time_s": row["time_s"],
        "gt_distance_m": row["gt_distance_m"],
        "gt_u_px": gt_u,
        "gt_v_px": gt_v,
        "vehicle_detection_count": len(vehicle_detections),
        "candidate_status": status,
        "candidate_class": best["class_name"] if best else "",
        "candidate_confidence": best["confidence"] if best else "",
        "bbox_x1": best["x1"] if best else "",
        "bbox_y1": best["y1"] if best else "",
        "bbox_x2": best["x2"] if best else "",
        "bbox_y2": best["y2"] if best else "",
        "center_error_px": (
            best["gt_center_error_px"] if best else ""
        ),
        "prediction_wall_ms": elapsed_ms,
        "image_filename": row["image_filename"],
    }

    records.append(record)

    print(
        f"Frame {frame:3d} | "
        f"distance={float(row['gt_distance_m']):6.2f}m | "
        f"vehicles={len(vehicle_detections)} | "
        f"{status} | "
        f"{elapsed_ms:.1f}ms"
    )

# Save frame-level summary
summary_file = DATA / "task12_6_multiframe_yolo_summary.csv"

with summary_file.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(records[0].keys())
    )
    writer.writeheader()
    writer.writerows(records)

# Save every vehicle detection, not only selected candidates.
detection_file = DATA / "task12_6_all_vehicle_detections.csv"

with detection_file.open(
    "w", newline="", encoding="utf-8"
) as f:
    fields = [
        "frame", "class_name", "confidence",
        "x1", "y1", "x2", "y2",
        "bbox_center_u", "bbox_center_v",
        "gt_center_error_px", "gt_center_inside_bbox"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(all_detections)

overlap = sum(
    r["candidate_status"] ==
    "PROVISIONAL_GT_CENTER_OVERLAP"
    for r in records
)

with_vehicle = sum(
    r["vehicle_detection_count"] > 0
    for r in records
)

report = [
    "TASK 12.6C - MULTI-FRAME YOLO VALIDATION",
    "Scenario: GEMSTAR MOR100",
    "Target GT ID: 76865",
    f"Model: {MODEL_NAME}",
    f"Device: {DEVICE}",
    f"Confidence threshold: {CONF}",
    f"Frames processed: {len(records)}",
    f"Frames with any vehicle detection: {with_vehicle}",
    f"Frames with provisional GT-center overlap: {overlap}",
    "",
    "IMPORTANT LIMITATIONS:",
    "GT center positions use provisional camera calibration.",
    "GT centers inside images do not guarantee actual visibility.",
    "A GT center inside a detection box is not proof of identity.",
    "No verified detection recall can be calculated yet.",
    "Image color ordering remains an implementation assumption.",
    "Single-run wall times are not controlled benchmarks.",
    "Frame 431 is a distant-object diagnostic.",
]

(FINDINGS / "task12_6_multiframe_yolo_findings.txt").write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\n===== FINAL SUMMARY =====")
print("Frames processed:", len(records))
print("Frames with vehicle detections:", with_vehicle)
print("Frames with provisional GT overlap:", overlap)
print("Saved CSV:", summary_file)
print("Saved detections:", detection_file)
print("Annotated images folder:", GRAPHS)
print("TASK 12.6C COMPLETED")
