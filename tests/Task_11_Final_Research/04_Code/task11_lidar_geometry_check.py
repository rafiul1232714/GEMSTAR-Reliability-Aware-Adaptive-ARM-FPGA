
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

FILE = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

# Inspect frame 101
TARGET_FRAME = 101

with FILE.open("rb") as f:

    for frame in range(1, TARGET_FRAME + 1):

        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Recording ended unexpectedly")

        size = int.from_bytes(header, "little")
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI record")

    sv = SensorView()
    sv.ParseFromString(payload)

print("===================================")
print("TASK 11.3C - LIDAR GEOMETRY CHECK")
print("===================================")

print("Frame:", TARGET_FRAME)
print("LiDAR streams:", len(sv.lidar_sensor_view))

for i, lidar in enumerate(sv.lidar_sensor_view):

    cfg = lidar.view_configuration

    print("\nLiDAR stream:", i)

    print("\nComplete LiDAR configuration:")
    print(cfg)

    print("\nNumber of reflections:", len(lidar.reflection))

    print("\nFirst reflection:")
    if lidar.reflection:
        print(lidar.reflection[0])

    print("\nReflection protobuf fields:")

    for field in lidar.reflection[0].DESCRIPTOR.fields:
        print("-", field.name)

    print("\nConfiguration protobuf fields:")

    for field in cfg.DESCRIPTOR.fields:
        print("-", field.name)

print("\nTASK 11.3C GEOMETRY INSPECTION COMPLETED")
