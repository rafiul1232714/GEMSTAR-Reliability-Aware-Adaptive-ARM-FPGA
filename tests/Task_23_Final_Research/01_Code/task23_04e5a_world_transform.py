import csv
import json
from pathlib import Path

import numpy as np

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

INPUT = (
    TASK / "08_Processed_Data"
    / "LiDAR_Vehicle_Source_Verified"
)
OUTPUT = (
    TASK / "08_Processed_Data"
    / "LiDAR_World_Candidate"
)
POSES = (
    TASK / "02_CSV_Data"
    / "task23_04e2_host_pose_recovery.csv"
)
CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

for folder in (OUTPUT, CSV_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

def rotation_matrix(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)

    rx = np.array([
        [1, 0, 0],
        [0, cr, -sr],
        [0, sr, cr]
    ])

    ry = np.array([
        [cp, 0, sp],
        [0, 1, 0],
        [-sp, 0, cp]
    ])

    rz = np.array([
        [cy, -sy, 0],
        [sy, cy, 0],
        [0, 0, 1]
    ])

    return rz @ ry @ rx

with POSES.open(
    newline="", encoding="utf-8-sig"
) as handle:
    pose_rows = list(csv.DictReader(handle))

pose_lookup = {
    (int(row["PairID"]), int(row["Frame"])): row
    for row in pose_rows
}

results = []
total_points = 0

print("\n=== TASK 23.4E-5A WORLD TRANSFORMATION ===")

for pair in (1, 2, 3):
    for frame in (1, 25, 99):
        key = (pair, frame)

        if key not in pose_lookup:
            raise RuntimeError(f"Missing host pose: {key}")

        pose = pose_lookup[key]

        if pose["PoseSource"] == "HOST_POSE_NOT_IDENTIFIED":
            raise RuntimeError(f"Unresolved host pose: {key}")

        position = np.array([
            float(pose["X"]),
            float(pose["Y"]),
            float(pose["Z"])
        ])

        roll = float(pose["Roll"])
        pitch = float(pose["Pitch"])
        yaw = float(pose["Yaw"])

        R = rotation_matrix(roll, pitch, yaw)

        input_path = INPUT / (
            f"pair{pair}_frame{frame:03d}_vehicle_osi.npz"
        )

        if not input_path.is_file():
            raise FileNotFoundError(input_path)

        with np.load(input_path, allow_pickle=False) as data:
            vehicle = data["points_vehicle_osi_m"].copy()
            ray_indices = data["valid_ray_indices"].copy()
            mount = data["mounting_position_osi_m"].copy()

        if not np.isfinite(vehicle).all():
            raise RuntimeError(f"Nonfinite points: {key}")

        if not np.isfinite(position).all():
            raise RuntimeError(f"Nonfinite host pose: {key}")

        # Row vectors: p_world = p_vehicle @ R.T + t
        world = vehicle @ R.T + position

        # Reconstruct the vehicle-frame points from world.
        recovered = (world - position) @ R

        inverse_error = float(np.max(np.abs(
            recovered - vehicle
        ))) if len(vehicle) else 0.0

        orthogonality_error = float(np.max(np.abs(
            R.T @ R - np.eye(3)
        )))

        determinant = float(np.linalg.det(R))

        passed = bool(
            inverse_error < 1e-9
            and orthogonality_error < 1e-12
            and abs(determinant - 1.0) < 1e-12
        )

        if not passed:
            raise RuntimeError(
                f"World transform validation failed: {key}"
            )

        output_path = OUTPUT / (
            f"pair{pair}_frame{frame:03d}_world_candidate.npz"
        )

        np.savez_compressed(
            output_path,
            points_world_candidate_m=world,
            points_vehicle_osi_m=vehicle,
            host_position_osi_m=position,
            host_orientation_rpy_rad=np.array(
                [roll, pitch, yaw]
            ),
            world_from_vehicle_rotation=R,
            lidar_mount_vehicle_osi_m=mount,
            valid_ray_indices=ray_indices,
            pose_source=np.array(pose["PoseSource"]),
            rotation_convention=np.array(
                "CANDIDATE_RZ_YAW_RY_PITCH_RX_ROLL"
            )
        )

        total_points += len(vehicle)

        result = {
            "PairID": pair,
            "Frame": frame,
            "Points": int(len(vehicle)),
            "HostX": float(position[0]),
            "HostY": float(position[1]),
            "HostZ": float(position[2]),
            "HostRoll": roll,
            "HostPitch": pitch,
            "HostYaw": yaw,
            "PoseSource": pose["PoseSource"],
            "RotationDeterminant": determinant,
            "OrthogonalityError": orthogonality_error,
            "InverseErrorM": inverse_error,
            "ValidationPass": passed
        }

        results.append(result)

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Points={len(vehicle)} | "
            f"Host={position.round(3).tolist()} | "
            f"Yaw={np.degrees(yaw):.3f} deg | "
            f"InverseError={inverse_error:.3e} | "
            f"PASS={passed}"
        )

csv_path = (
    CSV_DIR /
    "task23_04e5a_world_transform_validation.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=list(results[0])
    )
    writer.writeheader()
    writer.writerows(results)

findings_path = (
    FINDINGS /
    "task23_04e5a_world_transform_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-5A",
        "Status": "WORLD_TRANSFORM_INTERNAL_VALIDATION",
        "RotationConvention": "Rz(yaw)Ry(pitch)Rx(roll)",
        "Samples": results,
        "TotalPoints": total_points,
        "AllInternalChecksPassed": all(
            row["ValidationPass"] for row in results
        ),
        "Limitations": [
            "Rotation convention needs independent confirmation",
            "Host pose reference origin needs validation",
            "GroundTruth object alignment not yet tested",
            "Potential stationary-object serialization defect",
            "No external spatial accuracy metric yet"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-5A FINAL VERIFICATION ===")
print("Samples:", len(results))
print("Total points:", total_points)
print("All checks passed:", all(
    row["ValidationPass"] for row in results
))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", findings_path.is_file())
print(
    "World-coordinate NPZ files:",
    len(list(OUTPUT.glob("*world_candidate.npz")))
)

print("\n=== TASK 23.4E-5A COMPLETE ===")
