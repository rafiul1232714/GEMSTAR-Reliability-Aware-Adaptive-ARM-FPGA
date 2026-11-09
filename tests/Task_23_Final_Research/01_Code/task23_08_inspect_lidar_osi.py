from pathlib import Path
import struct
import statistics

from osi3 import osi_sensorview_pb2

path = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T190206Z_sv_380_X_336_GEMSTARLIDAR23.osi"
)

report = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests"
    r"\Task_23_Final_Research\06_Research_Findings"
    r"\task23_08_lidar_osi_inspection.txt"
)

if not path.is_file():
    raise FileNotFoundError(path)

SPEED_OF_LIGHT = 299792458.0

lines = []
frame_count = 0
lidar_views = 0
reflection_count = 0
valid_ranges = []

def emit(message):
    message = str(message)
    lines.append(message)
    print(message)

emit("=== TASK 23.8 — LIDAR OSI INSPECTION ===")
emit(f"File: {path}")
emit(f"File size: {path.stat().st_size} bytes")

with path.open("rb") as stream:
    for frame_index in range(10):

        header = stream.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete frame-length header")

        payload_size = struct.unpack("<I", header)[0]

        if payload_size <= 0 or payload_size > 100_000_000:
            raise RuntimeError(
                f"Invalid OSI payload size: {payload_size}"
            )

        payload = stream.read(payload_size)

        if len(payload) != payload_size:
            raise RuntimeError("Incomplete OSI frame payload")

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        frame_count += 1

        # Inspect the actual LiDAR SensorView payload.
        views = list(message.lidar_sensor_view)
        lidar_views += len(views)

        frame_reflections = 0
        frame_ranges = []

        for view in views:
            for reflection in view.reflection:
                frame_reflections += 1

                tof = reflection.time_of_flight
                distance_m = (
                    SPEED_OF_LIGHT * tof / 2.0
                )

                if 0 < distance_m <= 50:
                    frame_ranges.append(distance_m)
                    valid_ranges.append(distance_m)

        reflection_count += frame_reflections

        emit(
            f"Frame {frame_index + 1}: "
            f"LiDAR views={len(views)}, "
            f"reflections={frame_reflections}, "
            f"valid ranges={len(frame_ranges)}"
        )

emit("")
emit("=== SUMMARY ===")
emit(f"Frames inspected: {frame_count}")
emit(f"LiDAR views: {lidar_views}")
emit(f"Total reflections: {reflection_count}")
emit(f"Positive ranges <= 50 m: {len(valid_ranges)}")

if valid_ranges:
    emit(f"Minimum range: {min(valid_ranges):.4f} m")
    emit(f"Median range: {statistics.median(valid_ranges):.4f} m")
    emit(f"Maximum range: {max(valid_ranges):.4f} m")

    near_cube = [
        d for d in valid_ranges
        if 8.0 <= d <= 12.0
    ]

    emit(f"Ranges between 8 and 12 m: {len(near_cube)}")

    if near_cube:
        emit(
            "Median 8–12 m range: "
            f"{statistics.median(near_cube):.4f} m"
        )

status = (
    "LIDAR_PAYLOAD_PRESENT"
    if lidar_views > 0 and reflection_count > 0
    else "LIDAR_PAYLOAD_NOT_VERIFIED"
)

emit(f"Status: {status}")
emit(f"Report: {report}")

report.parent.mkdir(parents=True, exist_ok=True)
report.write_text("\n".join(lines) + "\n", encoding="utf-8")

if status != "LIDAR_PAYLOAD_PRESENT":
    raise RuntimeError("No LiDAR reflections found")
