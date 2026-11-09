
# TASK 13.3E - ACTOR 83185 INVESTIGATION
# GEMSTAR MOR100, frame 150
#
# Investigates spatial evidence and recorded actor IDs.
# Does not assume actor 83185 is road or vehicle.

from pathlib import Path
from collections import Counter
import csv
import statistics
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
PROJECT = Path("E:/GEMSTAR_Project/gemstar")
TASK = ROOT / "tests" / "Task_13_Final_Research"

DATA = TASK / "02_CSV_Data"
GRAPHS = TASK / "01_Graphs"
CODE = TASK / "04_Code"
FINDINGS = TASK / "06_Research_Findings"

for folder in (DATA, GRAPHS, CODE, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

JOIN_FILE = DATA / "task13_3d_lidar_actor_join.csv"
GT_FILE = (
    ROOT / "tests" / "Task_11_Final_Research"
    / "02_CSV_Data" / "task11_groundtruth_objects.csv"
)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


rows = read_csv(JOIN_FILE)
gt_rows = read_csv(GT_FILE)

target = next(
    r for r in gt_rows
    if int(r["frame"]) == 150
    and int(r["object_id"]) == 76865
)

target_z = float(target["z_m"])
half_height = float(target["height_m"])

box_bottom = target_z - half_height
box_top = target_z + half_height

ACTOR = "83185"

actor_rows = [
    r for r in rows
    if r["unreal_actor_id_diagnostic"] == ACTOR
]

inside = [
    r for r in actor_rows
    if int(r["inside_gt_box"]) == 1
]

near = [
    r for r in actor_rows
    if int(r["within_050m"]) == 1
]

other = [
    r for r in rows
    if r["unreal_actor_id_diagnostic"] != ACTOR
]


def heights(items):
    return [
        float(r["world_z_m"]) for r in items
    ]


print("\n===== TASK 13.3E - ACTOR 83185 =====")
print("Total LiDAR returns:", len(rows))
print("Actor 83185 total:", len(actor_rows))
print("Actor 83185 inside GT box:", len(inside))
print("Actor 83185 within 0.50 m:", len(near))

print("\nGT box Z interval:")
print(f"Bottom: {box_bottom:.4f} m")
print(f"Top:    {box_top:.4f} m")

for name, group in [
    ("All actor 83185", actor_rows),
    ("Inside GT box", inside),
    ("Within 0.50 m", near),
    ("Other actors", other),
]:
    zz = heights(group)

    if zz:
        print(
            f"{name}: count={len(zz)}, "
            f"minZ={min(zz):.4f}, "
            f"medianZ={statistics.median(zz):.4f}, "
            f"maxZ={max(zz):.4f}"
        )

# --------------------------------------------------
# Figure 1: Elevation distributions
# --------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

if heights(inside):
    axes[0].hist(heights(inside), bins=25)
axes[0].axvline(box_bottom, linestyle="--",
                label="GT box bottom")
axes[0].axvline(box_top, linestyle=":",
                label="GT box top")
axes[0].set_xlabel("OSI world Z (m)")
axes[0].set_ylabel("LiDAR return count")
axes[0].set_title("Actor 83185: Inside GT Box")
axes[0].legend()

if heights(actor_rows):
    axes[1].hist(heights(actor_rows), bins=35,
                 alpha=0.7, label="Actor 83185")
if heights(other):
    axes[1].hist(heights(other), bins=35,
                 alpha=0.5, label="Other actor IDs")
axes[1].set_xlabel("OSI world Z (m)")
axes[1].set_ylabel("LiDAR return count")
axes[1].set_title("Height Distributions by Actor")
axes[1].legend()

fig.suptitle("Task 13.3E - LiDAR Actor Height Investigation")
fig.tight_layout()

height_plot = GRAPHS / "task13_3e_actor_height_analysis.png"
fig.savefig(height_plot, dpi=250)
plt.close(fig)

# --------------------------------------------------
# Figure 2: Spatial distribution
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 8))

if other:
    ax.scatter(
        [float(r["world_x_m"]) for r in other],
        [float(r["world_y_m"]) for r in other],
        s=5, alpha=0.45, label="Other actors"
    )

if actor_rows:
    ax.scatter(
        [float(r["world_x_m"]) for r in actor_rows],
        [float(r["world_y_m"]) for r in actor_rows],
        s=8, alpha=0.5, label="Actor 83185"
    )

if inside:
    ax.scatter(
        [float(r["world_x_m"]) for r in inside],
        [float(r["world_y_m"]) for r in inside],
        s=15, label="Actor 83185 inside GT box"
    )

center_x = float(target["x_m"])
center_y = float(target["y_m"])
ex = float(target["length_m"])
ey = float(target["width_m"])

from matplotlib.patches import Rectangle

rect = Rectangle(
    (center_x - ex, center_y - ey),
    2 * ex, 2 * ey,
    fill=False, linewidth=2,
    label="Target GT world-AABB proxy"
)
ax.add_patch(rect)

ax.set_aspect("equal", adjustable="box")
ax.set_xlabel("OSI world X (m)")
ax.set_ylabel("OSI world Y (m)")
ax.set_title("Actor 83185 - Spatial Distribution")
ax.grid(True)
ax.legend()

spatial_plot = GRAPHS / "task13_3e_actor_spatial_map.png"
fig.tight_layout()
fig.savefig(spatial_plot, dpi=250)
plt.close(fig)

# --------------------------------------------------
# Search existing textual logs for actor ID.
# --------------------------------------------------

log_matches = []

possible_log_dirs = [
    PROJECT / "Saved" / "Logs",
    ROOT / "logs",
]

for folder in possible_log_dirs:
    if not folder.exists():
        continue

    for file in folder.rglob("*.log"):
        try:
            with file.open(
                "r", encoding="utf-8", errors="replace"
            ) as f:
                for line_no, line in enumerate(f, 1):
                    if ACTOR in line:
                        log_matches.append({
                            "file": str(file),
                            "line": line_no,
                            "text": line.strip()[:500]
                        })
        except OSError:
            pass

log_file = DATA / "task13_3e_actor_log_matches.csv"

with log_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["file", "line", "text"]
    )
    writer.writeheader()
    writer.writerows(log_matches)

# --------------------------------------------------
# Save numerical summary
# --------------------------------------------------

summary = []

for name, group in [
    ("all_actor_83185", actor_rows),
    ("inside_gt_box", inside),
    ("within_050m", near),
    ("other_actors", other),
]:
    zz = heights(group)
    summary.append({
        "region": name,
        "count": len(group),
        "min_z_m": min(zz) if zz else "",
        "median_z_m": statistics.median(zz) if zz else "",
        "max_z_m": max(zz) if zz else "",
    })

summary_file = DATA / "task13_3e_height_summary.csv"

with summary_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summary[0])
    )
    writer.writeheader()
    writer.writerows(summary)

findings = [
    "TASK 13.3E - ACTOR 83185 INVESTIGATION",
    "",
    f"Actor 83185 returns: {len(actor_rows)}",
    f"Inside GT box: {len(inside)}",
    f"Within 0.50 m: {len(near)}",
    f"Matching log lines: {len(log_matches)}",
    "",
    f"GT AABB bottom Z: {box_bottom:.6f} m",
    f"GT AABB top Z: {box_top:.6f} m",
    "",
    "IMPORTANT:",
    "The GT box is an approximate world-AABB proxy.",
    "Actor 83185 has not yet been semantically identified.",
    "Spatial overlap alone does not prove a vehicle hit.",
    "The identity mapping to OSI GT remains unverified.",
]

finding_file = (
    FINDINGS / "task13_3e_actor_investigation_findings.txt"
)
finding_file.write_text(
    "\n".join(findings) + "\n", encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\nMatching GEMSTAR log lines:", len(log_matches))
print("Saved:", height_plot)
print("Saved:", spatial_plot)
print("Saved:", summary_file)
print("Saved:", log_file)
print("TASK 13.3E COMPLETED")
