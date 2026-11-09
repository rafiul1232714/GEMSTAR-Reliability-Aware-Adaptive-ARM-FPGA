import csv
import json
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

WORLD_DIR = (
    TASK / "08_Processed_Data" /
    "LiDAR_World_Candidate"
)

OBJECTS_CSV = (
    CSV_DIR /
    "task23_04e5b_groundtruth_object_audit.csv"
)

HOST_CSV = (
    CSV_DIR /
    "task23_04e5c_host_association_summary.csv"
)

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        return list(csv.DictReader(handle))


def rotation_matrix(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)

    rx = np.array([
        [1, 0, 0],
        [0, cr, -sr],
        [0, sr, cr]
    ], dtype=float)

    ry = np.array([
        [cp, 0, sp],
        [0, 1, 0],
        [-sp, 0, cp]
    ], dtype=float)

    rz = np.array([
        [cy, -sy, 0],
        [sy, cy, 0],
        [0, 0, 1]
    ], dtype=float)

    return rz @ ry @ rx


def evaluate_box(points, center, half_size, rotation):
    # Transform world points to object-local coordinates.
    local = (points - center) @ rotation

    q = np.abs(local) - half_size

    # Distance outside the box.
    outside = np.linalg.norm(
        np.maximum(q, 0.0), axis=1
    )

    # Signed distance: negative inside the box.
    inside_term = np.minimum(
        np.max(q, axis=1), 0.0
    )

    signed = outside + inside_term

    # Absolute distance to the nearest box surface.
    surface_distance = np.abs(signed)

    return {
        "NearestSurfaceM": float(np.min(
            surface_distance
        )),
        "MedianSurfaceM": float(np.median(
            surface_distance
        )),
        "PointsWithin025M": int(np.count_nonzero(
            surface_distance <= 0.25
        )),
        "PointsWithin050M": int(np.count_nonzero(
            surface_distance <= 0.50
        )),
        "PointsInsideBox": int(np.count_nonzero(
            signed < 0.0
        )),
        "NearestExteriorDistanceM": float(
            np.min(outside)
        ),
    }


objects = read_csv(OBJECTS_CSV)
hosts = read_csv(HOST_CSV)

host_lookup = {}

for row in hosts:
    key = (int(row["PairID"]), int(row["Frame"]))

    if row["AssociationStatus"] != "UNIQUE_CANDIDATE":
        raise RuntimeError(
            f"Unresolved host association: {key}"
        )

    host_lookup[key] = int(
        row["CandidateHostObjectID"]
    )

results = []
summary = []

print("\n=== TASK 23.4E-5D BOUNDING-BOX CONSISTENCY ===")

for pair in (1, 2, 3):
    for frame in (1, 25, 99):
        key = (pair, frame)
        host_id = host_lookup[key]

        world_path = WORLD_DIR / (
            f"pair{pair}_frame{frame:03d}_"
            "world_candidate.npz"
        )

        if not world_path.is_file():
            raise FileNotFoundError(world_path)

        with np.load(
            world_path, allow_pickle=False
        ) as data:
            points = data[
                "points_world_candidate_m"
            ].copy()

        if not np.isfinite(points).all():
            raise RuntimeError(
                f"Invalid world points in {key}"
            )

        frame_objects = [
            obj for obj in objects
            if int(obj["PairID"]) == pair
            and int(obj["Frame"]) == frame
            and int(obj["ObjectID"]) != host_id
        ]

        print(
            f"\nPair {pair} | Frame {frame:02d} | "
            f"HostID={host_id} | "
            f"NonHostObjects={len(frame_objects)}"
        )

        for obj in frame_objects:
            center = np.array([
                float(obj["X"]),
                float(obj["Y"]),
                float(obj["Z"])
            ])

            dimensions = np.array([
                float(obj["Length"]),
                float(obj["Width"]),
                float(obj["Height"])
            ])

            angles = [
                float(obj["Roll"]),
                float(obj["Pitch"]),
                float(obj["Yaw"])
            ]

            if (
                not np.isfinite(center).all()
                or not np.isfinite(dimensions).all()
                or np.any(dimensions <= 0)
            ):
                print(
                    "  Invalid geometry, skipping:",
                    obj["ObjectID"]
                )
                continue

            rotation = rotation_matrix(*angles)

            # A: OSI values describe full dimensions.
            full_dimension = evaluate_box(
                points,
                center,
                dimensions / 2.0,
                rotation
            )

            # B: Source values describe half-extents.
            half_extent = evaluate_box(
                points,
                center,
                dimensions,
                rotation
            )

            large = (
                float(np.max(dimensions)) >= 8.0
            )

            object_id = int(obj["ObjectID"])

            for interpretation, metrics in (
                ("A_RECORDED_FULL_DIMENSIONS",
                 full_dimension),
                ("B_RECORDED_HALF_EXTENTS",
                 half_extent),
            ):
                results.append({
                    "PairID": pair,
                    "Frame": frame,
                    "ObjectID": object_id,
                    "ObjectCategory": obj["Category"],
                    "LargeObject": bool(large),
                    "Interpretation": interpretation,
                    "LiDARPointCount": len(points),
                    **metrics
                })

            summary.append({
                "PairID": pair,
                "Frame": frame,
                "ObjectID": object_id,
                "LargeObject": bool(large),
                "FullDimNearestSurfaceM": (
                    full_dimension["NearestSurfaceM"]
                ),
                "HalfExtentNearestSurfaceM": (
                    half_extent["NearestSurfaceM"]
                ),
                "FullDimWithin050M": (
                    full_dimension["PointsWithin050M"]
                ),
                "HalfExtentWithin050M": (
                    half_extent["PointsWithin050M"]
                )
            })

            print(
                f"  Object {object_id} | "
                f"Large={large} | "
                f"NearestSurface A="
                f"{full_dimension['NearestSurfaceM']:.3f} m | "
                f"B="
                f"{half_extent['NearestSurfaceM']:.3f} m"
            )


def write_csv(path, rows):
    if not rows:
        raise RuntimeError(
            f"No data for output: {path}"
        )

    with path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)


details_path = CSV_DIR / (
    "task23_04e5d_box_surface_metrics.csv"
)

summary_path = CSV_DIR / (
    "task23_04e5d_box_interpretation_comparison.csv"
)

write_csv(details_path, results)
write_csv(summary_path, summary)

# Figure: compare interpretations for every
# sampled non-host object.
labels = [
    f"P{r['PairID']}-F{r['Frame']}-O{r['ObjectID']}"
    for r in summary
]

x = np.arange(len(summary))
width = 0.38

fig, ax = plt.subplots(figsize=(13, 6))

ax.bar(
    x - width / 2,
    [r["FullDimNearestSurfaceM"] for r in summary],
    width,
    label="Recorded full dimensions"
)

ax.bar(
    x + width / 2,
    [r["HalfExtentNearestSurfaceM"] for r in summary],
    width,
    label="Recorded half-extents"
)

ax.set_xticks(x)
ax.set_xticklabels(
    labels, rotation=70, ha="right"
)
ax.set_ylabel(
    "Nearest LiDAR point to box surface (m)"
)
ax.set_title(
    "GroundTruth bounding-box interpretation audit"
)
ax.legend()
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()

graph_path = GRAPH_DIR / (
    "task23_04e5d_bounding_box_comparison.png"
)

fig.savefig(graph_path, dpi=180)
plt.close(fig)

findings_path = FINDINGS / (
    "task23_04e5d_box_consistency_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-5D",
        "Purpose": (
            "Diagnostic proximity comparison between "
            "LiDAR world points and non-host "
            "GroundTruth object bounding boxes."
        ),
        "NonHostObjectEntries": len(summary),
        "Evaluations": len(results),
        "LargeObjectEntries": sum(
            item["LargeObject"] for item in summary
        ),
        "Interpretations": {
            "A": "Recorded dimensions treated as full size",
            "B": "Recorded dimensions treated as half-extents"
        },
        "WorldPoseMethod": (
            "Candidate Rz(yaw)Ry(pitch)Rx(roll)"
        ),
        "ScientificStatus": (
            "DIAGNOSTIC_PROXIMITY_NOT_ACCURACY"
        ),
        "Limitations": [
            "Nearest point is not necessarily an object return",
            "Occlusion and sensor visibility not modeled",
            "Large simulation actors not identified",
            "Recorded dimension semantics not independently verified",
            "World pose convention not independently verified",
            "Source revision at recording time not confirmed",
            "No object-detection accuracy is inferred"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-5D FINAL VERIFICATION ===")
print("Non-host object entries:", len(summary))
print("Box evaluations:", len(results))
print(
    "Large non-host object entries:",
    sum(item["LargeObject"] for item in summary)
)
print("Metrics CSV saved:", details_path.is_file())
print("Comparison CSV saved:", summary_path.is_file())
print("Graph saved:", graph_path.is_file())
print("Findings JSON saved:", findings_path.is_file())

print("\n=== TASK 23.4E-5D COMPLETE ===")
