
from pathlib import Path
import csv
import math
from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

# TASK 11.2 - Extract GEMSTAR sensor measurements

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw" / "fog_mor100"

SV_FILE = RAW / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
GT_FILE = RAW / "20261027T224313Z_gt_380_X_466_GEMSTAR.osi"

OUT = ROOT / "tests" / "Task_11_Final_Research" / "02_CSV_Data"
OUT.mkdir(parents=True, exist_ok=True)

C = 299792458.0


def read_osi(path, message_type):
    with path.open("rb") as f:
        while True:
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = int.from_bytes(header, "little")
            if size <= 0:
                raise ValueError("Invalid OSI record length")

            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Incomplete OSI record")

            message = message_type()
            message.ParseFromString(payload)
            yield message


def get_time(message):
    return message.timestamp.seconds + message.timestamp.nanos / 1e9


def position(part):
    return [
        part.position.x,
        part.position.y,
        part.position.z
    ]


def write_header(writer, columns):
    writer.writerow(columns)


lidar_file = OUT / "task11_lidar_measurements.csv"
radar_file = OUT / "task11_radar_measurements.csv"
gt_file = OUT / "task11_groundtruth_objects.csv"

print("TASK 11.2 - EXTRACTING SENSOR MEASUREMENTS")

with lidar_file.open("w", newline="", encoding="utf-8") as lf, \
     radar_file.open("w", newline="", encoding="utf-8") as rf:

    lw = csv.writer(lf)
    rw = csv.writer(rf)

    write_header(lw, [
        "frame", "time_s", "sensor_index", "ray_index",
        "range_m", "signal_strength", "object_id_diagnostic",
        "mount_x", "mount_y", "mount_z"
    ])

    write_header(rw, [
        "frame", "time_s", "sensor_index", "ray_index",
        "range_m", "signal_strength", "doppler_hz",
        "horizontal_angle_rad", "vertical_angle_rad",
        "mount_x", "mount_y", "mount_z"
    ])

    for frame, sv in enumerate(read_osi(SV_FILE, SensorView), 1):
        t = get_time(sv)

        for si, lidar in enumerate(sv.lidar_sensor_view):
            mount = position(lidar.view_configuration.mounting_position)

            for ray_index, r in enumerate(lidar.reflection):
                tof = r.time_of_flight
                strength = r.signal_strength

                if not (
                    math.isfinite(tof)
                    and math.isfinite(strength)
                    and tof > 0
                    and strength > 0
                ):
                    continue

                distance = C * tof / 2.0

                object_id = (
                    r.object_id.value
                    if r.HasField("object_id")
                    else ""
                )

                lw.writerow([
                    frame, t, si, ray_index,
                    distance, strength, object_id,
                    *mount
                ])

        for si, radar in enumerate(sv.radar_sensor_view):
            mount = position(radar.view_configuration.mounting_position)

            for ray_index, r in enumerate(radar.reflection):
                tof = r.time_of_flight
                strength = r.signal_strength

                if not (
                    math.isfinite(tof)
                    and math.isfinite(strength)
                    and tof > 0
                    and strength > 0
                ):
                    continue

                distance = C * tof / 2.0

                rw.writerow([
                    frame, t, si, ray_index,
                    distance,
                    strength,
                    r.doppler_shift,
                    r.source_horizontal_angle,
                    r.source_vertical_angle,
                    *mount
                ])

        if frame % 100 == 0:
            print(f"Processed sensor frame {frame}")

print("Extracting Ground Truth objects...")

with gt_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    write_header(writer, [
        "frame", "time_s", "object_id", "model_reference",
        "x_m", "y_m", "z_m", "yaw_rad",
        "length_m", "width_m", "height_m"
    ])

    for frame, gt in enumerate(read_osi(GT_FILE, GroundTruth), 1):
        t = get_time(gt)

        for obj in gt.moving_object:
            b = obj.base

            writer.writerow([
                frame, t, obj.id.value,
                obj.model_reference,
                b.position.x,
                b.position.y,
                b.position.z,
                b.orientation.yaw,
                b.dimension.length,
                b.dimension.width,
                b.dimension.height
            ])

print("\nOutput files:")
print(lidar_file)
print(radar_file)
print(gt_file)
print("\nTASK 11.2 EXTRACTION COMPLETED")
