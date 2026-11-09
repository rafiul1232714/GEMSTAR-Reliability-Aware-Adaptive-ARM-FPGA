
# TASK 13.3D - LiDAR Actor Identity Diagnostic
# GEMSTAR MOR100, frame 150
#
# Tests whether LiDAR points near the target GT box
# are dominated by particular Unreal actor IDs.
#
# NOTE: Unreal actor IDs are NOT assumed to equal
# OSI Ground Truth vehicle IDs.

from pathlib import Path
from collections import Counter
import csv
import shutil

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
T11 = ROOT / "tests" / "Task_11_Final_Research"
T13 = ROOT / "tests" / "Task_13_Final_Research"

DATA = T13 / "02_CSV_Data"
GRAPHS = T13 / "01_Graphs"
CODE = T13 / "04_Code"
FINDINGS = T13 / "06_Research_Findings"

for folder in (DATA, GRAPHS, CODE, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

original_file = (
    T11 / "02_CSV_Data" /
    "task11_lidar_frame150_geometry.csv"
)

candidate_file = (
    DATA / "task13_3c_lidar_box_candidates.csv"
)

def load_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

original = load_csv(original_file)
candidates = load_csv(candidate_file)

def key(row):
    return (
        int(float(row["frame"])),
        int(float(row["ray_index"]))
    )

original_by_key = {}

for row in original:
    k = key(row)
    if k in original_by_key:
        raise ValueError(f"Duplicate original ray: {k}")
    original_by_key[k] = row

joined = []

for row in candidates:
    k = key(row)
    old = original_by_key.get(k)

    if old is None:
        raise ValueError(f"No original LiDAR match: {k}")

    actor_id = old.get("object_id_diagnostic", "").strip()

    if not actor_id:
        actor_id = "MISSING"

    distance = float(row["distance_to_box_m"])

    joined.append({
        "frame": k[0],
        "ray_index": k[1],
        "unreal_actor_id_diagnostic": actor_id,
        "distance_to_gt_box_m": distance,
        "inside_gt_box": int(float(row["inside_gt_box"])),
        "within_025m": int(distance <= 0.25),
        "within_050m": int(distance <= 0.50),
        "within_100m": int(distance <= 1.00),
        "world_x_m": float(row["world_x_m"]),
        "world_y_m": float(row["world_y_m"]),
        "world_z_m": float(row["world_z_m"])
    })

assert joined, "No LiDAR candidates found."

# Save every joined measurement.
joined_file = DATA / "task13_3d_lidar_actor_join.csv"

with joined_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(joined[0]))
    writer.writeheader()
    writer.writerows(joined)

# Compare actor distributions in different regions.
regions = {
    "all_points": joined,
    "inside_box": [
        r for r in joined if r["inside_gt_box"]
    ],
    "within_025m": [
        r for r in joined if r["within_025m"]
    ],
    "within_050m": [
        r for r in joined if r["within_050m"]
    ],
    "within_100m": [
        r for r in joined if r["within_100m"]
    ]
}

summary = []

print("\n===== TASK 13.3D - LIDAR ACTOR ANALYSIS =====")

for region, rows in regions.items():
    counts = Counter(
        r["unreal_actor_id_diagnostic"]
        for r in rows
    )

    print(f"\n{region}: {len(rows)} measurements")

    for actor_id, count in counts.most_common(10):
        fraction = count / len(rows) if rows else 0.0
        print(
            f"  Actor {actor_id:>12s}: "
            f"{count:4d} ({fraction:.1%})"
        )

    for actor_id, count in counts.items():
        summary.append({
            "region": region,
            "actor_id_diagnostic": actor_id,
            "measurement_count": count,
            "region_total": len(rows),
            "fraction_of_region": (
                count / len(rows) if rows else 0
            )
        })

summary_file = DATA / "task13_3d_actor_distribution.csv"

with summary_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "region",
            "actor_id_diagnostic",
            "measurement_count",
            "region_total",
            "fraction_of_region"
        ]
    )
    writer.writeheader()
    writer.writerows(summary)

# Generate an evidence chart for the inside-box region.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

inside_counts = Counter(
    r["unreal_actor_id_diagnostic"]
    for r in regions["inside_box"]
)

top = inside_counts.most_common(12)

fig, ax = plt.subplots(figsize=(11, 6))

if top:
    actor_labels = [str(a) for a, _ in top]
    actor_values = [count for _, count in top]

    ax.bar(actor_labels, actor_values)
    ax.set_xlabel("Unreal actor ID (diagnostic)")
    ax.set_ylabel("LiDAR points inside GT region")
    ax.tick_params(axis="x", rotation=45)
else:
    ax.text(
        0.5, 0.5, "No points inside GT box",
        ha="center", va="center",
        transform=ax.transAxes
    )

ax.set_title(
    "Task 13.3D - Actor IDs of Inside-Box LiDAR Points"
)

fig.tight_layout()

plot_file = GRAPHS / "task13_3d_inside_box_actor_ids.png"
fig.savefig(plot_file, dpi=250)
plt.close(fig)

findings = [
    "TASK 13.3D - LIDAR ACTOR IDENTITY DIAGNOSTIC",
    "",
    f"LiDAR measurements analyzed: {len(joined)}",
    f"Inside-box measurements: {len(regions['inside_box'])}",
    f"Within 0.25 m: {len(regions['within_025m'])}",
    "",
    "INTERPRETATION LIMITATIONS",
    "Actor IDs originate from the LiDAR simulation.",
    "They are not automatically OSI Ground Truth IDs.",
    "A scene mesh may belong to a larger shared actor.",
    "Inside-box overlap does not establish vehicle identity.",
    "Radar returns lack equivalent actor IDs in the",
    "inspected SimpleRadar.cpp reflection output.",
    "Further actor-to-GT mapping is required."
]

(FINDINGS / "task13_3d_lidar_actor_findings.txt").write_text(
    "\n".join(findings) + "\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\nSaved:", joined_file)
print("Saved:", summary_file)
print("Saved:", plot_file)
print("TASK 13.3D COMPLETED")
