import osi3.osi_sensorview_pb2 as osi_sensorview_pb2

def show_fields(name, descriptor):
    print(f"\n=== {name} ===")

    for field in descriptor.fields:
        print(
            f"{field.name} | "
            f"type={field.type} | "
            f"message={field.message_type.full_name if field.message_type else '-'}"
        )

show_fields(
    "SensorView",
    osi_sensorview_pb2.SensorView.DESCRIPTOR
)

for field in osi_sensorview_pb2.SensorView.DESCRIPTOR.fields:
    if field.name == "lidar_sensor_view" and field.message_type:
        show_fields(
            "LiDAR SensorView",
            field.message_type
        )
