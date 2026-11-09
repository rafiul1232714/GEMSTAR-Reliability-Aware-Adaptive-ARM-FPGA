import struct
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView
from task23_11F_lidar_reliability import score_lidar_frame


OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")

DATASETS = [
    (
        "CLEAR",
        "20261105T213845Z_sv_380_X_13819_T23_11E_CLEAR.osi",
        5090,
        "VALID"
    ),
    (
        "FOG100",
        "20261105T220440Z_sv_380_X_12386_T23_11E_FOG100.osi",
        5090,
        "VALID"
    ),
    (
        "FOG20",
        "20261105T215332Z_sv_380_X_14597_T23_11E_FOG20.osi",
        0,
        "NO_RETURNS"
    ),
]


def read_frame(stream):
    header = stream.read(4)

    if len(header) != 4:
        raise RuntimeError("Missing or incomplete frame header")

    length = struct.unpack("<I", header)[0]

    if length <= 0:
        raise RuntimeError("Invalid OSI frame length")

    payload = stream.read(length)

    if len(payload) != length:
        raise RuntimeError("Incomplete OSI frame payload")

    frame = SensorView()
    frame.ParseFromString(payload)
    return frame


for weather, filename, expected_positive, expected_status in DATASETS:
    path = OUTPUT / filename

    if not path.is_file():
        raise RuntimeError(f"Missing file: {path}")

    print(f"\n=== {weather} ===")

    previous_timestamp = None

    with path.open("rb") as stream:
        for frame_index in range(5):
            frame = read_frame(stream)

            timestamp = (
                frame.timestamp.seconds
                + frame.timestamp.nanos / 1_000_000_000
            )

            lidar = (
                frame.lidar_sensor_view[0]
                if len(frame.lidar_sensor_view) == 1
                else None
            )

            result = score_lidar_frame(
                lidar,
                timestamp,
                previous_timestamp
            )

            if result.status != expected_status:
                raise RuntimeError(
                    f"{weather} frame {frame_index}: "
                    f"unexpected status {result.status}"
                )

            if result.positive_returns != expected_positive:
                raise RuntimeError(
                    f"{weather} frame {frame_index}: "
                    f"unexpected count {result.positive_returns}"
                )

            expected_score = expected_positive / 5271

            if result.availability_score is None:
                raise RuntimeError("Unexpected undefined score")

            if abs(result.availability_score - expected_score) > 1e-12:
                raise RuntimeError("Availability score mismatch")

            print(
                f"FRAME={frame_index} "
                f"STATUS={result.status} "
                f"POSITIVE={result.positive_returns} "
                f"TOTAL={result.total_reflections} "
                f"RELIABILITY={result.availability_score:.6f}"
            )

            previous_timestamp = timestamp

    print(f"{weather}_RELIABILITY_PASS")


print("\nTOTAL_TESTED_FRAMES=15")
print("TASK23_11F_04A_REAL_OSI_RELIABILITY_PASS")
