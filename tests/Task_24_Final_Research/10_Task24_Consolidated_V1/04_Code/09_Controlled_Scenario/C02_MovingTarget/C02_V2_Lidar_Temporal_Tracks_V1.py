import csv
import math
from collections import defaultdict
from pathlib import Path

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

MAX_MISSED_FRAMES = 2
MAX_SPEED_MPS = 5.0
BASE_GATE_M = 1.0
MAX_GATE_M = 8.0
MOVING_DISPLACEMENT_M = 2.0
MIN_TRACK_OBSERVATIONS = 3

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

frames = read_csv(DIR / "selected_frames.csv")
clusters = read_csv(DIR / "lidar_cluster_candidates_v1.csv")

if len(frames) != 53:
    raise RuntimeError("Expected 53 frame records")

times = {}
for r in frames:
    k = int(r["frame"])
    if k in times:
        raise RuntimeError("Duplicate frame index")
    times[k] = float(r["time_s"])

by_frame = defaultdict(list)

for r in clusters:
    frame = int(r["frame"])
    if frame not in times:
        raise RuntimeError("Unexpected cluster frame")

    by_frame[frame].append({
        "frame": frame,
        "time": float(r["time_s"]),
        "cluster": int(r["local_cluster_id"]),
        "n": int(r["point_count"]),
        "x": float(r["median_x_m"]),
        "y": float(r["median_y_m"]),
        "z": float(r["median_z_m"])
    })

tracks = {}
observations = []
next_id = 1

ordered_frames = sorted(times)

for frame_order, frame in enumerate(ordered_frames):
    current_time = times[frame]
    candidates = by_frame[frame]

    eligible = []

    for tid, track in tracks.items():
        if frame_order - track["last_order"] > MAX_MISSED_FRAMES + 1:
            continue

        last = track["history"][-1]
        dt = current_time - last["time"]

        if dt <= 0:
            raise RuntimeError("Non-increasing timestamps")

        px, py = last["x"], last["y"]

        if len(track["history"]) >= 2:
            prev = track["history"][-2]
            historical_dt = last["time"] - prev["time"]

            if historical_dt > 0:
                vx = (last["x"] - prev["x"]) / historical_dt
                vy = (last["y"] - prev["y"]) / historical_dt

                speed = math.hypot(vx, vy)

                # Avoid extrapolating implausibly large jumps.
                if speed <= MAX_SPEED_MPS:
                    px += vx * dt
                    py += vy * dt

        gate = min(
            MAX_GATE_M,
            BASE_GATE_M + MAX_SPEED_MPS * dt
        )

        for j, c in enumerate(candidates):
            d = math.hypot(c["x"] - px, c["y"] - py)

            if d <= gate:
                eligible.append((d / gate, d, tid, j))

    # Global greedy one-to-one matching.
    eligible.sort()

    matched_tracks = set()
    matched_candidates = set()
    assignments = []

    for score, distance, tid, j in eligible:
        if tid in matched_tracks or j in matched_candidates:
            continue

        matched_tracks.add(tid)
        matched_candidates.add(j)
        assignments.append((tid, j, distance, "MATCHED"))

    # Unmatched candidates initiate separate tentative tracks.
    for j, c in enumerate(candidates):
        if j in matched_candidates:
            continue

        tid = next_id
        next_id += 1

        tracks[tid] = {
            "history": [],
            "last_order": frame_order
        }

        assignments.append((tid, j, None, "INITIALIZED"))

    for tid, j, distance, status in assignments:
        c = candidates[j]
        tracks[tid]["history"].append(c)
        tracks[tid]["last_order"] = frame_order

        observations.append({
            "track_id": tid,
            "frame": frame,
            "time_s": c["time"],
            "local_cluster_id": c["cluster"],
            "point_count": c["n"],
            "x_m": c["x"],
            "y_m": c["y"],
            "z_m": c["z"],
            "association_distance_m": (
                round(distance, 5)
                if distance is not None else ""
            ),
            "status": status
        })

summary = []

for tid in sorted(tracks):
    history = tracks[tid]["history"]
    first = history[0]
    last = history[-1]

    dx = last["x"] - first["x"]
    dy = last["y"] - first["y"]
    displacement = math.hypot(dx, dy)
    duration = last["time"] - first["time"]

    moving = (
        len(history) >= MIN_TRACK_OBSERVATIONS
        and displacement >= MOVING_DISPLACEMENT_M
    )

    track_status = (
        "MOVING_CANDIDATE"
        if moving else
        "SHORT_OR_LOW_DISPLACEMENT_CANDIDATE"
    )

    summary.append({
        "track_id": tid,
        "observations": len(history),
        "first_frame": first["frame"],
        "last_frame": last["frame"],
        "duration_s": round(duration, 5),
        "net_displacement_m": round(displacement, 5),
        "average_net_speed_mps": (
            round(displacement / duration, 5)
            if duration > 0 else ""
        ),
        "first_x_m": first["x"],
        "first_y_m": first["y"],
        "last_x_m": last["x"],
        "last_y_m": last["y"],
        "classification": track_status
    })

track_fields = [
    "track_id", "frame", "time_s", "local_cluster_id",
    "point_count", "x_m", "y_m", "z_m",
    "association_distance_m", "status"
]

summary_fields = [
    "track_id", "observations", "first_frame", "last_frame",
    "duration_s", "net_displacement_m",
    "average_net_speed_mps", "first_x_m", "first_y_m",
    "last_x_m", "last_y_m", "classification"
]

with (DIR / "lidar_temporal_tracks_v1.csv").open(
    "x", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=track_fields)
    writer.writeheader()
    writer.writerows(observations)

with (DIR / "lidar_temporal_track_summary_v1.csv").open(
    "x", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=summary_fields)
    writer.writeheader()
    writer.writerows(summary)

moving_tracks = [
    r for r in summary
    if r["classification"] == "MOVING_CANDIDATE"
]

print("=== TASK 24.9.3 RESULTS ===")
print("FRAMES_PROCESSED=", len(frames))
print("INPUT_CLUSTERS=", len(clusters))
print("TRACK_OBSERVATIONS=", len(observations))
print("TRACK_IDS_CREATED=", len(summary))
print("MOVING_CANDIDATES=", len(moving_tracks))

print("\n=== TRACK SUMMARY ===")
for r in sorted(
    summary,
    key=lambda x: (-x["observations"], x["track_id"])
):
    print(
        "TRACK=", r["track_id"],
        "OBS=", r["observations"],
        "FRAMES=", (r["first_frame"], r["last_frame"]),
        "DISPLACEMENT_M=", r["net_displacement_m"],
        "CLASS=", r["classification"]
    )

print("\n=== FRAME 530 ASSOCIATIONS ===")
for r in observations:
    if r["frame"] == 530:
        print(
            "TRACK=", r["track_id"],
            "CLUSTER=", r["local_cluster_id"],
            "POINTS=", r["point_count"],
            "XYZ=", (
                round(r["x_m"], 3),
                round(r["y_m"], 3),
                round(r["z_m"], 3)
            )
        )

print("TRACK_IDS_FROM_GROUND_TRUTH=NO")
print("CAMERA_USED_TO_SELECT_TRACKS=NO")
print("MATCHING_METHOD=GREEDY_NEAREST_PREDICTED_POSITION")
print("TRACK_VALIDATION_STATUS=PROVISIONAL")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_09_03_TEMPORAL_ASSOCIATION_COMPLETE")