
# TASK 13.3G - GROUND-SURFACE FILTERING
# GEMSTAR MOR100 - Frame 150
#
# Exclude candidate flat-surface actor 83185,
# then inspect remaining LiDAR actor distributions.
#
# The exclusion is diagnostic, not a verified
# semantic road/ground classification.

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
T11 = ROOT / "tests" / "Task_11_Final_Research"
T13 = ROOT / "tests" / "Task_13_Final_Research"

DATA = T13 / "02_CSV_Data"
GRAPHS = T13 / "01_Graphs"
CODE = T13 / "04_Code"
FIND = T13 / "06_Research_Findings"

for folder in (DATA, GRAPHS, CODE, FIND):
    folder.mkdir(parents=True, exist_ok=True)

ACTOR_EXCLUDED = "83185"
FRAME = 150
TARGET_ID = 76865

INPUT = DATA / "task13_3d_lidar_actor_join.csv"
GT_FILE = (
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


rows = read_csv(INPUT)
gt = read_csv(GT_FILE)

target = next(
    r for r in gt
    if int(r["frame"]) == FRAME
    and int(r["object_id"]) == TARGET_ID
)

# Preserve all original records and classify them.
for r in rows:
    actor = r["unreal_actor_id_diagnostic"]
    r["flat_surface_actor_excluded"] = int(
        actor == ACTOR_EXCLUDED
    )

remaining = [
    r for r in rows
    if r["unreal_actor_id_diagnostic"] != ACTOR_EXCLUDED
]

excluded = [
    r for r in rows
    if r["unreal_actor_id_diagnostic"] == ACTOR_EXCLUDED
]

inside_remaining = [
    r for r in remaining
    if int(float(r["inside_gt_box"])) == 1
]

near025_remaining = [
    r for r in remaining
    if float(r["distance_to_gt_box_m"]) <= 0.25
]

near050_remaining = [
    r for r in remaining
    if float(r["distance_to_gt_box_m"]) <= 0.50
]

near100_remaining = [
    r for r in remaining
    if float(r["distance_to_gt_box_m"]) <= 1.00
]

print("\n===== TASK 13.3G - GROUND FILTER =====")

print("Original LiDAR points:", len(rows))
print("Excluded actor 83185:", len(excluded))
print("Remaining points:", len(remaining))

print("\nAfter actor exclusion:")
print("Inside target GT box:", len(inside_remaining))
print("Within 0.25 m:", len(near025_remaining))
print("Within 0.50 m:", len(near050_remaining))
print("Within 1.00 m:", len(near100_remaining))

print("\nRemaining actor IDs:")

counts = Counter(
    r["unreal_actor_id_diagnostic"]
    for r in remaining
)

for actor, count in counts.most_common():
    near_count = sum(
        1 for r in near050_remaining
        if r["unreal_actor_id_diagnostic"] == actor
    )
    print(
        f"  Actor {actor}: {count} total, "
        f"{near_count} within 0.50 m"
    )

# -------------------------------------------------
# Save filtered dataset
# -------------------------------------------------

filtered_csv = DATA / "task13_3g_remaining_lidar_points.csv"

if remaining:
    with filtered_csv.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(remaining[0])
        )
        writer.writeheader()
        writer.writerows(remaining)

summary = []

for actor, count in counts.most_common():
    subset = [
        r for r in remaining
        if r["unreal_actor_id_diagnostic"] == actor
    ]

    zz = [float(r["world_z_m"]) for r in subset]

    summary.append({
        "actor_id": actor,
        "point_count": count,
        "min_z_m": min(zz),
        "max_z_m": max(zz),
        "inside_gt_box": sum(
            int(float(r["inside_gt_box"]))
            for r in subset
        ),
        "within_050m": sum(
            float(r["distance_to_gt_box_m"]) <= 0.50
            for r in subset
        ),
    })

summary_csv = DATA / "task13_3g_remaining_actor_summary.csv"

with summary_csv.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "actor_id",
            "point_count",
            "min_z_m",
            "max_z_m",
            "inside_gt_box",
            "within_050m"
        ]
    )
    writer.writeheader()
    writer.writerows(summary)

# -------------------------------------------------
# Figure 1 - BEFORE / AFTER top-view comparison
# -------------------------------------------------

cx = float(target["x_m"])
cy = float(target["y_m"])

ex = float(target["length_m"])
ey = float(target["width_m"])

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, group, label in [
    (axes[0], rows, "All LiDAR points"),
    (axes[1], remaining, "After excluding actor 83185")
]:
    if group:
        ax.scatter(
            [float(r["world_x_m"]) for r in group],
            [float(r["world_y_m"]) for r in group],
            s=8, alpha=0.6
        )

    ax.add_patch(Rectangle(
        (cx-ex, cy-ey),
        2*ex, 2*ey,
        fill=False,
        linewidth=2,
        label="Target GT box proxy"
    ))

    ax.scatter([cx], [cy], s=70, marker="x")
    ax.set_xlabel("OSI world X (m)")
    ax.set_ylabel("OSI world Y (m)")
    ax.set_title(label)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True)
    ax.legend()

# Shared scale makes the comparison meaningful.
all_x = [float(r["world_x_m"]) for r in rows]
all_y = [float(r["world_y_m"]) for r in rows]

xmin = min(all_x + [cx-ex]) - 1
xmax = max(all_x + [cx+ex]) + 1
ymin = min(all_y + [cy-ey]) - 1
ymax = max(all_y + [cy+ey]) + 1

for ax in axes:
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

fig.suptitle("Task 13.3G - Flat-Surface Actor Exclusion")
fig.tight_layout()

plot1 = GRAPHS / "task13_3g_before_after_filter.png"
fig.savefig(plot1, dpi=250)
plt.close(fig)

# -------------------------------------------------
# Figure 2 - Remaining actors in 3D
# -------------------------------------------------

fig = plt.figure(figsize=(11, 8))
ax = fig.add_subplot(111, projection="3d")

for actor in sorted(counts):
    group = [
        r for r in remaining
        if r["unreal_actor_id_diagnostic"] == actor
    ]

    ax.scatter(
        [float(r["world_x_m"]) for r in group],
        [float(r["world_y_m"]) for r in group],
        [float(r["world_z_m"]) for r in group],
        s=12,
        label=f"Actor {actor}"
    )

ax.set_xlabel("OSI world X (m)")
ax.set_ylabel("OSI world Y (m)")
ax.set_zlabel("OSI world Z (m)")
ax.set_title("Remaining LiDAR Actors - 3D Geometry")
ax.legend()

plot2 = GRAPHS / "task13_3g_remaining_actors_3d.png"

fig.tight_layout()
fig.savefig(plot2, dpi=250)
plt.close(fig)

# -------------------------------------------------
# Findings
# -------------------------------------------------

findings = [
    "TASK 13.3G - FLAT-SURFACE ACTOR FILTERING",
    "",
    f"Original LiDAR points: {len(rows)}",
    f"Excluded actor 83185: {len(excluded)}",
    f"Remaining LiDAR points: {len(remaining)}",
    f"Remaining inside GT box: {len(inside_remaining)}",
    f"Remaining within 0.25 m: {len(near025_remaining)}",
    f"Remaining within 0.50 m: {len(near050_remaining)}",
    f"Remaining within 1.00 m: {len(near100_remaining)}",
    "",
    "ACTOR COUNTS:",
    *[
        f"Actor {actor}: {count}"
        for actor, count in counts.most_common()
    ],
    "",
    "INTERPRETATION:",
    "Actor 83185 is excluded using its diagnostic ID.",
    "The flat-surface hypothesis is strongly supported",
    "but its semantic identity is not yet independently proven.",
    "Remaining actors are not automatically vehicles.",
    "GT AABB and sensor-origin assumptions remain provisional.",
    "Zero remaining candidates, if observed, do not",
    "prove the vehicle was absent or impossible to detect.",
    "No validated object-level fusion is claimed.",
]

finding_file = (
    FIND / "task13_3g_ground_filter_findings.txt"
)

finding_file.write_text(
    "\n".join(findings) + "\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\nSaved:", filtered_csv)
print("Saved:", summary_csv)
print("Saved:", plot1)
print("Saved:", plot2)
print("TASK 13.3G COMPLETED")
