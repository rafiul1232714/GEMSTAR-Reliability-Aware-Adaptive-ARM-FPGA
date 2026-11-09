from pathlib import Path
import csv
import shutil
import time

import cv2
from ultralytics import YOLO

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

MODEL_DIR = BASE / "03_Configurations" / "Models"
IMAGE_DIR = BASE / "08_Extracted_Images" / "Selected_Frames"
OUT = BASE / "08_Extracted_Images" / "YOLO11s_Detections"
CSV_DIR = BASE / "02_CSV_Data"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

print("\n=== TASK 18.7B STRONGER DETECTOR ===")

local_model = MODEL_DIR / "yolo11s.pt"

if local_model.exists():
    model = YOLO(str(local_model))
else:
    model = YOLO("yolo11s.pt")

    source = Path(model.ckpt_path)
    if source.exists() and source.resolve() != local_model.resolve():
        shutil.copy2(source, local_model)

print("Model:", "YOLO11 Small")
print("Model saved:", local_model.exists())

images = sorted(IMAGE_DIR.glob("task18_camera_frame_*.png"))

if len(images) != 12:
    raise RuntimeError(f"Expected 12 images, found {len(images)}")

# Warm-up before measurement.
model.predict(
    str(images[0]), device="cpu", imgsz=640,
    conf=0.25, agnostic_nms=True, verbose=False
)

details = []
summary = []

for path in images:
    frame = int(path.stem.rsplit("_", 1)[-1])

    start = time.perf_counter()

    result = model.predict(
        str(path),
        device="cpu",
        imgsz=640,
        conf=0.25,
        agnostic_nms=True,
        verbose=False
    )[0]

    wall_ms = (time.perf_counter() - start) * 1000

    annotated = result.plot()
    cv2.imwrite(
        str(OUT / f"task18_yolo11s_frame_{frame:03d}.png"),
        annotated
    )

    counts = {}

    for box in result.boxes:
        cls = int(box.cls.item())
        name = model.names[cls]
        confidence = float(box.conf.item())
        xyxy = [float(x) for x in box.xyxy[0].tolist()]

        counts[name] = counts.get(name, 0) + 1

        details.append({
            "Frame": frame,
            "ClassName": name,
            "Confidence": confidence,
            "X1": xyxy[0],
            "Y1": xyxy[1],
            "X2": xyxy[2],
            "Y2": xyxy[3]
        })

    summary.append({
        "Frame": frame,
        "Detections": len(result.boxes),
        "Classes": "; ".join(
            f"{k}:{v}" for k, v in sorted(counts.items())
        ),
        "InferenceMs": result.speed.get("inference", 0),
        "TotalWallMs": wall_ms
    })

    print(
        f"Frame {frame:3d} | "
        f"Objects={len(result.boxes)} | "
        f"Classes={summary[-1]['Classes'] or 'none'} | "
        f"Inference={summary[-1]['InferenceMs']:.2f} ms"
    )

def save_csv(name, rows, headers):
    with (CSV_DIR / name).open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

save_csv(
    "task18_yolo11s_detections.csv",
    details,
    ["Frame", "ClassName", "Confidence", "X1", "Y1", "X2", "Y2"]
)

save_csv(
    "task18_yolo11s_frame_summary.csv",
    summary,
    ["Frame", "Detections", "Classes", "InferenceMs", "TotalWallMs"]
)

print("\n=== TASK 18.7B SUMMARY ===")
print("Frames processed:", len(summary))
print("Total detections:", len(details))
print("Annotated images:", len(list(OUT.glob("*.png"))))
print("Detection CSV saved:",
      (CSV_DIR / "task18_yolo11s_detections.csv").exists())
print("Summary CSV saved:",
      (CSV_DIR / "task18_yolo11s_frame_summary.csv").exists())
