from pathlib import Path
import csv

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_15_Final_Research"

INPUT = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

OUTPUT = TASK / "02_CSV_Data" / "task15_sensor_coverage_test.csv"

MAX_MESSAGE_BYTES = 256 * 1024 * 1024


def main():
    frames = 0

    camera_views = 0
    lidar_views = 0
    radar_views = 0

    camera_payload = 0
    lidar_payload = 0
    radar_payload = 0

    if not INPUT.is_file():
        raise FileNotFoundError(INPUT)

    with INPUT.open("rb") as file:
        while True:
            header = file.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI message header")

            length = int.from_bytes(header, "little")

            if length <= 0 or length > MAX_MESSAGE_BYTES:
                raise ValueError(
                    f"Invalid or unexpectedly large message: {length} bytes"
                )

            data = file.read(length)

            if len(data) != length:
                raise ValueError("Incomplete OSI message payload")

            sv = SensorView()
            sv.ParseFromString(data)

            frames += 1

            cameras = sv.camera_sensor_view
            lidars = sv.lidar_sensor_view
            radars = sv.radar_sensor_view

            camera_views += int(len(cameras) > 0)
            lidar_views += int(len(lidars) > 0)
            radar_views += int(len(radars) > 0)

            camera_payload += int(
                any(len(c.image_data) > 0 for c in cameras)
            )

            lidar_payload += int(
                any(len(l.reflection) > 0 for l in lidars)
            )

            radar_payload += int(
                any(len(r.reflection) > 0 for r in radars)
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    results = {
        "Recording": INPUT.name,
        "TotalFrames": frames,
        "CameraViewFrames": camera_views,
        "LiDARViewFrames": lidar_views,
        "RadarViewFrames": radar_views,
        "CameraPayloadFrames": camera_payload,
        "LiDARPayloadFrames": lidar_payload,
        "RadarPayloadFrames": radar_payload,
    }

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results.keys())
        writer.writeheader()
        writer.writerow(results)

    print("\n=== TASK 15 SENSOR COVERAGE ===")

    for key, value in results.items():
        print(f"{key}: {value}")

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()