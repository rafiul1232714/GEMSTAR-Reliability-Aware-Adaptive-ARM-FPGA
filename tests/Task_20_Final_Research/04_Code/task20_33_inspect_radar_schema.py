from osi3.osi_sensorview_pb2 import SensorView
from google.protobuf.descriptor import FieldDescriptor

def describe(msg):
    for field in msg.DESCRIPTOR.fields:
        if field.type == FieldDescriptor.TYPE_MESSAGE:
            typename = field.message_type.full_name
        else:
            typename = str(field.type)

        print(
            f"{field.number:3d} | "
            f"{field.name:38s} | "
            f"{typename}"
        )

sv = SensorView()
radar_view = sv.radar_sensor_view.add()
cfg = radar_view.view_configuration

print("\n=== RADAR CONFIGURATION FIELDS ===")
describe(cfg)

print("\n=== RADAR SENSOR VIEW FIELDS ===")
describe(radar_view)

print("\n=== RADAR MOUNTING FIELDS ===")
describe(cfg.mounting_position)

print("\n=== INSPECTION COMPLETE ===")
