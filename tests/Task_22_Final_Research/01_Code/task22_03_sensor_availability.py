import csv
import json
import struct
from pathlib import Path
from collections import Counter

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

ROOT = Path(r"E:\GEMSTAR_Project")
TASK = ROOT / "sensor-health-monitor" / "tests" / "Task_22_Final_Research"
OUTPUT = ROOT / "gemstar" / "Output"

SV = OUTPUT / "20261102T180104Z_sv_380_X_806_GEMSTAR.osi"
GT = OUTPUT / "20261102T180104Z_gt_380_X_806_GEMSTAR.osi"

LIMIT = 100
MAX_SIZE = 100 * 1024 * 1024

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

CSV_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)


def read_messages(path, message_type, limit):
    with path.open("rb") as handle:
        for index in range(limit):
            header = handle.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError(
                    f"Incomplete header in {path.name}, frame {index}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= MAX_SIZE:
                raise ValueError(
                    f"Invalid message size {size} at frame {index}"
                )

            payload = handle.read(size)

            if len(payload) != size:
                raise ValueError(
                    f"Truncated payload at frame {index}"
                )

            msg = message_type()
            msg.ParseFromString(payload)

            yield index, msg


def timestamp_ns(msg):
    return (
        int(msg.timestamp.seconds) * 1_000_000_000
        + int(msg.timestamp.nanos)
    )


def populated_fields(message):
    # Inspect the actual protobuf fields without assuming
    # every OSI version has identical camera/LiDAR fields.
    return [
        field.name
        for field, value in message.ListFields()
    ]


def sensor_view_summary(view):
    # Report populated fields besides configuration;
    # presence is NOT equivalent to valid sensor payload.
    fields = populated_fields(view)
    return [
        name for name in fields
        if name not in (
            "view_configuration",
            "sensor_id",
            "mounting_position"
        )
    ]


print("\n=== TASK 22.3 PAIRED SENSOR AVAILABILITY ===")

if not SV.is_file():
    raise FileNotFoundError(f"SensorView missing: {SV}")

if not GT.is_file():
    raise FileNotFoundError(f"GroundTruth missing: {GT}")

print("SensorView:", SV.name)
print("GroundTruth:", GT.name)

sv_frames = dict(read_messages(SV, SensorView, LIMIT))
gt_frames = dict(read_messages(GT, GroundTruth, LIMIT))

rows = []
camera_fields = Counter()
lidar_fields = Counter()
radar_fields = Counter()

matching_timestamps = 0
mismatched_timestamps = 0
missing_gt_frames = 0

for frame, sv in sorted(sv_frames.items()):
    gt = gt_frames.get(frame)

    camera_views = list(sv.camera_sensor_view)
    lidar_views = list(sv.lidar_sensor_view)
    radar_views = list(sv.radar_sensor_view)

    camera_count = len(camera_views)
    lidar_count = len(lidar_views)
    radar_count = len(radar_views)

    lidar_reflections = 0
    radar_reflections = 0
    positive_radar_returns = 0

    for view in camera_views:
        camera_fields.update(sensor_view_summary(view))

    for view in lidar_views:
        lidar_fields.update(sensor_view_summary(view))

        if hasattr(view, "reflection"):
            lidar_reflections += len(view.reflection)

    for view in radar_views:
        radar_fields.update(sensor_view_summary(view))

        radar_reflections += len(view.reflection)

        for reflection in view.reflection:
            if (
                reflection.time_of_flight > 0
                and reflection.signal_strength > 0
            ):
                positive_radar_returns += 1

    if gt is None:
        timestamp_match = ""
        gt_object_count = ""
        missing_gt_frames += 1
    else:
        timestamp_match = (
            timestamp_ns(sv) == timestamp_ns(gt)
        )

        matching_timestamps += int(timestamp_match)
        mismatched_timestamps += int(not timestamp_match)

        gt_object_count = len(gt.moving_object)

    rows.append({
        "Frame": frame,
        "TimestampNs": timestamp_ns(sv),
        "CameraEntries": camera_count,
        "LiDAREntries": lidar_count,
        "RadarEntries": radar_count,
        "LiDARReflectionCount": lidar_reflections,
        "RadarReflectionSlots": radar_reflections,
        "PositiveRadarReturns": positive_radar_returns,
        "GTMovingObjects": gt_object_count,
        "TimestampMatch": timestamp_match
    })


csv_path = (
    CSV_DIR / "task22_03_paired_sensor_availability.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)


def frames_with(field):
    return sum(row[field] > 0 for row in rows)


summary = {
    "Task": "22.3",
    "SensorViewFile": str(SV),
    "GroundTruthFile": str(GT),
    "FramesInspected": len(rows),
    "GTFramesInspected": len(gt_frames),
    "CameraEntryFrames": frames_with("CameraEntries"),
    "LiDAREntryFrames": frames_with("LiDAREntries"),
    "RadarEntryFrames": frames_with("RadarEntries"),
    "LiDARReflectionFrames": frames_with("LiDARReflectionCount"),
    "RadarPositiveReturnFrames": frames_with("PositiveRadarReturns"),
    "MatchingTimestamps": matching_timestamps,
    "MismatchedTimestamps": mismatched_timestamps,
    "MissingGTFrames": missing_gt_frames,
    "CameraNonconfigurationFields": dict(camera_fields),
    "LiDARNonconfigurationFields": dict(lidar_fields),
    "RadarNonconfigurationFields": dict(radar_fields),
    "Limitations": [
        "Sensor entry presence does not validate sensor content",
        "Populated fields do not establish perception accuracy",
        "Matching message timestamps do not prove capture-time synchrony",
        "Only first 100 frames inspected",
        "Radar source-object identity remains unverified",
        "No CPU-FPGA energy measured"
    ]
}

json_path = (
    FINDINGS / "task22_03_sensor_availability_audit.json"
)

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("\n=== SENSOR AVAILABILITY SUMMARY ===")

for name in (
    "FramesInspected",
    "CameraEntryFrames",
    "LiDAREntryFrames",
    "RadarEntryFrames",
    "LiDARReflectionFrames",
    "RadarPositiveReturnFrames",
    "MatchingTimestamps",
    "MismatchedTimestamps",
    "MissingGTFrames"
):
    print(f"{name}: {summary[name]}")

print("\n=== POPULATED SENSOR FIELDS ===")

print("Camera:", dict(camera_fields))
print("LiDAR:", dict(lidar_fields))
print("Radar:", dict(radar_fields))

print("\n=== TASK 22.3 FILE CHECK ===")
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())

print("\n=== TASK 22.3 COMPLETE ===")
