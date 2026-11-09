import csv
import json
from pathlib import Path

import numpy as np

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

SOURCE = (
    TASK / "08_Processed_Data"
    / "LiDAR_Vehicle_Transform"
)
OUTPUT = (
    TASK / "08_Processed_Data"
    / "LiDAR_Vehicle_Source_Verified"
)
CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

for folder in (OUTPUT, CSV_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

results = []
max_error = 0.0
total_points = 0

print("\n=== TASK 23.4E-4D SOURCE-CONVENTION VALIDATION ===")

for pair in (1, 2, 3):
    for frame in (1, 25, 99):
        path = SOURCE / (
            f"pair{pair}_frame{frame:03d}_"
            "vehicle_hypotheses.npz"
        )

        if not path.is_file():
            raise FileNotFoundError(path)

        with np.load(path, allow_pickle=False) as data:
            sensor = data["points_sensor_m"].copy()
            vehicle = data["points_vehicle_flipped_y_m"].copy()
            alternate = data["points_vehicle_unreal_y_m"].copy()
            translation = data["mount_translation_m"].copy()
            orientation = data["mount_orientation_rpy_rad"].copy()
            ray_indices = data["valid_ray_indices"].copy()

        if sensor.ndim != 2 or sensor.shape[1] != 3:
            raise RuntimeError("Invalid sensor points")

        if not np.allclose(orientation, 0.0, atol=1e-9):
            raise RuntimeError(
                "Nonzero mounting rotation requires "
                "a general rotation transform."
            )

        # Source-verified Unreal-to-OSI axis conversion.
        reflect_y = np.array([1.0, -1.0, 1.0])

        expected = sensor * reflect_y + translation

        error = (
            float(np.max(np.abs(expected - vehicle)))
            if len(sensor) else 0.0
        )

        ranges_sensor = np.linalg.norm(sensor, axis=1)
        ranges_vehicle = np.linalg.norm(
            vehicle - translation,
            axis=1
        )

        range_error = (
            float(np.max(np.abs(
                ranges_sensor - ranges_vehicle
            )))
            if len(sensor) else 0.0
        )

        if not np.all(np.isfinite(vehicle)):
            raise RuntimeError("Nonfinite coordinates")

        passed = bool(
            error < 1e-10
            and range_error < 1e-10
        )

        if not passed:
            raise RuntimeError(
                f"Validation failed: pair={pair}, "
                f"frame={frame}"
            )

        max_error = max(max_error, error, range_error)
        total_points += len(sensor)

        destination = OUTPUT / (
            f"pair{pair}_frame{frame:03d}_"
            "vehicle_osi.npz"
        )

        np.savez_compressed(
            destination,
            points_vehicle_osi_m=vehicle,
            points_sensor_unreal_axes_m=sensor,
            rejected_hypothesis_points_m=alternate,
            mounting_position_osi_m=translation,
            valid_ray_indices=ray_indices,
            convention=np.array(
                "GEMSTAR_TOOSI_SOURCE_MATCHED"
            )
        )

        results.append({
            "PairID": pair,
            "Frame": frame,
            "Points": len(sensor),
            "CoordinateErrorM": error,
            "RangeErrorM": range_error,
            "ValidationPass": passed
        })

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Points={len(sensor)} | "
            f"CoordinateError={error:.3e} | "
            f"RangeError={range_error:.3e} | "
            f"PASS={passed}"
        )

csv_path = CSV_DIR / (
    "task23_04e4d_source_verified_coordinates.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0])
    )
    writer.writeheader()
    writer.writerows(results)

findings_path = FINDINGS / (
    "task23_04e4d_coordinate_convention_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-4D",
        "Status": "SOURCE_CONVENTION_VALIDATED",
        "Implementation": "ToOSI.cpp",
        "CoordinateRule": {
            "X": "Preserved",
            "Y": "Negated",
            "Z": "Preserved",
            "PositionUnits": "metres",
            "MountingRotation": "Zero in tested data"
        },
        "SelectedHypothesis": "Inverted Y",
        "RejectedHypothesis": "Unreal Y unchanged",
        "Samples": results,
        "TotalPoints": total_points,
        "MaximumNumericalErrorM": max_error,
        "Limitations": [
            "Source revision at recording time not proven",
            "No world-coordinate pose applied",
            "GroundTruth geometric accuracy not tested",
            "Stationary GroundTruth conversion needs audit",
            "No measured perception accuracy or energy"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-4D FINAL VERIFICATION ===")
print("Samples:", len(results))
print("Total points:", total_points)
print("Maximum numerical error:", max_error)
print("All passed:", all(r["ValidationPass"] for r in results))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", findings_path.is_file())
print(
    "Verified NPZ files:",
    len(list(OUTPUT.glob("*vehicle_osi.npz")))
)

print("\n=== TASK 23.4E-4D COMPLETE ===")
