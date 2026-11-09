from pathlib import Path
import shutil
from ultralytics import YOLO

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

MODEL_DIR = BASE / "03_Configurations" / "Models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("\n=== TASK 18.6C YOLO MODEL SETUP ===")

model = YOLO("yolo11n.pt")

print("Model loaded successfully")
print("Model task:", model.task)
print("Number of classes:", len(model.names))

for index in [0, 2, 5, 7]:
    print(f"Class {index}: {model.names[index]}")

source = Path(model.ckpt_path)

if source.exists():
    destination = MODEL_DIR / "yolo11n.pt"

    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)

    print("Model saved in research folder:", destination.exists())
    print("Model size (MB):",
          round(destination.stat().st_size / 1_000_000, 2))
else:
    print("Model source path not found:", source)

print("\n=== MODEL SETUP COMPLETE ===")
