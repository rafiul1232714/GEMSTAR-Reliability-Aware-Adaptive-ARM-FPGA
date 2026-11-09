
from pathlib import Path
import importlib.util

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")

IMAGE = (
    ROOT / "tests"
    / "Task_11_Final_Research"
    / "01_Graphs"
    / "task11_mor100_frame0150_camera_0.ppm"
)

print("\n===== TASK 11.8E - CAMERA DETECTOR SETUP =====")

for module in ["cv2", "ultralytics", "torch", "onnxruntime"]:

    available = importlib.util.find_spec(module) is not None

    status = "AVAILABLE" if available else "NOT INSTALLED"

    print(f"{module}: {status}")

print("\nCamera image exists:", IMAGE.is_file())

if IMAGE.is_file():
    print("Camera image bytes:", IMAGE.stat().st_size)

if importlib.util.find_spec("cv2") is not None:

    import cv2

    img = cv2.imread(str(IMAGE))

    if img is None:
        print("OpenCV image read: FAILED")
    else:
        print("OpenCV image read: SUCCESS")
        print("Image dimensions:", img.shape)

print("\nTASK 11.8E SETUP CHECK COMPLETED")
