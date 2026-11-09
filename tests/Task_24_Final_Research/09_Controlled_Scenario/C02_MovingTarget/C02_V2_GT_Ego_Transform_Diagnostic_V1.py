import math
import struct
import sys

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

FRAMES = (0, 245, 530, 816, 938)
TARGET_ID = 76897

def read_selected(path, message_type):
    result = {}

    with open(path, "rb") as f:
        for index in range(2122):
            header = f.read(4)
            if len(header) != 4:
                raise RuntimeError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]

            if not (0 < size < 100_000_000):
                raise RuntimeError("Invalid message size")

            if index not in FRAMES:
                f.seek(size, 1)
                continue

            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError("Incomplete OSI payload")

            msg = message_type()
            msg.ParseFromString(payload)
            result[index] = msg

    if set(result) != set(FRAMES):
        raise RuntimeError("Missing requested frames")

    return result

sv_frames = read_selected(sys.argv[1], SensorView)
gt_frames = read_selected(sys.argv[2], GroundTruth)

print("=== TASK 24.10.2B RESULTS ===")

for frame in FRAMES:
    sv = sv_frames[frame]
    gt = gt_frames[frame]

    embedded = sv.global_ground_truth
    host_id = int(embedded.host_vehicle_id.value)

    hosts = [
        o for o in embedded.moving_object
        if int(o.id.value) == host_id
    ]

    targets = [
        o for o in gt.moving_object
        if int(o.id.value) == TARGET_ID
    ]

    print()
    print("FRAME=", frame)
    print("HOST_ID=", host_id)
    print("EMBEDDED_HOST_ENTRIES=", len(hosts))
    print("GT_TARGET_ENTRIES=", len(targets))

    if not hosts or len(targets) != 1:
        print("TRANSFORM_STATUS=INSUFFICIENT_DATA")
        continue

    ego = hosts[0].base
    target = targets[0].base

    # Check whether all duplicated host poses agree.
    consistent = all(
        abs(h.base.position.x - ego.position.x) < 1e-6
        and abs(h.base.position.y - ego.position.y) < 1e-6
        and abs(h.base.orientation.yaw - ego.orientation.yaw) < 1e-6
        for h in hosts
    )

    dx = target.position.x - ego.position.x
    dy = target.position.y - ego.position.y
    yaw = ego.orientation.yaw

    # Preliminary conventional 2D world-to-ego rotation.
    local_x = math.cos(yaw)*dx + math.sin(yaw)*dy
    local_y = -math.sin(yaw)*dx + math.cos(yaw)*dy

    speed_raw = math.hypot(
        target.velocity.x, target.velocity.y
    )

    print("HOST_DUPLICATES_CONSISTENT=", consistent)
    print(
        "EGO_WORLD_XY_M=",
        (round(ego.position.x, 5),
         round(ego.position.y, 5))
    )
    print("EGO_YAW_DEG=", round(math.degrees(yaw), 5))
    print(
        "TARGET_WORLD_XY=",
        (round(target.position.x, 5),
         round(target.position.y, 5))
    )
    print(
        "TARGET_PRELIMINARY_EGO_XY=",
        (round(local_x, 5), round(local_y, 5))
    )
    print("GT_SPEED_RAW_MAGNITUDE=", round(speed_raw, 5))
    print(
        "GT_SPEED_IF_CM_PER_SEC=",
        round(speed_raw / 100.0, 5)
    )

print()
print("TRANSFORM_STATUS=PRELIMINARY_NOT_VALIDATED")
print("TARGET_ID_USED_FOR_EVALUATION_ONLY=YES")
print("TRACKING_ALGORITHM_MODIFIED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_10_02B_TRANSFORM_DIAGNOSTIC_COMPLETE")