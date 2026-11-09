import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(0, str(
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
))

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView, GroundTruth
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"
WORLD_DIR = (
    TASK / "08_Processed_Data" /
    "LiDAR_World_Candidate"
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)
HOST_CSV = (
    CSV_DIR /
    "task23_04e5c_host_association_summary.csv"
)

FRAMES = (1, 25, 99)
UINT64_MAX = (1 << 64) - 1

for folder in (CSV_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


manifest = {
    int(r["PairID"]): r for r in read_csv(MANIFEST)
}

host_lookup = {}

for row in read_csv(HOST_CSV):
    key = (int(row["PairID"]), int(row["Frame"]))
    if row["AssociationStatus"] != "UNIQUE_CANDIDATE":
        raise RuntimeError(f"Unresolved host: {key}")
    host_lookup[key] = int(row["CandidateHostObjectID"])

summaries = []
object_rows = []

print("\n=== TASK 23.4E-5E OBJECT-ID ASSOCIATION AUDIT ===")

for pair in (1, 2, 3):
    manifest_row = manifest[pair]

    sv_frames = {
        index: message
        for index, message, _ in iter_osi_messages(
            Path(manifest_row["SensorViewPath"]),
            SensorView, 100
        )
        if index in FRAMES
    }

    gt_frames = {
        index: message
        for index, message, _ in iter_osi_messages(
            Path(manifest_row["GroundTruthPath"]),
            GroundTruth, 100
        )
        if index in FRAMES
    }

    for frame in FRAMES:
        key = (pair, frame)

        if frame not in sv_frames or frame not in gt_frames:
            raise RuntimeError(f"Missing frame: {key}")

        sv = sv_frames[frame]
        gt = gt_frames[frame]

        if len(sv.lidar_sensor_view) != 1:
            raise RuntimeError(f"LiDAR count mismatch: {key}")

        reflections = sv.lidar_sensor_view[0].reflection

        with np.load(
            WORLD_DIR /
            f"pair{pair}_frame{frame:03d}_world_candidate.npz",
            allow_pickle=False
        ) as data:
            indices = data["valid_ray_indices"].copy()
            points = data["points_world_candidate_m"].copy()

        if len(indices) != len(points):
            raise RuntimeError(f"Point index mismatch: {key}")

        if len(indices) and int(np.max(indices)) >= len(reflections):
            raise RuntimeError(f"Invalid reflection index: {key}")

        gt_ids = {
            int(obj.id.value)
            for obj in gt.moving_object
        } | {
            int(obj.id.value)
            for obj in gt.stationary_object
        }

        host_id = host_lookup[key]

        matched = 0
        unmatched = 0
        missing_id = 0
        host_rays = 0

        id_counts = Counter()

        for ray_index in indices:
            reflection = reflections[int(ray_index)]

            # Only count an ID when its protobuf field is set.
            has_id = reflection.HasField("object_id")

            if not has_id:
                missing_id += 1
                continue

            object_id = int(reflection.object_id.value)

            if object_id == UINT64_MAX:
                missing_id += 1
                continue

            id_counts[object_id] += 1

            if object_id in gt_ids:
                matched += 1
            else:
                unmatched += 1

            if object_id == host_id:
                host_rays += 1

        for object_id, count in id_counts.most_common():
            object_rows.append({
                "PairID": pair,
                "Frame": frame,
                "ReflectionObjectID": object_id,
                "ValidRayCount": count,
                "InPairedGroundTruth": object_id in gt_ids,
                "IsHostCandidate": object_id == host_id,
            })

        result = {
            "PairID": pair,
            "Frame": frame,
            "ValidLiDARPoints": len(indices),
            "GroundTruthObjectIDs": len(gt_ids),
            "UniqueReflectionObjectIDs": len(id_counts),
            "MatchedGroundTruthRays": matched,
            "UnmatchedGroundTruthRays": unmatched,
            "MissingObjectIDRays": missing_id,
            "HostObjectRays": host_rays,
            "MatchedFraction": (
                matched / len(indices)
                if len(indices) else 0.0
            ),
        }

        if matched + unmatched + missing_id != len(indices):
            raise RuntimeError(f"Ray accounting mismatch: {key}")

        summaries.append(result)

        print(
            f"\nPair {pair} | Frame {frame:02d} | "
            f"ValidPoints={len(indices)} | "
            f"Matched={matched} | "
            f"Unmatched={unmatched} | "
            f"MissingID={missing_id} | "
            f"HostRays={host_rays}"
        )

        print("GroundTruth IDs:", sorted(gt_ids))
        print("Top reflection IDs:", id_counts.most_common(8))


summary_csv = (
    CSV_DIR /
    "task23_04e5e_object_id_frame_summary.csv"
)
detail_csv = (
    CSV_DIR /
    "task23_04e5e_reflection_object_id_counts.csv"
)

write_csv(
    summary_csv,
    summaries,
    list(summaries[0].keys())
)

write_csv(
    detail_csv,
    object_rows,
    [
        "PairID",
        "Frame",
        "ReflectionObjectID",
        "ValidRayCount",
        "InPairedGroundTruth",
        "IsHostCandidate",
    ]
)

totals = {
    "ValidPoints": sum(r["ValidLiDARPoints"] for r in summaries),
    "Matched": sum(r["MatchedGroundTruthRays"] for r in summaries),
    "Unmatched": sum(r["UnmatchedGroundTruthRays"] for r in summaries),
    "MissingID": sum(r["MissingObjectIDRays"] for r in summaries),
    "HostRays": sum(r["HostObjectRays"] for r in summaries),
}

findings_path = (
    FINDINGS /
    "task23_04e5e_object_id_association_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-5E",
        "Scope": "Recorded reflection IDs versus paired GroundTruth IDs",
        "FrameSummaries": summaries,
        "Totals": totals,
        "ScientificStatus": "SIMULATOR_METADATA_ASSOCIATION_AUDIT",
        "Limitations": [
            "An object ID is simulator metadata, not a detector prediction",
            "GroundTruth contains a limited object subset",
            "Missing ID does not establish false detection",
            "Weather processing may modify recorded reflections",
            "Matching IDs alone does not establish geometric accuracy",
            "Source revision at recording time is not proven"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-5E FINAL VERIFICATION ===")
print("Frames examined:", len(summaries))
print("Total valid LiDAR points:", totals["ValidPoints"])
print("Matched GroundTruth rays:", totals["Matched"])
print("Unmatched GroundTruth rays:", totals["Unmatched"])
print("Missing object ID rays:", totals["MissingID"])
print("Host object rays:", totals["HostRays"])
print("Frame summary CSV saved:", summary_csv.is_file())
print("Object ID counts CSV saved:", detail_csv.is_file())
print("Research JSON saved:", findings_path.is_file())

print("\n=== TASK 23.4E-5E COMPLETE ===")
