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

image_path = base / "Camera_NoVisualizer_V2_2122" / "clean_camera_02_frame00530.png"

output_path = base / "C02_V2_YOLO_Frame0530.png"
csv_path = base / "C02_V2_YOLO_Frame0530.csv"

model = YOLO(str(model_path))

results = model.predict(
    source=str(image_path),
    imgsz=640,
    conf=0.15,
    device="cpu",
    verbose=False
)

result = results[0]

rows = []

for box in result.boxes:
    class_id = int(box.cls[0].item())
    confidence = float(box.conf[0].item())
    x1, y1, x2, y2 = [
        float(v) for v in box.xyxy[0].tolist()
    ]

    rows.append({
        "Frame": 530,
        "ClassID": class_id,
        "ClassName": result.names[class_id],
        "Confidence": confidence,
        "X1": x1,
        "Y1": y1,
        "X2": x2,
        "Y2": y2
    })

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

annotated = result.plot()

if not cv2.imwrite(str(output_path), annotated):
    raise RuntimeError("Failed to save annotated image")

print("\n=== TASK 24.7.13 RESULTS ===")
print("MODEL=", model_path.name)
print("CAMERA_FRAME=530")
print("DETECTIONS=", len(rows))

for row in rows:
    print(
        f"CLASS={row['ClassName']} "
        f"CONFIDENCE={row['Confidence']:.3f} "
        f"BBOX=({row['X1']:.1f}, {row['Y1']:.1f}, "
        f"{row['X2']:.1f}, {row['Y2']:.1f})"
    )

print("ANNOTATED_IMAGE=", output_path)
print("DETECTION_CSV=", csv_path)
print("ORIGINAL_IMAGE_MODIFIED=NO")
print("OSI_MODIFIED=NO")
print("TASK24_07_13_YOLO_COMPLETE")