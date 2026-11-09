from pathlib import Path
import sys
import struct
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")

FILE = OUTPUT / (
    "20261103T152603Z_sv_380_X_1534_GEMSTARADAR.osi"
)

# Use the installed OSI3 protobuf package.
from osi3 import osi_sensorview_pb2

if not FILE.exists():
    raise FileNotFoundError(FILE)

print("\n=== TASK 23.7U - RADAR REFLECTION INSPECTION ===")

total_frames = 0
total_views = 0
total_reflections = 0

sample_reflection = None
sample_sensor = None

# Inspect a few distributed frames, then count all frames.
sample_frames = {1, 10, 100, 500, 1000, 1500}

with FILE.open("rb") as f:
    while True:
        header = f.read(4)
        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise ValueError("Incomplete payload")

        msg = osi_sensorview_pb2.SensorView()
        msg.ParseFromString(payload)

        total_frames += 1

        for sensor in msg.radar_sensor_view:
            total_views += 1
            total_reflections += len(sensor.reflection)

            if sample_sensor is None:
                sample_sensor = sensor

            if total_frames in sample_frames:
                print(
                    f"Frame {total_frames}: "
                    f"{len(sensor.reflection)} reflection entries"
                )

                if sensor.reflection:
                    print(
                        "First reflection:",
                        str(sensor.reflection[0])[:600]
                    )

            if sample_reflection is None and sensor.reflection:
                sample_reflection = sensor.reflection[0]

print("\n=== TOTALS ===")
print("Frames:", total_frames)
print("Radar views:", total_views)
print("Reflection entries:", total_reflections)

print("\n=== RADAR SENSOR FIELDS ===")

if sample_sensor is not None:
    for field in sample_sensor.DESCRIPTOR.fields:
        print(field.name)

print("\n=== REFLECTION FIELDS ===")

if sample_reflection is not None:
    for field in sample_reflection.DESCRIPTOR.fields:
        print(field.name)

print("\n=== TASK 23.7U INSPECTION COMPLETE ===")
