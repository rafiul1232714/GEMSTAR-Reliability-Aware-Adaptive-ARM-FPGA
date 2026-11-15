import argparse
import csv
import hashlib
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
OUT = ROOT / "tests" / "Task_28_Final_Research" / "02_CSV_Data"

FIELDS = [
    "Scenario", "Recording", "Frame", "Timestamp_ns",
    "DT_ms", "CameraPresent", "LiDARPresent",
    "RadarPresent", "CameraWidth", "CameraHeight",
    "CameraBytes", "LiDARRays", "RadarRays",
    "CameraPayloadRepeated", "LiDARPayloadRepeated",
    "RadarPayloadRepeated"
]

def digest(view):
    data = view.SerializeToString(deterministic=True)
    return hashlib.blake2b(data, digest_size=16).hexdigest()

def process(scenario, max_frames):
    folder = RAW / scenario

    if not folder.is_dir():
        raise RuntimeError(f"Missing scenario folder: {folder}")

    sources = sorted(folder.glob("*_sv_*.osi"))

    if len(sources) != 1:
        raise RuntimeError(
            f"Expected one SV recording, found {len(sources)}"
        )

    source = sources[0]
    OUT.mkdir(parents=True, exist_ok=True)

    dest = OUT / f"task28_2G5_{scenario}_first{max_frames}_frames.csv"

    if dest.exists():
        raise RuntimeError(
            f"Output already exists; not overwriting: {dest}"
        )

    temp = dest.with_suffix(".csv.partial")

    if temp.exists():
        raise RuntimeError(f"Existing partial output: {temp}")

    previous_timestamp = None
    previous_hashes = [None, None, None]
    rows_written = 0
    repeated_counts = [0, 0, 0]

    try:
        with source.open("rb") as stream, temp.open(
            "x", newline="", encoding="utf-8"
        ) as output:

            writer = csv.DictWriter(output, fieldnames=FIELDS)
            writer.writeheader()

            for frame in range(max_frames):
                header = stream.read(4)

                if not header:
                    break

                if len(header) != 4:
                    raise RuntimeError("Truncated OSI header")

                size = struct.unpack("<I", header)[0]

                if not 0 < size <= 100_000_000:
                    raise RuntimeError(
                        f"Invalid OSI frame size: {size}"
                    )

                payload = stream.read(size)

                if len(payload) != size:
                    raise RuntimeError(
                        f"Truncated OSI payload at frame {frame}"
                    )

                sv = osi_sensorview_pb2.SensorView()
                sv.ParseFromString(payload)

                ts = (
                    int(sv.timestamp.seconds) * 1_000_000_000
                    + int(sv.timestamp.nanos)
                )

                if previous_timestamp is None:
                    dt_ms = ""
                else:
                    dt_ms = (ts - previous_timestamp) / 1_000_000

                    if dt_ms <= 0:
                        raise RuntimeError(
                            f"Nonmonotonic timestamp at frame {frame}"
                        )

                previous_timestamp = ts

                groups = [
                    sv.camera_sensor_view,
                    sv.lidar_sensor_view,
                    sv.radar_sensor_view
                ]

                present = [int(len(group) > 0) for group in groups]
                repeated = [0, 0, 0]

                for index, group in enumerate(groups):
                    if len(group) == 0:
                        previous_hashes[index] = None
                        continue

                    current_hash = digest(group[0])

                    if previous_hashes[index] == current_hash:
                        repeated[index] = 1
                        repeated_counts[index] += 1

                    previous_hashes[index] = current_hash

                camera = groups[0][0] if present[0] else None
                lidar = groups[1][0] if present[1] else None
                radar = groups[2][0] if present[2] else None

                width = (
                    int(camera.view_configuration.number_of_pixels_horizontal)
                    if camera else 0
                )
                height = (
                    int(camera.view_configuration.number_of_pixels_vertical)
                    if camera else 0
                )

                writer.writerow({
                    "Scenario": scenario,
                    "Recording": source.name,
                    "Frame": frame,
                    "Timestamp_ns": ts,
                    "DT_ms": dt_ms,
                    "CameraPresent": present[0],
                    "LiDARPresent": present[1],
                    "RadarPresent": present[2],
                    "CameraWidth": width,
                    "CameraHeight": height,
                    "CameraBytes": (
                        len(camera.image_data) if camera else 0
                    ),
                    "LiDARRays": (
                        len(lidar.reflection) if lidar else 0
                    ),
                    "RadarRays": (
                        len(radar.reflection) if radar else 0
                    ),
                    "CameraPayloadRepeated": repeated[0],
                    "LiDARPayloadRepeated": repeated[1],
                    "RadarPayloadRepeated": repeated[2]
                })

                rows_written += 1

        temp.rename(dest)

    except Exception:
        if temp.exists():
            temp.unlink()
        raise

    print("\n=== TASK 28.2G.5 RESULTS ===")
    print(f"Scenario: {scenario}")
    print(f"Recording: {source.name}")
    print(f"Frames decoded: {rows_written}")
    print(f"Camera repeated: {repeated_counts[0]}")
    print(f"LiDAR repeated: {repeated_counts[1]}")
    print(f"Radar repeated: {repeated_counts[2]}")
    print(f"Saved CSV: {dest}")
    print("STATUS: SUCCESS")
    print("NOTE: Payload hashes do not prove acquisition-time freshness.")
    print("NOTE: This is a pilot, not complete sensor validation.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="baseline_clear")
    parser.add_argument("--max-frames", type=int, default=100)
    args = parser.parse_args()

    if args.max_frames < 1:
        parser.error("--max-frames must be positive")

    process(args.scenario, args.max_frames)
