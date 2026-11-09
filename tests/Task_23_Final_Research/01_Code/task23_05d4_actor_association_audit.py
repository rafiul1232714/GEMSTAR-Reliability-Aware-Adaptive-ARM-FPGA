import csv
import json
import sys
from collections import Counter, defaultdict
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
GRAPHS = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

RADAR_DIR = (
    TASK / "08_Processed_Data"
    / "Radar_3D_Source_Matched"
)

LIDAR_DIR = (
    TASK / "08_Processed_Data"
    / "LiDAR_Vehicle_Source_Verified"
)

MANIFEST = (
    TASK / "05_Raw_Data_References"
    / "task23_01_source_manifest.csv"
)

ASSOCIATIONS = (
    CSV_DIR /
    "task23_05d3_candidate_association_details.csv"
)

for directory in (CSV_DIR, GRAPHS, FINDINGS):
    directory.mkdir(parents=True, exist_ok=True)

PAIRS = (1, 2, 3)
FRAMES = (25, 99)
K = 5
LOCAL_RADIUS_M = 1.0
SENTINEL = (1 << 64) - 1


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def is_true(value):
    return str(value).strip().lower() == "true"


manifest = {
    int(r["PairID"]): r for r in read_csv(MANIFEST)
}

association_by_frame = defaultdict(list)

for row in read_csv(ASSOCIATIONS):
    key = (int(row["PairID"]), int(row["Frame"]))
    if key in {
        (p, f) for p in PAIRS for f in FRAMES
    }:
        association_by_frame[key].append(row)

detail = []
summary = []
actor_counts = Counter()

print("\n=== TASK 23.5D-4 ACTOR-ID ASSOCIATION AUDIT ===")

for pair in PAIRS:
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
            raise RuntimeError(f"Missing SensorView frame {key}")

        lidar_reflections = (
            sv_frames[frame].lidar_sensor_view[0].reflection
        )

        radar_path = RADAR_DIR / (
            f"pair{pair}_frame{frame:03d}_radar_3d.npz"
        )

        lidar_path = LIDAR_DIR / (
            f"pair{pair}_frame{frame:03d}_vehicle_osi.npz"
        )

        with np.load(radar_path, allow_pickle=False) as d:
            radar_xyz = d["points_vehicle_osi_m"].copy()
            radar_ray = d["valid_ray_indices"].copy()

        with np.load(lidar_path, allow_pickle=False) as d:
            lidar_xyz = d["points_vehicle_osi_m"].copy()
            lidar_ray = d["valid_ray_indices"].copy()

        if any(
            x.ndim != 2 or x.shape[1] != 3
            for x in (radar_xyz, lidar_xyz)
        ):
            raise RuntimeError(f"Invalid point shape {key}")

        if not (
            np.isfinite(radar_xyz).all()
            and np.isfinite(lidar_xyz).all()
        ):
            raise RuntimeError(f"Nonfinite point {key}")

        if (
            len(lidar_xyz) != len(lidar_ray)
            or len(radar_xyz) != len(radar_ray)
        ):
            raise RuntimeError(f"Ray/point mismatch {key}")

        if len(lidar_xyz) < K:
            raise RuntimeError(f"Too few LiDAR points {key}")

        if len(lidar_ray) and (
            np.max(lidar_ray) >= len(lidar_reflections)
        ):
            raise RuntimeError(f"LiDAR ray out of bounds {key}")

        lidar_ids = []

        for ray in lidar_ray:
            reflection = lidar_reflections[int(ray)]

            if reflection.HasField("object_id"):
                value = int(reflection.object_id.value)
            else:
                value = SENTINEL

            lidar_ids.append(value)

        lidar_ids = np.array(lidar_ids, dtype=np.uint64)

        # Reuse previous candidate decisions, with a strict
        # one-row-per-Radar-ray consistency check.
        previous = association_by_frame[key]

        by_ray = {
            int(r["RadarRayIndex"]): r
            for r in previous
        }

        if (
            len(previous) != len(radar_xyz)
            or len(by_ray) != len(radar_xyz)
        ):
            raise RuntimeError(
                f"Previous association count mismatch {key}"
            )

        candidate_count = 0
        local_agreement_count = 0

        for index, point in enumerate(radar_xyz):
            ray = int(radar_ray[index])

            if ray not in by_ray:
                raise RuntimeError(
                    f"Missing candidate row for ray {ray}: {key}"
                )

            old = by_ray[ray]
            candidate = is_true(old["CandidateAssociation"])

            distances = np.linalg.norm(
                lidar_xyz - point, axis=1
            )

            nearest_indices = np.argsort(distances)[:K]
            nearest = int(nearest_indices[0])

            nearest_ray = int(lidar_ray[nearest])
            nearest_actor = int(lidar_ids[nearest])

            if nearest_ray != int(
                old["NearestLiDARRayIndex"]
            ):
                raise RuntimeError(
                    f"Nearest ray changed at {key}, ray {ray}"
                )

            previous_distance = float(
                old["NearestDistanceM"]
            )

            if abs(
                float(distances[nearest]) - previous_distance
            ) > 1e-7:
                raise RuntimeError(
                    f"Nearest distance mismatch at {key}"
                )

            local_indices = [
                int(i) for i in nearest_indices
                if distances[int(i)] <= LOCAL_RADIUS_M
            ]

            local_ids = [
                int(lidar_ids[i])
                for i in local_indices
                if int(lidar_ids[i]) != SENTINEL
            ]

            valid_nearest_id = nearest_actor != SENTINEL

            if local_ids and valid_nearest_id:
                same_count = sum(
                    actor_id == nearest_actor
                    for actor_id in local_ids
                )
                local_purity = same_count / len(local_ids)
                local_agreement = (
                    len(local_ids) >= 2
                    and local_purity == 1.0
                )
            else:
                local_purity = None
                local_agreement = False

            if candidate:
                candidate_count += 1
                actor_counts[
                    (pair, frame, nearest_actor)
                ] += 1

                if local_agreement:
                    local_agreement_count += 1

            detail.append({
                "PairID": pair,
                "Frame": frame,
                "RadarRayIndex": ray,
                "CandidateAssociation": candidate,
                "NearestLiDARRayIndex": nearest_ray,
                "NearestLiDARActorID": (
                    str(nearest_actor)
                    if valid_nearest_id else ""
                ),
                "NearestDistanceM": float(distances[nearest]),
                "LocalLiDARNeighborsWithin1mTop5": len(local_indices),
                "LocalNeighborsWithActorID": len(local_ids),
                "LocalSameActorFraction": local_purity,
                "LocalActorAgreement": bool(local_agreement),
                "ActorIdentityIndependentlyVerified": False,
            })

        summary.append({
            "PairID": pair,
            "Frame": frame,
            "RadarPoints": len(radar_xyz),
            "LiDARPoints": len(lidar_xyz),
            "PreviousCandidateAssociations": candidate_count,
            "CandidatesWithLocalActorAgreement": (
                local_agreement_count
            ),
            "CandidateLocalAgreementFraction": (
                local_agreement_count / candidate_count
                if candidate_count else None
            ),
        })

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Radar={len(radar_xyz)} | "
            f"Candidates={candidate_count} | "
            f"LocalActorAgreement={local_agreement_count}"
        )


actor_rows = []

for (pair, frame, actor_id), count in sorted(
    actor_counts.items()
):
    actor_rows.append({
        "PairID": pair,
        "Frame": frame,
        "LiDARActorID": (
            str(actor_id) if actor_id != SENTINEL else ""
        ),
        "CandidateRadarReturns": count,
    })


detail_path = CSV_DIR / (
    "task23_05d4_actor_association_details.csv"
)

summary_path = CSV_DIR / (
    "task23_05d4_actor_association_summary.csv"
)

actor_path = CSV_DIR / (
    "task23_05d4_actor_candidate_counts.csv"
)

save_csv(detail_path, detail, list(detail[0]))
save_csv(summary_path, summary, list(summary[0]))

save_csv(
    actor_path, actor_rows,
    ["PairID", "Frame", "LiDARActorID", "CandidateRadarReturns"]
)


labels = [
    f"P{r['PairID']}/F{r['Frame']}"
    for r in summary
]

x = np.arange(len(summary))

fig, ax = plt.subplots(figsize=(10, 5))

ax.bar(
    x - 0.2,
    [r["PreviousCandidateAssociations"] for r in summary],
    width=0.4,
    label="Geometric candidates"
)

ax.bar(
    x + 0.2,
    [r["CandidatesWithLocalActorAgreement"] for r in summary],
    width=0.4,
    label="Candidates with local ID agreement"
)

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Radar return count")
ax.set_title(
    "Radar-LiDAR candidate and actor-metadata consistency"
)
ax.grid(axis="y", alpha=0.25)
ax.legend()
fig.tight_layout()

graph_path = GRAPHS / (
    "task23_05d4_actor_association_consistency.png"
)

fig.savefig(graph_path, dpi=180)
plt.close(fig)


candidate_total = sum(
    r["PreviousCandidateAssociations"] for r in summary
)

local_total = sum(
    r["CandidatesWithLocalActorAgreement"] for r in summary
)

findings_path = FINDINGS / (
    "task23_05d4_actor_association_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.5D-4",
        "Status": "SIMULATOR_METADATA_SUPPORTED_ASSOCIATION_AUDIT",
        "TotalRadarPoints": len(detail),
        "GeometricCandidateAssociations": candidate_total,
        "CandidatesWithLocalActorAgreement": local_total,
        "LocalActorAgreementDefinition": (
            "At least two of the five nearest LiDAR points "
            "within 1 metre have usable actor IDs, and all "
            "those usable IDs equal the nearest point's ID."
        ),
        "FrameSummaries": summary,
        "ScientificLimitations": [
            "Radar itself does not supply an actor ID here",
            "Assigned IDs originate from nearby LiDAR reflections",
            "Local ID agreement does not establish correct object association",
            "The five-neighbor test is an exploratory heuristic",
            "Only six sampled frames were analyzed",
            "GroundTruth actor-ID mappings remain unresolved",
            "No fusion accuracy or hardware energy savings demonstrated"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5D-4 FINAL VERIFICATION ===")
print("Radar points examined:", len(detail))
print("Geometric candidates:", candidate_total)
print("Candidates with local actor agreement:", local_total)
print("Detailed CSV saved:", detail_path.is_file())
print("Summary CSV saved:", summary_path.is_file())
print("Actor counts CSV saved:", actor_path.is_file())
print("Graph saved:", graph_path.is_file())
print("Findings JSON saved:", findings_path.is_file())

if len(detail) != 237 or candidate_total != 197:
    raise RuntimeError(
        "Results do not match Task 23.5D-3"
    )

print("\n=== TASK 23.5D-4 COMPLETE ===")
