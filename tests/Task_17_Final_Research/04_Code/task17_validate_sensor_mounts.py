from pathlib import Path
import csv
import math
import struct

from osi3 import osi_sensorview_pb2

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

SOURCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\data\raw\fog_mor100"
    r"\20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUT = BASE / "02_CSV_Data" / "task17_sensor_mounting_positions.csv"

with SOURCE.open("rb") as f:
    header = f.read(4)

    if len(header) != 4:
        raise RuntimeError("Missing OSI message header")

    size = struct.unpack("<I", header)[0]
    payload = f.read(size)

    if len(payload) != size:
        raise RuntimeError("Incomplete OSI message")

sv = osi_sensorview_pb2.SensorView()
sv.ParseFromString(payload)

groups = [
    ("Camera", sv.camera_sensor_view),
    ("LiDAR", sv.lidar_sensor_view),
    ("Radar", sv.radar_sensor_view),
]

rows = []

for name, entries in groups:

    if not entries:
        print(name, "MISSING")
        continue

    sensor = entries[0]
    config = sensor.view_configuration

    if not config.HasField("mounting_position"):
        print(name, "MOUNTING POSITION NOT POPULATED")
        continue

    mount = config.mounting_position
    p = mount.position
    o = mount.orientation

    rows.append({
        "Sensor": name,
        "X_m": p.x,
        "Y_m": p.y,
        "Z_m": p.z,
        "Roll_rad": o.roll,
        "Pitch_rad": o.pitch,
        "Yaw_rad": o.yaw,
        "Roll_deg": math.degrees(o.roll),
        "Pitch_deg": math.degrees(o.pitch),
        "Yaw_deg": math.degrees(o.yaw),
    })

OUT.parent.mkdir(parents=True, exist_ok=True)

if rows:
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

print("\n=== TASK 17.5A SENSOR MOUNTING CONFIGURATION ===")

for row in rows:
    print(
        f'{row["Sensor"]}: '
        f'X={row["X_m"]:.3f} m, '
        f'Y={row["Y_m"]:.3f} m, '
        f'Z={row["Z_m"]:.3f} m, '
        f'Roll={row["Roll_deg"]:.2f} deg, '
        f'Pitch={row["Pitch_deg"]:.2f} deg, '
        f'Yaw={row["Yaw_deg"]:.2f} deg'
    )

print("\n=== RELATIVE SENSOR DISTANCES ===")

for i in range(len(rows)):
    for j in range(i + 1, len(rows)):
        a, b = rows[i], rows[j]

        dx = a["X_m"] - b["X_m"]
        dy = a["Y_m"] - b["Y_m"]
        dz = a["Z_m"] - b["Z_m"]

        distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        print(
            f'{a["Sensor"]} <-> {b["Sensor"]}: '
            f'{distance:.4f} m'
        )

print("\nCSV saved:", OUT.exists())
