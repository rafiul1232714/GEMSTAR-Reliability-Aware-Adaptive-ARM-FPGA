from pathlib import Path
import csv
import time
import numpy as np
import cv2

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

SOURCE = (
    BASE / "08_Extracted_Images" /
    "task18_frame000_rgb_interpretation.png"
)

OUT = BASE / "08_Extracted_Images"
CSV = BASE / "02_CSV_Data" / "task18_preprocessing_metrics.csv"

OUT.mkdir(parents=True, exist_ok=True)
CSV.parent.mkdir(parents=True, exist_ok=True)

# OpenCV reads PNG images in BGR order.
bgr = cv2.imread(str(SOURCE))

if bgr is None:
    raise RuntimeError("Could not open source image")

# Measure grayscale conversion.
start = time.perf_counter()
gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
gray_ms = (time.perf_counter() - start) * 1000

# Measure Gaussian smoothing.
start = time.perf_counter()
blur = cv2.GaussianBlur(gray, (5, 5), 1.0)
blur_ms = (time.perf_counter() - start) * 1000

# Measure Sobel edge calculation.
start = time.perf_counter()

gx = cv2.Sobel(blur, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(blur, cv2.CV_32F, 0, 1, ksize=3)

magnitude = cv2.magnitude(gx, gy)
edges = cv2.convertScaleAbs(magnitude)

sobel_ms = (time.perf_counter() - start) * 1000

# Save individual images.
cv2.imwrite(str(OUT / "task18_frame000_grayscale.png"), gray)
cv2.imwrite(str(OUT / "task18_frame000_gaussian.png"), blur)
cv2.imwrite(str(OUT / "task18_frame000_sobel.png"), edges)

# Create comparison image.
original = cv2.resize(bgr, (640, 480))
gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
blur_bgr = cv2.cvtColor(blur, cv2.COLOR_GRAY2BGR)
edge_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

top = np.hstack((original, gray_bgr))
bottom = np.hstack((blur_bgr, edge_bgr))
comparison = np.vstack((top, bottom))

GRAPH = BASE / "01_Graphs" / "task18_camera_preprocessing_comparison.png"
GRAPH.parent.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(GRAPH), comparison)

metrics = [
    ("Grayscale", gray_ms),
    ("GaussianBlur", blur_ms),
    ("SobelEdges", sobel_ms),
]

with CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Operation", "TimeMilliseconds"])
    writer.writerows(metrics)

print("\n=== TASK 18.3A CAMERA PREPROCESSING ===")
print("Image:", SOURCE.name)
print("Resolution:", bgr.shape[1], "x", bgr.shape[0])

for name, duration in metrics:
    print(f"{name}: {duration:.4f} ms")

print("Individual images saved:", 3)
print("Comparison graph saved:", GRAPH.exists())
print("Metrics CSV saved:", CSV.exists())
