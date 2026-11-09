import csv
import math
import struct
import sys
from pathlib import Path
from statistics import median, mean

from osi3.osi_groundtruth_pb2 import GroundTruth

gt_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
report_path = Path(sys.argv[3])

TARGET_ID = 76897
EXPECTED_FRAMES = 2122

rows = []
all_frames = 0

with gt_path.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]

        if not 0 < size < 100_000_000:
            raise RuntimeError(
                f"Invalid OSI message size at frame {all_frames}"
            )

        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError(
                f"Incomplete OSI payload at frame {all_frames}"
            )

        msg = GroundTruth()
        msg.ParseFromString(payload)

        t = msg.timestamp.seconds + msg.timestamp.nanos * 1e-9

        targets = [
            o for o in msg.moving_object
            if int(o.id.value) == TARGET_ID
        ]

        if len(targets) > 1:
            raise RuntimeError(
                f"Duplicate target at frame {all_frames}"
            )

        if len(targets) == 1:
            obj = targets[0]
            p = obj.base.position
            v = obj.base.velocity

            # Source-verified: exporter stores raw Unreal
            # actor velocity in cm/s, with Y sign reversed.
            vx = float(v.x) / 100.0
            vy = float(v.y) / 100.0

            rows.append({
                "frame": all_frames,
                "time_s": t,
                "gt_world_x_m": float(p.x),
                "gt_world_y_m": float(p.y),
                "gt_actor_vx_mps": vx,
                "gt_actor_vy_mps": vy,
                "gt_actor_speed_mps": math.hypot(vx, vy),
                "fd_center_vx_mps": float("nan"),
                "fd_center_vy_mps": float("nan"),
                "fd_center_speed_mps": float("nan"),
                "actor_to_fd_speed_ratio": float("nan"),
                "actor_vs_fd_vector_error_mps": float("nan"),
                "zero_actor_during_center_motion": False,
            })

        all_frames += 1

    if all_frames != EXPECTED_FRAMES:
        raise RuntimeError(
            f"Expected {EXPECTED_FRAMES} frames, found {all_frames}"
        )

if len(rows) < 3:
    raise RuntimeError("Insufficient GT target observations")

# Compute a local centered derivative using only
# consecutive source frames. Never bridge a missing target.
for i in range(1, len(rows)-1):
    a = rows[i-1]
    b = rows[i]
    c = rows[i+1]

    if not (
        b["frame"] == a["frame"] + 1
        and c["frame"] == b["frame"] + 1
    ):
        continue

    dt = c["time_s"] - a["time_s"]

    if dt <= 0:
        raise RuntimeError(
            f"Non-increasing time near frame {b['frame']}"
        )

    fvx = (c["gt_world_x_m"] - a["gt_world_x_m"]) / dt
    fvy = (c["gt_world_y_m"] - a["gt_world_y_m"]) / dt
    fspeed = math.hypot(fvx, fvy)

    b["fd_center_vx_mps"] = fvx
    b["fd_center_vy_mps"] = fvy
    b["fd_center_speed_mps"] = fspeed

    b["actor_vs_fd_vector_error_mps"] = math.hypot(
        b["gt_actor_vx_mps"] - fvx,
        b["gt_actor_vy_mps"] - fvy
    )

    if fspeed > 0.5:
        b["actor_to_fd_speed_ratio"] = (
            b["gt_actor_speed_mps"] / fspeed
        )

    b["zero_actor_during_center_motion"] = (
        b["gt_actor_speed_mps"] < 0.05
        and fspeed > 0.5
    )

# Export full recording evidence.
with output_path.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

valid = [
    r for r in rows
    if math.isfinite(r["fd_center_speed_mps"])
]

moving = [
    r for r in valid
    if r["fd_center_speed_mps"] > 0.5
]

active = [
    r for r in moving
    if r["gt_actor_speed_mps"] > 0.5
]

ratios = [
    r["actor_to_fd_speed_ratio"]
    for r in active
    if math.isfinite(r["actor_to_fd_speed_ratio"])
]

vector_errors = [
    r["actor_vs_fd_vector_error_mps"]
    for r in valid
]

zero_flags = [
    r["frame"]
    for r in valid
    if r["zero_actor_during_center_motion"]
]

if not valid or not ratios:
    raise RuntimeError("No valid full-rate velocity comparisons")

times = [
    rows[i+1]["time_s"] - rows[i]["time_s"]
    for i in range(len(rows)-1)
    if rows[i+1]["frame"] == rows[i]["frame"] + 1
]

selected_frames = {
    245, 286, 326, 408, 449, 530, 571,
    612, 653, 816, 897, 938
}

print("=== TASK 24 FULL-RATE GT VELOCITY RESULTS ===")
print("TOTAL_OSI_FRAMES=", all_frames)
print("TARGET_PRESENT_FRAMES=", len(rows))
print("VALID_CENTER_DIFFERENCE_FRAMES=", len(valid))
print("MEDIAN_FRAME_INTERVAL_S=", round(median(times), 9))

print("FULLRATE_MEDIAN_ACTOR_SPEED_MPS=",
      round(median(r["gt_actor_speed_mps"] for r in valid), 6))
print("FULLRATE_MEDIAN_CENTER_FD_SPEED_MPS=",
      round(median(r["fd_center_speed_mps"] for r in valid), 6))
print("ACTIVE_MOTION_FRAMES=", len(active))
print("MEDIAN_ACTOR_TO_CENTER_FD_SPEED_RATIO=",
      round(median(ratios), 6))
print("MEAN_ACTOR_TO_CENTER_FD_SPEED_RATIO=",
      round(mean(ratios), 6))
print("MEDIAN_VECTOR_VELOCITY_DISAGREEMENT_MPS=",
      round(median(vector_errors), 6))

print("ZERO_ACTOR_DURING_CENTER_MOTION_COUNT=",
      len(zero_flags))
print("ZERO_MOTION_FIRST_25_FRAMES=", zero_flags[:25])

print()
print("=== PREVIOUSLY INVESTIGATED FRAMES ===")

by_frame = {r["frame"]: r for r in rows}

for frame in sorted(selected_frames):
    if frame not in by_frame:
        print("FRAME=", frame, "TARGET_MISSING")
        continue

    r = by_frame[frame]

    print(
        f"FRAME={frame} "
        f"TIME={r['time_s']:.4f} "
        f"ACTOR_SPEED={r['gt_actor_speed_mps']:.4f} "
        f"CENTER_FD_SPEED={r['fd_center_speed_mps']:.4f} "
        f"RATIO={r['actor_to_fd_speed_ratio']:.4f} "
        f"ZERO_FLAG={r['zero_actor_during_center_motion']}"
    )

lines = [
    "TASK 24 — FULL-RATE GT VELOCITY INTEGRITY AUDIT",
    "=" * 60,
    f"OSI frames: {all_frames}",
    f"Target-present frames: {len(rows)}",
    f"Valid centered derivatives: {len(valid)}",
    f"Median frame interval (s): {median(times):.9f}",
    f"Active frames used for ratio: {len(active)}",
    f"Median actor / GT-center speed ratio: {median(ratios):.6f}",
    f"Mean actor / GT-center speed ratio: {mean(ratios):.6f}",
    f"Median vector disagreement (m/s): {median(vector_errors):.6f}",
    f"Zero actor velocity despite center motion: {len(zero_flags)}",
    f"Flagged frames: {zero_flags}",
    "",
    "METHODOLOGICAL NOTES",
    "Actual OSI timestamps used for finite differences.",
    "Only consecutive frames included in derivative calculation.",
    "GT exporter actor velocity divided by 100.",
    "World-frame vector components compared without ego transform.",
    "Actor velocity and world-aligned bounding-center velocity",
    "may refer to different physical points.",
    "Derivative may be affected by simulation timing and GT sampling.",
    "No GT data used to alter the original EKF.",
    "Results are diagnostic and not a calibration.",
    "",
    "NEXT:",
    "Determine whether discrepancies persist at full frame rate.",
    "Investigate the exporter/simulation timing if necessary.",
    "Finalize velocity findings only after reference validation.",
]

with report_path.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print()
print("OUTPUT_CSV=", output_path)
print("REPORT=", report_path)
print("GT_VELOCITY_VALIDATION_STATUS=DIAGNOSTIC")
print("EKF_STATES_MODIFIED=NO")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_GT_FULLRATE_VELOCITY_AUDIT_COMPLETE")