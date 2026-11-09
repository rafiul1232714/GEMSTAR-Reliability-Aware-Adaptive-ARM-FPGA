
# TASK 11.8C - EXTRACT EXACT CAMERA FRAME 150
# GEMSTAR MOR100
# Reuses the Task 9 length-prefixed OSI reading method.
# Does not overwrite the original Task 9 metadata.

from pathlib import Path
import csv
import sys

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

# Make the existing project's OSI protobuf module importable.
sys.path.insert(0, str(ROOT / "src"))

try:
    from osi3.osi_sensorview_pb2 import SensorView
except ImportError:
    try:
        from osi_sensorview_pb2 import SensorView
    except ImportError as exc:
        raise SystemExit(
            "Cannot import OSI SensorView. Copy the "
            "working SensorView import from the top of "
            "task09_extract_mor100_camera.py into this script."
        ) from exc

INPUT = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"

OUTPUT = ARCHIVE / "01_Graphs"
CSV_DIR = ARCHIVE / "02_CSV_Data"

TARGET_FRAME = 150
WIDTH = 640
HEIGHT = 480
CHANNELS = 3

OUTPUT.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

assert INPUT.is_file(), f"OSI input missing: {INPUT}"

print("TASK 11.8C - CAMERA FRAME 150 EXTRACTION")

found = False
metadata = []

with INPUT.open("rb") as f:

    frame = 0

    while True:

        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete OSI header.")

        message_size = int.from_bytes(header, "little")

        if message_size <= 0:
            raise ValueError("Invalid OSI message size.")

        # Skip earlier payloads without loading them.
        if frame + 1 < TARGET_FRAME:
            f.seek(message_size, 1)
            frame += 1
            continue

        payload = f.read(message_size)

        if len(payload) != message_size:
            raise ValueError("Incomplete OSI payload.")

        frame += 1

        sv = SensorView()
        sv.ParseFromString(payload)

        timestamp_s = (
            sv.timestamp.seconds +
            sv.timestamp.nanos / 1e9
        )

        print(f"Reached frame: {frame}")
        print(f"Timestamp: {timestamp_s:.6f} s")
        print(f"Camera streams: {len(sv.camera_sensor_view)}")

        for index, camera in enumerate(sv.camera_sensor_view):

            raw = bytes(camera.image_data)
            expected = WIDTH * HEIGHT * CHANNELS

            if len(raw) != expected:
                print(
                    f"Skipping camera {index}: "
                    f"{len(raw)} bytes, expected {expected}"
                )
                continue

            filename = (
                f"task11_mor100_frame0150_camera_{index}.ppm"
            )

            output_file = OUTPUT / filename

            header_ppm = (
                f"P6\n{WIDTH} {HEIGHT}\n255\n"
            ).encode("ascii")

            with output_file.open("wb") as out:
                out.write(header_ppm)
                out.write(raw)

            metadata.append({
                "frame": frame,
                "timestamp_s": timestamp_s,
                "camera_index": index,
                "filename": filename,
                "raw_bytes": len(raw),
                "width": WIDTH,
                "height": HEIGHT,
                "color_order_status": "unverified"
            })

            print("Saved:", output_file)

        found = True
        break

if not found:
    raise RuntimeError("Frame 150 was not found in the OSI file.")

if not metadata:
    raise RuntimeError(
        "Frame 150 was found but no valid camera image was extracted."
    )

metadata_file = (
    CSV_DIR / "task11_camera_frame150_metadata.csv"
)

with metadata_file.open(
    "w", newline="", encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f, fieldnames=list(metadata[0].keys())
    )
    writer.writeheader()
    writer.writerows(metadata)

print("\nCamera images extracted:", len(metadata))
print("Metadata:", metadata_file)
print("TASK 11.8C COMPLETED")
