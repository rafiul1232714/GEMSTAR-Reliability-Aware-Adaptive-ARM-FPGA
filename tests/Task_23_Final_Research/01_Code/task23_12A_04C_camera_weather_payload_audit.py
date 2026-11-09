from pathlib import Path
import csv
import struct

from osi3 import osi_sensorview_pb2

task = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

source = Path(r"E:\GEMSTAR_Project\gemstar\Output")

recordings = {
    "CLEAR": "20261105T213845Z_sv_380_X_13819_T23_11E_CLEAR.osi",
    "FOG100": "20261105T220440Z_sv_380_X_12386_T23_11E_FOG100.osi",
    "FOG20": "20261105T215332Z_sv_380_X_14597_T23_11E_FOG20.osi",
}

csv_path = (
    task / "02_CSV_Data"
    / "task23_12A_04C_camera_weather_payload_audit.csv"
)

if csv_path.exists():
    raise RuntimeError("CSV already exists. Refusing to overwrite.")

MAX_FRAMES = 5
MAX_MESSAGE_BYTES = 64 * 1024 * 1024

rows = []

for weather, filename in recordings.items():
    path = source / filename

    if not path.is_file():
        raise FileNotFoundError(path)

    print(f"\n=== {weather} ===")
    print(f"SOURCE={filename}")

    with path.open("rb") as stream:
        for frame_number in range(1, MAX_FRAMES + 1):
            header = stream.read(4)

            if not header:
                print("END_OF_FILE")
                break

            if len(header) != 4:
                raise RuntimeError("Incomplete frame header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= MAX_MESSAGE_BYTES:
                raise RuntimeError(
                    f"Invalid SensorView size: {size}"
                )

            payload = stream.read(size)

            if len(payload) != size:
                raise RuntimeError("Incomplete SensorView payload")

            message = osi_sensorview_pb2.SensorView()
            message.ParseFromString(payload)

            cameras = message.camera_sensor_view

            payload_sizes = [
                len(camera.image_data)
                for camera in cameras
            ]

            status = (
                "MISSING_CAMERA"
                if not cameras else
                "EMPTY_CAMERA_PAYLOAD"
                if not any(payload_sizes) else
                "NONEMPTY_CAMERA_PAYLOAD"
            )

            rows.append({
                "Weather": weather,
                "SourceFile": filename,
                "Frame": frame_number,
                "CameraViews": len(cameras),
                "PayloadBytes": ";".join(
                    str(n) for n in payload_sizes
                ),
                "Status": status,
            })

            print(
                f"FRAME={frame_number} "
                f"VIEWS={len(cameras)} "
                f"BYTES={payload_sizes} "
                f"STATUS={status}"
            )

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=[
            "Weather",
            "SourceFile",
            "Frame",
            "CameraViews",
            "PayloadBytes",
            "Status",
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("\n=== FINAL AUDIT ===")
print(f"FRAMES_INSPECTED={len(rows)}")
print(f"CSV={csv_path}")
print("TASK23_12A_04C_CAMERA_PAYLOAD_AUDIT_COMPLETE")
