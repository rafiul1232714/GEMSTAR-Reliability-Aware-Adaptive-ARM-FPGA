from pathlib import Path
import struct
import zlib
import csv
import statistics
from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\gemstar\Output")
task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")

osi = root / "20261103T194105Z_sv_380_X_55_GEMSTARCAMERACLEAR23.osi"

image_dir = task / "03_Graphs"
csv_path = task / "02_CSV_Data/task23_09_camera_frame_inspection.csv"
report = task / "06_Research_Findings/task23_09_camera_payload_inspection.txt"

WIDTH = 640
HEIGHT = 480
EXPECTED_BYTES = WIDTH * HEIGHT * 3
MAX_FRAMES = 6

image_dir.mkdir(parents=True, exist_ok=True)
csv_path.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)

def png_chunk(tag, data):
    body = tag + data
    return (
        struct.pack(">I", len(data))
        + body
        + struct.pack(">I", zlib.crc32(body) & 0xffffffff)
    )

def save_rgb_png(path, rgb):
    """Write an RGB PNG using Python's standard library."""
    row_bytes = WIDTH * 3

    raw = b"".join(
        b"\x00" + rgb[y * row_bytes:(y + 1) * row_bytes]
        for y in range(HEIGHT)
    )

    signature = b"\x89PNG\r\n\x1a\n"

    ihdr = struct.pack(
        ">IIBBBBB",
        WIDTH, HEIGHT, 8, 2, 0, 0, 0
    )

    png = (
        signature
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(raw, level=6))
        + png_chunk(b"IEND", b"")
    )

    path.write_bytes(png)

def inspect_rgb(data):
    pixel_count = WIDTH * HEIGHT

    # Use every 16th pixel for fast image diagnostics.
    samples = [
        tuple(data[i:i+3])
        for i in range(0, len(data), 48)
    ]

    unique_sample_colors = len(set(samples))

    mean_rgb = [
        statistics.mean(data[i:i+3][channel] for i in range(0, len(data), 48))
        for channel in range(3)
    ]

    nonblack = sum(
        1 for rgb in samples
        if max(rgb) > 10
    )

    center_pixel_index = (
        (HEIGHT // 2) * WIDTH + WIDTH // 2
    ) * 3

    center_rgb = tuple(
        data[center_pixel_index:center_pixel_index+3]
    )

    return {
        "unique_sample_colors": unique_sample_colors,
        "nonblack_fraction": nonblack / len(samples),
        "mean_red": mean_rgb[0],
        "mean_green": mean_rgb[1],
        "mean_blue": mean_rgb[2],
        "center_rgb": center_rgb,
    }

if not osi.is_file():
    raise FileNotFoundError(osi)

rows = []
saved_images = []

print("\n=== TASK 23.9G — CAMERA OSI RGB VALIDATION ===")
print(f"OSI file: {osi.name}")
print(f"Expected RGB bytes per frame: {EXPECTED_BYTES}")

with osi.open("rb") as stream:
    for frame_number in range(1, MAX_FRAMES + 1):
        header = stream.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]

        if not 0 < size < 20_000_000:
            raise RuntimeError(f"Invalid OSI payload size: {size}")

        payload = stream.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        cameras = message.camera_sensor_view

        if len(cameras) != 1:
            raise RuntimeError(
                f"Frame {frame_number}: expected one camera view, "
                f"found {len(cameras)}"
            )

        rgb = cameras[0].image_data
        data_size = len(rgb)

        print(
            f"Frame {frame_number}: "
            f"camera views={len(cameras)}, "
            f"image bytes={data_size}"
        )

        if data_size != EXPECTED_BYTES:
            raise RuntimeError(
                f"Frame {frame_number}: "
                f"expected {EXPECTED_BYTES} RGB bytes, "
                f"got {data_size}"
            )

        info = inspect_rgb(rgb)

        row = {
            "frame": frame_number,
            "image_bytes": data_size,
            "unique_sample_colors": info["unique_sample_colors"],
            "nonblack_fraction": round(info["nonblack_fraction"], 6),
            "mean_red": round(info["mean_red"], 3),
            "mean_green": round(info["mean_green"], 3),
            "mean_blue": round(info["mean_blue"], 3),
            "center_rgb": str(info["center_rgb"]),
        }

        rows.append(row)

        # Save separate frames to check actual visual content.
        if frame_number in (1, 3, 6):
            path = image_dir / (
                f"task23_09_camera_baseline_frame{frame_number:03d}.png"
            )

            save_rgb_png(path, rgb)
            saved_images.append(path)

            print(f"  PNG saved: {path.name}")

if not rows:
    raise RuntimeError("No camera frames decoded")

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print("\n=== CAMERA IMAGE QUALITY CHECK ===")

for row in rows:
    print(
        f"Frame {row['frame']}: "
        f"unique sampled colors={row['unique_sample_colors']}, "
        f"nonblack={row['nonblack_fraction']:.2%}, "
        f"center RGB={row['center_rgb']}"
    )

# This checks basic pixel variation, not cube visibility.
has_variation = any(
    row["unique_sample_colors"] > 10
    and row["nonblack_fraction"] > 0.05
    for row in rows
)

status = (
    "CAMERA_RGB_PAYLOAD_VALID"
    if has_variation
    else "CAMERA_RGB_CONTENT_REQUIRES_INSPECTION"
)

lines = [
    "TASK 23.9 - CAMERA RGB INSPECTION",
    f"Source OSI: {osi}",
    f"Frames inspected: {len(rows)}",
    f"Resolution: {WIDTH} x {HEIGHT}",
    f"RGB bytes/frame: {EXPECTED_BYTES}",
    f"Status: {status}",
    "",
    "Saved images:",
    *[str(path) for path in saved_images],
    "",
    f"CSV: {csv_path}",
    "",
    "Limitation: valid RGB payload and pixel variation do not",
    "prove that the calibration cube is visible or correctly",
    "located in the camera image."
]

report.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n=== FINAL RESULT ===")
print(f"Status: {status}")
print(f"CSV: {csv_path}")
print(f"Report: {report}")

for path in saved_images:
    print(f"Image: {path}")
