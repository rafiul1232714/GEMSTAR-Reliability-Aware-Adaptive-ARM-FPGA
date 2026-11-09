import csv
import math
from pathlib import Path
from collections import defaultdict
from statistics import median

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

GATE_M = 1.5
DOPPLER_EPS = 1e-9

def read_csv(name):
    with (DIR / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

clusters = read_csv("lidar_cluster_candidates_v1.csv")
tracks = read_csv("lidar_temporal_tracks_v1.csv")
radar = read_csv("radar_returns.csv")

# Link each LiDAR cluster to its algorithm-generated temporal track.
cluster_to_track = {}
for row in tracks:
    key = (int(row["frame"]), int(row["local_cluster_id"]))
    if key in cluster_to_track:
        raise RuntimeError(f"Duplicate track assignment: {key}")
    cluster_to_track[key] = int(row["track_id"])

by_frame = defaultdict(list)
summary_lookup = {}

for row in clusters:
    frame = int(row["frame"])
    cluster_id = int(row["local_cluster_id"])
    key = (frame, cluster_id)

    if key not in cluster_to_track:
        raise RuntimeError(f"Cluster lacks temporal track: {key}")

    box = {
        "frame": frame,
        "cluster_id": cluster_id,
        "track_id": cluster_to_track[key],
        "time_s": float(row["time_s"]),
        "points": int(row["point_count"]),
        "xmin": float(row["min_x_m"]),
        "xmax": float(row["max_x_m"]),
        "ymin": float(row["min_y_m"]),
        "ymax": float(row["max_y_m"]),
        "zmin": float(row["min_z_m"]),
        "zmax": float(row["max_z_m"]),
    }

    if not (
        box["xmin"] <= box["xmax"]
        and box["ymin"] <= box["ymax"]
        and box["zmin"] <= box["zmax"]
    ):
        raise RuntimeError(f"Invalid cluster bounding box: {key}")

    by_frame[frame].append(box)
    summary_lookup[key] = {
        "frame": frame,
        "time_s": box["time_s"],
        "track_id": box["track_id"],
        "local_cluster_id": cluster_id,
        "lidar_cluster_points": box["points"],
        "radar_matched_returns": 0,
        "radar_nonzero_doppler_matches": 0,
        "nearest_spatial_gap_m": None,
        "matched_raw_doppler_values": [],
    }

def box_distance(x, y, z, box):
    dx = max(box["xmin"] - x, 0.0, x - box["xmax"])
    dy = max(box["ymin"] - y, 0.0, y - box["ymax"])
    dz = max(box["zmin"] - z, 0.0, z - box["zmax"])
    return math.sqrt(dx*dx + dy*dy + dz*dz)

matches = []
nonzero_input = 0
unassigned = 0

for row in radar:
    frame = int(row["frame"])
    x = float(row["x_vehicle_m"])
    y = float(row["y_vehicle_m"])
    z = float(row["z_vehicle_m"])
    doppler = float(row["doppler_shift_raw"])

    if not all(math.isfinite(v) for v in (x, y, z, doppler)):
        raise RuntimeError(f"Non-finite Radar data at frame {frame}")

    if abs(doppler) > DOPPLER_EPS:
        nonzero_input += 1

    candidates = by_frame.get(frame, [])

    if not candidates:
        unassigned += 1
        continue

    # A single Radar return can support only one LiDAR cluster.
    ranked = sorted(
        (
            box_distance(x, y, z, box),
            box["track_id"],
            box["cluster_id"],
            box,
        )
        for box in candidates
    )

    distance, track_id, cluster_id, box = ranked[0]

    if distance > GATE_M:
        unassigned += 1
        continue

    key = (frame, cluster_id)
    result = summary_lookup[key]

    result["radar_matched_returns"] += 1
    result["matched_raw_doppler_values"].append(doppler)

    if abs(doppler) > DOPPLER_EPS:
        result["radar_nonzero_doppler_matches"] += 1

    if (
        result["nearest_spatial_gap_m"] is None
        or distance < result["nearest_spatial_gap_m"]
    ):
        result["nearest_spatial_gap_m"] = distance

    matches.append({
        "frame": frame,
        "time_s": row["time_s"],
        "return_index": row["return_index"],
        "track_id": track_id,
        "local_cluster_id": cluster_id,
        "radar_x_m": x,
        "radar_y_m": y,
        "radar_z_m": z,
        "radar_range_m": row["range_m"],
        "spatial_gap_to_box_m": round(distance, 6),
        "doppler_shift_raw": doppler,
        "nonzero_doppler": int(abs(doppler) > DOPPLER_EPS),
        "association_status": "PROVISIONAL_BOX_GATE"
    })

summary_rows = []

for key in sorted(summary_lookup):
    item = summary_lookup[key]
    values = item["matched_raw_doppler_values"]

    summary_rows.append({
        "frame": item["frame"],
        "time_s": item["time_s"],
        "track_id": item["track_id"],
        "local_cluster_id": item["local_cluster_id"],
        "lidar_cluster_points": item["lidar_cluster_points"],
        "radar_matched_returns": item["radar_matched_returns"],
        "radar_nonzero_doppler_matches":
            item["radar_nonzero_doppler_matches"],
        "nearest_spatial_gap_m": (
            round(item["nearest_spatial_gap_m"], 6)
            if item["nearest_spatial_gap_m"] is not None else ""
        ),
        "median_doppler_raw": (
            median(values) if values else ""
        ),
        "doppler_unit_status": "UNVERIFIED",
        "association_status": (
            "PROVISIONAL_RADAR_SPATIAL_MATCH"
            if values else "NO_RADAR_SPATIAL_MATCH"
        )
    })

match_fields = [
    "frame", "time_s", "return_index", "track_id",
    "local_cluster_id", "radar_x_m", "radar_y_m",
    "radar_z_m", "radar_range_m",
    "spatial_gap_to_box_m", "doppler_shift_raw",
    "nonzero_doppler", "association_status"
]

summary_fields = [
    "frame", "time_s", "track_id",
    "local_cluster_id", "lidar_cluster_points",
    "radar_matched_returns",
    "radar_nonzero_doppler_matches",
    "nearest_spatial_gap_m", "median_doppler_raw",
    "doppler_unit_status", "association_status"
]

with (DIR / "radar_track_matches_v1.csv").open(
    "x", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=match_fields)
    writer.writeheader()
    writer.writerows(matches)

with (DIR / "radar_track_association_summary_v1.csv").open(
    "x", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=summary_fields)
    writer.writeheader()
    writer.writerows(summary_rows)

print("=== TASK 24.9.4 RESULTS ===")
print("RADAR_INPUT_RETURNS=", len(radar))
print("RADAR_NONZERO_DOPPLER_INPUT=", nonzero_input)
print("RADAR_SPATIALLY_MATCHED=", len(matches))
print("RADAR_UNASSIGNED=", unassigned)
print("MATCHED_NONZERO_DOPPLER=", sum(
    r["nonzero_doppler"] for r in matches
))

print("\n=== TRACK-LEVEL RADAR SUMMARY ===")
track_ids = sorted(set(r["track_id"] for r in summary_rows))

for tid in track_ids:
    observations = [
        r for r in summary_rows if r["track_id"] == tid
    ]
    matched_frames = sum(
        r["radar_matched_returns"] > 0 for r in observations
    )
    nonzero_frames = sum(
        r["radar_nonzero_doppler_matches"] > 0
        for r in observations
    )
    total_matches = sum(
        r["radar_matched_returns"] for r in observations
    )

    print(
        f"TRACK={tid} "
        f"LIDAR_OBSERVATIONS={len(observations)} "
        f"RADAR_SUPPORTED_FRAMES={matched_frames} "
        f"NONZERO_DOPPLER_FRAMES={nonzero_frames} "
        f"RADAR_MATCHES={total_matches}"
    )

print("\n=== TRACK 2 RADAR OBSERVATIONS ===")
for r in summary_rows:
    if r["track_id"] == 2:
        print(
            f"FRAME={r['frame']} "
            f"MATCHES={r['radar_matched_returns']} "
            f"NONZERO={r['radar_nonzero_doppler_matches']} "
            f"RAW_DOPPLER_MEDIAN={r['median_doppler_raw']}"
        )

print("\n=== FRAME 530 ===")
for r in summary_rows:
    if r["frame"] == 530:
        print(
            f"TRACK={r['track_id']} "
            f"RADAR_MATCHES={r['radar_matched_returns']} "
            f"STATUS={r['association_status']}"
        )

print("RADAR_GATE_M=", GATE_M)
print("MATCHING_METHOD=NEAREST_LIDAR_3D_BOX")
print("TRACK_ASSOCIATION_STATUS=PROVISIONAL")
print("DOPPLER_UNITS_VERIFIED=NO")
print("DOPPLER_CONVERTED_TO_MPS=NO")
print("SIMULATOR_OBJECT_IDS_USED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_09_04_RADAR_ASSOCIATION_COMPLETE")