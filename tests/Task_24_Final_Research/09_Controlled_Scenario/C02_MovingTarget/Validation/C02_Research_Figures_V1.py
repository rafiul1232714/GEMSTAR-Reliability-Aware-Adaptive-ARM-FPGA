import csv
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

comparison = load(os.environ["C02_COMPARE"])
gt = load(os.environ["C02_GT2D"])
track = load(os.environ["C02_TRACK"])

filters = {
    name: load(os.environ["C02_" + name])
    for name in ("V1", "V2", "V3")
}

if len(comparison) != 53 or len(gt) != 53 or len(track) != 53:
    raise RuntimeError("Expected 53 records per input")

for name, rows in filters.items():
    if len(rows) != 53:
        raise RuntimeError(f"{name} has incorrect row count")

times = np.array([float(r["time_s"]) for r in gt])

for i, (a, b, c) in enumerate(zip(comparison, gt, track)):
    if abs(float(a["time_s"]) - times[i]) > 1e-5:
        raise RuntimeError("Comparison timestamp mismatch")
    if abs(float(b["time_s"]) - times[i]) > 1e-5:
        raise RuntimeError("GroundTruth timestamp mismatch")
    if abs(float(c["sensor_time_s"]) - times[i]) > 0.1:
        raise RuntimeError("LiDAR timestamp mismatch")

for name, rows in filters.items():
    for i, r in enumerate(rows):
        if abs(float(r["sensor_time_s"]) - times[i]) > 1e-5:
            raise RuntimeError(f"{name} timestamp mismatch")

outdir = Path(os.environ["C02_FIGURES"])
names = [
    "C02_Figure_01_Aligned_Trajectories.png",
    "C02_Figure_02_2D_Tracking_Error.png",
    "C02_Figure_03_Velocity_Error.png",
    "C02_Figure_04_Lidar_Reliability.png"
]

for name in names:
    if (outdir / name).exists():
        raise RuntimeError(f"Output already exists: {name}")

plt.rcParams.update({
    "figure.dpi": 125,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.25
})

def save(fig, filename):
    fig.tight_layout()
    fig.savefig(outdir / filename, bbox_inches="tight")
    plt.close(fig)
    print("FIGURE_SAVED=", outdir / filename)

# Figure 1: initial-aligned 2D displacement trajectories.
fig, ax = plt.subplots(figsize=(8.5, 6.5))

gx = np.array([float(r["gt_x"]) for r in gt])
gy = np.array([float(r["gt_y"]) for r in gt])
ax.plot(gx-gx[0], gy-gy[0], linewidth=2.5, label="GroundTruth")

for name, rows in filters.items():
    x = np.array([float(r["ekf_x_m"]) for r in rows])
    y = np.array([float(r["ekf_y_m"]) for r in rows])
    ax.plot(x-x[0], y-y[0], linewidth=1.5, label=f"EKF {name}")

ax.set_title("C02: Initial-Aligned Target Displacement")
ax.set_xlabel("X displacement (m)")
ax.set_ylabel("Y displacement (m)")
ax.set_aspect("equal", adjustable="box")
ax.legend()
save(fig, names[0])

# Figure 2: 2D error versus time.
fig, ax = plt.subplots(figsize=(9, 5))

for name in filters:
    errors = [float(r[f"{name}_2d_error_m"]) for r in comparison]
    ax.plot(times, errors, label=f"EKF {name}", linewidth=1.6)

ax.axvspan(26.25, 28.2, alpha=0.10, label="Prediction-only interval")
ax.set_title("C02: Initial-Aligned 2D Displacement Error")
ax.set_xlabel("Simulation time (s)")
ax.set_ylabel("2D displacement error (m)")
ax.legend()
save(fig, names[1])

# Figure 3: velocity-vector error versus time.
fig, ax = plt.subplots(figsize=(9, 5))

for name in filters:
    errors = [
        float(r[f"{name}_velocity_error_mps"])
        if str(r[f"{name}_velocity_error_mps"]).strip()
        else np.nan
        for r in comparison
    ]
    ax.plot(times, errors, label=f"EKF {name}", linewidth=1.6)

ax.axvspan(26.25, 28.2, alpha=0.10, label="Prediction-only interval")
ax.set_title("C02: Velocity Vector Error")
ax.set_xlabel("Simulation time (s)")
ax.set_ylabel("Velocity-vector error (m/s)")
ax.legend()
save(fig, names[2])

# Figure 4: late-stage LiDAR reliability and 2D error.
fig, ax1 = plt.subplots(figsize=(9, 5.5))

points = np.array([
    int(r["selected_cluster_points"])
    if str(r["selected_cluster_points"]).strip() else 0
    for r in track
])

mask = times >= 22.0
ax1.plot(times[mask], points[mask], marker="o",
         label="Selected LiDAR cluster points")
ax1.set_xlabel("Simulation time (s)")
ax1.set_ylabel("LiDAR cluster points")

ax2 = ax1.twinx()

for name in filters:
    errors = np.array([
        float(r[f"{name}_2d_error_m"]) for r in comparison
    ])
    ax2.plot(times[mask], errors[mask], linestyle="--",
             label=f"EKF {name} 2D error")

ax2.set_ylabel("2D displacement error (m)")
ax1.set_title("C02: Sparse LiDAR Returns and Tracking Error")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
save(fig, names[3])

print("\nFIGURES_CREATED=", len(names))
print("METRIC=INITIAL_ALIGNED_2D_DISPLACEMENT")
print("ABSOLUTE_VEHICLE_CENTER_ACCURACY=NO")
print("GROUND_TRUTH_USED_FOR_PLOTS_ONLY=YES")
print("SOURCE_DATA_MODIFIED=NO")
print("TASK24_05_04Z_FIGURES_COMPLETE")
