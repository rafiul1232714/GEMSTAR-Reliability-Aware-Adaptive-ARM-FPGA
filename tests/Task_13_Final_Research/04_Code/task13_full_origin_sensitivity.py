
# TASK 13.3T - FULL ORIGIN CORRECTION SENSITIVITY
# Frame 150, GEMSTAR MOR100
#
# Compares original, Z-corrected and full-offset points.
# The full offset is a CROSS-RUN hypothesis.
# It is not an independently established MOR100 calibration.

from pathlib import Path
from collections import Counter
import csv
import shutil
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"
T11 = ROOT / "tests" / "Task_11_Final_Research"

DATA = TASK / "02_CSV_Data"
GRAPHS = TASK / "01_Graphs"
FIND = TASK / "06_Research_Findings"
CODE = TASK / "04_Code"

for folder in (DATA, GRAPHS, FIND, CODE):
    folder.mkdir(parents=True, exist_ok=True)

# Offset measured in NEW diagnostic run, Unreal cm:
# X = +15.738 cm
# Y = +7.349 cm
# Z = +82.620 cm
#
# Convert to OSI coordinates: reverse Unreal Y.
OFFSET_OSI = (0.15738, -0.07349, 0.82620)

FLAT_ACTOR = "83185"
TARGET_ID = 76865
FRAME = 150


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


points = load_csv(DATA / "task13_3d_lidar_actor_join.csv")
gt = load_csv(
    T11 / "02_CSV_Data" / "task11_groundtruth_objects.csv"
)

target = next(
    r for r in gt
    if int(float(r["frame"])) == FRAME
    and int(float(r["object_id"])) == TARGET_ID
)

center = (
    float(target["x_m"]),
    float(target["y_m"]),
    float(target["z_m"]),
)

# GEMSTAR exporter writes WORLD-AABB half extents.
extent = (
    float(target["length_m"]),
    float(target["width_m"]),
    float(target["height_m"]),
)

minimum = tuple(c-e for c, e in zip(center, extent))
maximum = tuple(c+e for c, e in zip(center, extent))


def distance_to_aabb(p):
    delta = [
        max(lo-v, 0.0, v-hi)
        for v, lo, hi in zip(p, minimum, maximum)
    ]
    return math.sqrt(sum(d*d for d in delta))


def analyze(label, offset):
    results = []
    for row in points:
        original = (
            float(row["world_x_m"]),
            float(row["world_y_m"]),
            float(row["world_z_m"])
        )

        corrected = tuple(
            v-d for v, d in zip(original, offset)
        )

        dist = distance_to_aabb(corrected)
        actor = row["unreal_actor_id_diagnostic"]

        results.append({
            "test": label,
            "frame": FRAME,
            "ray_index": int(float(row["ray_index"])),
            "actor_id": actor,
            "x_m": corrected[0],
            "y_m": corrected[1],
            "z_m": corrected[2],
            "box_distance_m": dist,
            "inside_box": int(dist <= 1e-9),
            "within_050m": int(dist <= 0.50),
            "within_100m": int(dist <= 1.00),
            "excluded_flat_actor": int(actor == FLAT_ACTOR),
        })

    return results


tests = [
    ("A_original", (0.0, 0.0, 0.0)),
    ("B_vertical_only", (0.0, 0.0, OFFSET_OSI[2])),
    ("C_full_cross_run", OFFSET_OSI),
]

all_results = []
summaries = []

print("\n===== TASK 13.3T - ORIGIN SENSITIVITY =====")

for label, offset in tests:
    rows = analyze(label, offset)
    all_results.extend(rows)

    nonflat = [
        r for r in rows
        if r["actor_id"] != FLAT_ACTOR
    ]

    near = [
        r for r in nonflat
        if r["within_100m"]
    ]

    inside = sum(r["inside_box"] for r in nonflat)
    half = sum(r["within_050m"] for r in nonflat)

    closest = min(
        (r["box_distance_m"] for r in nonflat),
        default=float("nan")
    )

    print(f"\n{label}")
    print("Applied OSI offset (m):", offset)
    print("Non-flat points:", len(nonflat))
    print("Non-flat inside box:", inside)
    print("Non-flat within 0.50m:", half)
    print("Non-flat within 1.00m:", len(near))
    print("Closest non-flat distance:", f"{closest:.6f} m")

    print(
        "Near-box non-flat actor IDs:",
        dict(Counter(r["actor_id"] for r in near))
    )

    summaries.append({
        "test": label,
        "offset_x_m": offset[0],
        "offset_y_m": offset[1],
        "offset_z_m": offset[2],
        "nonflat_point_count": len(nonflat),
        "nonflat_inside_box": inside,
        "nonflat_within_050m": half,
        "nonflat_within_100m": len(near),
        "minimum_nonflat_box_distance_m": closest,
    })


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


detail_file = DATA / "task13_3t_origin_sensitivity_points.csv"
summary_file = DATA / "task13_3t_origin_sensitivity_summary.csv"

write_csv(detail_file, all_results)
write_csv(summary_file, summaries)

# Graph 1: non-flat points within distance thresholds.
fig, ax = plt.subplots(figsize=(11, 6))

labels = [r["test"] for r in summaries]
counts05 = [r["nonflat_within_050m"] for r in summaries]
counts10 = [r["nonflat_within_100m"] for r in summaries]

x = list(range(len(labels)))

ax.bar(
    [v-0.18 for v in x], counts05,
    width=0.36, label="Within 0.50m"
)
ax.bar(
    [v+0.18 for v in x], counts10,
    width=0.36, label="Within 1.00m"
)

ax.set_xticks(x, labels)
ax.set_ylabel("Non-flat LiDAR point count")
ax.set_title(
    "Task 13.3T - Sensitivity to Origin Correction"
)
ax.grid(axis="y", alpha=0.3)
ax.legend()

fig.tight_layout()
graph1 = GRAPHS / "task13_3t_near_box_comparison.png"
fig.savefig(graph1, dpi=250)
plt.close(fig)

# Graph 2: corrected point clouds in world XY.
fig, axes = plt.subplots(1, 3, figsize=(17, 6))

for ax, (label, _) in zip(axes, tests):
    rows = [
        r for r in all_results
        if r["test"] == label
        and r["actor_id"] != FLAT_ACTOR
    ]

    if rows:
        ax.scatter(
            [r["x_m"] for r in rows],
            [r["y_m"] for r in rows],
            s=8, alpha=0.7
        )

    ax.add_patch(Rectangle(
        (minimum[0], minimum[1]),
        2*extent[0], 2*extent[1],
        fill=False, linewidth=2,
        label="Target GT AABB"
    ))

    ax.scatter(
        [center[0]], [center[1]],
        marker="x", s=60
    )

    ax.set_xlim(center[0]-12, center[0]+16)
    ax.set_ylim(center[1]-12, center[1]+12)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(label)
    ax.set_xlabel("OSI world X (m)")
    ax.set_ylabel("OSI world Y (m)")
    ax.grid(True)

fig.suptitle(
    "Non-flat LiDAR points: alternative origin assumptions"
)
fig.tight_layout()

graph2 = GRAPHS / "task13_3t_nonflat_xy_comparison.png"
fig.savefig(graph2, dpi=250)
plt.close(fig)

findings = [
    "TASK 13.3T - ORIGIN SENSITIVITY",
    "",
    "Test A: original reconstructed world coordinates.",
    "Test B: subtract independent Z-origin offset.",
    "Test C: subtract full cross-run WORLD offset.",
    "",
    "Measured new-run offset (OSI m):",
    str(OFFSET_OSI),
    "",
    "IMPORTANT LIMITATIONS:",
    "The full XY offset is from a different simulation.",
    "World-axis bounding offsets may depend on yaw.",
    "The correction is a sensitivity analysis only.",
    "Actor 83185 is excluded diagnostically.",
    "No actor-to-GT identity mapping has been proved.",
    "No target detection or fusion accuracy is claimed.",
    "",
    "RESULTS:",
]

for row in summaries:
    findings.append(str(row))

finding_file = (
    FIND / "task13_3t_origin_sensitivity_findings.txt"
)
finding_file.write_text(
    "\n".join(findings) + "\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\nSaved:", detail_file)
print("Saved:", summary_file)
print("Saved:", graph1)
print("Saved:", graph2)
print("Saved:", finding_file)
print("\nTASK 13.3T COMPLETED")
