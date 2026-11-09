
# TASK 13.5H - CAMERA PROJECTION PARAMETERS
# Read-only inspection of MOR100 frame 150.

from pathlib import Path
import struct
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

FILE = (
    ROOT / "data" / "raw" / "fog_mor100" /
    "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

FRAME = 150

with FILE.open("rb") as f:
    for frame in range(1, FRAME + 1):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Frame not found")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete frame")

        if frame == FRAME:
            sv = SensorView()
            sv.ParseFromString(payload)

camera = sv.camera_sensor_view[0]
cfg = camera.view_configuration

print("\n===== TASK 13.5H - CAMERA PARAMETERS =====")
print("Frame:", FRAME)
print(
    "Timestamp:",
    sv.timestamp.seconds + sv.timestamp.nanos / 1e9
)

print("\nRecorded camera configuration:")
print(cfg)

print("\nImage payload bytes:", len(camera.image_data))
print("TASK 13.5H COMPLETED")
