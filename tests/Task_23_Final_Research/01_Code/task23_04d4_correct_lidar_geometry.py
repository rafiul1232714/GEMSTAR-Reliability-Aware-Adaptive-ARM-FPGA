import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

DATA = TASK / "08_Processed_Data" / "LiDAR_Range"
CORRECTED = TASK / "08_Processed_Data" / "LiDAR_Source_Matched"
GRAPHS = TASK / "03_Graphs"
CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

CONFIG_CSV = (
    TASK / "04_Configurations"
    / "task23_04c_lidar_scan_configuration.csv"
)

for folder in (CORRECTED, GRAPHS, CSV_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

print("\n=== TASK 23.4D-4 GEOMETRY CORRECTION ===")

if not CONFIG_CSV.is_file():
    raise FileNotFoundError(CONFIG_CSV)

# Use the FOV and ray counts recorded in the OSI messages.
with CONFIG_CSV.open(
    newline="", encoding="utf-8-sig"
) as handle:
    configs = {
        (int(r["PairID"]), int(r["Frame"])): r
        for r in csv.DictReader(handle)
    }

summary = []
all_pass = True

def make_directions(nx, ny, hfov, vfov):
    # Source:
    # SimpleLidar.cpp SetSensorConfiguration()
    # Azimuth starts at -HFOV/2 and increases.
    # Elevation starts at -VFOV/2 and increases.

    azimuth = np.linspace(
        -hfov / 2.0,
        hfov / 2.0,
        nx,
        dtype=np.float64
    )

    elevation = np.linspace(
        -vfov / 2.0,
        vfov / 2.0,
        ny,
        dtype=np.float64
    )

    az, el = np.meshgrid(azimuth, elevation)

    # Unreal-local ray directions:
    # X forward, positive Y corresponds to positive yaw,
    # Z upward for positive pitch.
    directions = np.stack(
        (
            np.cos(el) * np.cos(az),
            np.cos(el) * np.sin(az),
            np.sin(el)
        ),
        axis=-1
    )

    vectors = directions.reshape(-1, 3)

    norms = np.linalg.norm(vectors, axis=1)

    if not np.allclose(norms, 1.0, atol=1e-12):
        raise RuntimeError("Nonunit ray directions.")

    return vectors, azimuth, elevation


for pair_id in (1, 2, 3):
    for frame in (1, 25, 99):

        key = (pair_id, frame)

        if key not in configs:
            raise RuntimeError(
                f"Missing configuration for {key}"
            )

        config = configs[key]

        nx = int(config["HorizontalRays"])
        ny = int(config["VerticalRays"])

        hfov = float(config["HorizontalFovRad"])
        vfov = float(config["VerticalFovRad"])

        path = (
            DATA /
            f"pair{pair_id}_frame{frame:03d}_lidar.npz"
        )

        if not path.is_file():
            raise FileNotFoundError(path)

        with np.load(path, allow_pickle=False) as data:
            range_image = data["range_image_m"]
            mask = data["valid_mask"].astype(bool)
            old_points = data["points_sensor_m"]

        if range_image.shape != (ny, nx):
            raise RuntimeError(
                f"Unexpected range-image shape: {key}"
            )

        if mask.shape != (ny, nx):
            raise RuntimeError(
                f"Unexpected mask shape: {key}"
            )

        directions, azimuth, elevation = (
            make_directions(nx, ny, hfov, vfov)
        )

        flat_range = range_image.reshape(-1)
        flat_mask = mask.reshape(-1)

        valid_indices = np.flatnonzero(flat_mask)

        corrected_points = (
            directions[valid_indices]
            * flat_range[valid_indices, None]
        )

        if corrected_points.shape != old_points.shape:
            raise RuntimeError(
                f"Point count mismatch in {key}"
            )

        corrected_distance = np.linalg.norm(
            corrected_points, axis=1
        )

        range_error = np.max(np.abs(
            corrected_distance - flat_range[valid_indices]
        )) if len(valid_indices) else 0.0

        coordinate_change = np.linalg.norm(
            corrected_points - old_points,
            axis=1
        )

        max_change = (
            float(np.max(coordinate_change))
            if len(coordinate_change) else 0.0
        )

        valid = (
            np.all(np.isfinite(corrected_points))
            and range_error < 1e-8
        )

        all_pass = all_pass and valid

        output = (
            CORRECTED /
            f"pair{pair_id}_frame{frame:03d}_"
            "source_matched_lidar.npz"
        )

        np.savez_compressed(
            output,
            range_image_m=range_image,
            valid_mask=mask,
            points_sensor_m=corrected_points,
            valid_ray_indices=valid_indices,
            azimuth_rad=azimuth,
            elevation_rad=elevation,
            geometry_method=np.array(
                "SIMPLELIDAR_SOURCE_MATCHED"
            ),
        )

        summary.append({
            "PairID": pair_id,
            "Frame": frame,
            "Points": len(corrected_points),
            "FirstAzimuthDeg": np.degrees(azimuth[0]),
            "LastAzimuthDeg": np.degrees(azimuth[-1]),
            "FirstElevationDeg": np.degrees(elevation[0]),
            "LastElevationDeg": np.degrees(elevation[-1]),
            "MaximumRangeErrorM": range_error,
            "MaximumCoordinateChangeM": max_change,
            "ValidationPass": bool(valid),
        })

        print(
            f"Pair {pair_id} | Frame {frame:02d} | "
            f"Points={len(corrected_points)} | "
            f"RangeError={range_error:.3e} m | "
            f"MaxCoordinateChange={max_change:.3f} m | "
            f"PASS={valid}"
        )

        # Save corrected point-cloud visualization for frame25.
        if frame == 25:
            fig = plt.figure(figsize=(10, 7))
            ax = fig.add_subplot(111, projection="3d")

            if len(corrected_points):
                ax.scatter(
                    corrected_points[:, 0],
                    corrected_points[:, 1],
                    corrected_points[:, 2],
                    c=corrected_distance,
                    s=1.2,
                    cmap="viridis"
                )

            ax.set_xlabel("Local X (forward, m)")
            ax.set_ylabel("Local Y (UE positive yaw, m)")
            ax.set_zlabel("Local Z (up, m)")
            ax.set_title(
                f"Pair {pair_id} - Frame 25\n"
                "SimpleLidar source-matched geometry"
            )

            graph = (
                GRAPHS /
                f"task23_04d4_pair{pair_id}_"
                "corrected_point_cloud.png"
            )

            fig.tight_layout()
            fig.savefig(graph, dpi=180)
            plt.close(fig)

csv_path = (
    CSV_DIR /
    "task23_04d4_geometry_correction_summary.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=list(summary[0].keys())
    )
    writer.writeheader()
    writer.writerows(summary)

findings_path = (
    FINDINGS /
    "task23_04d4_geometry_correction_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4D-4",
        "SourceImplementation": "SimpleLidar.cpp",
        "SourceEvidence": {
            "RayIndexing": "Index % horizontal and Index / horizontal",
            "AzimuthStart": "-horizontal_fov/2",
            "AzimuthEnd": "+horizontal_fov/2",
            "ElevationStart": "-vertical_fov/2",
            "ElevationEnd": "+vertical_fov/2",
        },
        "Samples": summary,
        "AllValidationChecksPassed": bool(all_pass),
        "Limitations": [
            "Source-matched geometry is not yet GroundTruth-validated",
            "Recorded implementation version still needs confirmation",
            "Points are in sensor-local coordinates",
            "World-frame mounting transformations not yet applied",
            "Weather-induced measurement effects not independently assessed",
            "No energy or perception accuracy measurements"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4D-4 FINAL VERIFICATION ===")
print("Source-matched samples:", len(summary))
print("All validations passed:", all_pass)
print("Summary CSV saved:", csv_path.is_file())
print("Research JSON saved:", findings_path.is_file())
print(
    "Corrected NPZ files:",
    len(list(CORRECTED.glob("*source_matched_lidar.npz")))
)
print(
    "Corrected point-cloud graphs:",
    len(list(GRAPHS.glob("task23_04d4_*corrected_point_cloud.png")))
)

if not all_pass:
    raise RuntimeError("Geometry validation failed.")

print("\n=== TASK 23.4D-4 COMPLETE ===")

