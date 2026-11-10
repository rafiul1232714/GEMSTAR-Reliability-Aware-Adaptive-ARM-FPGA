import csv
import hashlib
import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

OUT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests"
    r"\Task_25_Final_Research\02_CSV_Data"
    r"\task25_12_c02_fullrate_freshness.csv"
)

EXPECTED = 2122

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    if OUT.exists():
        raise FileExistsError(
            f"Output already exists: {OUT}"
        )

    rows = []
    previous = {}
    previous_time = None

    with SOURCE.open("rb") as stream:
        for frame in range(EXPECTED):
            header = stream.read(4)
            if len(header) != 4:
                raise RuntimeError(
                    f"Incomplete header: {frame}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError(
                    f"Invalid frame size: {frame}"
                )

            payload = stream.read(size)
            if len(payload) != size:
                raise RuntimeError(
                    f"Incomplete frame: {frame}"
                )

            sv = SensorView()
            sv.ParseFromString(payload)

            timestamp_ns = (
                int(sv.timestamp.seconds) * 1000000000
                + int(sv.timestamp.nanos)
            )

            if previous_time is not None:
                if timestamp_ns <= previous_time:
                    raise RuntimeError(
                        f"Nonmonotonic timestamp: {frame}"
                    )

            sensor_views = {
                "Camera": sv.camera_sensor_view,
                "LiDAR": sv.lidar_sensor_view,
                "Radar": sv.radar_sensor_view
            }

            row = {
                "Frame": frame,
                "Timestamp_ns": timestamp_ns,
                "DeltaTime_ms": (
                    "" if previous_time is None
                    else (timestamp_ns - previous_time)
                    / 1000000
                )
            }

            for sensor, views in sensor_views.items():
                if len(views) != 1:
                    raise RuntimeError(
                        f"{sensor} view count at {frame}: "
                        f"{len(views)}"
                    )

                view = views[0]

                # Sensor-view digest includes configuration.
                view_hash = digest(
                    view.SerializeToString(
                        deterministic=True
                    )
                )

                row[sensor + "_ViewSHA256"] = view_hash
                row[sensor + "_ViewRepeated"] = (
                    "" if sensor not in previous
                    else int(view_hash == previous[sensor])
                )

                previous[sensor] = view_hash

                if sensor == "Camera":
                    image = bytes(view.image_data)
                    image_hash = digest(image)
                    row["CameraImageBytes"] = len(image)
                    row["CameraImageSHA256"] = image_hash
                    row["CameraImageRepeated"] = (
                        "" if "CameraImage" not in previous
                        else int(
                            image_hash
                            == previous["CameraImage"]
                        )
                    )
                    previous["CameraImage"] = image_hash
                else:
                    row[sensor + "_ReflectionCount"] = (
                        len(view.reflection)
                    )

            rows.append(row)
            previous_time = timestamp_ns

            if frame % 250 == 0:
                print("PROCESSED_FRAME=", frame, flush=True)

        if stream.read(1):
            raise RuntimeError(
                "Unexpected data beyond 2122 frames"
            )

    with OUT.open(
        "x", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TASK 25 FULLRATE FRESHNESS ===")
    print("FRAMES=", len(rows))

    for column in (
        "CameraImageRepeated",
        "LiDAR_ViewRepeated",
        "Radar_ViewRepeated"
    ):
        repeated = sum(
            r[column] == 1 for r in rows
        )
        print(column, "=", repeated)

    print("SAVED=", OUT)
    print("ORIGINAL_OSI_MODIFIED=NO")
    print("ACQUISITION_AGE_VALIDATED=NO")

if __name__ == "__main__":
    main()
