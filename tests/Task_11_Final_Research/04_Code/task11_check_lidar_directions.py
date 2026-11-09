
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

FILE = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

TARGET_FRAME = 101

with FILE.open("rb") as f:
    for frame in range(1, TARGET_FRAME + 1):
        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = int.from_bytes(header, "little")
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

sv = SensorView()
sv.ParseFromString(payload)

print("TASK 11.3D - LIDAR RAY DIRECTION CHECK")
print("Frame:", TARGET_FRAME)

for i, lidar in enumerate(sv.lidar_sensor_view):
    cfg = lidar.view_configuration

    print("\nLiDAR sensor:", i)
    print("Horizontal rays:", cfg.number_of_rays_horizontal)
    print("Vertical rays:", cfg.number_of_rays_vertical)
    print("Reflections:", len(lidar.reflection))
    print("Direction entries:", len(cfg.directions))
    print("Timing entries:", len(cfg.timings))

    if len(cfg.directions) > 0:
        print("\nFirst five direction entries:")

        for j, direction in enumerate(cfg.directions[:5]):
            print(f"Direction {j}: {direction}")

        print("\nDirection entry at index 250:")
        if len(cfg.directions) > 250:
            print(cfg.directions[250])

        print("\nDirection entry at index 251:")
        if len(cfg.directions) > 251:
            print(cfg.directions[251])

        print("\nLast direction:")
        print(cfg.directions[-1])
    else:
        print("\nNo explicit ray directions recorded.")

    print("\nReflection count matches direction count:",
          len(lidar.reflection) == len(cfg.directions))

print("\nTASK 11.3D COMPLETED")
