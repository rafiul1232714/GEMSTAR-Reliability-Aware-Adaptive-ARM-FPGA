from pathlib import Path
import csv
import cv2
from ultralytics import YOLO

base = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

model_path = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research\03_Configurations\Models\yolo11s.pt"
)

image_dir = base / "Camera_NoVisualizer_V2_2122"
output_dir = base / "C02_V2_MultiFrame_YOLO_Results"

images = [
    (0, "clean_camera_01_frame00000.png"),
    (530, "clean_camera_02_frame00530.png"),
    (1060, "clean_camera_03_frame01060.png"),
    (1591, "clean_camera_04_frame01591.png"),
    (2121, "clean_camera_05_frame02121.png"),
]

for _, filename in images:
    if not (image_dir / filename).is_file():
        raise FileNotFoundError(filename)

output_dir.mkdir(parents=False, exist_ok=False)

model = YOLO(str(model_path))

rows = []

for frame, filename in images:
    result = model.predict(
        source=str(image_dir / filename),
        imgsz=640,
        conf=0.15,
        device="cpu",
        verbose=False
    )[0]

    frame_detections = 0

    for box in result.boxes:
        cls = int(box.cls[0].item())
        conf = float(box.conf[0].item())

        x1, y1, x2, y2 = [
            float(v) for v in box.xyxy[0].tolist()
        ]

        rows.append({
            "Frame": frame,
            "ClassID": cls,
            "ClassName": result.names[cls],
            "Confidence": conf,
            "X1": x1,
            "Y1": y1,
            "X2": x2,
            "Y2": y2
        })

        frame_detections += 1

    annotated = result.plot()

    out_image = output_dir / f"frame_{frame:05d}_yolo.png"

    if not cv2.imwrite(str(out_image), annotated):
        raise RuntimeError(f"Cannot save {out_image}")

    print(
        f"FRAME={frame} "
        f"DETECTIONS={frame_detections} "
        f"IMAGE={out_image.name}"
    )

csv_path = output_dir / "C02_V2_MultiFrame_YOLO_Detections.csv"

with csv_path.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Frame", "ClassID", "ClassName",
            "Confidence", "X1", "Y1", "X2", "Y2"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("\n=== FINAL RESULTS ===")
print("MODEL=", model_path.name)
print("FRAMES_TESTED=", len(images))
print("TOTAL_DETECTIONS=", len(rows))
print("OUTPUT_DIR=", output_dir)
print("CSV=", csv_path)
print("ORIGINAL_IMAGES_MODIFIED=NO")
print("OSI_MODIFIED=NO")
print("TASK24_07_20_MULTIFRAME_YOLO_COMPLETE")