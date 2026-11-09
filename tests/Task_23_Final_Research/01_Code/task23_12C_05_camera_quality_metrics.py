import csv
from pathlib import Path

import cv2
import numpy as np

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

IMAGES = TASK / "08_Processed_Data" / "Camera_Weather_Comparison"
CSV = TASK / "02_CSV_Data" / "task23_12C_05_camera_quality_metrics.csv"

SCENARIOS = {
    "CLEAR": "CLEAR_t0200ms.png",
    "FOG100": "FOG100_t0200ms.png",
    "FOG20": "FOG20_t0200ms.png",
}

if CSV.exists():
    raise RuntimeError("CSV already exists")

rows = []

for scenario, filename in SCENARIOS.items():

    image_path = IMAGES / filename
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError(f"Cannot read {image_path}")

    height, width = image.shape[:2]

    if (width, height) != (640, 480):
        raise RuntimeError("Unexpected image dimensions")

    regions = {
        "FULL": image,
        "CENTER": image[96:384, 128:512],
    }

    for region_name, region in regions.items():

        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

        edges = cv2.Canny(gray, 80, 160)

        laplacian = cv2.Laplacian(
            gray, cv2.CV_64F
        )

        row = {
            "scenario": scenario,
            "region": region_name,
            "mean_luminance": round(float(gray.mean()), 4),
            "contrast_std": round(float(gray.std()), 4),
            "edge_density": round(float(np.count_nonzero(edges) / edges.size), 6),
            "laplacian_variance": round(float(laplacian.var()), 4),
            "mean_saturation": round(float(hsv[:, :, 1].mean()), 4),
            "pixels": int(gray.size),
        }

        rows.append(row)

        print(
            f"{scenario:7s} {region_name:6s} "
            f"LUMA={row['mean_luminance']:.2f} "
            f"CONTRAST={row['contrast_std']:.2f} "
            f"EDGE={row['edge_density']:.5f} "
            f"LAPLACIAN={row['laplacian_variance']:.2f} "
            f"SATURATION={row['mean_saturation']:.2f}"
        )

with CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV_SAVED={CSV}")
print(f"METRIC_ROWS={len(rows)}")
print("TASK23_12C_05_CAMERA_QUALITY_METRICS_PASS")
