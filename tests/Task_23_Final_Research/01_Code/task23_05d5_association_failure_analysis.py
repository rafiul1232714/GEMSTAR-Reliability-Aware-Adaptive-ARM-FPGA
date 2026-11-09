import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS_DIR = TASK / "06_Research_Findings"

GEOMETRY = CSV_DIR / (
    "task23_05d3_candidate_association_details.csv"
)
ACTORS = CSV_DIR / (
    "task23_05d4_actor_association_details.csv"
)

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS_DIR):
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def is_true(value):
    return str(value).strip().lower() == "true"


def key_of(row):
    return (
        int(row["PairID"]),
        int(row["Frame"]),
        int(row["RadarRayIndex"])
    )


geometry_rows = read_csv(GEOMETRY)
actor_rows = read_csv(ACTORS)

geometry = {}

for row in geometry_rows:
    key = key_of(row)

    if key in geometry:
        raise RuntimeError(f"Duplicate geometry key: {key}")

    geometry[key] = row

actors = {}

for row in actor_rows:
    key = key_of(row)

    if key in actors:
        raise RuntimeError(f"Duplicate actor key: {key}")

    actors[key] = row

if set(geometry) != set(actors):
    raise RuntimeError(
        "Geometry and actor audit keys do not match"
    )

if len(geometry) != 237:
    raise RuntimeError(
        f"Expected 237 Radar returns; found {len(geometry)}"
    )


print("\n=== TASK 23.5D-5 ASSOCIATION FAILURE ANALYSIS ===")

details = []
frame_groups = defaultdict(list)
actor_distribution = Counter()
failure_patterns = Counter()

for key in sorted(geometry):
    geo = geometry[key]
    actor = actors[key]

    geometric_candidate = is_true(
        geo["CandidateAssociation"]
    )

    actor_candidate = is_true(
        actor["CandidateAssociation"]
    )

    if geometric_candidate != actor_candidate:
        raise RuntimeError(
            f"Candidate disagreement for {key}"
        )

    within_distance = is_true(geo["Within1m"])
    within_angle = is_true(geo["Within5DegBoth"])
    mutual = is_true(geo["MutualNearest"])
    local_agreement = is_true(
        actor["LocalActorAgreement"]
    )

    nearest_distance = float(
        geo["NearestDistanceM"]
    )

    bearing_error = float(
        geo["BearingErrorDeg"]
    )

    elevation_error = float(
        geo["ElevationErrorDeg"]
    )

    actor_id = actor["NearestLiDARActorID"].strip()

    reasons = []

    if not within_distance:
        reasons.append("DISTANCE")

    if not within_angle:
        reasons.append("ANGLE")

    if not mutual:
        reasons.append("NON_MUTUAL")

    if geometric_candidate:
        if local_agreement:
            category = "GEOMETRIC_AND_LOCAL_ACTOR_AGREEMENT"
        else:
            category = "GEOMETRIC_WITHOUT_LOCAL_ACTOR_AGREEMENT"
    else:
        category = "GEOMETRIC_REJECTED"

    if geometric_candidate and not reasons:
        failure_type = "NONE"
    else:
        failure_type = "+".join(reasons)

    if not geometric_candidate:
        failure_patterns[failure_type] += 1

    if geometric_candidate:
        actor_distribution[
            (key[0], key[1], actor_id or "MISSING")
        ] += 1

    item = {
        "PairID": key[0],
        "Frame": key[1],
        "RadarRayIndex": key[2],
        "Category": category,
        "FailurePattern": failure_type,
        "GeometricCandidate": geometric_candidate,
        "LocalActorAgreement": local_agreement,
        "NearestLiDARActorID": actor_id,
        "NearestDistanceM": nearest_distance,
        "BearingErrorDeg": bearing_error,
        "ElevationErrorDeg": elevation_error,
        "Within1m": within_distance,
        "Within5DegBoth": within_angle,
        "MutualNearest": mutual,
        "LocalNeighborCount": int(
            actor["LocalLiDARNeighborsWithin1mTop5"]
        ),
        "UsableActorIDNeighbors": int(
            actor["LocalNeighborsWithActorID"]
        ),
        "LocalSameActorFraction": (
            float(actor["LocalSameActorFraction"])
            if actor["LocalSameActorFraction"]
            not in ("", "None")
            else None
        ),
    }

    details.append(item)
    frame_groups[key[:2]].append(item)


frame_summaries = []

for pair in (1, 2, 3):
    for frame in (25, 99):
        rows = frame_groups[(pair, frame)]

        if not rows:
            raise RuntimeError(
                f"No Radar data for P{pair}/F{frame}"
            )

        accepted = sum(
            r["GeometricCandidate"] for r in rows
        )

        consistent = sum(
            r["GeometricCandidate"]
            and r["LocalActorAgreement"]
            for r in rows
        )

        rejected = len(rows) - accepted

        inconsistent = accepted - consistent

        frame_summaries.append({
            "PairID": pair,
            "Frame": frame,
            "RadarReturns": len(rows),
            "GeometricAccepted": accepted,
            "GeometricRejected": rejected,
            "LocalActorConsistent": consistent,
            "CandidateWithoutActorAgreement": inconsistent,
            "RejectedDistance": sum(
                not r["Within1m"]
                for r in rows
            ),
            "RejectedAngle": sum(
                not r["Within5DegBoth"]
                for r in rows
            ),
            "RejectedNonMutual": sum(
                not r["MutualNearest"]
                for r in rows
            ),
        })

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Radar={len(rows)} | "
            f"Accepted={accepted} | "
            f"Rejected={rejected} | "
            f"ActorConsistent={consistent} | "
            f"ActorDisagreement={inconsistent}"
        )


accepted_total = sum(
    r["GeometricAccepted"] for r in frame_summaries
)

rejected_total = sum(
    r["GeometricRejected"] for r in frame_summaries
)

consistent_total = sum(
    r["LocalActorConsistent"] for r in frame_summaries
)

inconsistent_total = sum(
    r["CandidateWithoutActorAgreement"]
    for r in frame_summaries
)

assert accepted_total == 197
assert rejected_total == 40
assert consistent_total == 193
assert inconsistent_total == 4


failure_rows = [
    r for r in details
    if (
        not r["GeometricCandidate"]
        or not r["LocalActorAgreement"]
    )
]

# Some rejected returns may nevertheless exhibit local
# actor agreement. Preserve the category distinction.
inconsistent_candidates = [
    r for r in details
    if (
        r["GeometricCandidate"]
        and not r["LocalActorAgreement"]
    )
]

rejected_returns = [
    r for r in details
    if not r["GeometricCandidate"]
]

actor_summary = []

for (pair, frame, actor_id), count in sorted(
    actor_distribution.items()
):
    actor_summary.append({
        "PairID": pair,
        "Frame": frame,
        "AssignedNearestLiDARActorID": actor_id,
        "GeometricCandidateReturns": count,
        "AssignmentMethod": "NEAREST_LIDAR_METADATA",
        "IndependentRadarActorIdentity": False,
    })


detail_path = CSV_DIR / (
    "task23_05d5_association_classification.csv"
)

failure_path = CSV_DIR / (
    "task23_05d5_failure_cases.csv"
)

frame_path = CSV_DIR / (
    "task23_05d5_frame_summary.csv"
)

actor_path = CSV_DIR / (
    "task23_05d5_candidate_actor_distribution.csv"
)

write_csv(detail_path, details, list(details[0]))
write_csv(failure_path, failure_rows, list(details[0]))
write_csv(
    frame_path, frame_summaries,
    list(frame_summaries[0])
)
write_csv(
    actor_path, actor_summary,
    [
        "PairID",
        "Frame",
        "AssignedNearestLiDARActorID",
        "GeometricCandidateReturns",
        "AssignmentMethod",
        "IndependentRadarActorIdentity",
    ]
)


# Graph 1: classify all Radar returns.
labels = [
    f"P{r['PairID']}/F{r['Frame']}"
    for r in frame_summaries
]

consistent = [
    r["LocalActorConsistent"]
    for r in frame_summaries
]

inconsistent = [
    r["CandidateWithoutActorAgreement"]
    for r in frame_summaries
]

rejected = [
    r["GeometricRejected"]
    for r in frame_summaries
]

x = np.arange(len(labels))

fig, ax = plt.subplots(figsize=(11, 6))

ax.bar(
    x, consistent,
    label="Geometric + local ID agreement"
)

ax.bar(
    x, inconsistent,
    bottom=consistent,
    label="Geometric, local ID disagreement"
)

bottom = np.array(consistent) + np.array(inconsistent)

ax.bar(
    x, rejected,
    bottom=bottom,
    label="Geometrically rejected"
)

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Radar return count")
ax.set_title(
    "Radar-LiDAR association outcome classification"
)
ax.grid(axis="y", alpha=0.2)
ax.legend()

fig.tight_layout()

graph1 = GRAPH_DIR / (
    "task23_05d5_association_outcomes.png"
)

fig.savefig(graph1, dpi=180)
plt.close(fig)


# Graph 2: rejection reasons can overlap.
reason_labels = ["DISTANCE", "ANGLE", "NON_MUTUAL"]

reason_counts = [
    sum(not r["Within1m"] for r in rejected_returns),
    sum(not r["Within5DegBoth"] for r in rejected_returns),
    sum(not r["MutualNearest"] for r in rejected_returns),
]

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(reason_labels, reason_counts)
ax.set_ylabel("Rejected returns exhibiting reason")
ax.set_title(
    "Geometric association rejection reasons "
    "(overlap allowed)"
)
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()

graph2 = GRAPH_DIR / (
    "task23_05d5_rejection_reasons.png"
)

fig.savefig(graph2, dpi=180)
plt.close(fig)


# Research findings.
top_actors = Counter()

for row in actor_summary:
    top_actors[row["AssignedNearestLiDARActorID"]] += (
        row["GeometricCandidateReturns"]
    )

findings = {
    "Task": "23.5D-5",
    "Status": "ASSOCIATION_FAILURE_AND_AMBIGUITY_AUDIT",
    "TotalRadarReturns": len(details),
    "GeometricAccepted": accepted_total,
    "GeometricRejected": rejected_total,
    "CandidatesWithLocalActorAgreement": consistent_total,
    "CandidatesWithoutLocalActorAgreement": inconsistent_total,
    "FrameSummaries": frame_summaries,
    "FailurePatterns": dict(failure_patterns),
    "TopAssignedLiDARActors": [
        {
            "ActorID": actor_id,
            "CandidateCount": count
        }
        for actor_id, count in top_actors.most_common()
    ],
    "ImportantInterpretation": (
        "Local LiDAR actor-ID consistency is not "
        "an independently validated Radar target identity."
    ),
    "ScientificLimitations": [
        "No independently labeled Radar-LiDAR correspondence",
        "Distance and angular gates are heuristic",
        "Rejection reasons can overlap",
        "Local agreement depends on five nearest LiDAR samples",
        "A single large map actor may dominate associations",
        "Six frames are insufficient to establish general accuracy",
        "No measured fusion accuracy or FPGA energy savings"
    ],
}

findings_path = FINDINGS_DIR / (
    "task23_05d5_association_failure_findings.json"
)

findings_path.write_text(
    json.dumps(findings, indent=2),
    encoding="utf-8"
)


print("\n=== REJECTION REASONS ===")
for reason, count in failure_patterns.most_common():
    print(f"{reason}: {count}")

print("\n=== GEOMETRIC CANDIDATES WITHOUT LOCAL ID AGREEMENT ===")

for row in inconsistent_candidates:
    print(
        f"P{row['PairID']} F{row['Frame']:02d} "
        f"Ray={row['RadarRayIndex']} "
        f"Actor={row['NearestLiDARActorID']} "
        f"Distance={row['NearestDistanceM']:.4f}m "
        f"LocalPurity={row['LocalSameActorFraction']}"
    )

print("\n=== TOP NEAREST-LIDAR ACTOR IDS ===")

for actor_id, count in top_actors.most_common(10):
    print(f"Actor {actor_id}: {count} geometric candidates")


print("\n=== TASK 23.5D-5 FINAL VERIFICATION ===")
print("Radar returns classified:", len(details))
print("Geometric candidates:", accepted_total)
print("Geometric rejections:", rejected_total)
print("Candidates with local actor agreement:", consistent_total)
print("Candidates without local actor agreement:", inconsistent_total)
print("Failure-case rows:", len(failure_rows))
print("Unique assigned actor IDs:", len(top_actors))
print("Classification CSV saved:", detail_path.is_file())
print("Failure-case CSV saved:", failure_path.is_file())
print("Frame-summary CSV saved:", frame_path.is_file())
print("Actor-distribution CSV saved:", actor_path.is_file())
print("Graphs saved:", graph1.is_file() and graph2.is_file())
print("Findings JSON saved:", findings_path.is_file())

assert len(details) == 237
assert len(rejected_returns) == 40
assert len(inconsistent_candidates) == 4
assert len(failure_rows) == 44

print("\n=== TASK 23.5D-5 COMPLETE ===")
