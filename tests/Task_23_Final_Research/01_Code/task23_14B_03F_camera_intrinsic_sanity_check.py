import csv
import math
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

SOURCE = TASK / "02_CSV_Data" / (
    "task23_09_camera_auto_measurements.csv"
)

DETAILS = TASK / "02_CSV_Data" / (
    "task23_09_camera_baseline_displaced.csv"
)

OUTPUT = TASK / "02_CSV_Data" / (
    "task23_14B_03F_camera_intrinsic_sanity_check.csv"
)

if OUTPUT.exists():
    raise RuntimeError("Output already exists")

with SOURCE.open(newline="", encoding="utf-8-sig") as f:
    measured = list(csv.DictReader(f))

with DETAILS.open(newline="", encoding="utf-8-sig") as f:
    distances = list(csv.DictReader(f))

if len(measured) != 2 or len(distances) != 2:
    raise RuntimeError("Unexpected calibration evidence")

width = 640
height = 480
hfov_deg = 90.0

fx = width / (2.0 * math.tan(math.radians(hfov_deg) / 2.0))
fy = fx
cx = width / 2.0
cy = height / 2.0

vertical_fov_deg = math.degrees(
    2.0 * math.atan(height / (2.0 * fy))
)

cube_face_width_m = 3.0
tolerance_px = 3.0

distance_by_condition = {
    row["condition"]: float(row["cube_front_face_m"])
    for row in distances
}

if set(distance_by_condition) != {"baseline", "displaced"}:
    raise RuntimeError("Unexpected calibration conditions")

rows = []

for row in measured:
    condition = row["condition"]

    if condition not in distance_by_condition:
        raise RuntimeError("Unknown calibration condition")

    distance_m = distance_by_condition[condition]
    measured_width = float(row["width_px"])

    if distance_m <= 0 or measured_width <= 0:
        raise RuntimeError("Invalid calibration measurement")

    predicted_width = fx * cube_face_width_m / distance_m
    error_px = measured_width - predicted_width

    passed = abs(error_px) <= tolerance_px

    rows.append({
        "Condition": condition,
        "DistanceM": distance_m,
        "CubeFaceWidthM": cube_face_width_m,
        "MeasuredWidthPx": measured_width,
        "PredictedWidthPx": predicted_width,
        "ErrorPx": error_px,
        "Result": "PASS" if passed else "FAIL",
    })

    print(
        f"CONDITION={condition} "
        f"DISTANCE_M={distance_m:.3f} "
        f"MEASURED_PX={measured_width:.3f} "
        f"PREDICTED_PX={predicted_width:.3f} "
        f"ERROR_PX={error_px:.4f} "
        f"RESULT={'PASS' if passed else 'FAIL'}"
    )

with OUTPUT.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"\nFX_PX={fx:.6f}")
print(f"FY_PX={fy:.6f}")
print(f"CX_PX={cx:.6f}")
print(f"CY_PX={cy:.6f}")
print(f"DERIVED_VERTICAL_FOV_DEG={vertical_fov_deg:.6f}")
print(f"DIAGNOSTIC_TOLERANCE_PX={tolerance_px:.3f}")
print(f"CSV_SAVED={OUTPUT}")

failures = sum(row["Result"] != "PASS" for row in rows)

print(f"VALIDATION_CASES={len(rows)}")
print(f"FAILED_CASES={failures}")

if failures:
    raise RuntimeError("Camera intrinsic sanity check failed")

print("TASK23_14B_03F_CAMERA_INTRINSIC_SANITY_PASS")
