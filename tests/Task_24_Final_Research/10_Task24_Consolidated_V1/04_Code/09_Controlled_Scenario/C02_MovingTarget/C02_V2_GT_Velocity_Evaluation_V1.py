import csv
import math
import struct
import sys
from pathlib import Path
from statistics import mean, median

from osi3.osi_groundtruth_pb2 import GroundTruth

gt_path, ekf_path, ref_path, id_path, out_path, report_path = map(
    Path, sys.argv[1:]
)

TARGET_ID = 76897

def load(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

ekf_rows = load(ekf_path)
references = load(ref_path)
identities = load(id_path)

if len(ekf_rows) != 24 or len(references) != 23 or len(identities) != 23:
    raise RuntimeError("Unexpected input row counts")

def index(rows):
    d = {}
    for r in rows:
        frame = int(r["frame"])
        if frame in d:
            raise RuntimeError(f"Duplicate frame: {frame}")
        d[frame] = r
    return d

ekf = index(ekf_rows)
ref = index(references)
identity = index(identities)

if set(ref) != set(identity):
    raise RuntimeError("Identity and reference frames differ")

for frame, r in identity.items():
    if str(r["nearest_is_target"]).strip().lower() not in ("true", "1"):
        raise RuntimeError(f"Unverified target identity at frame {frame}")
    if str(r["target_inside_4m_diagnostic_gate"]).strip().lower() not in ("true", "1"):
        raise RuntimeError(f"Target outside diagnostic gate at frame {frame}")

wanted = set(ref)
gt_messages = {}

with gt_path.open("rb") as f:
    frame = 0
    while True:
        header = f.read(4)
        if not header:
            break
        if len(header) != 4:
            raise RuntimeError("Incomplete GT header")
        size = struct.unpack("<I", header)[0]
        if not 0 < size < 100_000_000:
            raise RuntimeError(f"Invalid size at frame {frame}")
        if frame in wanted:
            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError("Incomplete GT payload")
            m = GroundTruth()
            m.ParseFromString(payload)
            gt_messages[frame] = m
        else:
            f.seek(size, 1)
        frame += 1

if frame != 2122 or set(gt_messages) != wanted:
    raise RuntimeError("GT frame count or selection mismatch")

rows = []

for frame in sorted(wanted):
    r = ref[frame]
    e = ekf[frame]
    m = gt_messages[frame]
    t = float(r["time_s"])

    mt = m.timestamp.seconds + m.timestamp.nanos * 1e-9
    if abs(mt - t) > 1e-6 or abs(float(e["time_s"]) - t) > 1e-6:
        raise RuntimeError(f"Timestamp mismatch at frame {frame}")

    targets = [o for o in m.moving_object if int(o.id.value) == TARGET_ID]
    if len(targets) != 1:
        raise RuntimeError(f"Target unavailable at frame {frame}")

    obj = targets[0]
    yaw = float(r["ego_yaw_rad"])
    co, si = math.cos(yaw), math.sin(yaw)

    # Verified GEMSTAR export: Unreal GetVelocity in cm/s,
    # sign flip on Y, no 0.01 scale in ToOSI::toOSIBaseMoving.
    wx = float(obj.base.velocity.x) / 100.0
    wy = float(obj.base.velocity.y) / 100.0

    # Ego world position was stationary across inspected samples.
    # This transforms velocity axes, but does not independently
    # establish that the ego platform never moved between samples.
    gx = co * wx + si * wy
    gy = -si * wx + co * wy

    lvx = float(e["lidar_only_vx_mps"])
    lvy = float(e["lidar_only_vy_mps"])
    rvx = float(e["radar_ekf_vx_mps"])
    rvy = float(e["radar_ekf_vy_mps"])

    rows.append({
        "frame": frame,
        "time_s": t,
        "gt_target_id": TARGET_ID,
        "gt_center_x_ego_m": float(r["gt_center_x_ego_m"]),
        "gt_center_y_ego_m": float(r["gt_center_y_ego_m"]),
        "gt_vx_ego_mps": gx,
        "gt_vy_ego_mps": gy,
        "gt_speed_mps": math.hypot(gx,gy),
        "lidar_vx_mps": lvx,
        "lidar_vy_mps": lvy,
        "radar_ekf_vx_mps": rvx,
        "radar_ekf_vy_mps": rvy,
        "lidar_velocity_error_mps": math.hypot(lvx-gx,lvy-gy),
        "radar_velocity_error_mps": math.hypot(rvx-gx,rvy-gy),
        "radar_minus_lidar_velocity_error_mps":
            math.hypot(rvx-gx,rvy-gy)-math.hypot(lvx-gx,lvy-gy),
        "gt_center_fd_vx_mps": float("nan"),
        "gt_center_fd_vy_mps": float("nan"),
        "gt_actor_vs_center_fd_error_mps": float("nan"),
    })

# Nonuniform-time, centered GT bounding-center finite differences.
# These are independent evaluation diagnostics, NOT EKF inputs.
for i in range(1, len(rows)-1):
    a, b = rows[i-1], rows[i+1]
    dt = b["time_s"]-a["time_s"]
    if dt <= 0:
        raise RuntimeError("Non-increasing timestamps")
    fd_x = (b["gt_center_x_ego_m"]-a["gt_center_x_ego_m"])/dt
    fd_y = (b["gt_center_y_ego_m"]-a["gt_center_y_ego_m"])/dt
    rows[i]["gt_center_fd_vx_mps"] = fd_x
    rows[i]["gt_center_fd_vy_mps"] = fd_y
    rows[i]["gt_actor_vs_center_fd_error_mps"] = math.hypot(
        rows[i]["gt_vx_ego_mps"]-fd_x,
        rows[i]["gt_vy_ego_mps"]-fd_y
    )

with out_path.open("x",newline="",encoding="utf-8") as f:
    writer = csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

lidar_errors = [r["lidar_velocity_error_mps"] for r in rows]
radar_errors = [r["radar_velocity_error_mps"] for r in rows]
fd_disagreements = [
    r["gt_actor_vs_center_fd_error_mps"]
    for r in rows if math.isfinite(r["gt_actor_vs_center_fd_error_mps"])
]

def rmse(a):
    return math.sqrt(mean(x*x for x in a))

lines = [
    "TASK 24 - GT VELOCITY EVALUATION V1",
    "=" * 56,
    f"Evaluated matched frames: {len(rows)}",
    f"GT target ID: {TARGET_ID}",
    "GT raw velocity divided by 100 (cm/s to m/s).",
    "GT velocity rotated using ego yaw recorded for each frame.",
    "Ego assumed stationary; full ego-motion validation pending.",
    "",
    f"LiDAR-only mean 2D velocity error (m/s): {mean(lidar_errors):.6f}",
    f"LiDAR-only 2D velocity RMSE (m/s): {rmse(lidar_errors):.6f}",
    f"LiDAR-Radar mean 2D velocity error (m/s): {mean(radar_errors):.6f}",
    f"LiDAR-Radar 2D velocity RMSE (m/s): {rmse(radar_errors):.6f}",
    f"Radar minus LiDAR mean velocity error (m/s): {mean(radar_errors)-mean(lidar_errors):.6f}",
    f"GT reported-velocity vs center finite-difference median discrepancy (m/s): {median(fd_disagreements):.6f}",
    "",
    "LIMITATIONS:",
    "GT exporter records axis-aligned bounding-box center for position.",
    "GT exporter records actor GetVelocity for velocity.",
    "Thus position-derived and actor velocity references may differ.",
    "Track 2 is provisional though all 23 frames passed GT nearest-center audit.",
    "Surface measurements need not have the same motion as GT actor center.",
    "No GT velocity was used to update the EKF.",
    "Only one recording and temporally correlated frames were evaluated.",
]

with report_path.open("x",encoding="utf-8") as f:
    f.write("\n".join(lines)+"\n")

print("=== TASK 24 GT VELOCITY RESULTS ===")
print("EVALUATED_FRAMES=",len(rows))
print("GT_VELOCITY_UNIT_CONVERSION=RAW_DIVIDED_BY_100")
print("LIDAR_MEAN_2D_VELOCITY_ERROR_MPS=",round(mean(lidar_errors),6))
print("LIDAR_2D_VELOCITY_RMSE_MPS=",round(rmse(lidar_errors),6))
print("RADAR_MEAN_2D_VELOCITY_ERROR_MPS=",round(mean(radar_errors),6))
print("RADAR_2D_VELOCITY_RMSE_MPS=",round(rmse(radar_errors),6))
print("RADAR_MINUS_LIDAR_MEAN_ERROR_MPS=",round(mean(radar_errors)-mean(lidar_errors),6))
print("GT_ACTOR_VS_CENTER_FD_MEDIAN_DIFFERENCE_MPS=",round(median(fd_disagreements),6))

print()
print("=== SELECTED FRAMES ===")
for r in rows:
    if r["frame"] in (245,286,326,530,816,938):
        print(
            f"FRAME={r['frame']} "
            f"GT_V=({r['gt_vx_ego_mps']:.3f},{r['gt_vy_ego_mps']:.3f}) "
            f"LIDAR_V_ERR={r['lidar_velocity_error_mps']:.3f} "
            f"RADAR_V_ERR={r['radar_velocity_error_mps']:.3f}"
        )

print("OUTPUT_CSV=",out_path)
print("REPORT=",report_path)
print("EGO_MOTION_FULLY_VERIFIED=NO")
print("GT_USED_FOR_FILTER_UPDATE=NO")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_GT_VELOCITY_EVALUATION_COMPLETE")