import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

output = Path(r"E:\GEMSTAR_Project\gemstar\Output")

files = sorted(
    output.glob("*_sv_*_T23_12_CAMERA_CLEAR.osi")
)

if len(files) != 1:
    raise RuntimeError(
        f"Expected one Clear SensorView file, found {len(files)}"
    )

path = files[0]

print("FILE:", path.name)
print("FILE_BYTES:", path.stat().st_size)

results = []

with path.open("rb") as f:
    for frame_index in range(3):

        header = f.read(4)

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI frame header")

        size = struct.unpack("<I", header)[0]

        if size == 0 or size > 100_000_000:
            raise RuntimeError(
                f"Unexpected frame size: {size}"
            )

        data = f.read(size)

        if len(data) != size:
            raise RuntimeError("Incomplete OSI message")

        message = SensorView()
        message.ParseFromString(data)

        camera_count = len(message.camera_sensor_view)

        if camera_count == 0:
            raise RuntimeError(
                f"No Camera payload in frame {frame_index}"
            )

        image = message.camera_sensor_view[0].image_data

        image_bytes = len(image)

        print(
            f"FRAME={frame_index} "
            f"CAMERA_COUNT={camera_count} "
            f"IMAGE_BYTES={image_bytes}"
        )

        if image_bytes == 0:
            raise RuntimeError("Empty Camera image")

        results.append(image_bytes)

expected = 640 * 480 * 3

print("EXPECTED_RGB_BYTES:", expected)
print("ALL_NONEMPTY:", all(x > 0 for x in results))
print("ALL_MATCH_RGB640x480:", all(x == expected for x in results))

if not all(x == expected for x in results):
    raise RuntimeError(
        "Camera payload does not match expected RGB image size"
    )

print("TASK23_12B_04_CAMERA_RGB_PAYLOAD_PASS")
