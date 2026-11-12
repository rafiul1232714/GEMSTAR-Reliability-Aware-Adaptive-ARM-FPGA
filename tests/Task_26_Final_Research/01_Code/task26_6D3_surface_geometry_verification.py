from pathlib import Path
import csv
import json
import math
import statistics

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

DATA = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
    / "C02_V2_EKF_Input_53Frames_V1"
)

ROOT = TESTS / "Task_26_Final_Research"

SOURCE = DATA / "gt_surface_offset_diagnostic_v1.csv"

SUMMARY = (
    ROOT / "02_CSV_Data"
    / "task26_6D3_surface_geometry_checks.csv"
)

REPORT = (
    ROOT / "06_Research_Findings"
    / "task26_6D3_surface_geometry_report.json"
)

def finite(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise RuntimeError(f"Nonfinite {key}")
    return value

def main():
    if SUMMARY.exists() or REPORT.exists():
        raise FileExistsError(
            "Existing research outputs preserved."
        )

    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    with SOURCE.open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        rows = list(csv.DictReader(stream))

    if len(rows) != 23:
        raise RuntimeError("Expected 23 GT surface records")

    results = []
    seen = set()

    for row in rows:
        frame = int(row["frame"])

        if frame in seen:
            raise RuntimeError("Duplicate frame")
        seen.add(frame)

        if row["reference_type"] != "APPROXIMATE_GT_REAR_FACE":
            raise RuntimeError("Unexpected reference type")

        length = finite(row, "gt_length_m")
        width = finite(row, "gt_width_m")
        yaw_deg = finite(row, "relative_yaw_deg")

        cx = finite(row, "gt_center_x_m")
        cy = finite(row, "gt_center_y_m")

        rear_x = finite(row, "approx_rear_face_x_m")
        rear_y = finite(row, "approx_rear_face_y_m")

        yaw_rad = math.radians(yaw_deg)
        half_length = length / 2.0

        # Diagnostic prediction only:
        # rear = center - half_length * heading.
        predicted_x = cx - half_length * math.cos(yaw_rad)
        predicted_y = cy - half_length * math.sin(yaw_rad)

        displacement = math.hypot(
            cx - rear_x, cy - rear_y
        )

        geometry_residual = math.hypot(
            rear_x - predicted_x,
            rear_y - predicted_y
        )

        lidar_center = finite(row, "lidar_center_error_m")
        lidar_rear = finite(row, "lidar_rear_face_error_m")

        radar_center = finite(row, "radar_center_error_m")
        radar_rear = finite(row, "radar_rear_face_error_m")

        camera_center = finite(row, "camera_center_error_m")
        camera_rear = finite(row, "camera_rear_face_error_m")

        results.append({
            "frame": frame,
            "relative_yaw_deg": yaw_deg,
            "gt_length_m": length,
            "gt_width_m": width,
            "half_length_m": half_length,
            "center_to_rear_displacement_m": displacement,
            "half_length_difference_m":
                abs(displacement-half_length),
            "geometry_residual_m": geometry_residual,
            "lidar_center_error_m": lidar_center,
            "lidar_rear_error_m": lidar_rear,
            "radar_center_error_m": radar_center,
            "radar_rear_error_m": radar_rear,
            "camera_center_error_m": camera_center,
            "camera_rear_error_m": camera_rear,
        })

    residual_max = max(
        r["geometry_residual_m"] for r in results
    )

    half_length_max_difference = max(
        r["half_length_difference_m"] for r in results
    )

    geometry_matches_hypothesis = (
        residual_max < 1e-6
        and half_length_max_difference < 1e-6
    )

    length_values = [r["gt_length_m"] for r in results]
    yaw_values = [r["relative_yaw_deg"] for r in results]

    center_errors = [
        r["radar_center_error_m"] for r in results
    ]
    rear_errors = [
        r["radar_rear_error_m"] for r in results
    ]

    print("=== TASK 26.6D.3 SURFACE GEOMETRY VERIFICATION ===")
    print("FRAMES:", len(results))
    print("GT_LENGTH_MIN_M:", min(length_values))
    print("GT_LENGTH_MAX_M:", max(length_values))
    print("RELATIVE_YAW_MIN_DEG:", min(yaw_values))
    print("RELATIVE_YAW_MAX_DEG:", max(yaw_values))
    print(
        "MAX_GEOMETRY_RESIDUAL_M:",
        f"{residual_max:.12g}"
    )
    print(
        "MAX_HALF_LENGTH_DIFFERENCE_M:",
        f"{half_length_max_difference:.12g}"
    )
    print(
        "REAR_FACE_FORMULA_MATCHES:",
        geometry_matches_hypothesis
    )
    print(
        "RADAR_CENTER_MEAN_ERROR_M:",
        f"{statistics.mean(center_errors):.6f}"
    )
    print(
        "RADAR_REAR_MEAN_ERROR_M:",
        f"{statistics.mean(rear_errors):.6f}"
    )

    print("\n=== SELECTED GEOMETRY FRAMES ===")

    for r in results:
        if r["frame"] in (41, 530, 816, 897, 938):
            print(
                f"FRAME={r['frame']} "
                f"YAW_DEG={r['relative_yaw_deg']:.3f} "
                f"LENGTH_M={r['gt_length_m']:.4f} "
                f"RESIDUAL_M={r['geometry_residual_m']:.9f}"
            )

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with SUMMARY.open(
        "x", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(results[0])
        )
        writer.writeheader()
        writer.writerows(results)

    report = {
        "task": "26.6D.3",
        "reference_type": "APPROXIMATE_GT_REAR_FACE",
        "frames": len(results),
        "geometry_hypothesis": (
            "rear = center - (length / 2) * "
            "[cos(relative_yaw), sin(relative_y)]"
        ),
        "formula_matches": geometry_matches_hypothesis,
        "maximum_geometry_residual_m": residual_max,
        "maximum_half_length_difference_m":
            half_length_max_difference,
        "gt_length_range_m": [
            min(length_values), max(length_values)
        ],
        "relative_yaw_range_deg": [
            min(yaw_values), max(yaw_values)
        ],
        "radar_center_mean_error_m":
            statistics.mean(center_errors),
        "radar_approx_rear_mean_error_m":
            statistics.mean(rear_errors),
        "limitations": [
            "Internal formula agreement is not independent GT validation.",
            "Vehicle length may be exporter-dependent.",
            "Approximate rear face is not a verified sensor-hit location.",
            "GT world-to-ego conversion is still preliminary.",
            "Target association is evaluation-only.",
            "No tracking-state correction has been applied.",
            "No energy measurement is included."
        ],
        "historical_inputs_modified": False
    }

    with REPORT.open(
        "x", encoding="utf-8"
    ) as f:
        json.dump(report, f, indent=2)

    print("\nTRACKING_CORRECTION_APPLIED: NO")
    print("PHYSICAL_REAR_FACE_VALIDATED: NO")
    print("HISTORICAL_INPUTS_MODIFIED: NO")

    if geometry_matches_hypothesis:
        print("TASK26_6D3_GEOMETRY_CHECK_PASS")
    else:
        print("TASK26_6D3_GEOMETRY_REVIEW_REQUIRED")

    print("SUMMARY:", SUMMARY)
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
