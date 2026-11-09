import csv
import math
import struct
import sys
from pathlib import Path
from statistics import mean

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

sv_path, gt_path, input_path, output_path, report_path = map(
    Path, sys.argv[1:]
)

TARGET_ID = 76897
HOST_ID = 76894
GATE_M = 4.0
TOTAL_FRAMES = 2122

with input_path.open(newline="", encoding="utf-8-sig") as f:
    original = list(csv.DictReader(f))

if len(original) != 23:
    raise RuntimeError("Expected 23 evaluation frames")

evaluation = {int(r["frame"]): r for r in original}

if len(evaluation) != 23:
    raise RuntimeError("Duplicate frame in evaluation CSV")

def read_selected(path, cls):
    selected = {}

    with path.open("rb") as f:
        for frame in range(TOTAL_FRAMES):
            header = f.read(4)

            if len(header) != 4:
                raise RuntimeError(
                    f"Incomplete OSI header at frame {frame}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size < 100_000_000:
                raise RuntimeError(
                    f"Invalid OSI size at frame {frame}"
                )

            if frame not in evaluation:
                f.seek(size, 1)
                continue

            payload = f.read(size)

            if len(payload) != size:
                raise RuntimeError(
                    f"Incomplete payload at frame {frame}"
                )

            msg = cls()
            msg.ParseFromString(payload)
            selected[frame] = msg

        if f.read(1):
            raise RuntimeError("Unexpected trailing OSI data")

    if set(selected) != set(evaluation):
        raise RuntimeError("Missing evaluated OSI frames")

    return selected

sv_frames = read_selected(sv_path, SensorView)
gt_frames = read_selected(gt_path, GroundTruth)

results = []
problems = []

for frame in sorted(evaluation):
    row = evaluation[frame]
    sv = sv_frames[frame]
    gt = gt_frames[frame]

    timestamp = float(row["time_s"])

    for label, msg in (("SV", sv), ("GT", gt)):
        observed_time = (
            msg.timestamp.seconds
            + msg.timestamp.nanos * 1e-9
        )
        if abs(observed_time - timestamp) > 1e-6:
            raise RuntimeError(
                f"{label} timestamp mismatch at frame {frame}"
            )

    embedded = sv.global_ground_truth

    if int(embedded.host_vehicle_id.value) != HOST_ID:
        raise RuntimeError(
            f"Unexpected host ID at frame {frame}"
        )

    host = [
        o for o in embedded.moving_object
        if int(o.id.value) == HOST_ID
    ]

    if not host:
        raise RuntimeError(
            f"Missing ego pose at frame {frame}"
        )

    ego = host[0].base

    if not all(
        abs(o.base.position.x - ego.position.x) < 1e-6
        and abs(o.base.position.y - ego.position.y) < 1e-6
        and abs(o.base.orientation.yaw -
                ego.orientation.yaw) < 1e-6
        for o in host
    ):
        raise RuntimeError(
            f"Inconsistent host poses at frame {frame}"
        )

    gx = float(row["gt_center_x_ego_m"])
    gy = float(row["gt_center_y_ego_m"])

    # Recover already-estimated LiDAR-only position from
    # stored signed error. Does not create a new estimate.
    tx = gx + float(row["lidar_x_error_m"])
    ty = gy + float(row["lidar_y_error_m"])

    yaw = ego.orientation.yaw
    co = math.cos(yaw)
    si = math.sin(yaw)

    candidates = []

    for obj in gt.moving_object:
        p = obj.base.position

        dx = p.x - ego.position.x
        dy = p.y - ego.position.y

        local_x = co * dx + si * dy
        local_y = -si * dx + co * dy

        distance = math.hypot(
            tx - local_x,
            ty - local_y
        )

        candidates.append({
            "id": int(obj.id.value),
            "distance": distance,
            "x": local_x,
            "y": local_y,
            "model": str(obj.model_reference),
        })

    candidates.sort(key=lambda x: x["distance"])

    target = [
        c for c in candidates if c["id"] == TARGET_ID
    ]

    if len(target) != 1:
        problems.append((frame, "TARGET_COUNT_INVALID"))
        continue

    target = target[0]
    nearest = candidates[0]

    competitors = [
        c for c in candidates if c["id"] != TARGET_ID
    ]

    next_distance = (
        min(c["distance"] for c in competitors)
        if competitors else float("nan")
    )

    margin = (
        next_distance - target["distance"]
        if competitors else float("nan")
    )

    nearest_is_target = nearest["id"] == TARGET_ID
    inside_gate = target["distance"] <= GATE_M

    if not nearest_is_target or not inside_gate:
        problems.append((frame, "AMBIGUOUS_OR_OUTSIDE_GATE"))

    results.append({
        "frame": frame,
        "time_s": timestamp,
        "lidar_track2_x_m": tx,
        "lidar_track2_y_m": ty,
        "gt_target_id": TARGET_ID,
        "gt_target_model": target["model"],
        "gt_target_distance_m": target["distance"],
        "nearest_gt_id": nearest["id"],
        "nearest_gt_distance_m": nearest["distance"],
        "nearest_is_target": nearest_is_target,
        "target_inside_4m_diagnostic_gate": inside_gate,
        "next_competitor_distance_m": next_distance,
        "target_vs_competitor_margin_m": margin,
        "gt_object_count": len(candidates),
        "evaluation_only": "YES",
    })

if len(results) != 23:
    raise RuntimeError(
        f"Expected 23 audited frames; got {len(results)}"
    )

with output_path.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

nearest_count = sum(
    r["nearest_is_target"] for r in results
)

gate_count = sum(
    r["target_inside_4m_diagnostic_gate"]
    for r in results
)

distances = [
    r["gt_target_distance_m"] for r in results
]

lines = [
    "TASK 24 — INDEPENDENT TRACK 2 / GT CORRESPONDENCE AUDIT",
    "=" * 60,
    f"Evaluated frames: {len(results)}",
    f"Target GT ID: {TARGET_ID}",
    f"Nearest-GT frames: {nearest_count}",
    f"Within 4 m diagnostic gate: {gate_count}",
    f"Mean GT-center separation: {mean(distances):.6f} m",
    f"Maximum separation: {max(distances):.6f} m",
    f"Problems: {problems}",
    "",
    "Interpretation:",
    "Nearest-center correspondence is evaluation evidence only.",
    "LiDAR measures visible surfaces, not necessarily GT centers.",
    "The fixed 4 m gate is diagnostic, not a calibrated criterion.",
    "GT data was never supplied to the original tracker.",
    "Results do not prove physical target identity independently.",
]

with report_path.open("x", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("=== TASK 24 GT IDENTITY AUDIT RESULTS ===")
print("EVALUATED_FRAMES=", len(results))
print("TARGET_GT_ID=", TARGET_ID)
print("TARGET_NEAREST_FRAMES=", nearest_count)
print("TARGET_WITHIN_4M_GATE_FRAMES=", gate_count)
print("MEAN_TARGET_CENTER_SEPARATION_M=",
      round(mean(distances), 6))
print("MAX_TARGET_CENTER_SEPARATION_M=",
      round(max(distances), 6))

print()
print("=== SELECTED FRAMES ===")

for r in results:
    if r["frame"] in (245, 530, 816, 938):
        print(
            f"FRAME={r['frame']} "
            f"NEAREST_ID={r['nearest_gt_id']} "
            f"TARGET_DISTANCE_M="
            f"{r['gt_target_distance_m']:.4f} "
            f"COMPETITOR_MARGIN_M="
            f"{r['target_vs_competitor_margin_m']:.4f} "
            f"MODEL={r['gt_target_model']}"
        )

print()
print("AUDIT_PROBLEMS=", problems)
print("OUTPUT_CSV=", output_path)
print("REPORT=", report_path)
print("GROUND_TRUTH_USED_FOR_TRACKING=NO")
print("TRACKING_ALGORITHM_MODIFIED=NO")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_GT_TRACK_IDENTITY_AUDIT_COMPLETE")