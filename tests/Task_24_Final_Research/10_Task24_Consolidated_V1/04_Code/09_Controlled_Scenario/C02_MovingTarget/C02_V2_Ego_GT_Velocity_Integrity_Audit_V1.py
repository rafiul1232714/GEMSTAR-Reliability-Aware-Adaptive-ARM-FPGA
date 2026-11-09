import csv
import math
import struct
import sys
from pathlib import Path
from statistics import median

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

sv_path, gt_path, input_path, output_path, report_path = map(
    Path, sys.argv[1:]
)

TOTAL_FRAMES = 2122
HOST_ID = 76894
TARGET_ID = 76897

with input_path.open(newline="", encoding="utf-8-sig") as f:
    previous = list(csv.DictReader(f))

if len(previous) != 23:
    raise RuntimeError("Expected 23 evaluation frames")

wanted = {int(r["frame"]) for r in previous}

if len(wanted) != 23:
    raise RuntimeError("Duplicate evaluation frames")

def read_selected(path, cls):
    results = {}

    with path.open("rb") as f:
        for index in range(TOTAL_FRAMES):
            header = f.read(4)

            if len(header) != 4:
                raise RuntimeError(
                    f"Incomplete OSI header at frame {index}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size < 100_000_000:
                raise RuntimeError(
                    f"Invalid message size at frame {index}"
                )

            if index not in wanted:
                f.seek(size, 1)
                continue

            payload = f.read(size)

            if len(payload) != size:
                raise RuntimeError(
                    f"Incomplete OSI message at frame {index}"
                )

            message = cls()
            message.ParseFromString(payload)

            results[index] = message

        if f.read(1):
            raise RuntimeError("Unexpected trailing OSI data")

    if set(results) != wanted:
        raise RuntimeError("Missing selected frames")

    return results

sv_data = read_selected(sv_path, SensorView)
gt_data = read_selected(gt_path, GroundTruth)

rows = []

for frame in sorted(wanted):
    sv = sv_data[frame]
    gt = gt_data[frame]

    t = gt.timestamp.seconds + gt.timestamp.nanos * 1e-9
    sv_t = sv.timestamp.seconds + sv.timestamp.nanos * 1e-9

    if abs(t - sv_t) > 1e-6:
        raise RuntimeError(f"SV-GT timestamp mismatch at {frame}")

    embedded = sv.global_ground_truth
    host_id = int(embedded.host_vehicle_id.value)

    if host_id != HOST_ID:
        raise RuntimeError(f"Unexpected ego ID at {frame}")

    hosts = [
        o for o in embedded.moving_object
        if int(o.id.value) == HOST_ID
    ]

    targets = [
        o for o in gt.moving_object
        if int(o.id.value) == TARGET_ID
    ]

    if not hosts or len(targets) != 1:
        raise RuntimeError(f"Missing host or target at {frame}")

    ego = hosts[0].base
    target = targets[0].base

    if not all(
        abs(o.base.position.x - ego.position.x) < 1e-6
        and abs(o.base.position.y - ego.position.y) < 1e-6
        and abs(o.base.orientation.yaw - ego.orientation.yaw) < 1e-6
        for o in hosts
    ):
        raise RuntimeError(f"Inconsistent ego poses at {frame}")

    yaw = ego.orientation.yaw
    co, si = math.cos(yaw), math.sin(yaw)

    dx = target.position.x - ego.position.x
    dy = target.position.y - ego.position.y

    local_x = co * dx + si * dy
    local_y = -si * dx + co * dy

    # GEMSTAR exporter stores Unreal actor velocity
    # without converting cm/s to m/s.
    raw_vx = float(target.velocity.x)
    raw_vy = float(target.velocity.y)

    world_vx = raw_vx / 100.0
    world_vy = raw_vy / 100.0

    local_vx = co * world_vx + si * world_vy
    local_vy = -si * world_vx + co * world_vy

    rows.append({
        "frame": frame,
        "time_s": t,
        "ego_x_world_m": ego.position.x,
        "ego_y_world_m": ego.position.y,
        "ego_yaw_rad": yaw,
        "target_x_ego_m": local_x,
        "target_y_ego_m": local_y,
        "gt_actor_vx_ego_mps": local_vx,
        "gt_actor_vy_ego_mps": local_vy,
        "gt_actor_speed_mps": math.hypot(
            local_vx, local_vy
        ),
        "target_fd_speed_mps": float("nan"),
        "reported_zero_during_measured_motion": False,
    })

# Centered finite differences on the 23 evaluation samples.
# Endpoints are deliberately excluded.
for i in range(1, len(rows)-1):
    before = rows[i-1]
    after = rows[i+1]
    current = rows[i]

    dt = after["time_s"] - before["time_s"]

    if dt <= 0:
        raise RuntimeError("Non-increasing timestamps")

    vx = (
        after["target_x_ego_m"]
        - before["target_x_ego_m"]
    ) / dt

    vy = (
        after["target_y_ego_m"]
        - before["target_y_ego_m"]
    ) / dt

    fd_speed = math.hypot(vx, vy)

    current["target_fd_speed_mps"] = fd_speed

    current["reported_zero_during_measured_motion"] = (
        current["gt_actor_speed_mps"] < 0.05
        and fd_speed > 0.5
    )

ego_x = [r["ego_x_world_m"] for r in rows]
ego_y = [r["ego_y_world_m"] for r in rows]
ego_yaw = [r["ego_yaw_rad"] for r in rows]

ego_displacement = [
    math.hypot(x-ego_x[0], y-ego_y[0])
    for x,y in zip(ego_x,ego_y)
]

yaw_change = [
    abs(math.atan2(
        math.sin(y-ego_yaw[0]),
        math.cos(y-ego_yaw[0])
    ))
    for y in ego_yaw
]

zero_flags = [
    r for r in rows
    if r["reported_zero_during_measured_motion"]
]

valid_fd = [
    r["target_fd_speed_mps"]
    for r in rows
    if math.isfinite(r["target_fd_speed_mps"])
]

with output_path.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

lines = [
    "TASK 24 — EGO MOTION / GT VELOCITY INTEGRITY AUDIT",
    "=" * 60,
    f"Evaluated frames: {len(rows)}",
    f"Ego ID: {HOST_ID}",
    f"Target ID: {TARGET_ID}",
    "",
    f"Maximum sampled ego position change (m): {max(ego_displacement):.9f}",
    f"Maximum sampled ego yaw change (deg): {math.degrees(max(yaw_change)):.9f}",
    "",
    f"GT actor-zero / center-motion flags: {len(zero_flags)}",
    f"Flagged frames: {[r['frame'] for r in zero_flags]}",
    f"Median finite-difference center speed (m/s): {median(valid_fd):.6f}",
    "",
    "LIMITATIONS",
    "Ego pose is checked at the 23 evaluated frames.",
    "This is not a continuous full-rate ego-motion audit.",
    "GT actor velocity is a different reference from AABB center motion.",
    "Finite differences use sparse, nonuniform evaluation samples.",
    "A zero-velocity flag indicates inconsistency, not its root cause.",
    "No measurements were used to alter the original EKF.",
]

with report_path.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("=== TASK 24 EGO / GT VELOCITY AUDIT RESULTS ===")
print("EVALUATED_FRAMES=", len(rows))
print("MAX_SAMPLED_EGO_DISPLACEMENT_M=",
      round(max(ego_displacement), 9))
print("MAX_SAMPLED_EGO_YAW_CHANGE_DEG=",
      round(math.degrees(max(yaw_change)), 9))
print("GT_ACTOR_ZERO_DURING_CENTER_MOTION_FRAMES=",
      len(zero_flags))
print("FLAGGED_FRAMES=",
      [r["frame"] for r in zero_flags])
print("MEDIAN_GT_CENTER_FD_SPEED_MPS=",
      round(median(valid_fd), 6))

print()
print("=== SELECTED FRAME DIAGNOSTICS ===")

for r in rows:
    if r["frame"] in (245, 286, 326, 530, 816, 938):
        print(
            f"FRAME={r['frame']} "
            f"ACTOR_SPEED={r['gt_actor_speed_mps']:.3f} "
            f"CENTER_FD_SPEED={r['target_fd_speed_mps']:.3f} "
            f"ZERO_MOTION_FLAG="
            f"{r['reported_zero_during_measured_motion']}"
        )

print()
print("OUTPUT_CSV=", output_path)
print("REPORT=", report_path)
print("FULL_RATE_EGO_MOTION_VERIFIED=NO")
print("GT_VELOCITY_EXPORTER_VALIDATED=NO")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_EGO_GT_VELOCITY_AUDIT_COMPLETE")