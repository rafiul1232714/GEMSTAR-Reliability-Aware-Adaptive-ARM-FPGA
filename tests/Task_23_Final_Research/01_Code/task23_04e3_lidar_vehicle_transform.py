import csv
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(0, str(
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
))

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

POSE_CSV = (
    TASK / "02_CSV_Data" /
    "task23_04e2_host_pose_recovery.csv"
)

SOURCE_DATA = (
    TASK / "08_Processed_Data" /
    "LiDAR_Source_Matched"
)

OUTPUT = (
    TASK / "08_Processed_Data" /
    "LiDAR_Vehicle_Transform"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

for folder in (OUTPUT, CSV_DIR, GRAPH_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

FRAMES = (1, 25, 99)
TOL = 1e-8

def load_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

pairs = {
    int(row["PairID"]): row
    for row in load_csv(MANIFEST)
}

poses = {
    (int(row["PairID"]), int(row["Frame"])): row
    for row in load_csv(POSE_CSV)
}

results = []
total_points = 0

print("\n=== TASK 23.4E-3 LIDAR VEHICLE TRANSFORM ===")

for pair_id in (1, 2, 3):
    source = Path(pairs[pair_id]["SensorViewPath"])

    sv_frames = {
        index: message
        for index, message, _ in iter_osi_messages(
            source, SensorView, 100
        )
        if index in FRAMES
    }

    for frame in FRAMES:
        key = (pair_id, frame)

        if key not in poses:
            raise RuntimeError(f"Host pose missing: {key}")

        pose = poses[key]
        source_name = pose["PoseSource"]

        if source_name == "HOST_POSE_NOT_IDENTIFIED":
            raise RuntimeError(f"Unresolved host pose: {key}")

        if frame not in sv_frames:
            raise RuntimeError(f"Sensor frame missing: {key}")

        message = sv_frames[frame]

        if len(message.lidar_sensor_view) != 1:
            raise RuntimeError(
                f"Expected one LiDAR entry: {key}"
            )

        cfg = message.lidar_sensor_view[0].view_configuration
        mount = cfg.mounting_position

        translation = np.array([
            mount.position.x,
            mount.position.y,
            mount.position.z
        ], dtype=np.float64)

        orientation = np.array([
            mount.orientation.roll,
            mount.orientation.pitch,
            mount.orientation.yaw
        ], dtype=np.float64)

        # These recordings previously reported zero
        # mounting rotation. Verify it rather than assume.
        if not np.allclose(
            orientation, 0.0, atol=1e-9, rtol=0
        ):
            raise RuntimeError(
                f"Nonzero mounting rotation at {key}; "
                "a full rotation matrix is required."
            )

        input_path = SOURCE_DATA / (
            f"pair{pair_id}_frame{frame:03d}_"
            "source_matched_lidar.npz"
        )

        if not input_path.is_file():
            raise FileNotFoundError(input_path)

        with np.load(input_path, allow_pickle=False) as data:
            sensor_points = data["points_sensor_m"].copy()
            ray_indices = data["valid_ray_indices"].copy()
            range_image = data["range_image_m"].copy()

        if sensor_points.ndim != 2 or sensor_points.shape[1] != 3:
            raise RuntimeError(f"Invalid points shape: {key}")

        if not np.isfinite(sensor_points).all():
            raise RuntimeError(f"Nonfinite sensor points: {key}")

        # Hypothesis A: preserve Unreal-local positive Y.
        vehicle_a = sensor_points + translation

        # Hypothesis B: invert lateral axis before using
        # the recorded OSI mounting translation.
        reflected = sensor_points.copy()
        reflected[:, 1] *= -1.0
        vehicle_b = reflected + translation

        # Both must preserve LiDAR-origin distances.
        ranges_original = np.linalg.norm(
            sensor_points, axis=1
        )
        ranges_a = np.linalg.norm(
            vehicle_a - translation, axis=1
        )
        ranges_b = np.linalg.norm(
            vehicle_b - translation, axis=1
        )

        error_a = float(np.max(np.abs(
            ranges_original - ranges_a
        ))) if len(sensor_points) else 0.0

        error_b = float(np.max(np.abs(
            ranges_original - ranges_b
        ))) if len(sensor_points) else 0.0

        passed = bool(error_a < TOL and error_b < TOL)

        if not passed:
            raise RuntimeError(
                f"Distance preservation failed: {key}"
            )

        output_path = OUTPUT / (
            f"pair{pair_id}_frame{frame:03d}_"
            "vehicle_hypotheses.npz"
        )

        np.savez_compressed(
            output_path,
            points_sensor_m=sensor_points,
            points_vehicle_unreal_y_m=vehicle_a,
            points_vehicle_flipped_y_m=vehicle_b,
            mount_translation_m=translation,
            mount_orientation_rpy_rad=orientation,
            valid_ray_indices=ray_indices,
            range_image_m=range_image,
            pose_source=np.array(source_name),
        )

        total_points += len(sensor_points)

        results.append({
            "PairID": pair_id,
            "Frame": frame,
            "Points": int(len(sensor_points)),
            "MountX": float(translation[0]),
            "MountY": float(translation[1]),
            "MountZ": float(translation[2]),
            "MountRoll": float(orientation[0]),
            "MountPitch": float(orientation[1]),
            "MountYaw": float(orientation[2]),
            "PoseSource": source_name,
            "DistanceErrorA": error_a,
            "DistanceErrorB": error_b,
            "ValidationPass": passed,
        })

        print(
            f"Pair {pair_id} | Frame {frame:02d} | "
            f"Points={len(sensor_points)} | "
            f"Mount={translation.tolist()} | "
            f"ErrorA={error_a:.3e} | "
            f"ErrorB={error_b:.3e} | PASS={passed}"
        )

        if frame == 25:
            fig, axes = plt.subplots(
                1, 2, figsize=(12, 5),
                sharex=False, sharey=False
            )

            for ax, points, title in zip(
                axes,
                (vehicle_a, vehicle_b),
                ("Unreal positive-Y hypothesis",
                 "Inverted-Y hypothesis")
            ):
                ax.scatter(
                    points[:, 0],
                    points[:, 1],
                    s=1,
                    alpha=0.6
                )
                ax.scatter(
                    translation[0],
                    translation[1],
                    marker="x",
                    s=80,
                    label="LiDAR origin"
                )
                ax.set_title(title)
                ax.set_xlabel("Vehicle-relative X (m)")
                ax.set_ylabel("Vehicle-relative Y (m)")
                ax.set_aspect("equal", adjustable="box")
                ax.grid(alpha=0.2)

            fig.suptitle(
                f"Pair {pair_id}, frame 25: "
                "candidate lateral-axis conventions"
            )
            fig.tight_layout()

            graph = GRAPH_DIR / (
                f"task23_04e3_pair{pair_id}_"
                "vehicle_axis_comparison.png"
            )

            fig.savefig(graph, dpi=180)
            plt.close(fig)

csv_path = CSV_DIR / (
    "task23_04e3_vehicle_transform_validation.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

findings_path = FINDINGS / (
    "task23_04e3_vehicle_transform_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-3",
        "Samples": results,
        "TotalPoints": total_points,
        "Validation": "LiDAR-origin distance preservation",
        "CoordinateHypotheses": [
            "Retain Unreal-local Y and add mounting position",
            "Invert local Y and add OSI mounting position"
        ],
        "Status": "CANDIDATE_TRANSFORMS_ONLY",
        "Limitations": [
            "Lateral sign convention not established",
            "No host orientation applied",
            "No world-frame points generated",
            "No comparison with GroundTruth geometry yet",
            "Pose sources preserved but not validated externally"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-3 FINAL VERIFICATION ===")
print("Samples transformed:", len(results))
print("Total transformed points:", total_points)
print("All numerical checks passed:", all(
    item["ValidationPass"] for item in results
))
print("Validation CSV saved:", csv_path.is_file())
print("Findings JSON saved:", findings_path.is_file())
print("NPZ files:", len(list(
    OUTPUT.glob("*vehicle_hypotheses.npz")
)))
print("Comparison graphs:", len(list(
    GRAPH_DIR.glob("task23_04e3_*vehicle_axis_comparison.png")
)))

print("\n=== TASK 23.4E-3 COMPLETE ===")

