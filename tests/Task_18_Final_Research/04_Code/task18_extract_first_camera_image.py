from pathlib import Path
import struct
import numpy as np
from PIL import Image
from osi3 import osi_sensorview_pb2

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

SOURCE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\data\raw\fog_mor100"
    r"\20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUT = BASE / "08_Extracted_Images"
OUT.mkdir(parents=True, exist_ok=True)

with SOURCE.open("rb") as f:
    header = f.read(4)
    if len(header) != 4:
        raise RuntimeError("Incomplete OSI header")

    size = struct.unpack("<I", header)[0]
    payload = f.read(size)

    if len(payload) != size:
        raise RuntimeError("Incomplete OSI payload")

sv = osi_sensorview_pb2.SensorView()
sv.ParseFromString(payload)

cam = sv.camera_sensor_view[0]
cfg = cam.view_configuration

width = cfg.number_of_pixels_horizontal
height = cfg.number_of_pixels_vertical
data = cam.image_data

expected = width * height * 3

if len(data) != expected:
    raise RuntimeError(
        f"Unexpected image size: {len(data)} vs {expected}"
    )

pixels = np.frombuffer(
    data, dtype=np.uint8
).reshape(height, width, 3)

# Interpretation A: bytes represent R, G, B.
rgb_image = Image.fromarray(pixels, mode="RGB")

# Interpretation B: bytes represent B, G, R.
bgr_image = Image.fromarray(pixels[:, :, ::-1], mode="RGB")

rgb_path = OUT / "task18_frame000_rgb_interpretation.png"
bgr_path = OUT / "task18_frame000_bgr_interpretation.png"

rgb_image.save(rgb_path)
bgr_image.save(bgr_path)

print("\n=== TASK 18.2A IMAGE EXTRACTION ===")
print("Frame:", 0)
print("Timestamp (s):",
      sv.timestamp.seconds + sv.timestamp.nanos / 1e9)
print("Resolution:", width, "x", height)
print("Raw bytes:", len(data))
print("Pixel array:", pixels.shape)
print("RGB candidate saved:", rgb_path.exists())
print("BGR candidate saved:", bgr_path.exists())
print("Output folder:", OUT)
