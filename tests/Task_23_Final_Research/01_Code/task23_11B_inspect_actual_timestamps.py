import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

source = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi"
)

print("=== TIMESTAMP SCHEMA ===")

descriptor = osi_sensorview_pb2.SensorView.DESCRIPTOR.fields_by_name[
    "timestamp"
].message_type

for field in descriptor.fields:
    print(field.name, field.type)

print("\n=== ACTUAL LIDAR FRAMES ===")

with source.open("rb") as file:
    for frame_index in range(1, 11):

        header = file.read(4)

        if not header:
            print("End of recording")
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete frame header")

        size = struct.unpack("<I", header)[0]

        payload = file.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete frame payload")

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        print(
            "Frame:", frame_index,
            "| Timestamp:", message.timestamp,
            "| LiDAR views:", len(message.lidar_sensor_view),
            "| Sensor ID:", message.sensor_id
        )
