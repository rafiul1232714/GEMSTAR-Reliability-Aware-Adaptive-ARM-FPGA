from pathlib import Path
from statistics import median
import struct
import csv
import math

from osi3 import osi_sensorview_pb2

BASE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T155916Z_sv_380_X_2393_GEMSTARADAR.osi"
)

MOVED = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T161227Z_sv_380_X_2168_GEMSTARADAR.osi"
)

CSV = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research\02_CSV_Data"
    r"\task23_07aj_all_rays_comparison.csv"
)

C = 299792458.0

def extract(path):
    data = {}
    frames = 0

    with path.open("rb") as file:
        while True:
            header = file.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete header")

            length = struct.unpack("<I", header)[0]
            payload = file.read(length)

            if len(payload) != length:
                raise ValueError("Truncated OSI message")

            msg = osi_sensorview_pb2.SensorView()
            msg.ParseFromString(payload)
            frames += 1

            if len(msg.radar_sensor_view) != 1:
                raise ValueError("Expected exactly one Radar view")

            radar = msg.radar_sensor_view[0]

            for i, reflection in enumerate(radar.reflection):
                distance = C * reflection.time_of_flight / 2

                if math.isfinite(distance) and distance > 0:
                    data.setdefault(i, []).append(distance)

    return frames, {
        ray: median(values)
        for ray, values in data.items()
    }

frames_a, a = extract(BASE)
frames_b, b = extract(MOVED)

all_rays = sorted(set(a) | set(b))
rows = []
changed = []

for ray in all_rays:
    before = a.get(ray)
    after = b.get(ray)

    delta = (
        after - before
        if before is not None and after is not None
        else None
    )

    if delta is None:
        status = "RETURN_ADDED_OR_LOST"
        changed.append(ray)
    elif abs(delta) > 0.01:
        status = "CHANGED"
        changed.append(ray)
    else:
        status = "UNCHANGED"

    rows.append({
        "RayIndex": ray,
        "BaselineRange_m": before,
        "MovedRange_m": after,
        "Delta_m": delta,
        "Status": status
    })

CSV.parent.mkdir(parents=True, exist_ok=True)

with CSV.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 23.7AJ — ALL-RAY COMPARISON ===")
print("Baseline frames:", frames_a)
print("Moved frames:", frames_b)
print("Rays with positive returns in either recording:", len(all_rays))
print("Rays changed by more than 1 cm or gained/lost:", len(changed))
print("Changed ray indices:", changed)

print("\nLargest range changes:")

numeric = [
    row for row in rows
    if row["Delta_m"] is not None
]

for row in sorted(
    numeric,
    key=lambda x: abs(x["Delta_m"]),
    reverse=True
)[:10]:
    print(
        f"Ray {row['RayIndex']}: "
        f"before={row['BaselineRange_m']:.4f} m, "
        f"after={row['MovedRange_m']:.4f} m, "
        f"delta={row['Delta_m']:.4f} m"
    )

print("\nCSV saved:", CSV)
print("STATUS: ALL_RAYS_COMPARED")
