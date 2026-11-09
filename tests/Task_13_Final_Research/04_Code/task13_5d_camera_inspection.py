
# TASK 13.5D - CAMERA IMAGE INSPECTION
# Inspect the CameraSensorView structure and payload
# from the original MOR100 recording.
#
# Read-only. No previous research data is overwritten.

from pathlib import Path
import struct

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

OSI_FILE = (
    ROOT / "data" / "raw" / "fog_mor100" /
    "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

FRAME = 150


def read_messages(path):
    with path.open("rb") as f:
        while True:
            header = f.read(4)
            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]
            data = f.read(size)

            if len(data) != size:
                raise RuntimeError("Incomplete OSI message")

            sv = SensorView()
            sv.ParseFromString(data)
            yield sv


print("\n===== TASK 13.5D - CAMERA INSPECTION =====")

for frame, sv in enumerate(read_messages(OSI_FILE), 1):
    if frame != FRAME:
        continue

    print("Frame:", frame)
    print(
        "Timestamp:",
        sv.timestamp.seconds + sv.timestamp.nanos / 1e9
    )

    print("Camera views:", len(sv.camera_sensor_view))

    for i, camera in enumerate(sv.camera_sensor_view):
        print(f"\n===== CAMERA {i} =====")

        print("Message size:", camera.ByteSize(), "bytes")

        print("\nAvailable protobuf fields:")
        for field in camera.DESCRIPTOR.fields:
            print(
                f"  {field.name}: "
                f"{field.message_type.full_name if field.message_type else field.type}"
            )

        print("\nPopulated fields:")
        for field, value in camera.ListFields():
            if isinstance(value, bytes):
                print(
                    f"  {field.name}: binary payload, "
                    f"{len(value)} bytes"
                )
            elif field.is_repeated:
                print(
                    f"  {field.name}: "
                    f"{len(value)} elements"
                )
            elif hasattr(value, "ByteSize"):
                print(
                    f"  {field.name}: nested message, "
                    f"{value.ByteSize()} bytes"
                )
            else:
                print(f"  {field.name}: {value}")

    break

else:
    raise RuntimeError(f"Frame {FRAME} not found")

print("\nTASK 13.5D COMPLETED")
