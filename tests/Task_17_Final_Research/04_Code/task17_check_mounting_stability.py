from pathlib import Path
import csv
import struct
import math

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

SUMMARY = BASE / "02_CSV_Data" / "task17_mounting_consistency.csv"
EVENTS = BASE / "02_CSV_Data" / "task17_mounting_change_events.csv"

SENSORS = ["Camera", "LiDAR", "Radar"]
TOLERANCE = 1e-6

baseline = {}
counts = {
    name: {
        "present": 0,
        "missing": 0,
        "mount_missing": 0,
        "changed": 0
    }
    for name in SENSORS
}

events = []

def extract_mount(config):
    mount = config.mounting_position
    p = mount.position
    o = mount.orientation

    return (
        p.x, p.y, p.z,
        o.roll, o.pitch, o.yaw
    )

with SOURCE.open("rb") as f:
    frame = 0

    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Invalid OSI header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(payload)

        groups = {
            "Camera": sv.camera_sensor_view,
            "LiDAR": sv.lidar_sensor_view,
            "Radar": sv.radar_sensor_view
        }

        for name, entries in groups.items():

            if len(entries) != 1:
                counts[name]["missing"] += 1

                events.append({
                    "Frame": frame,
                    "Sensor": name,
                    "Issue": "ENTRY_COUNT_NOT_ONE",
                    "Details": str(len(entries))
                })

                continue

            counts[name]["present"] += 1
            config = entries[0].view_configuration

            if not config.HasField("mounting_position"):
                counts[name]["mount_missing"] += 1

                events.append({
                    "Frame": frame,
                    "Sensor": name,
                    "Issue": "MOUNTING_POSITION_MISSING",
                    "Details": ""
                })

                continue

            current = extract_mount(config)

            if name not in baseline:
                baseline[name] = current
                continue

            max_difference = max(
                abs(a - b)
                for a, b in zip(current, baseline[name])
            )

            if max_difference > TOLERANCE:
                counts[name]["changed"] += 1

                events.append({
                    "Frame": frame,
                    "Sensor": name,
                    "Issue": "MOUNTING_CHANGED",
                    "Details": f"{max_difference:.9f}"
                })

        frame += 1

SUMMARY.parent.mkdir(parents=True, exist_ok=True)

summary_rows = []

for name in SENSORS:
    c = counts[name]

    summary_rows.append({
        "Sensor": name,
        "TotalFrames": frame,
        "PresentFrames": c["present"],
        "MissingOrMultipleEntries": c["missing"],
        "MissingMountConfigurations": c["mount_missing"],
        "ChangedMountConfigurations": c["changed"],
        "Stable": (
            c["present"] == frame
            and c["mount_missing"] == 0
            and c["changed"] == 0
        )
    })

with SUMMARY.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

with EVENTS.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["Frame", "Sensor", "Issue", "Details"]
    )
    writer.writeheader()
    writer.writerows(events)

print("\n=== TASK 17.5C MOUNTING STABILITY ===")
print("Frames checked:", frame)

for row in summary_rows:
    print(
        f'{row["Sensor"]}: '
        f'present={row["PresentFrames"]}, '
        f'missing_mount={row["MissingMountConfigurations"]}, '
        f'changed={row["ChangedMountConfigurations"]}, '
        f'stable={row["Stable"]}'
    )

print("Total events:", len(events))
print("Summary CSV saved:", SUMMARY.exists())
print("Events CSV saved:", EVENTS.exists())
