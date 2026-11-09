from pathlib import Path
import struct
from osi3 import osi_sensorview_pb2, osi_groundtruth_pb2

output = Path(r"E:\GEMSTAR_Project\gemstar\Output")
prefix = "20261103T152603Z"

sv_path = next(output.glob(prefix + "*_sv_*.osi"), None)
gt_path = next(output.glob(prefix + "*_gt_*.osi"), None)

# Some recordings put the timestamp before _sv_ or _gt_.
if sv_path is None:
    sv_path = next(output.glob(prefix + "_sv_*.osi"))
if gt_path is None:
    gt_path = next(output.glob(prefix + "_gt_*.osi"))

def first_message(path, message_type):
    with path.open("rb") as f:
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Invalid OSI header")
        size = struct.unpack("<I", header)[0]
        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Incomplete OSI message")
    msg = message_type()
    msg.ParseFromString(payload)
    return msg

sv = first_message(sv_path, osi_sensorview_pb2.SensorView)
gt = first_message(gt_path, osi_groundtruth_pb2.GroundTruth)

print("\n=== TASK 23.7W — RADAR REFERENCE GEOMETRY ===")

print("\n=== RECORDED RADAR CONFIGURATION ===")
for radar in sv.radar_sensor_view:
    print(str(radar.view_configuration)[:3500])

print("\n=== SENSORVIEW AVAILABLE FIELDS ===")
for field, value in sv.ListFields():
    if field.name not in ("radar_sensor_view",
                          "camera_sensor_view",
                          "lidar_sensor_view"):
        print(field.name, ":", str(value)[:350])

print("\n=== GROUNDTRUTH OBJECT COUNTS ===")
for name in ("moving_object", "stationary_object"):
    if hasattr(gt, name):
        objects = getattr(gt, name)
        print(name, ":", len(objects))
        for obj in list(objects)[:3]:
            print(str(obj)[:900])

print("\n=== TASK 23.7W COMPLETE ===")
