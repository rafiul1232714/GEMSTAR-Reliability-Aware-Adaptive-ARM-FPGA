import csv
import math
import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

OSI = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

OUT = BASE / "C02_V2_EKF_Input_53Frames_V1"

TOTAL_FRAMES = 2122
SAMPLE_COUNT = 53
C = 299792458.0

selected = [
    round(k * (TOTAL_FRAMES - 1) / (SAMPLE_COUNT - 1))
    for k in range(SAMPLE_COUNT)
]

assert len(selected) == 53
assert len(set(selected)) == 53
assert selected[0] == 0
assert selected[-1] == 2121
assert 530 in selected

OUT.mkdir(parents=False, exist_ok=False)

summary_path = OUT / "selected_frames.csv"
lidar_path = OUT / "lidar_points.csv"
radar_path = OUT / "radar_returns.csv"

summary_fields = [
    "frame", "time_s", "lidar_valid_points",
    "radar_valid_returns", "radar_nonzero_doppler_returns",
    "camera_payload_present"
]

lidar_fields = [
    "frame", "time_s", "ray_index", "range_m",
    "x_vehicle_m", "y_vehicle_m", "z_vehicle_m",
    "signal_strength"
]

radar_fields = [
    "frame", "time_s", "return_index", "range_m",
    "x_vehicle_m", "y_vehicle_m", "z_vehicle_m",
    "horizontal_angle_rad", "vertical_angle_rad",
    "doppler_shift_raw", "signal_strength"
]

total_lidar = 0
total_radar = 0
total_nonzero = 0

with (
    OSI.open("rb") as source,
    summary_path.open("x", newline="", encoding="utf-8") as sf,
    lidar_path.open("x", newline="", encoding="utf-8") as lf,
    radar_path.open("x", newline="", encoding="utf-8") as rf
):
    sw = csv.DictWriter(sf, fieldnames=summary_fields)
    lw = csv.DictWriter(lf, fieldnames=lidar_fields)
    rw = csv.DictWriter(rf, fieldnames=radar_fields)

    sw.writeheader()
    lw.writeheader()
    rw.writeheader()

    chosen = set(selected)

    for frame in range(TOTAL_FRAMES):
        header = source.read(4)

        if len(header) != 4:
            raise RuntimeError(f"Missing OSI header at frame {frame}")

        size = struct.unpack("<I", header)[0]

        if size <= 0:
            raise RuntimeError(f"Invalid OSI size at frame {frame}")

        if frame not in chosen:
            source.seek(size, 1)
            continue

        payload = source.read(size)

        if len(payload) != size:
            raise RuntimeError(f"Incomplete OSI frame {frame}")

        sv = SensorView()
        sv.ParseFromString(payload)

        if len(sv.lidar_sensor_view) != 1:
            raise RuntimeError(f"Unexpected LiDAR count: {frame}")

        if len(sv.radar_sensor_view) != 1:
            raise RuntimeError(f"Unexpected Radar count: {frame}")

        time_s = (
            sv.timestamp.seconds +
            sv.timestamp.nanos * 1e-9
        )

        lidar = sv.lidar_sensor_view[0]
        radar = sv.radar_sensor_view[0]

        cfg = lidar.view_configuration

        nh = int(cfg.number_of_rays_horizontal)
        nv = int(cfg.number_of_rays_vertical)

        if (nh, nv) != (251, 21):
            raise RuntimeError(f"LiDAR grid changed at frame {frame}")

        if len(lidar.reflection) != nh * nv:
            raise RuntimeError(f"LiDAR ray count mismatch: {frame}")

        lidar_count = 0
        radar_count = 0
        nonzero_count = 0

        for i, ref in enumerate(lidar.reflection):
            tof = float(ref.time_of_flight)

            if not math.isfinite(tof) or tof <= 0:
                continue

            distance = C * tof / 2

            if not math.isfinite(distance) or distance <= 0.01:
                continue

            hi = i % nh
            vi = i // nh

            yaw = (
                -cfg.field_of_view_horizontal / 2
                + hi * cfg.field_of_view_horizontal / (nh - 1)
            )

            pitch = (
                -cfg.field_of_view_vertical / 2
                + vi * cfg.field_of_view_vertical / (nv - 1)
            )

            sx = distance * math.cos(pitch) * math.cos(yaw)
            sy = distance * math.cos(pitch) * math.sin(yaw)
            sz = distance * math.sin(pitch)

            x = 2.6 + sx
            y = -sy
            z = 0.7 + sz

            lw.writerow({
                "frame": frame,
                "time_s": time_s,
                "ray_index": i,
                "range_m": distance,
                "x_vehicle_m": x,
                "y_vehicle_m": y,
                "z_vehicle_m": z,
                "signal_strength": ref.signal_strength
            })

            lidar_count += 1

        for i, ref in enumerate(radar.reflection):
            tof = float(ref.time_of_flight)

            if not math.isfinite(tof) or tof <= 0:
                continue

            distance = C * tof / 2

            yaw = float(ref.source_horizontal_angle)
            pitch = float(ref.source_vertical_angle)
            doppler = float(ref.doppler_shift)

            if not all(
                math.isfinite(v)
                for v in (distance, yaw, pitch, doppler)
            ):
                continue

            if distance <= 0.01:
                continue

            x = (
                2.0
                + distance * math.cos(pitch) * math.cos(yaw)
            )
            y = (
                -distance * math.cos(pitch) * math.sin(yaw)
            )
            z = 0.8 + distance * math.sin(pitch)

            rw.writerow({
                "frame": frame,
                "time_s": time_s,
                "return_index": i,
                "range_m": distance,
                "x_vehicle_m": x,
                "y_vehicle_m": y,
                "z_vehicle_m": z,
                "horizontal_angle_rad": yaw,
                "vertical_angle_rad": pitch,
                "doppler_shift_raw": doppler,
                "signal_strength": ref.signal_strength
            })

            radar_count += 1

            if abs(doppler) > 1e-9:
                nonzero_count += 1

        camera_present = any(
            len(view.image_data) > 0
            for view in sv.camera_sensor_view
        )

        sw.writerow({
            "frame": frame,
            "time_s": time_s,
            "lidar_valid_points": lidar_count,
            "radar_valid_returns": radar_count,
            "radar_nonzero_doppler_returns": nonzero_count,
            "camera_payload_present": camera_present
        })

        total_lidar += lidar_count
        total_radar += radar_count
        total_nonzero += nonzero_count

        print(
            f"FRAME={frame} "
            f"TIME_S={time_s:.6f} "
            f"LIDAR={lidar_count} "
            f"RADAR={radar_count} "
            f"NONZERO_DOPPLER={nonzero_count}"
        )

    if source.read(1):
        raise RuntimeError("Unexpected data after 2122 frames")

print("\n=== TASK 24.9.1 SUMMARY ===")
print("SAMPLED_FRAMES=", len(selected))
print("FRAME530_INCLUDED=", 530 in selected)
print("LIDAR_MEASUREMENT_ROWS=", total_lidar)
print("RADAR_MEASUREMENT_ROWS=", total_radar)
print("NONZERO_DOPPLER_ROWS=", total_nonzero)
print("OUTPUT=", OUT)
print("OBJECT_IDS_USED=NO")
print("DOPPLER_CONVERTED_TO_SPEED=NO")
print("TRACK_ASSOCIATION_PERFORMED=NO")
print("ORIGINAL_OSI_MODIFIED=NO")
print("TASK24_09_01_EXTRACTION_COMPLETE")