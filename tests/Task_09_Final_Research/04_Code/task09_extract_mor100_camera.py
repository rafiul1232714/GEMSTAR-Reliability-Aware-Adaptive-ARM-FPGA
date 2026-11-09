
from pathlib import Path
import csv

from osi3.osi_sensorview_pb2 import SensorView

# ===========================================
# TASK 9.2.3B - GEMSTAR RAW CAMERA EXTRACTION
# Fog MOR 100
# ===========================================

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

INPUT = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUTPUT = (
    ROOT / "results" / "figures"
    / "fog_mor100_camera"
)

ARCHIVE = (
    ROOT / "tests"
    / "Task_09_Final_Research"
    / "02_CSV_Data"
)

OUTPUT.mkdir(parents=True, exist_ok=True)
ARCHIVE.mkdir(parents=True, exist_ok=True)

WIDTH = 640
HEIGHT = 480
CHANNELS = 3

# Initially extract approximately 47 images
FRAME_INTERVAL = 10


def read_osi(path):

    with path.open("rb") as f:

        while True:

            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = int.from_bytes(header, "little")

            if size <= 0:
                raise ValueError("Invalid OSI message size")

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Incomplete OSI payload")

            message = SensorView()
            message.ParseFromString(payload)

            yield message


def get_timestamp(message):

    return (
        message.timestamp.seconds
        + message.timestamp.nanos / 1e9
    )


metadata = []
total_frames = 0
extracted = 0

print("====================================")
print("TASK 9.2.3B - RAW CAMERA EXTRACTION")
print("====================================")

for frame, sv in enumerate(read_osi(INPUT), start=1):

    total_frames += 1

    if (frame - 1) % FRAME_INTERVAL != 0:
        continue

    for camera_index, camera in enumerate(
        sv.camera_sensor_view
    ):

        raw = bytes(camera.image_data)

        expected_size = WIDTH * HEIGHT * CHANNELS

        if len(raw) != expected_size:

            print(
                f"Frame {frame}: unexpected size "
                f"{len(raw)} (expected {expected_size})"
            )

            continue

        filename = (
            f"mor100_frame_{frame:04d}"
            f"_camera_{camera_index}.ppm"
        )

        output_file = OUTPUT / filename

        # PPM P6 is a binary RGB image format.
        # The raw bytes are preserved unchanged.
        # RGB/BGR ordering must be confirmed visually.

        ppm_header = (
            f"P6\n{WIDTH} {HEIGHT}\n255\n"
        ).encode("ascii")

        with output_file.open("wb") as f:

            f.write(ppm_header)
            f.write(raw)

        metadata.append([
            frame,
            get_timestamp(sv),
            camera_index,
            filename,
            len(raw),
            WIDTH,
            HEIGHT
        ])

        extracted += 1

        print("Saved:", filename)


csv_file = (
    ARCHIVE / "task09_mor100_camera_frames.csv"
)

with csv_file.open(
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "frame",
        "timestamp_s",
        "camera_index",
        "filename",
        "raw_bytes",
        "width",
        "height"
    ])

    writer.writerows(metadata)


print("\n====================================")
print("CAMERA EXTRACTION SUMMARY")
print("====================================")

print("Total OSI frames:", total_frames)
print("Extracted images:", extracted)
print("Output:", OUTPUT)
print("CSV:", csv_file)

print("\nTASK 9.2.3B COMPLETED")
