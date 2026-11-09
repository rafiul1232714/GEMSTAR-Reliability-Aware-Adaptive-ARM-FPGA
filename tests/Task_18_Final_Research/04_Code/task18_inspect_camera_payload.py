from pathlib import Path
import struct
from osi3 import osi_sensorview_pb2

source = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\data\raw\fog_mor100"
    r"\20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

with source.open("rb") as f:
    header = f.read(4)

    if len(header) != 4:
        raise RuntimeError("Invalid OSI header")

    size = struct.unpack("<I", header)[0]
    payload = f.read(size)

    if len(payload) != size:
        raise RuntimeError("Incomplete OSI payload")

sv = osi_sensorview_pb2.SensorView()
sv.ParseFromString(payload)

if not sv.camera_sensor_view:
    raise RuntimeError("No Camera entry found")

cam = sv.camera_sensor_view[0]
cfg = cam.view_configuration
data = cam.image_data

width = cfg.number_of_pixels_horizontal
height = cfg.number_of_pixels_vertical

print("\n=== TASK 18.1B CAMERA PAYLOAD ===")
print("Timestamp:", sv.timestamp.seconds + sv.timestamp.nanos / 1e9)
print("Width:", width)
print("Height:", height)
print("Image data type:", type(data).__name__)
print("Image data length:", len(data))
print("First 32 bytes (hex):", data[:32].hex())

print("\n=== CONFIGURATION ===")
print("Channel format:", list(cfg.channel_format))
print("Samples per pixel:", cfg.samples_per_pixel)
print("Pixel order:", cfg.pixel_order)

print("\n=== EXPECTED RAW IMAGE SIZES ===")
print("Grayscale 8-bit:", width * height)
print("RGB 8-bit:", width * height * 3)
print("RGBA 8-bit:", width * height * 4)

print("\n=== FILE SIGNATURE CHECK ===")

if data.startswith(b"\xff\xd8\xff"):
    print("Possible JPEG image")
elif data.startswith(b"\x89PNG\r\n\x1a\n"):
    print("Possible PNG image")
else:
    print("No JPEG/PNG signature found")
    print("Raw pixel storage or another encoding is possible")

print("\n=== INSPECTION COMPLETE ===")
