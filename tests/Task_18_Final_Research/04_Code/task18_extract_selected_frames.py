from pathlib import Path
import csv
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

OUT = BASE / "08_Extracted_Images" / "Selected_Frames"
CSV = BASE / "02_CSV_Data" / "task18_selected_camera_frames.csv"

OUT.mkdir(parents=True, exist_ok=True)
CSV.parent.mkdir(parents=True, exist_ok=True)

SELECTED = {
    0, 50, 100, 150, 200, 250,
    300, 350, 400, 423, 424, 450
}

rows = []

with SOURCE.open("rb") as f:
    frame = 0

    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

        if frame in SELECTED:
            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            if not sv.camera_sensor_view:
                raise RuntimeError(
                    f"Camera missing at frame {frame}"
                )

            cam = sv.camera_sensor_view[0]
            cfg = cam.view_configuration

            width = cfg.number_of_pixels_horizontal
            height = cfg.number_of_pixels_vertical
            data = cam.image_data

            if len(data) != width * height * 3:
                raise RuntimeError(
                    f"Unexpected image size at frame {frame}"
                )

            pixels = np.frombuffer(
                data, dtype=np.uint8
            ).reshape(height, width, 3)

            timestamp = (
                sv.timestamp.seconds
                + sv.timestamp.nanos / 1e9
            )

            filename = f"task18_camera_frame_{frame:03d}.png"
            Image.fromarray(pixels, "RGB").save(OUT / filename)

            rows.append({
                "Frame": frame,
                "TimestampSeconds": f"{timestamp:.9f}",
                "TimingRegime": (
                    "HIGH_RATE" if frame < 424 else "LOW_RATE"
                ),
                "Width": width,
                "Height": height,
                "ImageFile": filename
            })

        frame += 1

with CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 18.5A CAMERA DATASET EXTRACTION ===")
print("Recording frames scanned:", frame)
print("Selected frames extracted:", len(rows))
print("Expected selected frames:", len(SELECTED))
print("CSV saved:", CSV.exists())
print("Image folder:", OUT)

for row in rows:
    print(
        f'Frame {row["Frame"]:3d} | '
        f'Time {row["TimestampSeconds"]} s | '
        f'{row["TimingRegime"]}'
    )
