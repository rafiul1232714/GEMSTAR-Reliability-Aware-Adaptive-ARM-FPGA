import hashlib
import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi"
)

TARGETS = {1, 2, 25, 100, 300, 573}

frame = 0
results = {}

with SOURCE.open("rb") as file:
    while True:
        header = file.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete frame header")

        size = struct.unpack("<I", header)[0]

        if size <= 0 or size > 100_000_000:
            raise RuntimeError("Invalid frame size")

        payload = file.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete frame payload")

        frame += 1

        if frame not in TARGETS:
            continue

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        hasher = hashlib.sha256()
        count = 0

        for view in message.lidar_sensor_view:
            for reflection in view.reflection:
                hasher.update(
                    struct.pack(
                        "<dd",
                        float(reflection.time_of_flight),
                        float(reflection.signal_strength)
                    )
                )
                count += 1

        results[frame] = {
            "hash": hasher.hexdigest(),
            "reflections": count
        }

print("\n=== RAW LIDAR FRAME COMPARISON ===")

for number in sorted(results):
    result = results[number]

    print(
        f"Frame {number}: "
        f"{result['reflections']} reflections | "
        f"SHA256={result['hash']}"
    )

unique_hashes = len({
    result["hash"]
    for result in results.values()
})

print("\nSelected frames:", len(results))
print("Unique reflection hashes:", unique_hashes)

if len(results) != len(TARGETS):
    print("Status: INCOMPLETE_FRAME_SAMPLE")
elif unique_hashes == 1:
    print("Status: IDENTICAL_SAMPLED_REFLECTIONS")
else:
    print("Status: REFLECTION_DATA_VARIATION_DETECTED")
