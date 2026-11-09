from pathlib import Path
import csv
import math
import numpy as np

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

SOURCE = BASE / "02_CSV_Data" / "task17_sensor_mounting_positions.csv"
MATRIX_OUT = BASE / "02_CSV_Data" / "task17_transformation_matrices.csv"
CHECK_OUT = BASE / "02_CSV_Data" / "task17_transformation_checks.csv"

def rotation_matrix(roll, pitch, yaw):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    Rx = np.array([
        [1, 0, 0],
        [0, cr, -sr],
        [0, sr, cr]
    ])

    Ry = np.array([
        [cp, 0, sp],
        [0, 1, 0],
        [-sp, 0, cp]
    ])

    Rz = np.array([
        [cy, -sy, 0],
        [sy, cy, 0],
        [0, 0, 1]
    ])

    return Rz @ Ry @ Rx

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    sensors = list(csv.DictReader(f))

matrix_rows = []
check_rows = []
transforms = {}

for sensor in sensors:
    name = sensor["Sensor"]

    translation = np.array([
        float(sensor["X_m"]),
        float(sensor["Y_m"]),
        float(sensor["Z_m"])
    ])

    rotation = rotation_matrix(
        float(sensor["Roll_rad"]),
        float(sensor["Pitch_rad"]),
        float(sensor["Yaw_rad"])
    )

    T = np.eye(4)
    T[:3, :3] = rotation
    T[:3, 3] = translation

    transforms[name] = T

    # A sensor's local origin must map to its mounting position.
    local_origin = np.array([0., 0., 0., 1.])
    transformed_origin = T @ local_origin

    origin_error = np.linalg.norm(
        transformed_origin[:3] - translation
    )

    inverse_error = np.max(
        np.abs(np.linalg.inv(T) @ T - np.eye(4))
    )

    determinant = np.linalg.det(rotation)
    orthogonality_error = np.max(
        np.abs(rotation.T @ rotation - np.eye(3))
    )

    for i in range(4):
        matrix_rows.append({
            "Sensor": name,
            "Row": i,
            "C0": T[i, 0],
            "C1": T[i, 1],
            "C2": T[i, 2],
            "C3": T[i, 3],
        })

    check_rows.append({
        "Sensor": name,
        "OriginError_m": origin_error,
        "InverseError": inverse_error,
        "RotationDeterminant": determinant,
        "OrthogonalityError": orthogonality_error,
        "NumericalPass": (
            origin_error < 1e-9
            and inverse_error < 1e-9
            and abs(determinant - 1) < 1e-9
            and orthogonality_error < 1e-9
        )
    })

    print(f"\n=== {name.upper()} TRANSFORMATION ===")
    print(np.array2string(T, precision=4, suppress_small=True))
    print("Origin error (m):", origin_error)
    print("Inverse error:", inverse_error)

for output, rows in [
    (MATRIX_OUT, matrix_rows),
    (CHECK_OUT, check_rows)
]:
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

print("\n=== TASK 17.5B SUMMARY ===")
print("Sensors processed:", len(transforms))
print("Numerical passes:", sum(r["NumericalPass"] for r in check_rows))
print("Matrices CSV saved:", MATRIX_OUT.exists())
print("Validation CSV saved:", CHECK_OUT.exists())
print("Coordinate convention verified: NO - pending independent checks")
