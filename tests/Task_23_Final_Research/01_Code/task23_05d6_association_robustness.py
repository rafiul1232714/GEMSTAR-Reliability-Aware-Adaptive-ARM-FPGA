import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

INPUT = CSV_DIR / (
    "task23_05d5_association_classification.csv"
)

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows):
    if not rows:
        raise RuntimeError("Cannot save empty CSV")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)


def to_bool(value):
    return str(value).strip().lower() == "true"


rows = read_csv(INPUT)

if len(rows) != 237:
    raise RuntimeError(
        f"Expected 237 Radar returns; found {len(rows)}"
    )

keys = [
    (
        int(r["PairID"]),
        int(r["Frame"]),
        int(r["RadarRayIndex"])
    )
    for r in rows
]

if len(set(keys)) != len(keys):
    raise RuntimeError("Duplicate Radar return keys")

distance = np.array([
    float(r["NearestDistanceM"])
    for r in rows
], dtype=float)

bearing = np.array([
    float(r["BearingErrorDeg"])
    for r in rows
], dtype=float)

elevation = np.array([
    float(r["ElevationErrorDeg"])
    for r in rows
], dtype=float)

mutual = np.array([
    to_bool(r["MutualNearest"])
    for r in rows
], dtype=bool)

original_candidate = np.array([
    to_bool(r["GeometricCandidate"])
    for r in rows
], dtype=bool)

local_agreement = np.array([
    to_bool(r["LocalActorAgreement"])
    for r in rows
], dtype=bool)

actor_ids = [
    r["NearestLiDARActorID"].strip()
    or "MISSING"
    for r in rows
]

if not all(np.isfinite(a).all() for a in (
    distance, bearing, elevation
)):
    raise RuntimeError("Nonfinite association measurements")


def candidate_mask(distance_gate, angle_gate, require_mutual):
    accepted = (
        (distance <= distance_gate)
        & (bearing <= angle_gate)
        & (elevation <= angle_gate)
    )
    if require_mutual:
        accepted &= mutual
    return accepted


baseline = candidate_mask(1.0, 5.0, True)

if not np.array_equal(baseline, original_candidate):
    raise RuntimeError(
        "Recomputed baseline differs from Task 23.5D-5"
    )

if int(baseline.sum()) != 197:
    raise RuntimeError("Expected 197 baseline candidates")

if int(np.count_nonzero(baseline & local_agreement)) != 193:
    raise RuntimeError("Expected 193 local-consistent candidates")


DISTANCE_GATES = (0.25, 0.5, 1.0, 2.0)
ANGLE_GATES = (2.0, 5.0, 10.0)
MUTUAL_MODES = (True, False)

results = []

print("\n=== TASK 23.5D-6 ROBUSTNESS ANALYSIS ===")

for require_mutual in MUTUAL_MODES:
    for distance_gate in DISTANCE_GATES:
        for angle_gate in ANGLE_GATES:
            accepted = candidate_mask(
                distance_gate,
                angle_gate,
                require_mutual
            )

            count = int(accepted.sum())
            retained = int(
                np.count_nonzero(accepted & baseline)
            )
            added = int(
                np.count_nonzero(accepted & ~baseline)
            )
            lost = int(
                np.count_nonzero(baseline & ~accepted)
            )

            local_count = int(np.count_nonzero(
                accepted & local_agreement
            ))

            actor_counts = Counter(
                actor_ids[i]
                for i in np.flatnonzero(accepted)
            )

            top_actor, top_count = (
                actor_counts.most_common(1)[0]
                if actor_counts else ("", 0)
            )

            result = {
                "DistanceGateM": distance_gate,
                "AngleGateDeg": angle_gate,
                "RequireMutual": require_mutual,
                "Accepted": count,
                "AcceptedFraction": count / len(rows),
                "RetainedBaseline": retained,
                "AddedVsBaseline": added,
                "LostVsBaseline": lost,
                "LocalActorAgreementCount": local_count,
                "LocalAgreementAmongAccepted": (
                    local_count / count if count else None
                ),
                "TopNearestLiDARActorID": top_actor,
                "TopActorCandidates": top_count,
                "TopActorFraction": (
                    top_count / count if count else None
                ),
                "DistinctAssignedActorIDs": len(actor_counts),
            }

            results.append(result)

            print(
                f"Distance={distance_gate:4.2f} m | "
                f"Angle={angle_gate:4.1f} deg | "
                f"Mutual={require_mutual} | "
                f"Accepted={count:3d} | "
                f"TopActorShare="
                f"{result['TopActorFraction']}"
            )


# Save the full threshold sweep.
sweep_csv = CSV_DIR / (
    "task23_05d6_threshold_sensitivity.csv"
)

save_csv(sweep_csv, results)


# Baseline breakdown by frame and nearest LiDAR actor.
baseline_rows = []

for pair in (1, 2, 3):
    for frame in (25, 99):
        indices = [
            i for i, key in enumerate(keys)
            if key[0] == pair and key[1] == frame
        ]

        accepted_indices = [
            i for i in indices if baseline[i]
        ]

        actor_counter = Counter(
            actor_ids[i] for i in accepted_indices
        )

        baseline_rows.append({
            "PairID": pair,
            "Frame": frame,
            "RadarReturns": len(indices),
            "Accepted": len(accepted_indices),
            "LocalActorAgreement": sum(
                bool(local_agreement[i])
                for i in accepted_indices
            ),
            "DistinctAssignedActorIDs": len(actor_counter),
            "TopActorID": (
                actor_counter.most_common(1)[0][0]
                if actor_counter else ""
            ),
            "TopActorCount": (
                actor_counter.most_common(1)[0][1]
                if actor_counter else 0
            ),
            "TopActorFraction": (
                actor_counter.most_common(1)[0][1]
                / len(accepted_indices)
                if accepted_indices else None
            ),
        })

baseline_csv = CSV_DIR / (
    "task23_05d6_frame_actor_concentration.csv"
)

save_csv(baseline_csv, baseline_rows)


# Graph 1: threshold sweep with mutual matching enabled.
heatmap = np.array([
    [
        next(
            r["Accepted"]
            for r in results
            if (
                r["DistanceGateM"] == d
                and r["AngleGateDeg"] == a
                and r["RequireMutual"] is True
            )
        )
        for a in ANGLE_GATES
    ]
    for d in DISTANCE_GATES
])

fig, ax = plt.subplots(figsize=(8, 6))

image = ax.imshow(heatmap, aspect="auto")

ax.set_xticks(range(len(ANGLE_GATES)))
ax.set_xticklabels(
    [str(a) for a in ANGLE_GATES]
)

ax.set_yticks(range(len(DISTANCE_GATES)))
ax.set_yticklabels(
    [str(d) for d in DISTANCE_GATES]
)

ax.set_xlabel("Angle gate (degrees)")
ax.set_ylabel("Distance gate (metres)")
ax.set_title(
    "Radar-LiDAR candidate sensitivity "
    "(mutual nearest required)"
)

for i in range(len(DISTANCE_GATES)):
    for j in range(len(ANGLE_GATES)):
        ax.text(
            j, i, str(heatmap[i, j]),
            ha="center", va="center"
        )

fig.colorbar(image, ax=ax, label="Accepted candidates")
fig.tight_layout()

graph1 = GRAPH_DIR / (
    "task23_05d6_threshold_sensitivity.png"
)
fig.savefig(graph1, dpi=180)
plt.close(fig)


# Graph 2: effect of requiring mutual nearest matching.
fig, ax = plt.subplots(figsize=(9, 5))

for require_mutual in MUTUAL_MODES:
    subset = [
        r for r in results
        if r["DistanceGateM"] == 1.0
        and r["RequireMutual"] == require_mutual
    ]

    subset.sort(key=lambda r: r["AngleGateDeg"])

    ax.plot(
        [r["AngleGateDeg"] for r in subset],
        [r["Accepted"] for r in subset],
        marker="o",
        label=(
            "Mutual required"
            if require_mutual else "Mutual not required"
        )
    )

ax.set_xlabel("Angle gate (degrees)")
ax.set_ylabel("Accepted Radar candidates")
ax.set_title("Effect of mutual-nearest constraint at 1 m")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

graph2 = GRAPH_DIR / (
    "task23_05d6_mutual_constraint_effect.png"
)
fig.savefig(graph2, dpi=180)
plt.close(fig)


baseline_actor_counts = Counter(
    actor_ids[i]
    for i in np.flatnonzero(baseline)
)

baseline_top_actor, baseline_top_count = (
    baseline_actor_counts.most_common(1)[0]
)

findings_path = FINDINGS / (
    "task23_05d6_association_robustness_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.5D-6",
        "Status": "HEURISTIC_ASSOCIATION_SENSITIVITY_AUDIT",
        "RadarReturns": len(rows),
        "ConfigurationsTested": len(results),
        "Baseline": {
            "DistanceGateM": 1.0,
            "AngleGateDeg": 5.0,
            "RequireMutual": True,
            "Accepted": int(baseline.sum()),
            "LocallyActorConsistent": int(
                np.count_nonzero(baseline & local_agreement)
            ),
            "DominantNearestLiDARActorID": baseline_top_actor,
            "DominantActorCandidates": baseline_top_count,
            "DominantActorFraction": (
                baseline_top_count / int(baseline.sum())
            )
        },
        "ThresholdSweep": results,
        "FrameActorConcentration": baseline_rows,
        "ScientificInterpretation": (
            "Changing heuristic thresholds changes candidate "
            "counts; this is not an accuracy evaluation."
        ),
        "Limitations": [
            "Ground-truth cross-sensor correspondences unavailable",
            "Actor IDs are assigned via nearby LiDAR data",
            "High actor concentration may bias aggregate statistics",
            "Thresholds are not calibrated",
            "Changing gates cannot prove detection correctness",
            "Sensor-specific acquisition timing not independently proven",
            "No measured hardware energy or latency"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== BASELINE ACTOR CONCENTRATION ===")
for actor_id, count in baseline_actor_counts.most_common():
    print(
        f"Actor {actor_id}: {count} / {int(baseline.sum())}"
    )

print("\n=== TASK 23.5D-6 FINAL VERIFICATION ===")
print("Radar returns:", len(rows))
print("Threshold configurations:", len(results))
print("Baseline accepted:", int(baseline.sum()))
print(
    "Baseline locally actor-consistent:",
    int(np.count_nonzero(baseline & local_agreement))
)
print("Dominant actor:", baseline_top_actor)
print("Dominant actor candidates:", baseline_top_count)
print("Threshold CSV:", sweep_csv.is_file())
print("Actor concentration CSV:", baseline_csv.is_file())
print("Sensitivity graph:", graph1.is_file())
print("Mutual effect graph:", graph2.is_file())
print("Research JSON:", findings_path.is_file())

assert len(results) == 24
assert len(baseline_rows) == 6
assert int(baseline.sum()) == 197
assert baseline_top_count == 116

print("\n=== TASK 23.5D-6 COMPLETE ===")
