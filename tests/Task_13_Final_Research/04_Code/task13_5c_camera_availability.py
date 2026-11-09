
# TASK 13.5C - CAMERA AVAILABILITY
# Read the original MOR100 SensorView file.
# No modifications to previous datasets.

from pathlib import Path
import struct

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

FILE = (
    ROOT / "data" / "raw" / "fog_mor100" /
    "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

def read_messages(path):
    with path.open("rb") as f:
        while True:
            size_bytes = f.read(4)

            if not size_bytes:
                break

            if len(size_bytes) != 4:
                raise RuntimeError("Incomplete OSI header")

            size = struct.unpack("<I", size_bytes)[0]

            payload = f.read(size)

            if len(payload) != size:
                raise RuntimeError("Incomplete OSI message")

            message = SensorView()
            message.ParseFromString(payload)
            yield message


total_frames = 0
camera_frames = 0
lidar_frames = 0
radar_frames = 0

camera_types = set()
camera_sizes = []

print("\n===== TASK 13.5C - CAMERA AVAILABILITY =====")

for frame, sv in enumerate(read_messages(FILE), 1):
    total_frames += 1

    cameras = list(sv.camera_sensor_view)

    if cameras:
        camera_frames += 1

        for camera in cameras:
            camera_types.add(
                camera.DESCRIPTOR.full_name
            )
            camera_sizes.append(
                camera.ByteSize()
            )

    if sv.lidar_sensor_view:
        lidar_frames += 1

    if sv.radar_sensor_view:
        radar_frames += 1

    if frame in (1, 150, 300, 466):
        print(f"\nFrame {frame}")
        print("Time:", (
            sv.timestamp.seconds +
            sv.timestamp.nanos / 1e9
        ))
        print("Camera views:", len(sv.camera_sensor_view))
        print("LiDAR views:", len(sv.lidar_sensor_view))
        print("Radar views:", len(sv.radar_sensor_view))

print("\n===== SUMMARY =====")
print("Total frames:", total_frames)
print("Frames with camera views:", camera_frames)
print("Frames with LiDAR views:", lidar_frames)
print("Frames with Radar views:", radar_frames)

if camera_sizes:
    print("Camera message types:", sorted(camera_types))
    print("Smallest camera view size:", min(camera_sizes))
    print("Largest camera view size:", max(camera_sizes))
else:
    print("No camera SensorView messages found.")

print("\nTASK 13.5C COMPLETED")
