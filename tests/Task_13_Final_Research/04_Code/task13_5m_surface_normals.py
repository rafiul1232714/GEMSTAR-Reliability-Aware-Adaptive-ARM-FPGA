
# TASK 13.5M - LIDAR SURFACE NORMAL CLASSIFICATION
# MOR100 frame 150
# Reads original OSI data without modifying Task 11 files.

from pathlib import Path
from collections import defaultdict
import csv
import math
import statistics

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

OSI_FILE = (
    ROOT / "data" / "raw" / "fog_mor100" /
    "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUT = (
    ROOT / "tests" / "Task_13_Final_Research" /
    "02_CSV_Data"
)
OUT.mkdir(parents=True, exist_ok=True)

FRAME = 150
C = 299792458.0
NO_HIT = (1 << 64) - 1

# Read only frame 150.
with OSI_FILE.open("rb") as f:
    for frame in range(1, FRAME + 1):
        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = int.from_bytes(header, "little")
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

sv = SensorView()
sv.ParseFromString(payload)

rows = []
groups = defaultdict(list)

for sensor_index, lidar in enumerate(sv.lidar_sensor_view):
    for ray_index, reflection in enumerate(lidar.reflection):

        actor_id = reflection.object_id.value
        tof = reflection.time_of_flight

        if actor_id == NO_HIT or not math.isfinite(tof) or tof <= 0:
            continue

        rng = C * tof / 2.0

        if rng < 0.1:
            continue

        n = reflection.normal_to_surface
        magnitude = math.sqrt(
            n.x*n.x + n.y*n.y + n.z*n.z
        )

        if magnitude < 1e-8:
            continue

        nx = n.x / magnitude
        ny = n.y / magnitude
        nz = n.z / magnitude

        # Absolute Z measures how close the normal is
        # to vertical, regardless of its direction.
        abs_nz = abs(nz)

        # Exploratory surface-orientation categories.
        if abs_nz >= 0.9:
            category = "HORIZONTAL_LIKE"
        elif abs_nz <= 0.2:
            category = "VERTICAL_LIKE"
        else:
            category = "ANGLED_OR_MIXED"

        record = {
            "frame": FRAME,
            "sensor_index": sensor_index,
            "ray_index": ray_index,
            "actor_id": actor_id,
            "range_m": rng,
            "normal_x": nx,
            "normal_y": ny,
            "normal_z": nz,
            "abs_normal_z": abs_nz,
            "surface_category": category
        }

        rows.append(record)
        groups[str(actor_id)].append(record)

output = OUT / "task13_5m_surface_normals_frame150.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0])
    )
    writer.writeheader()
    writer.writerows(rows)

print("\n===== TASK 13.5M - SURFACE NORMALS =====")
print("Frame:", FRAME)
print("Valid reflections:", len(rows))

for actor, points in sorted(
    groups.items(),
    key=lambda item: -len(item[1])
):
    values = [p["normal_z"] for p in points]

    horizontal = sum(
        p["surface_category"] == "HORIZONTAL_LIKE"
        for p in points
    )

    vertical = sum(
        p["surface_category"] == "VERTICAL_LIKE"
        for p in points
    )

    angled = len(points) - horizontal - vertical

    print(f"\nActor {actor}")
    print("  Reflections:", len(points))
    print("  Median normal Z:", round(statistics.median(values), 6))
    print("  Horizontal-like:", horizontal)
    print("  Vertical-like:", vertical)
    print("  Angled/mixed:", angled)

print("\nSaved:", output)
print("TASK 13.5M COMPLETED")
