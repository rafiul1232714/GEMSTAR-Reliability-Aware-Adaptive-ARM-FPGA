import struct
import sys

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

FRAME = 530

def read_frame(path, cls):
    with open(path, "rb") as f:
        for index in range(FRAME + 1):
            header = f.read(4)
            if len(header) != 4:
                raise RuntimeError("Incomplete OSI header")
            size = struct.unpack("<I", header)[0]
            if size <= 0 or size > 100_000_000:
                raise RuntimeError("Invalid OSI message size")
            if index < FRAME:
                f.seek(size, 1)
            else:
                payload = f.read(size)
                if len(payload) != size:
                    raise RuntimeError("Incomplete OSI message")
    msg = cls()
    msg.ParseFromString(payload)
    return msg

def fields(msg):
    return [field.name for field, _ in msg.ListFields()]

sv = read_frame(sys.argv[1], SensorView)
gt = read_frame(sys.argv[2], GroundTruth)

print("FRAME=", FRAME)
print("SENSORVIEW_TOP_LEVEL_FIELDS=", fields(sv))
print("GROUNDTRUTH_TOP_LEVEL_FIELDS=", fields(gt))

print("GT_HOST_VEHICLE_ID=", 
      str(getattr(gt, "host_vehicle_id", "FIELD_NOT_PRESENT")))

print("SV_HOST_VEHICLE_ID=",
      str(getattr(sv, "host_vehicle_id", "FIELD_NOT_PRESENT")))

if hasattr(sv, "mounting_position"):
    print("SV_MOUNTING_POSITION=", str(sv.mounting_position))

print("GT_MOVING_OBJECT_COUNT=", len(gt.moving_object))

for obj in gt.moving_object:
    print(
        "GT_OBJECT_ID=", obj.id.value,
        "POSITION=", str(obj.base.position).replace("\n", " "),
        "ORIENTATION=", str(obj.base.orientation).replace("\n", " "),
        "VELOCITY=", str(obj.base.velocity).replace("\n", " ")
    )

if hasattr(sv, "global_ground_truth"):
    inner = sv.global_ground_truth
    print("SV_EMBEDDED_GT_FIELDS=", fields(inner))
    print("SV_EMBEDDED_GT_MOVING_OBJECTS=",
          len(inner.moving_object))
    for obj in list(inner.moving_object)[:5]:
        print(
            "SV_EMBEDDED_OBJECT_ID=", obj.id.value,
            "POSITION=", str(obj.base.position).replace("\n", " "),
            "ORIENTATION=", str(obj.base.orientation).replace("\n", " ")
        )

for label, views in (
    ("CAMERA", sv.camera_sensor_view),
    ("LIDAR", sv.lidar_sensor_view),
    ("RADAR", sv.radar_sensor_view)
):
    print(label + "_VIEW_COUNT=", len(views))
    if views:
        print(label + "_VIEW_FIELDS=", fields(views[0]))
        print(label + "_CONFIG_FIELDS=",
              fields(views[0].view_configuration))

print("GT_USED_FOR_TRACK_ASSOCIATION=NO")
print("FILES_MODIFIED=NO")
print("TASK24_10_02_OSI_STRUCTURE_COMPLETE")