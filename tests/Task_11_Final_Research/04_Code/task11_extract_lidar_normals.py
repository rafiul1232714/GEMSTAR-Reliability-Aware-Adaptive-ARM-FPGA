
from pathlib import Path
import csv
import math

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

FILE = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUT = (
    ROOT / "tests"
    / "Task_11_Final_Research"
    / "02_CSV_Data"
)

OUT.mkdir(parents=True, exist_ok=True)

TARGET_FRAME = 101
C = 299792458.0

with FILE.open("rb") as f:

    for frame in range(1, TARGET_FRAME + 1):

        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Invalid OSI header")

        size = int.from_bytes(header, "little")

        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI message")

sv = SensorView()
sv.ParseFromString(payload)

rows = []

for sensor_index, lidar in enumerate(sv.lidar_sensor_view):

    for ray_index, reflection in enumerate(lidar.reflection):

        tof = reflection.time_of_flight
        strength = reflection.signal_strength

        if not (
            math.isfinite(tof)
            and math.isfinite(strength)
            and tof > 0
            and strength > 0
        ):
            continue

        distance = C * tof / 2.0

        if distance < 0.1:
            continue

        normal = reflection.normal_to_surface

        nx = normal.x
        ny = normal.y
        nz = normal.z

        norm = math.sqrt(nx*nx + ny*ny + nz*nz)

        rows.append([
            TARGET_FRAME,
            sensor_index,
            ray_index,
            distance,
            strength,
            nx,
            ny,
            nz,
            norm
        ])

output = OUT / "task11_lidar_normals_frame101.csv"

with output.open("w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
        "frame",
        "sensor_index",
        "ray_index",
        "range_m",
        "signal_strength",
        "normal_x",
        "normal_y",
        "normal_z",
        "normal_magnitude"
    ])

    writer.writerows(rows)

print("TASK 11.5B - LIDAR NORMAL EXTRACTION")
print("Frame:", TARGET_FRAME)
print("Valid reflections:", len(rows))
print("Saved:", output)
print("TASK 11.5B COMPLETED")
