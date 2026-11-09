
from pathlib import Path
import csv
import math

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

# ============================================
# TASK 9.2.1 - FOG MOR 100 SENSOR ANALYSIS
# Camera + LiDAR + Radar + Ground Truth
# ============================================

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

RAW = ROOT / "data" / "raw" / "fog_mor100"

SV_FILE = (
    RAW / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

GT_FILE = (
    RAW / "20261027T224313Z_gt_380_X_466_GEMSTAR.osi"
)

# Save CSV results directly in Task 09 research archive
ARCHIVE = (
    ROOT / "tests"
    / "Task_09_Final_Research"
    / "02_CSV_Data"
)

ARCHIVE.mkdir(parents=True, exist_ok=True)

SPEED_OF_LIGHT = 299792458.0


# ============================================
# 1. READ LENGTH-PREFIXED OSI MESSAGES
# ============================================

def read_osi(path, message_type):

    with path.open("rb") as file:

        while True:

            header = file.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError(
                    f"Incomplete OSI header: {path}"
                )

            size = int.from_bytes(
                header,
                byteorder="little"
            )

            if size <= 0:
                raise ValueError(
                    f"Invalid OSI message size: {size}"
                )

            payload = file.read(size)

            if len(payload) != size:
                raise ValueError(
                    f"Incomplete OSI message: {path}"
                )

            message = message_type()
            message.ParseFromString(payload)

            yield message


# ============================================
# 2. EXTRACT TIMESTAMP
# ============================================

def get_timestamp(message):

    return (
        message.timestamp.seconds
        + message.timestamp.nanos / 1e9
    )


# ============================================
# 3. LiDAR / RADAR STATISTICS
# ============================================

def sensor_statistics(sensor_views):

    total_records = 0
    positive_records = 0

    max_range = 0.0

    beyond_7m = 0
    beyond_10m = 0

    for sensor in sensor_views:

        for reflection in sensor.reflection:

            total_records += 1

            strength = reflection.signal_strength
            tof = reflection.time_of_flight

            if not (
                math.isfinite(strength)
                and math.isfinite(tof)
                and strength > 0
                and tof > 0
            ):
                continue

            positive_records += 1

            # Distance from round-trip time of flight
            distance = (
                SPEED_OF_LIGHT * tof / 2.0
            )

            max_range = max(
                max_range,
                distance
            )

            if distance > 7.0:
                beyond_7m += 1

            if distance > 10.0:
                beyond_10m += 1

    positive_pct = (
        100.0 * positive_records / total_records
        if total_records > 0
        else 0.0
    )

    return (
        total_records,
        positive_records,
        positive_pct,
        max_range,
        beyond_7m,
        beyond_10m
    )


# ============================================
# 4. CHECK INPUT FILES
# ============================================

if not SV_FILE.exists():
    raise FileNotFoundError(SV_FILE)

if not GT_FILE.exists():
    raise FileNotFoundError(GT_FILE)

print("======================================")
print("TASK 9.2.1 - LIGHT FOG MOR 100")
print("======================================")

print("SensorView:", SV_FILE.name)
print("GroundTruth:", GT_FILE.name)


# ============================================
# 5. PROCESS CAMERA, LiDAR AND RADAR
# ============================================

rows = []

sensor_times = []
gt_times = []

print("\nReading SensorView...")

for frame, sv in enumerate(
    read_osi(SV_FILE, SensorView),
    start=1
):

    timestamp = get_timestamp(sv)
    sensor_times.append(timestamp)

    # Camera availability
    camera_streams = len(
        sv.camera_sensor_view
    )

    camera_with_image = sum(
        1
        for camera in sv.camera_sensor_view
        if len(camera.image_data) > 0
    )

    # LiDAR statistics
    lidar = sensor_statistics(
        sv.lidar_sensor_view
    )

    # Radar statistics
    radar = sensor_statistics(
        sv.radar_sensor_view
    )

    rows.append([
        frame,
        timestamp,
        camera_streams,
        camera_with_image,
        *lidar,
        *radar
    ])

    if frame % 100 == 0:
        print(
            f"Processed {frame} SensorView frames"
        )


# ============================================
# 6. PROCESS GROUND TRUTH
# ============================================

print("\nReading Ground Truth...")

for gt in read_osi(GT_FILE, GroundTruth):

    gt_times.append(
        get_timestamp(gt)
    )


# ============================================
# 7. CHECK SYNCHRONIZATION
# ============================================

if len(sensor_times) != len(gt_times):

    print(
        "WARNING: SensorView and Ground Truth "
        "have different frame counts!"
    )

    print(
        "SensorView frames:", len(sensor_times)
    )

    print(
        "Ground Truth frames:", len(gt_times)
    )

sync_errors_ms = [
    abs(sensor_time - gt_time) * 1000.0
    for sensor_time, gt_time
    in zip(sensor_times, gt_times)
]


# ============================================
# 8. SAVE FRAME-BY-FRAME CSV
# ============================================

header = [
    "frame",
    "timestamp_s",
    "camera_streams",
    "camera_with_image",

    "lidar_records",
    "lidar_positive",
    "lidar_positive_pct",
    "lidar_max_range_m",
    "lidar_beyond_7m",
    "lidar_beyond_10m",

    "radar_records",
    "radar_positive",
    "radar_positive_pct",
    "radar_max_range_m",
    "radar_beyond_7m",
    "radar_beyond_10m"
]

diagnostics_file = (
    ARCHIVE
    / "task09_mor100_sensor_diagnostics.csv"
)

with diagnostics_file.open(
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow(header)
    writer.writerows(rows)


# ============================================
# 9. CALCULATE SUMMARY
# ============================================

if not rows:
    raise RuntimeError(
        "No SensorView frames were found."
    )


def average(column_index):

    return (
        sum(row[column_index] for row in rows)
        / len(rows)
    )


def maximum(column_index):

    return max(
        row[column_index] for row in rows
    )


summary_rows = [
    ["Weather", "Fog"],

    ["MOR_m", 100],

    ["PrecipitationIntensity", 0],

    ["SensorViewFrames", len(sensor_times)],

    ["GroundTruthFrames", len(gt_times)],

    [
        "CameraFramesWithImage",
        sum(row[3] > 0 for row in rows)
    ],

    [
        "MeanLiDARPositivePct",
        average(6)
    ],

    [
        "MaximumLiDARRange_m",
        maximum(7)
    ],

    [
        "TotalLiDARReturnsBeyond7m",
        sum(row[8] for row in rows)
    ],

    [
        "TotalLiDARReturnsBeyond10m",
        sum(row[9] for row in rows)
    ],

    [
        "MeanRadarPositivePct",
        average(12)
    ],

    [
        "MaximumRadarRange_m",
        maximum(13)
    ],

    [
        "MaximumSensorGTTimeError_ms",
        (
            max(sync_errors_ms)
            if sync_errors_ms
            else "N/A"
        )
    ]
]


# ============================================
# 10. SAVE SUMMARY CSV
# ============================================

summary_file = (
    ARCHIVE
    / "task09_mor100_summary.csv"
)

with summary_file.open(
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Metric",
        "Value"
    ])

    writer.writerows(summary_rows)


# ============================================
# 11. DISPLAY RESULTS
# ============================================

print("\n======================================")
print("TASK 9.2.1 - RESULTS")
print("======================================")

for metric, value in summary_rows:

    print(
        f"{metric}: {value}"
    )


print("\nSaved research CSV files:")

print(diagnostics_file)
print(summary_file)

print("\nTASK 9.2.1 COMPLETED SUCCESSFULLY")
