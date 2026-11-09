
# TASK 13.3U - TARGET LIDAR FIELD-OF-VIEW CHECK
# GEMSTAR MOR100, frame 150
#
# Checks whether GT target center and GT AABB corners
# fall within the LiDAR's nominal angular coverage.
#
# This is a geometric test, NOT an occlusion test.
# The origin correction is transferred from another run
# and is therefore provisional.

from pathlib import Path
import csv
import math
import shutil

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
T11 = ROOT / "tests" / "Task_11_Final_Research"
T13 = ROOT / "tests" / "Task_13_Final_Research"

DATA = T13 / "02_CSV_Data"
FIND = T13 / "06_Research_Findings"
CODE = T13 / "04_Code"

for folder in (DATA, FIND, CODE):
    folder.mkdir(parents=True, exist_ok=True)

FRAME = 150
EGO_ID = 76895
TARGET_ID = 76865

# LiDAR configuration, metres/degrees
MOUNT_X = 2.60
MOUNT_Y = 0.00
MOUNT_Z = 0.70

HFOV_DEG = 90.0
VFOV_DEG = 20.0

# New diagnostic run: world-axis actor-to-bounds offset
# converted to OSI metres.
# This is a hypothesis for frame 150, not a verified
# transform at this frame.
OFFSET_WORLD = (0.15738, -0.07349, 0.82620)

GT_FILE = (
    T11 / "02_CSV_Data" /
    "task11_groundtruth_objects.csv"
)

with GT_FILE.open(
    newline="", encoding="utf-8-sig"
) as f:
    rows = list(csv.DictReader(f))


def get_vehicle(object_id):
    matches = [
        row for row in rows
        if int(row["frame"]) == FRAME
        and int(row["object_id"]) == object_id
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one GT row for {object_id}"
        )
    return matches[0]


ego = get_vehicle(EGO_ID)
target = get_vehicle(TARGET_ID)

ego_gt = (
    float(ego["x_m"]),
    float(ego["y_m"]),
    float(ego["z_m"])
)

target_gt = (
    float(target["x_m"]),
    float(target["y_m"]),
    float(target["z_m"])
)

yaw = float(ego["yaw_rad"])
c = math.cos(yaw)
s = math.sin(yaw)

# Hypothetical actor origin based on the diagnostic offset.
actor_world = tuple(
    ego_gt[i] - OFFSET_WORLD[i]
    for i in range(3)
)

# Configured sensor mounting offsets are in Unreal
# coordinates; OSI reverses the Y direction.
#
# Zero mounting rotation.
mount_osi = (MOUNT_X, -MOUNT_Y, MOUNT_Z)

# Rotate the mount offset with ego yaw.
mount_world = (
    c * mount_osi[0] - s * mount_osi[1],
    s * mount_osi[0] + c * mount_osi[1],
    mount_osi[2]
)

lidar_world = tuple(
    actor_world[i] + mount_world[i]
    for i in range(3)
)


def sensor_angles(point):
    dx = point[0] - lidar_world[0]
    dy = point[1] - lidar_world[1]
    dz = point[2] - lidar_world[2]

    # Inverse ego rotation.
    forward = c * dx + s * dy
    lateral = -s * dx + c * dy

    # These use OSI lateral sign.
    azimuth = math.degrees(math.atan2(lateral, forward))
    elevation = math.degrees(
        math.atan2(dz, math.hypot(forward, lateral))
    )

    distance = math.sqrt(dx*dx + dy*dy + dz*dz)

    in_fov = (
        forward > 0
        and abs(azimuth) <= HFOV_DEG / 2
        and abs(elevation) <= VFOV_DEG / 2
    )

    return {
        "forward_m": forward,
        "lateral_m": lateral,
        "vertical_m": dz,
        "range_m": distance,
        "azimuth_deg": azimuth,
        "elevation_deg": elevation,
        "inside_nominal_fov": int(in_fov)
    }


# Interpret exported GT dimension fields as world-axis
# half-extents, based on inspected GetActorBounds() code.
extent = (
    float(target["length_m"]),
    float(target["width_m"]),
    float(target["height_m"])
)

points = [("center", target_gt)]

corner_id = 0

for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1):
            corner_id += 1
            point = (
                target_gt[0] + sx*extent[0],
                target_gt[1] + sy*extent[1],
                target_gt[2] + sz*extent[2]
            )
            points.append((f"corner_{corner_id}", point))

results = []

for name, point in points:
    result = sensor_angles(point)

    results.append({
        "point": name,
        "world_x_m": point[0],
        "world_y_m": point[1],
        "world_z_m": point[2],
        **result
    })

output_file = (
    DATA / "task13_3u_target_lidar_fov.csv"
)

with output_file.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0])
    )
    writer.writeheader()
    writer.writerows(results)

center = results[0]
corners_in_fov = sum(
    row["inside_nominal_fov"]
    for row in results[1:]
)

print("\n===== TASK 13.3U - LIDAR VISIBILITY =====")

print("Frame:", FRAME)
print("Target GT ID:", TARGET_ID)

print("\nProvisional LiDAR world origin:")
print(
    f"X={lidar_world[0]:.4f}, "
    f"Y={lidar_world[1]:.4f}, "
    f"Z={lidar_world[2]:.4f} m"
)

print("\nTarget center in LiDAR frame:")
print(f"Forward: {center['forward_m']:.4f} m")
print(f"Lateral: {center['lateral_m']:.4f} m")
print(f"Vertical: {center['vertical_m']:.4f} m")
print(f"Distance: {center['range_m']:.4f} m")

print("\nTarget center angular position:")
print(f"Azimuth: {center['azimuth_deg']:.3f} deg")
print(f"Elevation: {center['elevation_deg']:.3f} deg")

print("\nConfigured nominal field of view:")
print(f"Horizontal: +/-{HFOV_DEG/2:.1f} deg")
print(f"Vertical: +/-{VFOV_DEG/2:.1f} deg")

print(
    "Target center inside nominal FOV:",
    bool(center["inside_nominal_fov"])
)

print(
    "GT bounding corners inside nominal FOV:",
    f"{corners_in_fov}/8"
)

finding_file = (
    FIND / "task13_3u_lidar_visibility_findings.txt"
)

finding_file.write_text(
    "\n".join([
        "TASK 13.3U - TARGET LIDAR FOV",
        "",
        f"Frame: {FRAME}",
        f"Target GT ID: {TARGET_ID}",
        f"Center distance: {center['range_m']:.6f} m",
        f"Center azimuth: {center['azimuth_deg']:.6f} deg",
        f"Center elevation: {center['elevation_deg']:.6f} deg",
        f"Center inside nominal FOV: "
        f"{bool(center['inside_nominal_fov'])}",
        f"Bounding corners inside FOV: {corners_in_fov}/8",
        "",
        "LIMITATIONS:",
        "Actor offset transferred from another run.",
        "Only the target AABB center and corners are tested.",
        "Corner counts do not establish total visible area.",
        "Visibility/occlusion has not been verified.",
        "The sensor's complete pose is not independently logged.",
        "Angular coverage is not proof of a sensor reflection.",
        "No vehicle association is claimed."
    ]) + "\n",
    encoding="utf-8"
)

shutil.copy2(
    Path(__file__), CODE / Path(__file__).name
)

print("\nSaved:", output_file)
print("Saved:", finding_file)
print("TASK 13.3U COMPLETED")
