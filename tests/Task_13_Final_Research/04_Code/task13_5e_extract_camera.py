
# TASK 13.5E - CAMERA IMAGE EXTRACTION
# GEMSTAR MOR100, frame 150
#
# Extracts the raw camera payload in two candidate
# channel orders: RGB and BGR.
# Does not modify previous research datasets.

from pathlib import Path
import struct
import numpy as np
from PIL import Image

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

OSI_FILE = (
    ROOT / "data" / "raw" / "fog_mor100" /
    "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUT = (
    ROOT / "tests" / "Task_13_Final_Research" /
    "01_Graphs"
)
OUT.mkdir(parents=True, exist_ok=True)

FRAME = 150
WIDTH = 640
HEIGHT = 480


def read_messages(path):
    with path.open("rb") as f:
        while True:
            header = f.read(4)

            if not header:
                return

            if len(header) != 4:
                raise RuntimeError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]
            data = f.read(size)

            if len(data) != size:
                raise RuntimeError("Incomplete OSI payload")

            message = SensorView()
            message.ParseFromString(data)
            yield message


print("\n===== TASK 13.5E - CAMERA EXTRACTION =====")

for frame, sv in enumerate(read_messages(OSI_FILE), 1):
    if frame != FRAME:
        continue

    if not sv.camera_sensor_view:
        raise RuntimeError("No camera in selected frame")

    camera = sv.camera_sensor_view[0]
    payload = camera.image_data

    print("Frame:", frame)
    print("Payload bytes:", len(payload))

    expected = WIDTH * HEIGHT * 3

    if len(payload) != expected:
        raise RuntimeError(
            f"Expected {expected} bytes, got {len(payload)}"
        )

    array = np.frombuffer(
        payload, dtype=np.uint8
    ).reshape(HEIGHT, WIDTH, 3)

    # Candidate 1: payload is RGB.
    rgb_file = OUT / "task13_5e_camera_frame150_rgb.png"
    Image.fromarray(array, "RGB").save(rgb_file)

    # Candidate 2: payload is BGR.
    bgr_file = OUT / "task13_5e_camera_frame150_bgr.png"
    Image.fromarray(array[:, :, ::-1], "RGB").save(bgr_file)

    print("\nSaved RGB interpretation:", rgb_file)
    print("Saved BGR interpretation:", bgr_file)

    print("\nChannel statistics:")
    for i in range(3):
        channel = array[:, :, i]
        print(
            f"Channel {i}: "
            f"min={channel.min()}, "
            f"max={channel.max()}, "
            f"mean={channel.mean():.2f}"
        )

    print("\nTASK 13.5E COMPLETED")
    break

else:
    raise RuntimeError("Requested frame not found")
