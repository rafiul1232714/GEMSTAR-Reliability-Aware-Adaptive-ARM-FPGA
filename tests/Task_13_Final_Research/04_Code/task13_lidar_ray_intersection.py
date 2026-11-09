
# TASK 13.3V - LIDAR RAY / TARGET BOX INTERSECTION
# GEMSTAR MOR100, frame 150
#
# Geometrically traces the configured LiDAR rays
# against the approximate target Ground Truth AABB.
#
# IMPORTANT:
# - Uses a provisional sensor origin from Task 13.3U.
# - The recorded GT box is an approximate world AABB.
# - A ray-box intersection is NOT proof of visibility.
# - A measured hit may belong to an occluding actor.

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

NH = 251
NV = 21
HFOV = math.radians(90.0)
VFOV = math.radians(20.0)

# LiDAR mounting offset (Unreal cm -> OSI m).
MOUNT = (2.60, 0.0, 0.70)

# Cross-run offset, OSI world metres.
# This remains provisional for MOR100 frame 150.
ACTOR_TO_BOUNDS = (0.15738, -0.07349, 0.82620)

gt_path = T11 / "02_CSV_Data" / "task11_groundtruth_objects.csv"
lidar_path = T11 / "02_CSV_Data" / "task11_lidar_frame150_geometry.csv"


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


gt = read_csv(gt_path)
lidar = read_csv(lidar_path)


def vehicle(oid):
    matches = [
        r for r in gt
        if int(float(r["frame"])) == FRAME
        and int(float(r["object_id"])) == oid
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one GT row for {oid}")
    return matches[0]


ego = vehicle(EGO_ID)
target = vehicle(TARGET_ID)

ego_center = (
    float(ego["x_m"]),
    float(ego["y_m"]),
    float(ego["z_m"])
)

target_center = (
    float(target["x_m"]),
    float(target["y_m"]),
    float(target["z_m"])
)

extent = (
    float(target["length_m"]),
    float(target["width_m"]),
    float(target["height_m"])
)

box_min = tuple(c - e for c, e in zip(target_center, extent))
box_max = tuple(c + e for c, e in zip(target_center, extent))

yaw = float(ego["yaw_rad"])
c = math.cos(yaw)
s = math.sin(yaw)

actor_origin = tuple(
    ego_center[i] - ACTOR_TO_BOUNDS[i]
    for i in range(3)
)

sensor_origin = (
    actor_origin[0] + c * MOUNT[0] - s * MOUNT[1],
    actor_origin[1] + s * MOUNT[0] + c * MOUNT[1],
    actor_origin[2] + MOUNT[2]
)


def ray_box_intersection(origin, direction):
    """Return positive ray entry/exit distances or None."""
    near = -math.inf
    far = math.inf

    for axis in range(3):
        o = origin[axis]
        d = direction[axis]
        lo = box_min[axis]
        hi = box_max[axis]

        if abs(d) < 1e-12:
            if o < lo or o > hi:
                return None
            continue

        t1 = (lo - o) / d
        t2 = (hi - o) / d

        if t1 > t2:
            t1, t2 = t2, t1

        near = max(near, t1)
        far = min(far, t2)

        if far < near:
            return None

    if far < 0:
        return None

    return max(near, 0.0), far


# Inspect recorded ray-index convention.
# Task 13.2A assumes zero-based indexing.
indices = [int(float(r["ray_index"])) for r in lidar]

if len(indices) != len(set(indices)):
    raise RuntimeError("Duplicate recorded LiDAR ray indices.")

if any(i < 0 or i >= NH * NV for i in indices):
    raise RuntimeError(
        "Recorded ray indices fall outside the expected "
        "zero-based grid. Verify ray indexing before proceeding."
    )

measured = {
    int(float(r["ray_index"])): r
    for r in lidar
}

intersections = []
all_rays = []

for vertical_index in range(NV):
    elevation = (
        -VFOV / 2
        + vertical_index * VFOV / (NV - 1)
    )

    for horizontal_index in range(NH):
        azimuth_unreal = (
            -HFOV / 2
            + horizontal_index * HFOV / (NH - 1)
        )

        ray_index = vertical_index * NH + horizontal_index

        # Unreal local ray:
        # +X forward, +Y for positive Unreal azimuth.
        #
        # OSI reverses Y, so local OSI Y is negative.
        dx_local = (
            math.cos(elevation) * math.cos(azimuth_unreal)
        )
        dy_local = (
            -math.cos(elevation) * math.sin(azimuth_unreal)
        )
        dz_local = math.sin(elevation)

        # Rotate with ego OSI yaw.
        direction = (
            c * dx_local - s * dy_local,
            s * dx_local + c * dy_local,
            dz_local
        )

        hit_box = ray_box_intersection(
            sensor_origin, direction
        )

        record = measured.get(ray_index)

        actor = (
            record.get("object_id_diagnostic", "").strip()
            if record else "NO_RECORDED_HIT"
        )

        measured_range = (
            float(record["range_m"])
            if record else None
        )

        ray_record = {
            "ray_index": ray_index,
            "horizontal_index": horizontal_index,
            "vertical_index": vertical_index,
            "azimuth_unreal_deg":
                math.degrees(azimuth_unreal),
            "elevation_deg": math.degrees(elevation),
            "intersects_target_box": int(hit_box is not None),
            "recorded_hit": int(record is not None),
            "recorded_actor_id": actor,
        }

        all_rays.append(ray_record)

        if hit_box is None:
            continue

        entry, exit_ = hit_box

        if measured_range is None:
            relation = "NO_RECORDED_HIT"
        elif measured_range < entry - 0.05:
            relation = "HIT_BEFORE_BOX"
        elif measured_range <= exit_ + 0.05:
            relation = "HIT_AT_BOX_RANGE"
        else:
            relation = "HIT_BEYOND_BOX"

        intersections.append({
            **ray_record,
            "box_entry_m": entry,
            "box_exit_m": exit_,
            "recorded_range_m":
                measured_range if measured_range is not None else "",
            "range_relation": relation
        })


print("\n===== TASK 13.3V - LIDAR RAY TEST =====")
print("Nominal total rays:", NH * NV)
print("Recorded valid hits:", len(measured))
print("Target GT ID:", TARGET_ID)
print(
    "Provisional LiDAR origin:",
    tuple(round(v, 4) for v in sensor_origin)
)

print("\nRays intersecting target GT AABB:", len(intersections))

with_hits = [
    r for r in intersections if r["recorded_hit"]
]

print("Intersecting rays with recorded hits:", len(with_hits))
print(
    "Intersecting rays without recorded hits:",
    len(intersections) - len(with_hits)
)

relations = Counter(r["range_relation"] for r in intersections)
actors = Counter(r["recorded_actor_id"] for r in with_hits)

print("\nRecorded range relationship to target box:")
for label, count in relations.most_common():
    print(f"  {label}: {count}")

print("\nActors hit by rays intersecting target box:")
for actor, count in actors.most_common():
    print(f"  Actor {actor}: {count}")

print("\nIndividual intersecting rays:")
for row in intersections[:30]:
    print(
        f"Ray {row['ray_index']:4d} | "
        f"az={row['azimuth_unreal_deg']:7.3f} | "
        f"el={row['elevation_deg']:6.3f} | "
        f"box_entry={row['box_entry_m']:.3f} m | "
        f"actor={row['recorded_actor_id']} | "
        f"{row['range_relation']}"
    )


def save_csv(path, records):
    if not records:
        return
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(records[0])
        )
        writer.writeheader()
        writer.writerows(records)


all_file = DATA / "task13_3v_all_lidar_rays.csv"
intersection_file = DATA / "task13_3v_target_ray_intersections.csv"

save_csv(all_file, all_rays)

# Ensure header exists even if zero intersections.
if intersections:
    save_csv(intersection_file, intersections)
else:
    intersection_file.write_text(
        "ray_index,intersects_target_box\n",
        encoding="utf-8"
    )

# Figure: actual scan-grid directions that intersect the box.
fig, ax = plt.subplots(figsize=(11, 7))

ax.scatter(
    [r["azimuth_unreal_deg"] for r in all_rays],
    [r["elevation_deg"] for r in all_rays],
    s=3, alpha=0.2,
    label="All nominal rays"
)

if intersections:
    ax.scatter(
        [r["azimuth_unreal_deg"] for r in intersections],
        [r["elevation_deg"] for r in intersections],
        s=35,
        label="Rays intersecting target AABB"
    )

ax.set_xlabel("Unreal ray azimuth (degrees)")
ax.set_ylabel("Ray elevation (degrees)")
ax.set_title(
    "Task 13.3V - LiDAR Scan Grid vs Target AABB"
)
ax.grid(True)
ax.legend()
fig.tight_layout()

graph = GRAPHS / "task13_3v_lidar_target_scan_grid.png"
fig.savefig(graph, dpi=250)
plt.close(fig)

finding = FIND / "task13_3v_ray_intersection_findings.txt"

finding.write_text(
    "\n".join([
        "TASK 13.3V - LIDAR RAY / GT BOX INTERSECTION",
        "",
        f"Total configured rays: {NH * NV}",
        f"Recorded valid hits: {len(measured)}",
        f"Rays intersecting target AABB: {len(intersections)}",
        f"Intersecting rays with recorded hits: {len(with_hits)}",
        "",
        "Range relationships:",
        *[f"{k}: {v}" for k, v in relations.items()],
        "",
        "Recorded actors:",
        *[f"{k}: {v}" for k, v in actors.items()],
        "",
        "LIMITATIONS:",
        "Cross-run actor-to-GT correction is provisional.",
        "GT bounding box is an approximate world AABB.",
        "Zero-based ray indexing is assumed.",
        "AABB intersection is not proof of vehicle visibility.",
        "Ray-range comparisons are not identity validation.",
        "No confirmed Camera-LiDAR-Radar association."
    ]) + "\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\nSaved:", all_file)
print("Saved:", intersection_file)
print("Saved:", graph)
print("Saved:", finding)
print("TASK 13.3V COMPLETED")
