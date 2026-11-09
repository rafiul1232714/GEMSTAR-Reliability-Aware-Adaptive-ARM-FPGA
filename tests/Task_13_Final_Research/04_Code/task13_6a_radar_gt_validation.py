
# TASK 13.6A - RADAR vs GROUND TRUTH
# GEMSTAR MOR100, frame 150
# Exploratory geometry check; no confirmed object identity.

from pathlib import Path
import csv
import math
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
SOURCE = ROOT / "tests" / "Task_11_Final_Research" / "02_CSV_Data"
OUT = ROOT / "tests" / "Task_13_Final_Research" / "02_CSV_Data"
OUT.mkdir(parents=True, exist_ok=True)

FRAME = 150
EGO_ID = 76895
TARGET_ID = 76865

# Provisional cross-run actor-to-bounds world offset,
# expressed in OSI coordinates, metres.
OFFSET = (0.15738, -0.07349, 0.82620)
RADAR_MOUNT = (2.0, 0.0, 0.8)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


gt = read_csv(SOURCE / "task11_groundtruth_objects.csv")
radar = [
    r for r in read_csv(SOURCE / "task11_radar_measurements.csv")
    if int(r["frame"]) == FRAME
    and float(r["range_m"]) > 0.1
    and float(r["signal_strength"]) > 0
]


def vehicle(object_id):
    matches = [
        r for r in gt
        if int(r["frame"]) == FRAME
        and int(r["object_id"]) == object_id
    ]
    if len(matches) != 1:
        raise RuntimeError(f"GT object {object_id} not unique")
    return matches[0]


ego = vehicle(EGO_ID)
target = vehicle(TARGET_ID)

ego_center = tuple(float(ego[k]) for k in ("x_m", "y_m", "z_m"))
target_center = tuple(float(target[k]) for k in ("x_m", "y_m", "z_m"))
dimensions = tuple(
    float(target[k]) for k in ("length_m", "width_m", "height_m")
)

ego_origin = tuple(ego_center[i] - OFFSET[i] for i in range(3))
yaw = float(ego["yaw_rad"])
c, s = math.cos(yaw), math.sin(yaw)


def to_world(x, y, z):
    return (
        ego_origin[0] + c*x - s*y,
        ego_origin[1] + s*x + c*y,
        ego_origin[2] + z,
    )


def aabb_distance(point, half_extents):
    gaps = [
        max(abs(point[i] - target_center[i]) - half_extents[i], 0.0)
        for i in range(3)
    ]
    return math.sqrt(sum(g*g for g in gaps))


results = []

for r in radar:
    rng = float(r["range_m"])
    az = float(r["horizontal_angle_rad"])
    el = float(r["vertical_angle_rad"])

    # Radar local ray: Unreal +X forward.
    # Convert Unreal +Y to OSI -Y.
    x = RADAR_MOUNT[0] + rng*math.cos(el)*math.cos(az)
    y = RADAR_MOUNT[1] - rng*math.cos(el)*math.sin(az)
    z = RADAR_MOUNT[2] + rng*math.sin(el)

    point = to_world(x, y, z)

    # Model A: exporter uses GetActorBounds half-extents.
    dist_a = aabb_distance(point, dimensions)

    # Model B: interpret recorded fields as full dimensions.
    dist_b = aabb_distance(
        point, tuple(d/2 for d in dimensions)
    )

    results.append({
        "frame": FRAME,
        "ray_index": int(r["ray_index"]),
        "range_m": rng,
        "signal_strength": float(r["signal_strength"]),
        "world_x_m": point[0],
        "world_y_m": point[1],
        "world_z_m": point[2],
        "distance_model_a_m": dist_a,
        "distance_model_b_m": dist_b,
        "inside_model_a": int(dist_a <= 1e-9),
        "inside_model_b": int(dist_b <= 1e-9),
    })

output = OUT / "task13_6a_radar_gt_distances.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

print("\n===== TASK 13.6A - RADAR GT VALIDATION =====")
print("Frame:", FRAME)
print("Radar candidates:", len(results))
print("Target GT object:", TARGET_ID)
print("Provisional ego origin:", ego_origin)

for label, key, flag in [
    ("Model A - exporter half-extents", "distance_model_a_m", "inside_model_a"),
    ("Model B - full dimensions", "distance_model_b_m", "inside_model_b")
]:
    distances = [r[key] for r in results]
    print(f"\n{label}")
    print("Inside target box:", sum(r[flag] for r in results))
    print("Within 0.5 m:", sum(d <= 0.5 for d in distances))
    print("Within 1.0 m:", sum(d <= 1.0 for d in distances))
    print("Minimum distance:", f"{min(distances):.4f} m")
    print("Median distance:", f"{statistics.median(distances):.4f} m")

print("\nFive closest Radar candidates (Model B):")
for row in sorted(results, key=lambda r: r["distance_model_b_m"])[:5]:
    print(
        f"Ray {row['ray_index']}: "
        f"range={row['range_m']:.3f}m, "
        f"distance_A={row['distance_model_a_m']:.3f}m, "
        f"distance_B={row['distance_model_b_m']:.3f}m"
    )

print("\nSaved:", output)
print("TASK 13.6A COMPLETED")
