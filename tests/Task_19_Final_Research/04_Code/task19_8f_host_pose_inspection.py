import json
import struct
from pathlib import Path
from google.protobuf.json_format import MessageToDict
from osi3 import osi_groundtruth_pb2, osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

folder = root / "data" / "raw" / "fog_mor100"

gt_file = folder / "20261027T224313Z_gt_380_X_466_GEMSTAR.osi"
sv_file = folder / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"

target_frame = 150

def read_frame(path, message_type, index):
    with path.open("rb") as f:
        for n in range(index + 1):
            header = f.read(4)
            if len(header) != 4:
                raise RuntimeError(f"Incomplete header: {path}")

            length = struct.unpack("<I", header)[0]

            if n == index:
                payload = f.read(length)
                if len(payload) != length:
                    raise RuntimeError("Incomplete message")

                msg = message_type()
                msg.ParseFromString(payload)
                return msg

            f.seek(length, 1)

gt = read_frame(gt_file, osi_groundtruth_pb2.GroundTruth, target_frame)
sv = read_frame(sv_file, osi_sensorview_pb2.SensorView, target_frame)

print("\n=== TASK 19.8F HOST POSE INSPECTION ===")

host_id = (
    int(gt.host_vehicle_id.value)
    if gt.HasField("host_vehicle_id") else None
)

print("Ground-truth host ID:", host_id)
print("Moving objects:", len(gt.moving_object))

host_matches = []

for obj in gt.moving_object:
    oid = int(obj.id.value)

    if oid == host_id:
        host_matches.append(
            MessageToDict(obj, preserving_proto_field_name=True)
        )

        print("\nHOST VEHICLE OBJECT:")
        print(json.dumps(host_matches[-1], indent=2)[:5000])

print("\nHost found in moving objects:", bool(host_matches))

print("\nSensorView global_ground_truth present:",
      sv.HasField("global_ground_truth"))

if sv.HasField("global_ground_truth"):
    sgt = sv.global_ground_truth

    print("SensorView GT moving objects:",
          len(sgt.moving_object))

    print("SensorView GT host ID:",
          int(sgt.host_vehicle_id.value)
          if sgt.HasField("host_vehicle_id") else None)

    for obj in sgt.moving_object[:5]:
        print(
            "SV GT object:",
            json.dumps(
                MessageToDict(
                    obj, preserving_proto_field_name=True
                ),
                indent=2
            )[:2000]
        )

lidar = sv.lidar_sensor_view[0]
mount = lidar.view_configuration.mounting_position

print("\nLiDAR mounting position:")
print("X:", mount.position.x)
print("Y:", mount.position.y)
print("Z:", mount.position.z)

print("LiDAR mounting orientation:")
print("Roll:", mount.orientation.roll)
print("Pitch:", mount.orientation.pitch)
print("Yaw:", mount.orientation.yaw)

report = {
    "frame": target_frame,
    "ground_truth_host_id": host_id,
    "host_found_in_gt": bool(host_matches),
    "host_objects": host_matches,
    "sensorview_gt": (
        MessageToDict(
            sv.global_ground_truth,
            preserving_proto_field_name=True
        )
        if sv.HasField("global_ground_truth") else None
    ),
    "lidar_mounting": MessageToDict(
        mount, preserving_proto_field_name=True
    )
}

output = (
    base / "05_Raw_Data_References"
    / "task19_8f_host_pose_inspection.json"
)

output.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 19.8F COMPLETE ===")
print("JSON saved:", output.is_file())
