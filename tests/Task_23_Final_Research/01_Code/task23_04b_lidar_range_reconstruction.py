import csv
import json
import math
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
    iter_osi_messages,
    SensorView,
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"
DATA_DIR = (
    TASK / "08_Processed_Data" / "LiDAR_Range"
)

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS, DATA_DIR):
    folder.mkdir(parents=True, exist_ok=True)

C = 299792458.0
FRAME_LIMIT = 100
SAMPLE_FRAMES = {1, 25, 99}

# Screening rule, not a validated sensor-detection rule.
MIN_RANGE_M = 0.05
MAX_RANGE_M = 200.0


def get_ranges(reflections):
    tof = np.asarray(
        [r.time_of_flight for r in reflections],
        dtype=np.float64
    )

    strength = np.asarray(
        [r.signal_strength for r in reflections],
        dtype=np.float64
    )

    range_m = C * tof / 2.0

    positive = (
        np.isfinite(tof)
        & np.isfinite(strength)
        & (tof > 0)
        & (strength > 0)
    )

    screened = (
        positive
        & np.isfinite(range_m)
        & (range_m >= MIN_RANGE_M)
        & (range_m <= MAX_RANGE_M)
    )

    image_values = range_m.copy()
    image_values[~screened] = np.nan

    return image_values, positive, screened


def get_ray_directions(config, width, height):
    """Prefer explicit directions. Otherwise uniform-angle hypothesis."""
    n = width * height
    explicit = getattr(config, "directions", [])

    if len(explicit) == n:
        vectors = np.array([
            [v.x, v.y, v.z] for v in explicit
        ], dtype=np.float64)

        norms = np.linalg.norm(vectors, axis=1)
        good = np.all(np.isfinite(vectors), axis=1) & (norms > 0)

        if np.all(good):
            return (
                vectors / norms[:, None],
                "EXPLICIT_OSI_DIRECTIONS"
            )

    # Assumption: uniformly spaced rays including FOV endpoints.
    # Azimuth positive means left under the chosen OSI frame.
    azimuths = np.linspace(
        config.field_of_view_horizontal / 2,
        -config.field_of_view_horizontal / 2,
        width
    )

    elevations = np.linspace(
        config.field_of_view_vertical / 2,
        -config.field_of_view_vertical / 2,
        height
    )

    az, el = np.meshgrid(azimuths, elevations)

    # x = forward, y = left, z = up.
    # This is the provisional conventional spherical mapping.
    directions = np.stack([
        np.cos(el) * np.cos(az),
        np.cos(el) * np.sin(az),
        np.sin(el)
    ], axis=-1)

    return directions.reshape(-1, 3), "UNIFORM_FOV_HYPOTHESIS"


def save_range_image(range_image, pair_id, frame):
    path = GRAPH_DIR / (
        f"task23_04b_pair{pair_id}_"
        f"frame{frame:03d}_range_image.png"
    )

    fig, ax = plt.subplots(figsize=(11, 4))

    im = ax.imshow(
        range_image,
        aspect="auto",
        interpolation="nearest",
        cmap="viridis",
        vmin=0,
        vmax=50
    )

    ax.set_title(
        f"Pair {pair_id} - LiDAR range image - frame {frame}"
    )
    ax.set_xlabel("Horizontal ray index")
    ax.set_ylabel("Vertical ray index")
    fig.colorbar(im, ax=ax, label="Range (m)")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)

    return path


def save_point_cloud(points, pair_id, frame, method):
    path = GRAPH_DIR / (
        f"task23_04b_pair{pair_id}_"
        f"frame{frame:03d}_point_cloud.png"
    )

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    if len(points):
        # Plot a deterministic subset if needed.
        step = max(1, math.ceil(len(points) / 4000))
        subset = points[::step]

        artist = ax.scatter(
            subset[:, 0],
            subset[:, 1],
            subset[:, 2],
            c=subset[:, 0],
            cmap="viridis",
            s=1.5
        )
        fig.colorbar(
            artist, ax=ax, shrink=0.65,
            label="Forward distance (m)"
        )

    ax.set_xlabel("X forward (m)")
    ax.set_ylabel("Y left (m)")
    ax.set_zlabel("Z up (m)")
    ax.set_title(
        f"Pair {pair_id}, frame {frame}\n"
        f"{method} - geometry not independently validated"
    )

    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)

    return path


def write_csv(path, rows, columns):
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


print("\n=== TASK 23.4B LIDAR RANGE RECONSTRUCTION ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as handle:
    pairs = list(csv.DictReader(handle))

frame_rows = []
sampled_points = []
all_ranges = {}
methods = {}

for pair in pairs:
    pair_id = pair["PairID"]
    source = Path(pair["SensorViewPath"])

    print(f"\n=== PAIR {pair_id} ===")

    pair_ranges = []
    seen = 0

    for frame, message, size in iter_osi_messages(
        source, SensorView, FRAME_LIMIT
    ):
        seen += 1
        views = message.lidar_sensor_view

        if not views:
            frame_rows.append({
                "PairID": pair_id,
                "Frame": frame,
                "RaySlots": 0,
                "PositiveReturns": 0,
                "ScreenedReturns": 0,
                "CoveragePct": 0,
                "MinRangeM": "",
                "MedianRangeM": "",
                "MeanRangeM": "",
                "MaxRangeM": "",
                "GeometryMethod": "NO_LIDAR"
            })
            continue

        lidar = views[0]
        config = lidar.view_configuration

        width = int(config.number_of_rays_horizontal)
        height = int(config.number_of_rays_vertical)
        expected = width * height

        if expected != len(lidar.reflection):
            raise ValueError(
                f"Pair {pair_id}, frame {frame}: "
                "ray count does not match configuration"
            )

        distances, positive, screened = get_ranges(
            lidar.reflection
        )

        valid = distances[screened]
        pair_ranges.extend(valid.tolist())

        coverage = 100.0 * (
            int(np.count_nonzero(screened)) / expected
        )

        if len(valid):
            minimum = float(np.min(valid))
            median = float(np.median(valid))
            mean = float(np.mean(valid))
            maximum = float(np.max(valid))
        else:
            minimum = median = mean = maximum = ""

        # Direction source is checked on every processed frame.
        directions, method = get_ray_directions(
            config, width, height
        )
        methods.setdefault(pair_id, set()).add(method)

        frame_rows.append({
            "PairID": pair_id,
            "Frame": frame,
            "RaySlots": expected,
            "PositiveReturns": int(np.count_nonzero(positive)),
            "ScreenedReturns": int(np.count_nonzero(screened)),
            "CoveragePct": coverage,
            "MinRangeM": minimum,
            "MedianRangeM": median,
            "MeanRangeM": mean,
            "MaxRangeM": maximum,
            "GeometryMethod": method
        })

        if frame in SAMPLE_FRAMES:
            range_image = distances.reshape(height, width)

            # Reconstructed points in sensor coordinates.
            pts_all = (
                directions * distances.reshape(-1, 1)
            )
            points = pts_all[screened]

            npz_path = DATA_DIR / (
                f"pair{pair_id}_frame{frame:03d}_lidar.npz"
            )

            np.savez_compressed(
                npz_path,
                range_image_m=range_image,
                points_sensor_m=points,
                valid_mask=screened.reshape(height, width),
                reconstruction_method=np.array(method)
            )

            save_range_image(
                range_image, pair_id, frame
            )

            if frame == 25:
                save_point_cloud(
                    points, pair_id, frame, method
                )

                original_indices = np.flatnonzero(screened)

                for idx, xyz in zip(original_indices, points):
                    sampled_points.append({
                        "PairID": pair_id,
                        "Frame": frame,
                        "RayIndex": int(idx),
                        "XSensorM": float(xyz[0]),
                        "YSensorM": float(xyz[1]),
                        "ZSensorM": float(xyz[2]),
                        "RangeM": float(distances[idx]),
                        "GeometryMethod": method
                    })

    if seen != FRAME_LIMIT:
        raise RuntimeError(
            f"Pair {pair_id}: expected 100 frames, got {seen}"
        )

    all_ranges[pair_id] = pair_ranges
    pair_frames = [
        r for r in frame_rows if r["PairID"] == pair_id
    ]

    print("Frames analyzed:", seen)
    print(
        "Total screened returns:",
        sum(int(r["ScreenedReturns"]) for r in pair_frames)
    )
    print(
        "Geometry methods:",
        ", ".join(sorted(methods.get(pair_id, {"NO_LIDAR"})))
    )

# ---------------------------------------------------------
# Save frame metrics
# ---------------------------------------------------------

metrics_path = (
    CSV_DIR / "task23_04b_lidar_frame_range_metrics.csv"
)

write_csv(
    metrics_path,
    frame_rows,
    list(frame_rows[0].keys())
)

# ---------------------------------------------------------
# Save candidate 3D points from frame 25
# ---------------------------------------------------------

points_path = (
    DATA_DIR / "task23_04b_frame25_candidate_points.csv"
)

if sampled_points:
    write_csv(
        points_path,
        sampled_points,
        list(sampled_points[0].keys())
    )

# ---------------------------------------------------------
# Summary per recording
# ---------------------------------------------------------

summary = []

for pair in pairs:
    pair_id = pair["PairID"]
    records = [
        r for r in frame_rows if r["PairID"] == pair_id
    ]
    ranges = np.asarray(
        all_ranges[pair_id], dtype=np.float64
    )

    summary.append({
        "PairID": pair_id,
        "Frames": len(records),
        "RaySlots": sum(int(r["RaySlots"]) for r in records),
        "PositiveReturns": sum(
            int(r["PositiveReturns"]) for r in records
        ),
        "ScreenedReturns": int(ranges.size),
        "MeanCoveragePct": float(np.mean([
            float(r["CoveragePct"]) for r in records
        ])),
        "MedianRangeM": (
            float(np.median(ranges)) if ranges.size else ""
        ),
        "MaxRangeM": (
            float(np.max(ranges)) if ranges.size else ""
        ),
        "GeometryMethods": ";".join(
            sorted(methods.get(pair_id, {"NO_LIDAR"}))
        )
    })

summary_path = (
    CSV_DIR / "task23_04b_lidar_recording_summary.csv"
)

write_csv(
    summary_path, summary, list(summary[0].keys())
)

# ---------------------------------------------------------
# Graph 1: Return coverage over 100 frames
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5))

for pair_id in ("1", "2", "3"):
    subset = [
        r for r in frame_rows if r["PairID"] == pair_id
    ]

    ax.plot(
        [r["Frame"] for r in subset],
        [r["CoveragePct"] for r in subset],
        label=f"Pair {pair_id}"
    )

ax.set_xlabel("Recorded frame index")
ax.set_ylabel("Screened return coverage (%)")
ax.set_title("LiDAR usable-return screening over 100 frames")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

coverage_path = (
    GRAPH_DIR / "task23_04b_lidar_return_coverage.png"
)

fig.savefig(coverage_path, dpi=180)
plt.close(fig)

# ---------------------------------------------------------
# Graph 2: Distribution of reconstructed ranges
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(10, 5))

for pair_id in ("1", "2", "3"):
    values = np.asarray(all_ranges[pair_id])

    if values.size:
        ax.hist(
            values,
            bins=75,
            range=(0, 75),
            density=True,
            histtype="step",
            linewidth=1.5,
            label=f"Pair {pair_id}"
        )

ax.set_xlabel("Reconstructed range (m)")
ax.set_ylabel("Density")
ax.set_title("LiDAR reconstructed-range distributions")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

histogram_path = (
    GRAPH_DIR / "task23_04b_lidar_range_distribution.png"
)

fig.savefig(histogram_path, dpi=180)
plt.close(fig)

# ---------------------------------------------------------
# Save research interpretation and limitations
# ---------------------------------------------------------

findings_path = (
    FINDINGS / "task23_04b_lidar_range_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4B",
        "FrameLimitPerRecording": FRAME_LIMIT,
        "SpeedOfLightMPerS": C,
        "RangeFormula": "range_m = c * time_of_flight_s / 2",
        "ScreeningRangeM": [
            MIN_RANGE_M, MAX_RANGE_M
        ],
        "RangeImageShape": "21 rows x 251 columns",
        "Recordings": summary,
        "GeometryStatus": {
            key: sorted(value)
            for key, value in methods.items()
        },
        "Limitations": [
            "Uniform beam directions are a hypothesis unless explicit OSI directions exist",
            "Sensor-frame 3D coordinates are not yet GroundTruth validated",
            "Positive TOF and signal strength do not guarantee correct detections",
            "Distance thresholds are preliminary screening choices",
            "Object IDs were not used as perception predictions",
            "Frame zero remains included but flagged for later evaluation",
            "No CPU-versus-FPGA energy measurements have been made"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4B RECORDING SUMMARY ===")

for item in summary:
    print(
        f"Pair {item['PairID']} | "
        f"Frames={item['Frames']} | "
        f"Positive={item['PositiveReturns']} | "
        f"Screened={item['ScreenedReturns']} | "
        f"Coverage={item['MeanCoveragePct']:.2f}% | "
        f"MedianRange={item['MedianRangeM']}"
    )

print("\n=== TASK 23.4B FINAL VERIFICATION ===")
print("Total frame records:", len(frame_rows))
print("Frame metrics CSV:", metrics_path.is_file())
print("Recording summary CSV:", summary_path.is_file())
print("Frame 25 candidate points:", points_path.is_file())
print("Return coverage graph:", coverage_path.is_file())
print("Range distribution graph:", histogram_path.is_file())
print("Research findings:", findings_path.is_file())
print("NPZ samples:", len(list(DATA_DIR.glob("*.npz"))))

print("\n=== TASK 23.4B COMPLETE ===")
