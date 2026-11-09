import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

WORLD_DIR = (
    TASK / "08_Processed_Data"
    / "LiDAR_World_Candidate"
)

MANIFEST = (
    TASK / "05_Raw_Data_References"
    / "task23_01_source_manifest.csv"
)

for directory in (CSV_DIR, GRAPH_DIR, FINDINGS):
    directory.mkdir(parents=True, exist_ok=True)

FRAMES = (1, 25, 99)
SENTINEL = (1 << 64) - 1


def read_csv(path):
    with path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, columns):
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


manifest = {
    int(row["PairID"]): row
    for row in read_csv(MANIFEST)
}

groups = []
point_cache = {}
actor_observations = defaultdict(set)

print("\n=== TASK 23.4E-5F ACTOR SPATIAL AUDIT ===")

for pair in (1, 2, 3):
    sv_frames = {
        index: msg
        for index, msg, _ in iter_osi_messages(
            Path(manifest[pair]["SensorViewPath"]),
            SensorView,
            100
        )
        if index in FRAMES
    }

    for frame in FRAMES:
        key = (pair, frame)

        if frame not in sv_frames:
            raise RuntimeError(f"Missing SV frame {key}")

        sv = sv_frames[frame]

        if len(sv.lidar_sensor_view) != 1:
            raise RuntimeError(f"Unexpected LiDAR count {key}")

        reflections = sv.lidar_sensor_view[0].reflection

        npz_path = WORLD_DIR / (
            f"pair{pair}_frame{frame:03d}_"
            "world_candidate.npz"
        )

        with np.load(npz_path, allow_pickle=False) as d:
            xyz = d["points_world_candidate_m"].copy()
            ray_indices = d["valid_ray_indices"].copy()
            host_pos = d["host_position_osi_m"].copy()

        if len(xyz) != len(ray_indices):
            raise RuntimeError(f"Ray count mismatch {key}")

        if not np.isfinite(xyz).all():
            raise RuntimeError(f"Nonfinite points {key}")

        ids = np.array([
            int(reflections[int(i)].object_id.value)
            if reflections[int(i)].HasField("object_id")
            else SENTINEL
            for i in ray_indices
        ], dtype=np.uint64)

        if np.any(ids == SENTINEL):
            raise RuntimeError(
                f"Unexpected missing actor ID {key}"
            )

        point_cache[key] = {
            "rays": ray_indices,
            "ids": ids,
            "xyz": xyz,
            "host": host_pos,
        }

        counts = []

        for actor_id in np.unique(ids):
            subset = xyz[ids == actor_id]

            center = np.median(subset, axis=0)
            minimum = np.min(subset, axis=0)
            maximum = np.max(subset, axis=0)
            extent = maximum - minimum

            actor_id = int(actor_id)

            actor_observations[actor_id].add(key)

            groups.append({
                "PairID": pair,
                "Frame": frame,
                "ActorID": actor_id,
                "PointCount": int(len(subset)),
                "MedianX": float(center[0]),
                "MedianY": float(center[1]),
                "MedianZ": float(center[2]),
                "ExtentX": float(extent[0]),
                "ExtentY": float(extent[1]),
                "ExtentZ": float(extent[2]),
                "MinX": float(minimum[0]),
                "MinY": float(minimum[1]),
                "MinZ": float(minimum[2]),
                "MaxX": float(maximum[0]),
                "MaxY": float(maximum[1]),
                "MaxZ": float(maximum[2]),
            })

            counts.append((actor_id, len(subset)))

        counts.sort(key=lambda x: x[1], reverse=True)

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Points={len(xyz)} | "
            f"UniqueActorIDs={len(counts)} | "
            f"Top={counts[:5]}"
        )


# Cross-recording check specifically for frame 1.
# Corresponding ray indices are compared, not
# unrelated nearest-neighbor points.
comparisons = []

for pair_a, pair_b in ((1, 2), (1, 3), (2, 3)):
    a = point_cache[(pair_a, 1)]
    b = point_cache[(pair_b, 1)]

    common, ia, ib = np.intersect1d(
        a["rays"],
        b["rays"],
        return_indices=True
    )

    if not len(common):
        raise RuntimeError(
            "No common frame-1 ray indices"
        )

    id_equal = a["ids"][ia] == b["ids"][ib]

    coordinate_differences = np.linalg.norm(
        a["xyz"][ia] - b["xyz"][ib],
        axis=1
    )

    host_difference = float(np.linalg.norm(
        a["host"] - b["host"]
    ))

    result = {
        "PairA": pair_a,
        "PairB": pair_b,
        "Frame": 1,
        "CommonRayIndices": int(len(common)),
        "MatchingActorIDs": int(np.count_nonzero(id_equal)),
        "ActorIDAgreementFraction": float(np.mean(id_equal)),
        "HostPositionDifferenceM": host_difference,
        "MedianPointDifferenceM": float(
            np.median(coordinate_differences)
        ),
        "MaximumPointDifferenceM": float(
            np.max(coordinate_differences)
        ),
    }

    comparisons.append(result)

    print(
        f"Frame 1 pair {pair_a} vs {pair_b} | "
        f"CommonRays={result['CommonRayIndices']} | "
        f"IDAgreement="
        f"{result['ActorIDAgreementFraction']:.4f} | "
        f"MedianXYZDifference="
        f"{result['MedianPointDifferenceM']:.6f} m"
    )


# Actor-ID recurrence summary.
actor_summary = []

for actor_id, observations in sorted(
    actor_observations.items()
):
    pair_set = {p for p, f in observations}
    frame_set = {f for p, f in observations}

    actor_summary.append({
        "ActorID": actor_id,
        "ObservationCount": len(observations),
        "RecordingPairs": len(pair_set),
        "SampledFrames": len(frame_set),
        "PresentAllThreePairs": len(pair_set) == 3,
        "StaticActorStatus": "NOT_VERIFIED",
    })


group_path = CSV_DIR / (
    "task23_04e5f_actor_spatial_groups.csv"
)

comparison_path = CSV_DIR / (
    "task23_04e5f_frame1_pair_consistency.csv"
)

recurrence_path = CSV_DIR / (
    "task23_04e5f_actor_recurrence.csv"
)

save_csv(group_path, groups, list(groups[0]))
save_csv(
    comparison_path,
    comparisons,
    list(comparisons[0])
)
save_csv(
    recurrence_path,
    actor_summary,
    list(actor_summary[0])
)


# Graph: actor labels and world-coordinate points
# for pair 1, frame 25.
sample = point_cache[(1, 25)]
fig, ax = plt.subplots(figsize=(10, 7))

for actor_id in np.unique(sample["ids"]):
    mask = sample["ids"] == actor_id
    pts = sample["xyz"][mask]

    ax.scatter(
        pts[:, 0],
        pts[:, 1],
        s=2,
        alpha=0.6,
        label=f"Actor {int(actor_id)}"
    )

ax.scatter(
    sample["host"][0],
    sample["host"][1],
    marker="x",
    s=90,
    c="black",
    label="Host vehicle"
)

ax.set_xlabel("World X (m)")
ax.set_ylabel("World Y (m)")
ax.set_title(
    "Pair 1, frame 25: LiDAR points grouped "
    "by simulator actor ID"
)
ax.set_aspect("equal", adjustable="box")
ax.grid(alpha=0.25)
ax.legend(markerscale=3, fontsize=8)

fig.tight_layout()

graph_path = GRAPH_DIR / (
    "task23_04e5f_actor_id_world_distribution.png"
)

fig.savefig(graph_path, dpi=180)
plt.close(fig)


findings_path = FINDINGS / (
    "task23_04e5f_actor_spatial_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-5F",
        "Status": "ACTOR_ID_SPATIAL_REPEATABILITY_AUDIT",
        "TotalValidPoints": sum(
            len(item["xyz"])
            for item in point_cache.values()
        ),
        "UniqueActorIDs": len(actor_summary),
        "ActorObservations": len(groups),
        "Frame1CrossRecordingComparisons": comparisons,
        "Limitations": [
            "Repeated actor IDs do not prove actor stationarity",
            "World rotation convention is still provisional",
            "Centroids depend on visibility and sampled surfaces",
            "Same-frame agreement is simulation repeatability",
            "No independent target-surface accuracy tested",
            "No real-sensor performance or energy measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-5F FINAL VERIFICATION ===")
print("Total valid points:", sum(
    len(item["xyz"])
    for item in point_cache.values()
))
print("Unique actor IDs:", len(actor_summary))
print("Actor-frame groups:", len(groups))
print("Frame-1 comparisons:", len(comparisons))
print("Spatial group CSV:", group_path.is_file())
print("Recurrence CSV:", recurrence_path.is_file())
print("Comparison CSV:", comparison_path.is_file())
print("Distribution graph:", graph_path.is_file())
print("Findings JSON:", findings_path.is_file())

print("\n=== TASK 23.4E-5F COMPLETE ===")
