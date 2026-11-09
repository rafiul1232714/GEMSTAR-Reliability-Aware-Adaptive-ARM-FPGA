import csv
import gzip
import hashlib
import math
import os
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_24_Final_Research"
)

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261105T231919Z_sv_380_X_372_GEMSTAR.osi"
)

DATA = ROOT / "02_CSV_Data"
PROCESSED = ROOT / "08_Processed_Data"

CAMERA_OUT = PROCESSED / "task24_03_05C_camera_metadata_372frames.csv"
LIDAR_OUT = PROCESSED / "task24_03_05C_lidar_measurements_372frames.csv.gz"
RADAR_OUT = PROCESSED / "task24_03_05C_radar_measurements_372frames.csv.gz"

OUTPUTS = [CAMERA_OUT, LIDAR_OUT, RADAR_OUT]

C = 299792458.0
MIN_RANGE_M = 0.01

MOUNTS = {
    "LiDAR": (2.6, 0.0, 0.7),
    "Radar": (2.0, 0.0, 0.8),
}

CAMERA_FIELDS = [
    "Frame", "Timestamp_ns", "Width", "Height",
    "ImageBytes", "ImageSHA256", "PayloadFreshness",
    "IndependentAcquisitionTimeKnown"
]

POINT_FIELDS = [
    "Frame", "Timestamp_ns", "Sensor", "RayIndex",
    "HorizontalIndex", "VerticalIndex",
    "Yaw_rad", "Pitch_rad",
    "TOF_s", "Range_m", "SignalStrength",
    "Doppler_Hz", "RadialVelocity_mps",
    "X_sensor_UE_m", "Y_sensor_UE_m", "Z_sensor_UE_m",
    "X_vehicle_OSI_m", "Y_vehicle_OSI_m", "Z_vehicle_OSI_m",
    "ReturnCategory", "PayloadFreshness",
    "DopplerReviewFlag", "CoordinateModel"
]

def read_csv_indexed(path):
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    indexed = {int(row["Frame"]): row for row in rows}

    if len(rows) != 372 or set(indexed) != set(range(372)):
        raise RuntimeError(f"Invalid reliability manifest: {path}")

    return indexed

def extract_points(frame, timestamp, sensor, view, writer, quality):
    cfg = view.view_configuration

    nh = int(cfg.number_of_rays_horizontal)
    nv = int(cfg.number_of_rays_vertical)

    if nh < 2 or nv < 2 or len(view.reflection) != nh * nv:
        raise RuntimeError(
            f"Invalid {sensor} grid at frame {frame}"
        )

    expected = (251, 21) if sensor == "LiDAR" else (10, 10)

    if (nh, nv) != expected:
        raise RuntimeError(
            f"Unexpected {sensor} dimensions: {(nh, nv)}"
        )

    hfov = float(cfg.field_of_view_horizontal)
    vfov = float(cfg.field_of_view_vertical)

    mount_x, mount_y, mount_z = MOUNTS[sensor]

    freshness_key = (
        "LiDARPayloadFreshness"
        if sensor == "LiDAR"
        else "RadarPayloadFreshness"
    )

    if sensor == "Radar":
        carrier = float(cfg.emitter_frequency)

        if not math.isfinite(carrier) or carrier <= 0:
            raise RuntimeError("Invalid Radar carrier frequency")
    else:
        carrier = None

    candidate_count = 0

    for index, reflection in enumerate(view.reflection):
        hi = index % nh
        vi = index // nh

        if sensor == "Radar":
            yaw = float(reflection.source_horizontal_angle)
            pitch = float(reflection.source_vertical_angle)
        else:
            yaw = -hfov / 2 + hi * hfov / (nh - 1)
            pitch = -vfov / 2 + vi * vfov / (nv - 1)

        tof = float(reflection.time_of_flight)
        signal = float(reflection.signal_strength)
        doppler = float(reflection.doppler_shift)

        if not all(math.isfinite(value) for value in (
            yaw, pitch, tof, signal, doppler
        )):
            raise RuntimeError(
                f"Nonfinite {sensor} measurement: "
                f"frame={frame}, ray={index}"
            )

        distance = C * tof / 2

        if tof <= 0:
            category = "NO_HIT_OR_ZERO_TOF"
        elif distance <= MIN_RANGE_M:
            category = "NEAR_ZERO_DIAGNOSTIC"
        else:
            category = "CANDIDATE"
            candidate_count += 1

        x = distance * math.cos(pitch) * math.cos(yaw)
        y = distance * math.cos(pitch) * math.sin(yaw)
        z = distance * math.sin(pitch)

        if sensor == "Radar":
            radial_velocity = C * doppler / (2 * carrier)
            doppler_flag = quality["RadarDopplerReviewFlag"]
        else:
            radial_velocity = ""
            doppler_flag = "NOT_MEASURED"

        writer.writerow({
            "Frame": frame,
            "Timestamp_ns": timestamp,
            "Sensor": sensor,
            "RayIndex": index,
            "HorizontalIndex": hi,
            "VerticalIndex": vi,
            "Yaw_rad": yaw,
            "Pitch_rad": pitch,
            "TOF_s": tof,
            "Range_m": distance,
            "SignalStrength": signal,
            "Doppler_Hz": doppler,
            "RadialVelocity_mps": radial_velocity,
            "X_sensor_UE_m": x,
            "Y_sensor_UE_m": y,
            "Z_sensor_UE_m": z,
            "X_vehicle_OSI_m": x + mount_x,
            "Y_vehicle_OSI_m": -y + mount_y,
            "Z_vehicle_OSI_m": z + mount_z,
            "ReturnCategory": category,
            "PayloadFreshness": quality[freshness_key],
            "DopplerReviewFlag": doppler_flag,
            "CoordinateModel": "NOMINAL_UNCALIBRATED"
        })

    return nh * nv, candidate_count

def main():
    if not SOURCE.is_file():
        raise RuntimeError(f"Missing recording: {SOURCE}")

    if not PROCESSED.is_dir():
        raise RuntimeError(f"Missing processed-data folder: {PROCESSED}")

    for path in OUTPUTS:
        if path.exists() or path.with_name(path.name + ".partial").exists():
            raise RuntimeError(f"Output already exists: {path}")

    manifest = read_csv_indexed(
        DATA / "task24_03_04_sensor_reliability_manifest.csv"
    )

    # Temporary files prevent incomplete outputs from being
    # mistaken for validated research datasets.
    temporary = [
        path.with_name(path.name + ".partial")
        for path in OUTPUTS
    ]

    camera_count = 0
    lidar_count = 0
    radar_count = 0
    lidar_candidates = 0
    radar_candidates = 0

    previous_timestamp = None

    try:
        with temporary[0].open("x", newline="", encoding="utf-8") as fc, \
             gzip.open(temporary[1], "xt", encoding="utf-8",
                       newline="", compresslevel=3) as fl, \
             gzip.open(temporary[2], "xt", encoding="utf-8",
                       newline="", compresslevel=3) as fr:

            wc = csv.DictWriter(fc, fieldnames=CAMERA_FIELDS)
            wl = csv.DictWriter(fl, fieldnames=POINT_FIELDS)
            wr = csv.DictWriter(fr, fieldnames=POINT_FIELDS)

            wc.writeheader()
            wl.writeheader()
            wr.writeheader()

            with SOURCE.open("rb") as stream:
                while True:
                    header = stream.read(4)

                    if not header:
                        break

                    if len(header) != 4:
                        raise RuntimeError("Incomplete OSI header")

                    size = struct.unpack("<I", header)[0]

                    if not 0 < size <= 100_000_000:
                        raise RuntimeError("Invalid OSI frame size")

                    payload = stream.read(size)

                    if len(payload) != size:
                        raise RuntimeError("Incomplete OSI payload")

                    sv = osi_sensorview_pb2.SensorView()
                    sv.ParseFromString(payload)

                    frame = camera_count

                    if frame >= 372:
                        raise RuntimeError("More than 372 frames")

                    if any(
                        len(getattr(sv, field)) != 1
                        for field in (
                            "camera_sensor_view",
                            "lidar_sensor_view",
                            "radar_sensor_view"
                        )
                    ):
                        raise RuntimeError(
                            f"Sensor count mismatch at frame {frame}"
                        )

                    timestamp = (
                        int(sv.timestamp.seconds) * 1_000_000_000
                        + int(sv.timestamp.nanos)
                    )

                    if (
                        previous_timestamp is not None
                        and timestamp <= previous_timestamp
                    ):
                        raise RuntimeError("Nonmonotonic timestamp")

                    previous_timestamp = timestamp
                    quality = manifest[frame]

                    if str(timestamp) != quality["Timestamp_ns"]:
                        raise RuntimeError(
                            f"Manifest timestamp mismatch at {frame}"
                        )

                    camera = sv.camera_sensor_view[0]
                    cfg = camera.view_configuration

                    width = int(cfg.number_of_pixels_horizontal)
                    height = int(cfg.number_of_pixels_vertical)
                    image = bytes(camera.image_data)

                    if (width, height) != (640, 480):
                        raise RuntimeError("Unexpected Camera resolution")

                    if len(image) != width * height * 3:
                        raise RuntimeError("Unexpected Camera image size")

                    wc.writerow({
                        "Frame": frame,
                        "Timestamp_ns": timestamp,
                        "Width": width,
                        "Height": height,
                        "ImageBytes": len(image),
                        "ImageSHA256": hashlib.sha256(image).hexdigest(),
                        "PayloadFreshness":
                            quality["CameraPayloadFreshness"],
                        "IndependentAcquisitionTimeKnown": 0
                    })

                    lidar_n, lidar_valid = extract_points(
                        frame, timestamp, "LiDAR",
                        sv.lidar_sensor_view[0], wl, quality
                    )

                    radar_n, radar_valid = extract_points(
                        frame, timestamp, "Radar",
                        sv.radar_sensor_view[0], wr, quality
                    )

                    camera_count += 1
                    lidar_count += lidar_n
                    radar_count += radar_n
                    lidar_candidates += lidar_valid
                    radar_candidates += radar_valid

                    if frame in (0, 9, 49, 99, 149, 199,
                                 249, 299, 349, 371):
                        print(
                            f"FRAME={frame} "
                            f"LIDAR_ROWS={lidar_count} "
                            f"RADAR_ROWS={radar_count}",
                            flush=True
                        )

        if camera_count != 372:
            raise RuntimeError(
                f"Incorrect frame count: {camera_count}"
            )

        if lidar_count != 1_960_812:
            raise RuntimeError(
                f"Incorrect LiDAR count: {lidar_count}"
            )

        if radar_count != 37_200:
            raise RuntimeError(
                f"Incorrect Radar count: {radar_count}"
            )

        # Verify gzip streams can be opened and headers match.
        for path in temporary[1:]:
            with gzip.open(path, "rt", encoding="utf-8") as f:
                header = next(csv.reader(f))
                if header != POINT_FIELDS:
                    raise RuntimeError("Compressed CSV header mismatch")

        for temp, final in zip(temporary, OUTPUTS):
            os.rename(temp, final)

    except Exception:
        for path in temporary:
            if path.exists():
                path.unlink()
        raise

    print("\n=== TASK 24.3.5.C FULL EXTRACTION ===")
    print(f"CAMERA_FRAMES={camera_count}")
    print(f"LIDAR_REFLECTIONS={lidar_count}")
    print(f"RADAR_REFLECTIONS={radar_count}")
    print(f"LIDAR_CANDIDATES={lidar_candidates}")
    print(f"RADAR_CANDIDATES={radar_candidates}")

    for path in OUTPUTS:
        print(f"OUTPUT={path}")
        print(f"OUTPUT_BYTES={path.stat().st_size}")

    print("OBJECT_IDENTITIES_EXPORTED=NO")
    print("RAW_OSI_MODIFIED=NO")
    print("GEOMETRY=NOMINAL_UNCALIBRATED")
    print("TASK24_03_05C_FULL_EXTRACTION_PASS")

if __name__ == "__main__":
    main()