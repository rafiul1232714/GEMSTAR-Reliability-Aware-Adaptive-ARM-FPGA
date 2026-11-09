import csv
import math
from pathlib import Path
from collections import defaultdict, deque
from statistics import median

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

CELL_M = 0.50
MIN_POINTS = 8

# Exploratory region and height filtering, not a calibrated
# ground-segmentation or object-classification method.
X_MIN, X_MAX = 3.0, 60.0
Y_LIMIT = 15.0
Z_MIN, Z_MAX = 0.45, 3.50

frames = {}
with (DIR / "selected_frames.csv").open(
    newline="", encoding="utf-8-sig"
) as f:
    for row in csv.DictReader(f):
        frame = int(row["frame"])
        if frame in frames:
            raise RuntimeError("Duplicate selected frame")
        frames[frame] = float(row["time_s"])

if len(frames) != 53:
    raise RuntimeError("Expected 53 selected frames")

points_by_frame = defaultdict(list)
total_input = 0
filtered_points = 0

with (DIR / "lidar_points.csv").open(
    newline="", encoding="utf-8-sig"
) as f:
    for row in csv.DictReader(f):
        total_input += 1
        frame = int(row["frame"])
        if frame not in frames:
            raise RuntimeError("Unexpected LiDAR frame")

        x = float(row["x_vehicle_m"])
        y = float(row["y_vehicle_m"])
        z = float(row["z_vehicle_m"])

        if not all(math.isfinite(v) for v in (x, y, z)):
            continue

        if not (
            X_MIN <= x <= X_MAX
            and abs(y) <= Y_LIMIT
            and Z_MIN <= z <= Z_MAX
        ):
            continue

        points_by_frame[frame].append((x, y, z))
        filtered_points += 1


def cluster_frame(points):
    cells = defaultdict(list)

    for p in points:
        key = (
            math.floor(p[0] / CELL_M),
            math.floor(p[1] / CELL_M)
        )
        cells[key].append(p)

    visited = set()
    components = []

    for start in sorted(cells):
        if start in visited:
            continue

        visited.add(start)
        queue = deque([start])
        members = []

        while queue:
            key = queue.popleft()
            members.extend(cells[key])

            x, y = key

            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = (x + dx, y + dy)

                    if (
                        neighbor in cells
                        and neighbor not in visited
                    ):
                        visited.add(neighbor)
                        queue.append(neighbor)

        if len(members) >= MIN_POINTS:
            components.append(members)

    # Deterministic ordering; not target identity.
    components.sort(
        key=lambda ps: (
            -len(ps),
            median(p[0] for p in ps),
            median(p[1] for p in ps)
        )
    )

    return components


candidate_rows = []
summary_rows = []

for frame in sorted(frames):
    points = points_by_frame[frame]
    clusters = cluster_frame(points)

    for cluster_id, cluster in enumerate(clusters):
        xs = [p[0] for p in cluster]
        ys = [p[1] for p in cluster]
        zs = [p[2] for p in cluster]

        candidate_rows.append({
            "frame": frame,
            "time_s": frames[frame],
            "local_cluster_id": cluster_id,
            "point_count": len(cluster),
            "median_x_m": round(median(xs), 5),
            "median_y_m": round(median(ys), 5),
            "median_z_m": round(median(zs), 5),
            "min_x_m": round(min(xs), 5),
            "max_x_m": round(max(xs), 5),
            "min_y_m": round(min(ys), 5),
            "max_y_m": round(max(ys), 5),
            "min_z_m": round(min(zs), 5),
            "max_z_m": round(max(zs), 5),
            "status": "UNVALIDATED_GEOMETRIC_CANDIDATE"
        })

    summary_rows.append({
        "frame": frame,
        "time_s": frames[frame],
        "filtered_points": len(points),
        "clusters_found": len(clusters),
        "largest_cluster_points": (
            len(clusters[0]) if clusters else 0
        ),
        "retained_cluster_points": sum(
            len(cluster) for cluster in clusters
        )
    })

    print(
        f"FRAME={frame} "
        f"FILTERED_POINTS={len(points)} "
        f"CLUSTERS={len(clusters)} "
        f"LARGEST={len(clusters[0]) if clusters else 0}"
    )

candidate_fields = [
    "frame", "time_s", "local_cluster_id",
    "point_count", "median_x_m", "median_y_m",
    "median_z_m", "min_x_m", "max_x_m",
    "min_y_m", "max_y_m", "min_z_m", "max_z_m",
    "status"
]

summary_fields = [
    "frame", "time_s", "filtered_points",
    "clusters_found", "largest_cluster_points",
    "retained_cluster_points"
]

with (
    DIR / "lidar_cluster_candidates_v1.csv"
).open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=candidate_fields)
    writer.writeheader()
    writer.writerows(candidate_rows)

with (
    DIR / "lidar_clustering_summary_v1.csv"
).open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=summary_fields)
    writer.writeheader()
    writer.writerows(summary_rows)

frame530 = [
    r for r in candidate_rows if r["frame"] == 530
]

print("\n=== TASK 24.9.2 SUMMARY ===")
print("FRAMES_PROCESSED=", len(summary_rows))
print("INPUT_LIDAR_ROWS=", total_input)
print("FILTERED_POINTS=", filtered_points)
print("TOTAL_CLUSTER_CANDIDATES=", len(candidate_rows))
print("FRAME530_CLUSTER_COUNT=", len(frame530))

print("\n=== FRAME 530 NEAREST 10 CLUSTERS ===")
for row in sorted(
    frame530,
    key=lambda r: (
        abs(r["median_x_m"] - 24.175),
        abs(r["median_y_m"] + 0.135)
    )
)[:10]:
    print(
        "CLUSTER_ID=", row["local_cluster_id"],
        "POINTS=", row["point_count"],
        "XYZ=", (
            row["median_x_m"],
            row["median_y_m"],
            row["median_z_m"]
        )
    )

print("GROUND_TRUTH_USED=NO")
print("OBJECT_IDS_USED=NO")
print("TEMPORAL_TRACKING_PERFORMED=NO")
print("CLUSTER_IDS_ARE_FRAME_LOCAL=YES")
print("INPUT_FILES_MODIFIED=NO")
print("TASK24_09_02_CLUSTERING_COMPLETE")