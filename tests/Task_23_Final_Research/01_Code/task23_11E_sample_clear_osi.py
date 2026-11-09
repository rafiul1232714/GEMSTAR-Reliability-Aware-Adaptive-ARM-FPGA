import struct
import hashlib
import math
import sys

from osi3.osi_sensorview_pb2 import SensorView

path = sys.argv[1]

# Pass 1: Count frames without retaining their payloads.
frame_count = 0

with open(path, "rb") as f:
    while True:
        prefix = f.read(4)

        if not prefix:
            break

        if len(prefix) != 4:
            raise RuntimeError("Incomplete frame-length prefix")

        size = struct.unpack("<I", prefix)[0]

        if size == 0:
            raise RuntimeError("Zero-length OSI frame")

        f.seek(size, 1)
        if f.tell() > f.seek(0, 2):
            raise RuntimeError("Frame extends beyond EOF")

        frame_count += 1

        f.seek(0, 2) if False else None

if frame_count == 0:
    raise RuntimeError("No OSI frames found")

targets = set([
    0,
    frame_count // 4,
    frame_count // 2,
    (3 * frame_count) // 4,
    frame_count - 1
])

print("TOTAL_FRAMES=" + str(frame_count))
print("SAMPLED_FRAME_INDICES=" + str(sorted(targets)))

# Pass 2: Decode only the selected frames.
with open(path, "rb") as f:
    for index in range(frame_count):
        prefix = f.read(4)
        size = struct.unpack("<I", prefix)[0]

        if index not in targets:
            f.seek(size, 1)
            continue

        data = f.read(size)
        if len(data) != size:
            raise RuntimeError("Truncated frame")

        sv = SensorView()
        sv.ParseFromString(data)

        timestamp = sv.timestamp.seconds + (
            sv.timestamp.nanos / 1e9
        )

        lidar_views = len(sv.lidar_sensor_view)

        print(
            "\nFRAME={} TIMESTAMP={:.9f} LIDAR_VIEWS={}".format(
                index, timestamp, lidar_views
            )
        )

        for lidar in sv.lidar_sensor_view:
            reflections = lidar.view_configuration
            measurements = lidar.reflection

            valid = sum(
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

            print(
                "REFLECTIONS={} POSITIVE_RETURNS={} COVERAGE={:.4f}%".format(
                    len(measurements),
                    valid,
                    100.0 * valid / len(measurements)
                    if measurements else 0.0
                )
            )

            print("REFLECTION_SHA256=" + digest.hexdigest())

print("\nTASK23_11E_CLEAR_SAMPLE_DECODE_PASS")
