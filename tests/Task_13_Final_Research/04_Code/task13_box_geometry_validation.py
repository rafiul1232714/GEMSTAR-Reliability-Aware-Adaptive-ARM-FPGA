
# TASK 13.3W - GT BOX GEOMETRY VALIDATION
# MOR100 frame 150
#
# Compare two interpretations of dimension fields:
# A: recorded fields are world-AABB half-extents
# B: recorded fields are full dimensions
#
# Uses the SAME provisional sensor pose as Task 13.3V.
# This is a geometry sensitivity test, not a detection test.

from pathlib import Path
import csv
import math
import shutil
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

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
HFOV = math.radians(90)
VFOV = math.radians(20)

# Same values used in Task 13.3V:
MOUNT = (2.60, 0.0, 0.70)
OFFSET_OSI = (0.15738, -0.07349, 0.82620)


def load_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


gt = load_csv(
    T11 / "02_CSV_Data" /
    "task11_groundtruth_objects.csv"
)


def get_vehicle(oid):
    matches = [
        r for r in gt
        if int(float(r["frame"])) == FRAME
        and int(float(r["object_id"])) == oid
    ]
    if len(matches) != 1:
        raise RuntimeError("Missing or duplicate GT vehicle")
    return matches[0]


ego = get_vehicle(EGO_ID)
target = get_vehicle(TARGET_ID)

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

recorded_dims = (
    float(target["length_m"]),
    float(target["width_m"]),
    float(target["height_m"])
)

yaw = float(ego["yaw_rad"])
c = math.cos(yaw)
s = math.sin(yaw)

actor_origin = tuple(
    ego_center[i] - OFFSET_OSI[i]
    for i in range(3)
)

sensor = (
    actor_origin[0] + c*MOUNT[0] - s*MOUNT[1],
    actor_origin[1] + s*MOUNT[0] + c*MOUNT[1],
    actor_origin[2] + MOUNT[2]
)


def ray_hits_box(origin, direction, lo, hi):
    near = -float("inf")
    far = float("inf")

    for i in range(3):
        if abs(direction[i]) < 1e-12:
            if origin[i] < lo[i] or origin[i] > hi[i]:
                return False
            continue

        a = (lo[i] - origin[i]) / direction[i]
        b = (hi[i] - origin[i]) / direction[i]

        near = max(near, min(a, b))
        far = min(far, max(a, b))

        if far < near:
            return False

    return far >= max(near, 0.0)


# Recreate full nominal ray directions.
directions = []

for vi in range(NV):
    el = -VFOV/2 + vi*VFOV/(NV-1)

    for hi in range(NH):
        az = -HFOV/2 + hi*HFOV/(NH-1)

        # Unreal local -> OSI local
        dx = math.cos(el)*math.cos(az)
        dy = -math.cos(el)*math.sin(az)
        dz = math.sin(el)

        directions.append((
            c*dx - s*dy,
            s*dx + c*dy,
            dz
        ))


models = [
    ("A_exporter_half_extents", recorded_dims),
    ("B_standard_full_dimensions",
        tuple(v/2 for v in recorded_dims))
]

summaries = []
boxes = []

print("\n===== TASK 13.3W - BOX GEOMETRY =====")
print("Provisional LiDAR origin:", sensor)
print("Target GT center:", target_center)

for name, ext in models:

    lo = tuple(
        target_center[i]-ext[i] for i in range(3)
    )
    hi = tuple(
        target_center[i]+ext[i] for i in range(3)
    )

    inside_sensor = all(
        lo[i] <= sensor[i] <= hi[i]
        for i in range(3)
    )

    axis_clearance = tuple(
        max(lo[i]-sensor[i], 0, sensor[i]-hi[i])
        for i in range(3)
    )

    nearest = math.sqrt(
        sum(v*v for v in axis_clearance)
    )

    ray_count = sum(
        ray_hits_box(sensor, direction, lo, hi)
        for direction in directions
    )

    row = {
        "model": name,
        "box_span_x_m": 2*ext[0],
        "box_span_y_m": 2*ext[1],
        "box_span_z_m": 2*ext[2],
        "sensor_inside_box": int(inside_sensor),
        "sensor_to_box_distance_m": nearest,
        "intersecting_nominal_rays": ray_count,
        "intersection_percentage":
            100*ray_count/len(directions)
    }

    summaries.append(row)
    boxes.append((name, lo, hi))

    print("\n", name)
    for key, value in row.items():
        if key != "model":
            print(f"  {key}: {value}")

summary_csv = (
    DATA / "task13_3w_box_geometry_comparison.csv"
)

with summary_csv.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summaries[0])
    )
    writer.writeheader()
    writer.writerows(summaries)

# Top-view comparison
fig, ax = plt.subplots(figsize=(11, 8))

for name, lo, hi in boxes:
    ax.add_patch(Rectangle(
        (lo[0], lo[1]),
        hi[0]-lo[0],
        hi[1]-lo[1],
        fill=False,
        linewidth=2,
        label=name
    ))

ax.scatter(
    [sensor[0]], [sensor[1]],
    s=130, marker="*",
    label="Provisional LiDAR origin"
)

ax.scatter(
    [target_center[0]], [target_center[1]],
    s=90, marker="x",
    label="Target GT center"
)

ax.plot(
    [sensor[0], target_center[0]],
    [sensor[1], target_center[1]],
    linestyle="--"
)

ax.set_xlabel("OSI world X (m)")
ax.set_ylabel("OSI world Y (m)")
ax.set_title(
    "Task 13.3W - Target Box Interpretation"
)
ax.set_aspect("equal", adjustable="box")
ax.grid(True)
ax.legend()

fig.tight_layout()

graph = (
    GRAPHS / "task13_3w_box_geometry_comparison.png"
)

fig.savefig(graph, dpi=250)
plt.close(fig)

findings = [
    "TASK 13.3W - GT BOX GEOMETRY VALIDATION",
    "",
    "Model A follows the inspected GEMSTAR exporter:",
    "GetActorBounds(false, Origin, Extent)",
    "dimension fields = Extent * 0.01",
    "",
    "Model B tests standard full-dimension interpretation.",
    "It is not evidence that this exporter uses that format.",
    "",
    "Both models use a provisional cross-run sensor pose.",
    "The actor-to-bounds XY offset may vary with yaw.",
    "These comparisons do not establish target detection.",
    "",
    "RESULTS:",
]

for row in summaries:
    findings.append(str(row))

find_file = (
    FIND / "task13_3w_box_geometry_findings.txt"
)

find_file.write_text(
    "\n".join(findings)+"\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\nSaved:", summary_csv)
print("Saved:", graph)
print("Saved:", find_file)
print("TASK 13.3W COMPLETED")
