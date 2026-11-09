
# TASK 13.3F - FLAT SURFACE HYPOTHESIS
# GEMSTAR MOR100, frame 150
#
# Goal:
# Examine whether Unreal actor 83185 produces
# reflections on a nearly horizontal plane.
#
# Note:
# A flat reconstructed surface is NOT proof of road identity.

from pathlib import Path
from collections import defaultdict
from statistics import median, mean, pstdev
import csv
import math
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
T11 = ROOT / "tests" / "Task_11_Final_Research"
T13 = ROOT / "tests" / "Task_13_Final_Research"

DATA = T13 / "02_CSV_Data"
GRAPHS = T13 / "01_Graphs"
CODE = T13 / "04_Code"
FIND = T13 / "06_Research_Findings"

for folder in (DATA, GRAPHS, CODE, FIND):
    folder.mkdir(parents=True, exist_ok=True)

ACTOR = "83185"
NH = 251
NV = 21
FOV_VERTICAL = math.radians(20)

LIDAR_MOUNT_Z = 0.70

original_file = (
    T11 / "02_CSV_Data" /
    "task11_lidar_frame150_geometry.csv"
)

joined_file = (
    DATA / "task13_3d_lidar_actor_join.csv"
)

gt_file = (
    T11 / "02_CSV_Data" /
    "task11_groundtruth_objects.csv"
)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))


original = read_csv(original_file)
joined = read_csv(joined_file)
gt = read_csv(gt_file)

ego = next(
    row for row in gt
    if int(row["frame"]) == 150
    and int(row["object_id"]) == 76895
)

ego_z = float(ego["z_m"])

original_by_ray = {
    int(float(row["ray_index"])): row
    for row in original
}

records = []

for row in joined:
    ray = int(row["ray_index"])

    if ray not in original_by_ray:
        raise RuntimeError(
            f"Original ray not found: {ray}"
        )

    original_row = original_by_ray[ray]

    rng = float(original_row["range_m"])

    vertical_index = ray // NH

    elevation = (
        -FOV_VERTICAL / 2
        + vertical_index * FOV_VERTICAL / (NV - 1)
    )

    world_z = float(row["world_z_m"])

    # Reconstructed height from ray range and
    # vertical angle, using zero mounting rotation.
    calculated_world_z = (
        ego_z
        + LIDAR_MOUNT_Z
        + rng * math.sin(elevation)
    )

    records.append({
        "ray_index": ray,
        "actor_id": row["unreal_actor_id_diagnostic"],
        "range_m": rng,
        "vertical_index": vertical_index,
        "elevation_deg": math.degrees(elevation),
        "world_x_m": float(row["world_x_m"]),
        "world_y_m": float(row["world_y_m"]),
        "world_z_m": world_z,
        "recalculated_z_m": calculated_world_z,
        "z_consistency_error_m": abs(
            calculated_world_z - world_z
        ),
        "inside_gt_box": int(row["inside_gt_box"]),
    })

actor = [
    r for r in records
    if r["actor_id"] == ACTOR
]

other = [
    r for r in records
    if r["actor_id"] != ACTOR
]

if not actor:
    raise RuntimeError("No actor 83185 returns.")

z = [r["world_z_m"] for r in actor]
plane_z = median(z)

deviations = [
    abs(value - plane_z) for value in z
]

print("\n===== TASK 13.3F - FLAT SURFACE TEST =====")
print("Actor:", ACTOR)
print("Actor returns:", len(actor))
print("Median plane height:", round(plane_z, 6), "m")
print("Z standard deviation:", round(pstdev(z), 9), "m")
print("Maximum Z deviation:", round(max(deviations), 9), "m")
print("Ego GT center height:", round(ego_z, 6), "m")
print(
    "Plane minus ego center height:",
    round(plane_z - ego_z, 6), "m"
)

# Recalculate range expected for a horizontal plane.
# This is an INTERNAL geometric consistency test;
# it is not independent proof of surface identity.

range_errors = []

for row in actor:
    sin_elevation = math.sin(
        math.radians(row["elevation_deg"])
    )

    if abs(sin_elevation) < 1e-8:
        continue

    expected_range = (
        plane_z - ego_z - LIDAR_MOUNT_Z
    ) / sin_elevation

    if expected_range > 0:
        range_errors.append(
            abs(expected_range - row["range_m"])
        )

print("Usable plane-range comparisons:", len(range_errors))

if range_errors:
    print(
        "Mean plane-range residual:",
        round(mean(range_errors), 6), "m"
    )

print(
    "Distinct vertical ray indices:",
    sorted({r["vertical_index"] for r in actor})
)

# --------------------------------------------------
# Figure 1 - Height vs horizontal position
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 6))

ax.scatter(
    [r["world_x_m"] for r in other],
    [r["world_z_m"] for r in other],
    s=9, alpha=0.45,
    label="Other actor IDs"
)

ax.scatter(
    [r["world_x_m"] for r in actor],
    [r["world_z_m"] for r in actor],
    s=10, alpha=0.65,
    label="Actor 83185"
)

ax.axhline(
    plane_z, linestyle="--",
    label=f"Median plane Z = {plane_z:.4f} m"
)

ax.set_xlabel("OSI world X (m)")
ax.set_ylabel("OSI world Z (m)")
ax.set_title(
    "Task 13.3F - Reconstructed Surface Height"
)
ax.grid(True)
ax.legend()
fig.tight_layout()

plot1 = GRAPHS / "task13_3f_actor_height_plane.png"
fig.savefig(plot1, dpi=250)
plt.close(fig)

# --------------------------------------------------
# Figure 2 - Elevation vs range
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 7))

ax.scatter(
    [r["elevation_deg"] for r in actor],
    [r["range_m"] for r in actor],
    s=12, alpha=0.65,
    label="Recorded actor 83185 rays"
)

angles = [
    -9.5 + i * 0.1
    for i in range(95)
]

curve_x = []
curve_y = []

for degrees in angles:
    value = math.sin(math.radians(degrees))

    if abs(value) < 1e-8:
        continue

    predicted = (
        plane_z - ego_z - LIDAR_MOUNT_Z
    ) / value

    if 0 < predicted < 200:
        curve_x.append(degrees)
        curve_y.append(predicted)

ax.plot(
    curve_x, curve_y,
    linestyle="--",
    label="Predicted horizontal-plane range"
)

ax.set_xlabel("Vertical ray angle (degrees)")
ax.set_ylabel("Range (m)")
ax.set_title(
    "Task 13.3F - LiDAR Range vs Elevation"
)
ax.grid(True)
ax.legend()

fig.tight_layout()

plot2 = GRAPHS / "task13_3f_range_elevation_plane.png"
fig.savefig(plot2, dpi=250)
plt.close(fig)

# --------------------------------------------------
# Save point-by-point analysis
# --------------------------------------------------

output_csv = DATA / "task13_3f_flat_surface_analysis.csv"

with output_csv.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(records[0])
    )
    writer.writeheader()
    writer.writerows(records)

# Save actor statistics
summary = []

groups = defaultdict(list)

for row in records:
    groups[row["actor_id"]].append(
        row["world_z_m"]
    )

for actor_id, values in groups.items():
    summary.append({
        "actor_id": actor_id,
        "point_count": len(values),
        "min_z_m": min(values),
        "median_z_m": median(values),
        "max_z_m": max(values),
        "z_std_m": pstdev(values),
    })

summary_csv = DATA / "task13_3f_actor_height_statistics.csv"

with summary_csv.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summary[0])
    )
    writer.writeheader()
    writer.writerows(summary)

# --------------------------------------------------
# Save research findings
# --------------------------------------------------

findings = [
    "TASK 13.3F - HORIZONTAL SURFACE HYPOTHESIS",
    "",
    f"Actor ID: {ACTOR}",
    f"Actor returns: {len(actor)}",
    f"Median height: {plane_z:.9f} m",
    f"Height standard deviation: {pstdev(z):.9f} m",
    f"Maximum height deviation: {max(deviations):.9f} m",
    f"Ego GT center height: {ego_z:.9f} m",
    f"Usable plane-range comparisons: {len(range_errors)}",
    "",
    "RESEARCH INTERPRETATION",
    "Near-constant reconstructed height supports",
    "a horizontal-surface hypothesis.",
    "The actor could be road/ground geometry,",
    "but its semantic identity is not yet verified.",
    "",
    "LIMITATIONS",
    "Range-angle testing reuses the same reconstructed",
    "measurements and is not independent validation.",
    "Potential sensor timing and origin errors remain.",
    "OSI GT object IDs do not directly identify",
    "the Unreal actor from these measurements.",
    "No confirmed target vehicle association.",
]

(FIND / "task13_3f_flat_surface_findings.txt").write_text(
    "\n".join(findings) + "\n",
    encoding="utf-8"
)

shutil.copy2(
    Path(__file__), CODE / Path(__file__).name
)

print("\nSaved:", output_csv)
print("Saved:", summary_csv)
print("Saved:", plot1)
print("Saved:", plot2)
print("TASK 13.3F COMPLETED")
