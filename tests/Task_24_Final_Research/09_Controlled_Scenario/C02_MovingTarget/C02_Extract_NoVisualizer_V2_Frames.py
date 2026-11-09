from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView
import struct
import csv
import zlib

SOURCE = Path(r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi")

OUT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\Camera_NoVisualizer_V2_2122")

# First pass: collect only frame metadata.
# Second pass: decode five frames distributed across the recording.
records = []

with SOURCE.open("rb") as stream:
    index = 0

    while True:
        header = stream.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]

        if not 0 < size <= 100_000_000:
            raise RuntimeError("Invalid OSI message length")

        offset = stream.tell()

        payload = stream.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI message")

        msg = SensorView()
        msg.ParseFromString(payload)

        if msg.camera_sensor_view:
            camera = msg.camera_sensor_view[0]

            if camera.image_data:
                records.append((index, offset - 4))

        index += 1

if not records:
    raise RuntimeError("No Camera image payloads found")

positions = sorted(set(
    round(i * (len(records) - 1) / 4)
    for i in range(5)
))

selected = [records[i] for i in positions]

def chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    )

def save_png(path, rgb, width, height):
    expected = width * height * 3

    if len(rgb) != expected:
        raise RuntimeError(
            f"Invalid RGB size: {len(rgb)} != {expected}"
        )

    stride = width * 3

    scanlines = b"".join(
        b"\x00" + rgb[y*stride:(y+1)*stride]
        for y in range(height)
    )

    ihdr = struct.pack(
        ">IIBBBBB", width, height, 8, 2, 0, 0, 0
    )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(scanlines, 6))
        + chunk(b"IEND", b"")
    )

    path.write_bytes(png)

OUT.mkdir(parents=False, exist_ok=False)

rows = []

with SOURCE.open("rb") as stream:
    for image_number, (frame_index, offset) in enumerate(selected, 1):
        stream.seek(offset)

        size = struct.unpack("<I", stream.read(4))[0]

        msg = SensorView()
        msg.ParseFromString(stream.read(size))

        camera = msg.camera_sensor_view[0]

        width = camera.view_configuration.number_of_pixels_horizontal
        height = camera.view_configuration.number_of_pixels_vertical

        filename = f"clean_camera_{image_number:02d}_frame{frame_index:05d}.png"

        path = OUT / filename

        save_png(
            path,
            bytes(camera.image_data),
            width,
            height
        )

        timestamp = (
            msg.timestamp.seconds
            + msg.timestamp.nanos * 1e-9
        )

        rows.append({
            "frame_index": frame_index,
            "timestamp_seconds": timestamp,
            "width": width,
            "height": height,
            "image": filename,
        })

        print(
            f"FRAME={frame_index} "
            f"TIME={timestamp:.6f} "
            f"RESOLUTION={width}x{height} "
            f"PNG={filename}"
        )

with (OUT / "camera_frames.csv").open(
    "x", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"CAMERA_FRAMES_AVAILABLE={len(records)}")
print(f"CAMERA_IMAGES_EXTRACTED={len(rows)}")
print(f"OUTPUT_DIR={OUT}")
print("TASK24_06_04U_EXTRACTION_COMPLETE")