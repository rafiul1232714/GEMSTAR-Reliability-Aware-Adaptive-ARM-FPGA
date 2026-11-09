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

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

RADAR_DIR = (
    TASK / "08_Processed_Data"
    / "Radar_3D_Source_Matched"
)

LIDAR_DIR = (
    TASK / "08_Processed_Data"
    / "LiDAR_Vehicle_Source_Verified"
)

for directory in (CSV_DIR, GRAPH_DIR, FINDINGS):
    directory.mkdir(parents=True, exist_ok=True)

PAIRS = (1, 2, 3)
FRAMES = (25, 99)

RADAR_EXPECTED_MOUNT = np.array([2.0, 0.0, 0.8])
LIDAR_EXPECTED_MOUNT = np.array([2.6, 0.0, 0.7])


def load_array(path, key):
    if not path.is_file():
        raise FileNotFoundError(path)

    with np.load(path, allow_pickle=False) as dataset:
        if key not in dataset.files:
            raise KeyError(
                f"Missing key {key!r} in {path.name}; "
                f"available: {dataset.files}"
            )
        return dataset[key].copy()


def validate_points(points, label):
    if points.ndim != 2 or points.shape[1] != 3:
        raise RuntimeError(
            f"{label}: expected Nx3 coordinates, "
            f"got {points.shape}"
        )

    if not np.isfinite(points).all():
        raise RuntimeError(
            f"{label}: nonfinite coordinates"
        )


def nearest_distance(source, target):
    """
    Minimum Euclidean distance to any target point.
    Batches source points to limit temporary memory.
    This is NOT a confirmed sensor-object association.
    """
    if not len(source) or not len(target):
        return np.empty(0, dtype=np.float64)

    output = []

    for start in range(0, len(source), 128):
        block = source[start:start + 128]

        distances_squared = np.sum(
            (block[:, None, :] - target[None, :, :]) ** 2,
            axis=2
        )

        output.append(
            np.sqrt(np.min(distances_squared, axis=1))
        )

    return np.concatenate(output)


rows = []
clouds = {}

print("\n=== TASK 23.5D-1 RADAR-LIDAR ALIGNMENT ===")

for pair in PAIRS:
    for frame in FRAMES:

        radar_path = RADAR_DIR / (
            f"pair{pair}_frame{frame:03d}_radar_3d.npz"
        )

        lidar_path = LIDAR_DIR / (
            f"pair{pair}_frame{frame:03d}_vehicle_osi.npz"
        )

        radar = load_array(
            radar_path, "points_vehicle_osi_m"
        )
        lidar = load_array(
            lidar_path, "points_vehicle_osi_m"
        )

        radar_mount = load_array(
            radar_path, "mounting_position_osi_m"
        )
        lidar_mount = load_array(
            lidar_path, "mounting_position_osi_m"
        )

        validate_points(radar, "Radar")
        validate_points(lidar, "LiDAR")

        if not np.allclose(
            radar_mount, RADAR_EXPECTED_MOUNT,
            atol=1e-6, rtol=0
        ):
            raise RuntimeError(
                f"Unexpected Radar mount: pair {pair}, frame {frame}"
            )

        if not np.allclose(
            lidar_mount, LIDAR_EXPECTED_MOUNT,
            atol=1e-6, rtol=0
        ):
            raise RuntimeError(
                f"Unexpected LiDAR mount: pair {pair}, frame {frame}"
            )

        distances = nearest_distance(radar, lidar)

        if len(distances):
            median_d = float(np.median(distances))
            p95_d = float(np.percentile(distances, 95))
            min_d = float(np.min(distances))
            below_05 = int(np.count_nonzero(distances <= 0.5))
            below_10 = int(np.count_nonzero(distances <= 1.0))
        else:
            median_d = None
            p95_d = None
            min_d = None
            below_05 = 0
            below_10 = 0

        rows.append({
            "PairID": pair,
            "Frame": frame,
            "RadarPoints": len(radar),
            "LiDARPoints": len(lidar),
            "RadarMountX": float(radar_mount[0]),
            "RadarMountY": float(radar_mount[1]),
            "RadarMountZ": float(radar_mount[2]),
            "LiDARMountX": float(lidar_mount[0]),
            "LiDARMountY": float(lidar_mount[1]),
            "LiDARMountZ": float(lidar_mount[2]),
            "MinNearestDistanceM": min_d,
            "MedianNearestDistanceM": median_d,
            "P95NearestDistanceM": p95_d,
            "RadarPointsWithin05mOfLiDAR": below_05,
            "RadarPointsWithin10mOfLiDAR": below_10,
            "CoordinateFormat": "VEHICLE_OSI_METRES",
            "ObjectAssociationVerified": False,
        })

        clouds[(pair, frame)] = (radar, lidar)

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Radar={len(radar):3d} | "
            f"LiDAR={len(lidar):4d} | "
            f"MedianNearest={median_d} m | "
            f"Within1m={below_10}"
        )


csv_path = CSV_DIR / (
    "task23_05d1_radar_lidar_alignment.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=list(rows[0])
    )
    writer.writeheader()
    writer.writerows(rows)


# Save one XY overlay for each recording pair.
for pair in PAIRS:

    fig, axes = plt.subplots(
        1, 2, figsize=(13, 6),
        sharex=False, sharey=False
    )

    for ax, frame in zip(axes, FRAMES):

        radar, lidar = clouds[(pair, frame)]

        ax.scatter(
            lidar[:, 0], lidar[:, 1],
            s=2, alpha=0.35,
            label="LiDAR"
        )

        ax.scatter(
            radar[:, 0], radar[:, 1],
            s=30, alpha=0.85,
            marker="x",
            label="Radar"
        )

        ax.scatter(
            0, 0, marker="s", s=65,
            label="Vehicle origin"
        )

        ax.set_title(
            f"Pair {pair} / Frame {frame}"
        )
        ax.set_xlabel("Vehicle OSI X (m)")
        ax.set_ylabel("Vehicle OSI Y (m)")
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.2)
        ax.legend(fontsize=8)

    fig.suptitle(
        "Radar-LiDAR vehicle-coordinate comparison"
    )

    fig.tight_layout()

    fig.savefig(
        GRAPH_DIR /
        f"task23_05d1_pair{pair}_radar_lidar_overlay.png",
        dpi=180
    )

    plt.close(fig)


# Draw frame-level nearest-neighbor statistics.
fig, ax = plt.subplots(figsize=(10, 5))

labels = [
    f"P{r['PairID']}/F{r['Frame']}"
    for r in rows
]

values = [
    r["MedianNearestDistanceM"]
    for r in rows
]

ax.bar(labels, values)
ax.set_ylabel(
    "Median Radar-to-nearest-LiDAR distance (m)"
)
ax.set_title(
    "Exploratory cross-sensor proximity"
)
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()

graph_path = GRAPH_DIR / (
    "task23_05d1_nearest_distance_summary.png"
)

fig.savefig(graph_path, dpi=180)
plt.close(fig)


findings_path = FINDINGS / (
    "task23_05d1_alignment_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.5D-1",
        "Status": "EXPLORATORY_SPATIAL_ALIGNMENT_AUDIT",
        "CoordinateFrame": "Vehicle OSI, metres",
        "Frames": rows,
        "Limitations": [
            "Both clouds are derived from GEMSTAR simulation",
            "Common vehicle coordinate units and recorded mount positions checked",
            "Same frame index does not independently prove acquisition-time synchronization",
            "Radar and LiDAR may sample different target surfaces",
            "Nearest-neighbor distance is not a confirmed target association",
            "No independent perception accuracy validated",
            "No hardware energy or latency measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5D-1 FINAL VERIFICATION ===")
print("Frame comparisons:", len(rows))
print(
    "Radar points compared:",
    sum(r["RadarPoints"] for r in rows)
)
print(
    "LiDAR points compared:",
    sum(r["LiDARPoints"] for r in rows)
)
print("Comparison CSV:", csv_path.is_file())
print("Research JSON:", findings_path.is_file())
print(
    "Graphs:",
    len(list(GRAPH_DIR.glob("task23_05d1_*.png")))
)

if len(rows) != 6:
    raise RuntimeError(
        "Expected six pair/frame comparisons"
    )

if sum(r["RadarPoints"] for r in rows) != 237:
    raise RuntimeError(
        "Radar count does not match previous audit"
    )

print("\n=== TASK 23.5D-1 COMPLETE ===")
