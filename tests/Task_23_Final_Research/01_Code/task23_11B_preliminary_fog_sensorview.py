import csv
import struct
from pathlib import Path
from google.protobuf.message import DecodeError
from osi3 import osi_sensorview_pb2

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T190206Z_sv_380_X_336_GEMSTARLIDAR23.osi"
)

OUTPUT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research\02_CSV_Data"
    r"\task23_11B_preliminary_fog_sensorview_integrity.csv"
)

REPORT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research\06_Research_Findings"
    r"\task23_11B_preliminary_fog_sensorview_integrity_report.txt"
)

rows = []
previous_timestamp = None
errors = []
frame_index = 0

with SOURCE.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            errors.append("Incomplete frame header")
            break

        size = struct.unpack("<I", header)[0]

        if size == 0 or size > 100_000_000:
            errors.append(
                f"Invalid frame size at frame {frame_index + 1}: {size}"
            )
            break

        payload = f.read(size)

        if len(payload) != size:
            errors.append(
                f"Incomplete frame payload at frame {frame_index + 1}"
            )
            break

        message = osi_sensorview_pb2.SensorView()

        try:
            message.ParseFromString(payload)
        except DecodeError as e:
            errors.append(
                f"Protobuf decoding failed at frame {frame_index + 1}: {e}"
            )
            break

        frame_index += 1

        timestamp_present = message.HasField("timestamp")

        if timestamp_present:
            timestamp_ns = (
                message.timestamp.seconds * 1_000_000_000
                + message.timestamp.nanos
            )
        else:
            timestamp_ns = None

        monotonic = (
            timestamp_ns is not None
            and (
                previous_timestamp is None
                or timestamp_ns > previous_timestamp
            )
        )

        interval_ms = (
            (timestamp_ns - previous_timestamp) / 1_000_000
            if timestamp_ns is not None
            and previous_timestamp is not None
            else None
        )

        lidar_views = len(message.lidar_sensor_view)

        reflections = sum(
            len(v.reflection)
            for v in message.lidar_sensor_view
        )

        rows.append({
            "Frame": frame_index,
            "TimestampNS": timestamp_ns,
            "TimestampPresent": timestamp_present,
            "StrictlyIncreasing": monotonic,
            "IntervalMS": interval_ms,
            "LiDARViews": lidar_views,
            "ReflectionSlots": reflections,
        })

        if timestamp_ns is not None:
            previous_timestamp = timestamp_ns

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Frame",
        "TimestampNS",
        "TimestampPresent",
        "StrictlyIncreasing",
        "IntervalMS",
        "LiDARViews",
        "ReflectionSlots",
    ])
    writer.writeheader()
    writer.writerows(rows)

missing_timestamps = sum(
    not r["TimestampPresent"] for r in rows
)

non_monotonic = sum(
    not r["StrictlyIncreasing"] for r in rows
)

missing_lidar = sum(
    r["LiDARViews"] == 0 for r in rows
)

empty_reflections = sum(
    r["ReflectionSlots"] == 0 for r in rows
)

passed = (
    frame_index > 0
    and not errors
    and missing_timestamps == 0
    and non_monotonic == 0
    and missing_lidar == 0
    and empty_reflections == 0
)

status = (
    "FRAME_INTEGRITY_PASS"
    if passed else "FRAME_INTEGRITY_REQUIRES_INVESTIGATION"
)

summary = [
    "TASK 23.11.B - FULL LIDAR FRAME INTEGRITY",
    f"Source: {SOURCE}",
    f"Frames inspected: {frame_index}",
    f"Missing timestamps: {missing_timestamps}",
    f"Non-monotonic timestamps: {non_monotonic}",
    f"Frames without LiDAR views: {missing_lidar}",
    f"Frames without reflections: {empty_reflections}",
    f"Parsing errors: {len(errors)}",
    *errors,
    f"Status: {status}",
    f"CSV: {OUTPUT}",
]

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    "\n".join(summary) + "\n",
    encoding="utf-8"
)

print("\n".join(summary))

