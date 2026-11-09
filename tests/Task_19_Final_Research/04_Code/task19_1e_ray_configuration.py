import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

target_frame = 150

with source.open("rb") as f:
    for frame in range(target_frame + 1):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Missing OSI frame header")

        length = struct.unpack("<I", header)[0]

        if frame == target_frame:
            payload = f.read(length)
            if len(payload) != length:
                raise RuntimeError("Truncated OSI frame")

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)
        else:
            f.seek(length, 1)

lidar = sv.lidar_sensor_view[0]
cfg = lidar.view_configuration

print("\n=== TASK 19.1E RAY CONFIGURATION ===")
print("Frame:", target_frame)
print("Reflections:", len(lidar.reflection))

print("\nPopulated configuration fields:")
for field, value in cfg.ListFields():
    if field.is_repeated:
        print(field.name, ": count =", len(value))
    elif field.message_type:
        print(field.name, ": message present")
    else:
        print(field.name, ":", value)

print("\nAvailable protobuf fields:")
for field in cfg.DESCRIPTOR.fields:
    print(field.name)

directions = getattr(cfg, "directions", None)
timings = getattr(cfg, "timings", None)

print("\nDirections count:",
      len(directions) if directions is not None else "NOT DEFINED")
print("Timings count:",
      len(timings) if timings is not None else "NOT DEFINED")

if directions is not None and len(directions):
    print("\nFirst 5 directions:")
    for d in list(directions)[:5]:
        print(d)

if timings is not None and len(timings):
    print("\nFirst 5 timings:")
    for t in list(timings)[:5]:
        print(t)

print("\n=== TASK 19.1E COMPLETE ===")
