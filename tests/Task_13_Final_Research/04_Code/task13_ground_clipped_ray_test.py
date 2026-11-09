
# TASK 13.3X - GROUND-CLIPPED RAY TEST
# GEMSTAR MOR100, frame 150
#
# Reuses Task 13.3V ray geometry.
# Compares original GT box with a box clipped at Z=0.30m.
#
# Does not claim confirmed occlusion or vehicle detection.

from pathlib import Path
from collections import Counter
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
FIND = T13 / "06_Research_Findings"
CODE = T13 / "04_Code"

for folder in (DATA, GRAPHS, FIND, CODE):
    folder.mkdir(parents=True, exist_ok=True)

FRAME = 150
EGO_ID = 76895
TARGET_ID = 76865

GROUND_CLIP_Z = 0.30
RANGE_TOLERANCE = 0.05

MOUNT = (2.60, 0.0, 0.70)
OFFSET_OSI = (0.15738, -0.07349, 0.82620)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


gt = read_csv(
    T11 / "02_CSV_Data" /
    "task11_groundtruth_objects.csv"
)

all_rays = read_csv(
    DATA / "task13_3v_all_lidar_rays.csv"
)

lidar = read_csv(
    T11 / "02_CSV_Data" /
    "task11_lidar_frame150_geometry.csv"
)


def vehicle(oid):
    matches = [
        r for r in gt
        if int(float(r["frame"])) == FRAME
        and int(float(r["object_id"])) == oid
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Unexpected GT rows for {oid}")
    return matches[0]


ego = vehicle(EGO_ID)
target = vehicle(TARGET_ID)

ego_pos = (
    float(ego["x_m"]),
    float(ego["y_m"]),
    float(ego["z_m"])
)

center = (
    float(target["x_m"]),
    float(target["y_m"]),
    float(target["z_m"])
)

extent = (
    float(target["length_m"]),
    float(target["width_m"]),
    float(target["height_m"])
)

yaw = float(ego["yaw_rad"])
c = math.cos(yaw)
s = math.sin(yaw)

actor_origin = tuple(
    ego_pos[i] - OFFSET_OSI[i]
    for i in range(3)
)

sensor_origin = (
    actor_origin[0] + c*MOUNT[0] - s*MOUNT[1],
    actor_origin[1] + s*MOUNT[0] + c*MOUNT[1],
    actor_origin[2] + MOUNT[2]
)

box_lo = tuple(
    center[i]-extent[i] for i in range(3)
)
box_hi = tuple(
    center[i]+extent[i] for i in range(3)
)

clipped_lo = (
    box_lo[0],
    box_lo[1],
    max(box_lo[2], GROUND_CLIP_Z)
)

if clipped_lo[2] >= box_hi[2]:
    raise RuntimeError("Clipping removed the entire box.")


def intersection(origin, direction, low, high):
    near = -math.inf
    far = math.inf

    for j in range(3):
        o = origin[j]
        d = direction[j]

        if abs(d) < 1e-12:
            if o < low[j] or o > high[j]:
                return None
            continue

        a = (low[j]-o)/d
        b = (high[j]-o)/d

        near = max(near, min(a, b))
        far = min(far, max(a, b))

        if far < near:
            return None

    if far < 0:
        return None

    return max(0.0, near), far


# Only actual valid reflections are included in this CSV.
measured = {
    int(float(r["ray_index"])): r
    for r in lidar
}

if len(measured) != len(lidar):
    raise RuntimeError("Duplicate ray indices in LiDAR data.")

results = []

for row in all_rays:

    ray = int(row["ray_index"])

    az = math.radians(
        float(row["azimuth_unreal_deg"])
    )
    el = math.radians(
        float(row["elevation_deg"])
    )

    # Unreal local -> OSI local.
    dx = math.cos(el)*math.cos(az)
    dy = -math.cos(el)*math.sin(az)
    dz = math.sin(el)

    direction = (
        c*dx - s*dy,
        s*dx + c*dy,
        dz
    )

    original = intersection(
        sensor_origin, direction,
        box_lo, box_hi
    )

    clipped = intersection(
        sensor_origin, direction,
        clipped_lo, box_hi
    )

    hit = measured.get(ray)

    rng = (
        float(hit["range_m"])
        if hit is not None else None
    )

    actor = (
        hit["object_id_diagnostic"]
        if hit is not None
        else "NO_RECORDED_HIT"
    )

    if clipped is None:
        relation = "NO_CLIPPED_INTERSECTION"
    elif rng is None:
        relation = "NO_RECORDED_HIT"
    elif rng < clipped[0]-RANGE_TOLERANCE:
        relation = "HIT_BEFORE_CLIPPED_BOX"
    elif rng <= clipped[1]+RANGE_TOLERANCE:
        relation = "HIT_AT_CLIPPED_BOX_RANGE"
    else:
        relation = "HIT_BEYOND_CLIPPED_BOX"

    results.append({
        "ray_index": ray,
        "vertical_index": int(row["vertical_index"]),
        "elevation_deg": float(row["elevation_deg"]),
        "actor_id": actor,
        "recorded_range_m": rng if rng is not None else "",
        "intersects_original": int(original is not None),
        "intersects_clipped": int(clipped is not None),
        "original_entry_m":
            original[0] if original else "",
        "clipped_entry_m":
            clipped[0] if clipped else "",
        "clipped_exit_m":
            clipped[1] if clipped else "",
        "range_relation": relation
    })


def count_if(condition):
    return sum(bool(condition(r)) for r in results)


original_count = count_if(
    lambda r: r["intersects_original"]
)
clipped_count = count_if(
    lambda r: r["intersects_clipped"]
)

clipped_rays = [
    r for r in results
    if r["intersects_clipped"]
]

clipped_hit_rays = [
    r for r in clipped_rays
    if r["actor_id"] != "NO_RECORDED_HIT"
]

actor_counts = Counter(
    r["actor_id"]
    for r in clipped_hit_rays
)

relation_counts = Counter(
    r["range_relation"]
    for r in clipped_rays
)

print("\n===== TASK 13.3X - GROUND-CLIPPED RAYS =====")

print("Original box minimum Z:", round(box_lo[2], 6))
print("Clipped box minimum Z:", GROUND_CLIP_Z)

print("\nNominal rays:", len(results))
print("Intersecting original box:", original_count)
print("Intersecting clipped box:", clipped_count)

print(
    "Clipped-box rays with recorded hits:",
    len(clipped_hit_rays)
)

print("\nActor distribution on clipped-box rays:")

for actor, count in actor_counts.most_common():
    print(f"  Actor {actor}: {count}")

print("\nRange relationships:")

for relation, count in relation_counts.most_common():
    print(f"  {relation}: {count}")

print("\nVertical-index distribution:")

vertical_counts = Counter(
    r["vertical_index"]
    for r in clipped_rays
)

for index, count in sorted(vertical_counts.items()):
    print(f"  Vertical index {index}: {count}")

# Save per-ray records.
out_file = DATA / "task13_3x_ground_clipped_rays.csv"

with out_file.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0])
    )
    writer.writeheader()
    writer.writerows(results)

# Save summary.
summary = [
    {"metric": "nominal_rays", "value": len(results)},
    {"metric": "original_intersections",
     "value": original_count},
    {"metric": "clipped_intersections",
     "value": clipped_count},
    {"metric": "clipped_with_recorded_hits",
     "value": len(clipped_hit_rays)},
    {"metric": "clipped_flat_actor_hits",
     "value": actor_counts.get("83185", 0)}
]

summary_file = DATA / "task13_3x_ground_clip_summary.csv"

with summary_file.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=["metric", "value"]
    )
    writer.writeheader()
    writer.writerows(summary)

# Figure: before/after angular coverage by elevation.
orig_el = Counter(
    r["vertical_index"]
    for r in results if r["intersects_original"]
)

clip_el = Counter(
    r["vertical_index"]
    for r in clipped_rays
)

fig, ax = plt.subplots(figsize=(11, 6))

indices = list(range(21))

ax.plot(
    indices,
    [orig_el.get(i, 0) for i in indices],
    marker="o",
    label="Original GT box"
)

ax.plot(
    indices,
    [clip_el.get(i, 0) for i in indices],
    marker="s",
    label="GT box clipped above 0.30m"
)

ax.set_xlabel("LiDAR vertical ray index")
ax.set_ylabel("Intersecting ray count")
ax.set_title("Task 13.3X - Ground Clip Sensitivity")
ax.grid(True)
ax.legend()

fig.tight_layout()

graph_file = GRAPHS / "task13_3x_ground_clip_comparison.png"
fig.savefig(graph_file, dpi=250)
plt.close(fig)

find_file = FIND / "task13_3x_ground_clip_findings.txt"

find_file.write_text(
    "\n".join([
        "TASK 13.3X - GROUND-CLIPPED RAY TEST",
        "",
        f"Original GT box bottom: {box_lo[2]:.6f} m",
        f"Clipped GT box bottom: {GROUND_CLIP_Z:.6f} m",
        f"Original intersections: {original_count}",
        f"Clipped intersections: {clipped_count}",
        f"Clipped rays with recorded hits: "
        f"{len(clipped_hit_rays)}",
        "",
        "Actor distribution:",
        *[f"{a}: {n}" for a, n in actor_counts.items()],
        "",
        "Range relationships:",
        *[f"{a}: {n}" for a, n in relation_counts.items()],
        "",
        "LIMITATIONS:",
        "Clipping at 0.30m is an exploratory threshold.",
        "The target box remains an approximate world AABB.",
        "Sensor pose is transferred from a different run.",
        "A ray intersecting the box is not a vehicle hit.",
        "A preceding reflection may indicate occlusion,",
        "but identity and timing are still unverified.",
        "No validated sensor fusion is claimed."
    ])+"\n",
    encoding="utf-8"
)

shutil.copy2(
    Path(__file__), CODE / Path(__file__).name
)

print("\nSaved:", out_file)
print("Saved:", summary_file)
print("Saved:", graph_file)
print("Saved:", find_file)
print("TASK 13.3X COMPLETED")
