import os
import sys
import struct
import hashlib
import math

from osi3.osi_sensorview_pb2 import SensorView

path = sys.argv[1]
file_size = os.path.getsize(path)

frame_count = 0

# PASS 1: Count frames without decoding or loading them.
with open(path, "rb") as f:
    while f.tell() < file_size:
        prefix = f.read(4)

        if len(prefix) != 4:
            raise RuntimeError(
                "Incomplete frame prefix at index {}".format(frame_count)
            )

        size = struct.unpack("<I", prefix)[0]

        if size == 0:
            raise RuntimeError(
                "Zero-length frame at index {}".format(frame_count)
            )

        if f.tell() + size > file_size:
            raise RuntimeError(
                "Truncated frame at index {}".format(frame_count)
            )

        f.seek(size, os.SEEK_CUR)
        frame_count += 1

if frame_count == 0:
    raise RuntimeError("No OSI frames found")

targets = sorted(set([
    0,
    frame_count // 4,
    frame_count // 2,
    (3 * frame_count) // 4,
    frame_count - 1
]))

print("FILE_BYTES={}".format(file_size))
print("TOTAL_FRAMES={}".format(frame_count))
print("SAMPLED_FRAME_INDICES={}".format(targets))

timestamps = []
hashes = []

# PASS 2: Decode only five selected frames.
with open(path, "rb") as f:
    for index in range(frame_count):
        size = struct.unpack("<I", f.read(4))[0]

        if index not in targets:
            f.seek(size, os.SEEK_CUR)
            continue

        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Truncated selected frame")

        sv = SensorView()
        sv.ParseFromString(payload)

        timestamp = (
            sv.timestamp.seconds +
            sv.timestamp.nanos / 1e9
        )

        timestamps.append(timestamp)

        print(
            "\nFRAME={} TIMESTAMP={:.9f} LIDAR_VIEWS={}".format(
                index,
                timestamp,
                len(sv.lidar_sensor_view)
            )
        )

        if len(sv.lidar_sensor_view) == 0:
            raise RuntimeError(
                "Selected frame has no LiDAR view"
            )

        for lidar in sv.lidar_sensor_view:
            measurements = lidar.reflection

            positive = sum(
                1 for r in measurements
                if (
                    math.isfinite(r.time_of_flight)
                    and math.isfinite(r.signal_strength)
                    and r.time_of_flight > 0
                    and r.signal_strength > 0
                )
            )

            digest = hashlib.sha256()

            for r in measurements:
                digest.update(
                    struct.pack(
                        "<dd",
                        r.time_of_flight,
                        r.signal_strength
                    )
                )

            reflection_hash = digest.hexdigest()
            hashes.append(reflection_hash)

            coverage = (
                100.0 * positive / len(measurements)
                if measurements else 0.0
            )

            print("REFLECTIONS={}".format(len(measurements)))
            print("POSITIVE_RETURNS={}".format(positive))
            print("COVERAGE={:.6f}%".format(coverage))
            print("REFLECTION_SHA256={}".format(reflection_hash))

if any(b <= a for a, b in zip(timestamps, timestamps[1:])):
    raise RuntimeError("Sampled timestamps are not increasing")

print("\nSAMPLED_TIMESTAMPS_INCREASING=True")
print("UNIQUE_REFLECTION_HASHES={}".format(len(set(hashes))))
print("TASK23_11E_CLEAR_SAMPLE_DECODE_FIXED_PASS")
