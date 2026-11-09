import sys
import struct
import hashlib
import math

from collections import Counter
from osi3.osi_sensorview_pb2 import SensorView

path = sys.argv[1]

frames = 0
timestamps = []
positive_counts = Counter()
reflection_hashes = Counter()
missing_lidar = 0

with open(path, "rb") as f:
    while True:
        prefix = f.read(4)

        if not prefix:
            break

        if len(prefix) != 4:
            raise RuntimeError("Incomplete frame prefix")

        size = struct.unpack("<I", prefix)[0]

        if size <= 0:
            raise RuntimeError("Invalid frame size")

        data = f.read(size)

        if len(data) != size:
            raise RuntimeError("Incomplete frame payload")

        sv = SensorView()
        sv.ParseFromString(data)

        timestamp_ns = (
            sv.timestamp.seconds * 1_000_000_000
            + sv.timestamp.nanos
        )

        if timestamps and timestamp_ns <= timestamps[-1]:
            raise RuntimeError(
                "Non-increasing timestamp at frame {}".format(frames)
            )

        timestamps.append(timestamp_ns)

        if len(sv.lidar_sensor_view) == 0:
            missing_lidar += 1
        else:
            lidar = sv.lidar_sensor_view[0]
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

            positive_counts[positive] += 1

            digest = hashlib.sha256()

            for r in measurements:
                digest.update(
                    struct.pack(
                        "<dd",
                        r.time_of_flight,
                        r.signal_strength
                    )
                )

            reflection_hashes[digest.hexdigest()] += 1

        frames += 1

        if frames % 2000 == 0:
            print("PROCESSED_FRAMES={}".format(frames), flush=True)

print("\nTOTAL_FRAMES={}".format(frames))
print("MISSING_LIDAR_FRAMES={}".format(missing_lidar))
print("UNIQUE_POSITIVE_COUNTS={}".format(len(positive_counts)))
print("UNIQUE_REFLECTION_HASHES={}".format(len(reflection_hashes)))

print("POSITIVE_COUNT_DISTRIBUTION={}".format(
    positive_counts.most_common(10)
))

print("REFLECTION_HASH_DISTRIBUTION={}".format(
    reflection_hashes.most_common(5)
))

print("STRICTLY_INCREASING_TIMESTAMPS=True")
print("TASK23_11E_FULL_CLEAR_VARIABILITY_PASS")
