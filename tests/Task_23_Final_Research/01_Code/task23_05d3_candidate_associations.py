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

CSV = TASK / "02_CSV_Data"
GRAPHS = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

RADAR = (
    TASK / "08_Processed_Data"
    / "Radar_3D_Source_Matched"
)
LIDAR = (
    TASK / "08_Processed_Data"
    / "LiDAR_Vehicle_Source_Verified"
)

TIMESTAMPS = CSV / "task23_05d2_radar_lidar_timestamps.csv"

for directory in (CSV, GRAPHS, FINDINGS):
    directory.mkdir(parents=True, exist_ok=True)

DISTANCE_GATE_M = 1.0
ANGLE_GATE_DEG = 5.0
PAIRS = (1, 2, 3)
FRAMES = (25, 99)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def angle_difference(a, b):
    return np.arctan2(np.sin(a-b), np.cos(a-b))


if not TIMESTAMPS.is_file():
    raise FileNotFoundError(TIMESTAMPS)

time_rows = {
    (int(r["PairID"]), int(r["Frame"])): r
    for r in read_csv(TIMESTAMPS)
}

detail = []
summary = []

print("\n=== TASK 23.5D-3 CANDIDATE ASSOCIATIONS ===")

for pair in PAIRS:
    for frame in FRAMES:
        key = (pair, frame)

        time_row = time_rows.get(key)

        if time_row is None:
            raise RuntimeError(f"Timestamp entry missing: {key}")

        sv_time = time_row["SensorViewTimestampNs"]
        gt_time = time_row["GroundTruthTimestampNs"]

        if not sv_time or not gt_time or sv_time != gt_time:
            raise RuntimeError(
                f"SV/GT timestamp mismatch or unavailable: {key}"
            )

        radar_path = RADAR / (
            f"pair{pair}_frame{frame:03d}_radar_3d.npz"
        )
        lidar_path = LIDAR / (
            f"pair{pair}_frame{frame:03d}_vehicle_osi.npz"
        )

        with np.load(radar_path, allow_pickle=False) as d:
            radar_xyz = d["points_vehicle_osi_m"].copy()
            radar_mount = d["mounting_position_osi_m"].copy()
            radar_az = d["horizontal_angle_rad"].copy()
            radar_el = d["vertical_angle_rad"].copy()
            radar_ray = d["valid_ray_indices"].copy()

        with np.load(lidar_path, allow_pickle=False) as d:
            lidar_xyz = d["points_vehicle_osi_m"].copy()
            lidar_ray = d["valid_ray_indices"].copy()

        for xyz, name in [
            (radar_xyz, "Radar"),
            (lidar_xyz, "LiDAR")
        ]:
            if xyz.ndim != 2 or xyz.shape[1] != 3:
                raise RuntimeError(f"{name} shape invalid: {key}")
            if not np.isfinite(xyz).all():
                raise RuntimeError(f"{name} nonfinite: {key}")

        if len(radar_xyz) == 0 or len(lidar_xyz) == 0:
            raise RuntimeError(
                f"Empty cloud in selected steady-state frame {key}"
            )

        if len(radar_xyz) != len(radar_az) or \
           len(radar_xyz) != len(radar_el) or \
           len(radar_xyz) != len(radar_ray):
            raise RuntimeError(f"Radar array length mismatch: {key}")

        if len(lidar_xyz) != len(lidar_ray):
            raise RuntimeError(f"LiDAR array length mismatch: {key}")

        # Matrix of Radar-to-LiDAR Euclidean distances.
        squared = np.sum(
            (
                radar_xyz[:, None, :]
                - lidar_xyz[None, :, :]
            ) ** 2,
            axis=2
        )

        radar_to_lidar = np.argmin(squared, axis=1)
        nearest_d = np.sqrt(
            squared[
                np.arange(len(radar_xyz)),
                radar_to_lidar
            ]
        )

        # Identify which Radar point is nearest to each LiDAR point.
        lidar_to_radar = np.argmin(squared, axis=0)

        selected_lidar = lidar_xyz[radar_to_lidar]

        # Convert LiDAR vehicle-OSI coordinates to
        # local Unreal-axis directions about Radar mount.
        delta_osi = selected_lidar - radar_mount
        delta_ue = delta_osi * np.array([1.0, -1.0, 1.0])

        xy = np.hypot(delta_ue[:, 0], delta_ue[:, 1])

        lidar_bearing = np.arctan2(
            delta_ue[:, 1], delta_ue[:, 0]
        )
        lidar_elevation = np.arctan2(
            delta_ue[:, 2], xy
        )

        bearing_error = np.degrees(np.abs(
            angle_difference(lidar_bearing, radar_az)
        ))
        elevation_error = np.degrees(np.abs(
            lidar_elevation - radar_el
        ))

        within_distance = nearest_d <= DISTANCE_GATE_M
        within_angle = (
            (bearing_error <= ANGLE_GATE_DEG)
            & (elevation_error <= ANGLE_GATE_DEG)
        )

        mutual = (
            lidar_to_radar[radar_to_lidar]
            == np.arange(len(radar_xyz))
        )

        candidate = within_distance & within_angle & mutual

        for i in range(len(radar_xyz)):
            j = int(radar_to_lidar[i])
            detail.append({
                "PairID": pair,
                "Frame": frame,
                "RadarRayIndex": int(radar_ray[i]),
                "NearestLiDARRayIndex": int(lidar_ray[j]),
                "NearestDistanceM": float(nearest_d[i]),
                "BearingErrorDeg": float(bearing_error[i]),
                "ElevationErrorDeg": float(elevation_error[i]),
                "Within1m": bool(within_distance[i]),
                "Within5DegBoth": bool(within_angle[i]),
                "MutualNearest": bool(mutual[i]),
                "CandidateAssociation": bool(candidate[i]),
            })

        counts = {
            "PairID": pair,
            "Frame": frame,
            "RadarPoints": int(len(radar_xyz)),
            "LiDARPoints": int(len(lidar_xyz)),
            "Within1m": int(np.count_nonzero(within_distance)),
            "WithinAngularGate": int(np.count_nonzero(within_angle)),
            "MutualNearest": int(np.count_nonzero(mutual)),
            "CandidateAssociations": int(np.count_nonzero(candidate)),
            "CandidateFraction": float(np.mean(candidate)),
            "MedianDistanceM": float(np.median(nearest_d)),
            "MedianBearingErrorDeg": float(
                np.median(bearing_error)
            ),
            "MedianElevationErrorDeg": float(
                np.median(elevation_error)
            ),
            "SharedSVGTRecordedTimestamp": True,
            "IndependentRadarLiDARTimingVerified": False,
        }

        summary.append(counts)

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Radar={len(radar_xyz):3d} | "
            f"Within1m={counts['Within1m']:3d} | "
            f"Mutual={counts['MutualNearest']:3d} | "
            f"AllGates={counts['CandidateAssociations']:3d}"
        )


detail_path = CSV / (
    "task23_05d3_candidate_association_details.csv"
)
summary_path = CSV / (
    "task23_05d3_candidate_association_summary.csv"
)

save_csv(detail_path, detail, list(detail[0].keys()))
save_csv(summary_path, summary, list(summary[0].keys()))

labels = [
    f"P{r['PairID']}/F{r['Frame']}"
    for r in summary
]

x = np.arange(len(summary))

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(
    x - 0.2,
    [r["Within1m"] for r in summary],
    width=0.4,
    label="Within 1 m"
)
ax.bar(
    x + 0.2,
    [r["CandidateAssociations"] for r in summary],
    width=0.4,
    label="All three candidate tests"
)

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Radar return count")
ax.set_title("Exploratory Radar-LiDAR candidate associations")
ax.legend()
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()

graph_path = GRAPHS / (
    "task23_05d3_candidate_association_counts.png"
)
fig.savefig(graph_path, dpi=180)
plt.close(fig)

findings_path = FINDINGS / (
    "task23_05d3_candidate_association_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.5D-3",
        "Status": "EXPLORATORY_CROSS_SENSOR_ASSOCIATION",
        "DistanceGateM": DISTANCE_GATE_M,
        "HorizontalAndVerticalAngleGateDeg": ANGLE_GATE_DEG,
        "MutualNearestNeighborRequired": True,
        "Frames": summary,
        "Totals": {
            "RadarPoints": sum(r["RadarPoints"] for r in summary),
            "LiDARPoints": sum(r["LiDARPoints"] for r in summary),
            "CandidateAssociations": sum(
                r["CandidateAssociations"] for r in summary
            )
        },
        "Limitations": [
            "Thresholds are exploratory and not calibrated",
            "No object identity established",
            "Mutual nearest neighbor is not proof of correspondence",
            "Nearest point may be on a different target surface",
            "Only shared SensorView timestamps are available",
            "Coordinate conventions are source-based but not externally calibrated",
            "No detection accuracy, fusion accuracy, or energy benefit measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

total_radar = sum(r["RadarPoints"] for r in summary)
total_candidate = sum(
    r["CandidateAssociations"] for r in summary
)

print("\n=== TASK 23.5D-3 FINAL VERIFICATION ===")
print("Frame comparisons:", len(summary))
print("Radar returns examined:", total_radar)
print("Candidate associations:", total_candidate)
print("Detail CSV saved:", detail_path.is_file())
print("Summary CSV saved:", summary_path.is_file())
print("Graph saved:", graph_path.is_file())
print("Research JSON saved:", findings_path.is_file())

assert len(summary) == 6
assert total_radar == 237
assert len(detail) == 237

print("\n=== TASK 23.5D-3 COMPLETE ===")
