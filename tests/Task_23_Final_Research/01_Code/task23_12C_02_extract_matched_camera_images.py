import csv
import struct
import zlib
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\gemstar\Output")
TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

OUT = TASK / "08_Processed_Data" / "Camera_Weather_Comparison"
CSV = TASK / "02_CSV_Data" / "task23_12C_02_matched_camera_frames.csv"

TARGET_TIME = 0.20
WIDTH = 640
HEIGHT = 480

SCENARIOS = {
    "CLEAR": "*_sv_*_T23_12_CAMERA_CLEAR.osi",
    "FOG100": "*_sv_*_T23_12_CAMERA_FOG100.osi",
    "FOG20": "*_sv_*_T23_12_CAMERA_FOG20.osi",
}

if OUT.exists() or CSV.exists():
    raise RuntimeError("Output already exists")

OUT.mkdir(parents=True)

def png_chunk(tag, data):
    payload = tag + data
    return (
        struct.pack(">I", len(data))
        + payload
        + struct.pack(">I", zlib.crc32(payload) & 0xffffffff)
    )

def save_rgb_png(path, rgb):
    expected = WIDTH * HEIGHT * 3

    if len(rgb) != expected:
        raise RuntimeError("RGB payload size mismatch")

    stride = WIDTH * 3

    raw = b"".join(
        b"\x00" + rgb[y * stride:(y + 1) * stride]
        for y in range(HEIGHT)
    )

    header = b"\x89PNG\r\n\x1a\n"

    ihdr = struct.pack(
        ">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0
    )

    path.write_bytes(
        header
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(raw, 6))
        + png_chunk(b"IEND", b"")
    )

rows = []

for scenario, pattern in SCENARIOS.items():

    matches = list(ROOT.glob(pattern))

    if len(matches) != 1:
        raise RuntimeError(f"{scenario}: recording not unique")

    source = matches[0]

    best = None

    with source.open("rb") as stream:

        for index in range(30):

            header = stream.read(4)

            if len(header) != 4:
                break

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid OSI message length")

            data = stream.read(size)

            if len(data) != size:
                raise RuntimeError("Incomplete OSI message")

            msg = SensorView()
            msg.ParseFromString(data)

            if len(msg.camera_sensor_view) != 1:
                continue

            timestamp = (
                msg.timestamp.seconds
                + msg.timestamp.nanos * 1e-9
            )

            difference = abs(timestamp - TARGET_TIME)

            if best is None or difference < best["difference"]:
                best = {
                    "frame": index,
                    "timestamp": timestamp,
                    "difference": difference,
                    "rgb": bytes(
                        msg.camera_sensor_view[0].image_data
                    ),
                }

    if best is None:
        raise RuntimeError(f"{scenario}: no Camera frames")

    if best["difference"] > 0.05:
        raise RuntimeError(
            f"{scenario}: closest frame too far from target time"
        )

    image_path = OUT / f"{scenario}_t0200ms.png"

    save_rgb_png(image_path, best["rgb"])

    rows.append({
        "scenario": scenario,
        "frame_index": best["frame"],
        "timestamp_seconds": f'{best["timestamp"]:.9f}',
        "target_seconds": TARGET_TIME,
        "time_difference_ms": f'{best["difference"] * 1000:.3f}',
        "image_path": str(image_path),
        "source_osi": str(source),
    })

    print(
        f"{scenario}: FRAME={best['frame']} "
        f"TIME={best['timestamp']:.6f} "
        f"DIFFERENCE_MS={best['difference'] * 1000:.3f} "
        f"PNG={image_path.name}"
    )

with CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV_SAVED={CSV}")
print("IMAGES_EXTRACTED=3")
print("TASK23_12C_02_MATCHED_CAMERA_IMAGES_PASS")
