import csv
import sys
from pathlib import Path

import cv2
import numpy as np

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

sys.path.insert(0, str(TASK / "01_Code"))

from task23_12C_06_camera_cpu_preprocessing import preprocess_camera

IMAGE = (
    TASK / "08_Processed_Data"
    / "Camera_Weather_Comparison"
    / "CLEAR_t0200ms.png"
)

CSV = (
    TASK / "02_CSV_Data"
    / "task23_12D_01_camera_robustness_tests.csv"
)

if CSV.exists():
    raise RuntimeError("CSV already exists")

valid_image = cv2.imread(str(IMAGE), cv2.IMREAD_COLOR)

if valid_image is None:
    raise RuntimeError("Reference Camera image missing")

tests = [
    ("VALID_FULL", valid_image, None, True),
    ("VALID_CENTER_ROI", valid_image, (128, 96, 384, 288), True),
    ("MISSING_IMAGE", None, None, False),
    ("EMPTY_IMAGE", np.empty((0, 0, 3), dtype=np.uint8), None, False),
    ("WRONG_DTYPE", valid_image.astype(np.float32), None, False),
    ("GRAYSCALE_INPUT", cv2.cvtColor(valid_image, cv2.COLOR_BGR2GRAY), None, False),
    ("ROI_OUT_OF_BOUNDS", valid_image, (600, 400, 100, 100), False),
    ("ROI_ZERO_WIDTH", valid_image, (0, 0, 0, 100), False),
]

rows = []
failures = 0

for name, image, roi, should_accept in tests:

    accepted = False
    error_type = ""

    try:
        result = preprocess_camera(image, roi=roi)
        accepted = result["status"] == "VALID"

    except (TypeError, ValueError) as exc:
        error_type = type(exc).__name__

    passed = accepted == should_accept

    if not passed:
        failures += 1

    rows.append({
        "test": name,
        "expected_accept": should_accept,
        "actual_accept": accepted,
        "error_type": error_type,
        "result": "PASS" if passed else "FAIL",
    })

    print(
        f"TEST={name} "
        f"EXPECTED_ACCEPT={should_accept} "
        f"ACTUAL_ACCEPT={accepted} "
        f"RESULT={'PASS' if passed else 'FAIL'}"
    )

with CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV_SAVED={CSV}")
print(f"TESTS_TOTAL={len(rows)}")
print(f"TESTS_PASSED={len(rows) - failures}")
print(f"TESTS_FAILED={failures}")

if failures:
    raise RuntimeError("Camera preprocessing robustness tests failed")

print("TASK23_12D_01_CAMERA_ROBUSTNESS_PASS")
