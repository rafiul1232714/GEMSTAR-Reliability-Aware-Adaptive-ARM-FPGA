import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(0, str(
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
))

from task22_02_reusable_osi_reader import (
    iter_osi_messages, GroundTruth
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

WORLD_DIR = (
    TASK / "08_Processed_Data" /
    "LiDAR_World_Candidate"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

FRAMES = (1, 25, 99)

for folder in (CSV_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def inspect_object(obj, category, pair, frame, points):
    base = obj.base

    position = np.array([
        base.position.x,
        base.position.y,
        base.position.z
    ], dtype=float)

    dimension = np.array([
        base.dimension.length,
        base.dimension.width,
        base.dimension.height
    ], dtype=float)

    orientation = np.array([
        base.orientation.roll,
        base.orientation.pitch,
        base.orientation.yaw
    ], dtype=float)

    # Diagnostic only: distance to object center.
    # This is NOT a point-to-surface error metric.
    if len(points) and np.isfinite(position).all():
        delta = points - position

        nearest_3d = float(np.min(
            np.linalg.norm(delta, axis=1)
        ))

        nearest_xy = float(np.min(
            np.linalg.norm(delta[:, :2], axis=1)
        ))
    else:
        nearest_3d = None
        nearest_xy = None

    return {
        "PairID": pair,
        "Frame": frame,
        "Category": category,
        "ObjectID": int(obj.id.value),
        "X": float(position[0]),
        "Y": float(position[1]),
        "Z": float(position[2]),
        "Length": float(dimension[0]),
        "Width": float(dimension[1]),
        "Height": float(dimension[2]),
        "Roll": float(orientation[0]),
        "Pitch": float(orientation[1]),
        "Yaw": float(orientation[2]),
        "NearZeroX": bool(abs(position[0]) < 1e-9),
        "FinitePosition": bool(np.isfinite(position).all()),
        "PositiveDimensions": bool(
            np.isfinite(dimension).all()
            and np.all(dimension > 0)
        ),
        "NearestLiDARCenterDistanceM": nearest_3d,
        "NearestLiDARCenterDistanceXYM": nearest_xy,
    }


print("\n=== TASK 23.4E-5B GROUNDTRUTH GEOMETRY AUDIT ===")

manifest = {
    int(row["PairID"]): row
    for row in read_csv(MANIFEST)
}

rows = []
frame_summary = []

for pair in (1, 2, 3):
    gt_path = Path(manifest[pair]["GroundTruthPath"])

    selected_frames = {
        index: gt
        for index, gt, _ in iter_osi_messages(
            gt_path, GroundTruth, 100
        )
        if index in FRAMES
    }

    for frame in FRAMES:
        if frame not in selected_frames:
            raise RuntimeError(
                f"Missing GroundTruth: pair {pair}, frame {frame}"
            )

        gt = selected_frames[frame]

        world_path = WORLD_DIR / (
            f"pair{pair}_frame{frame:03d}_"
            "world_candidate.npz"
        )

        if not world_path.is_file():
            raise FileNotFoundError(world_path)

        with np.load(world_path, allow_pickle=False) as data:
            points = data["points_world_candidate_m"]

        if not np.isfinite(points).all():
            raise RuntimeError(
                f"Nonfinite LiDAR points: pair {pair}, frame {frame}"
            )

        moving = list(gt.moving_object)
        stationary = list(gt.stationary_object)

        current = []

        for obj in moving:
            current.append(inspect_object(
                obj, "MOVING", pair, frame, points
            ))

        for obj in stationary:
            current.append(inspect_object(
                obj, "STATIONARY", pair, frame, points
            ))

        rows.extend(current)

        suspicious_stationary = sum(
            item["NearZeroX"]
            for item in current
            if item["Category"] == "STATIONARY"
        )

        frame_summary.append({
            "PairID": pair,
            "Frame": frame,
            "LiDARPoints": len(points),
            "MovingObjects": len(moving),
            "StationaryObjects": len(stationary),
            "StationaryNearZeroX": suspicious_stationary,
            "InvalidDimensions": sum(
                not item["PositiveDimensions"]
                for item in current
            ),
        })

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"LiDARPoints={len(points)} | "
            f"Moving={len(moving)} | "
            f"Stationary={len(stationary)} | "
            f"StationaryXNearZero={suspicious_stationary}"
        )

        for item in current[:3]:
            print(
                f"  {item['Category']} "
                f"ID={item['ObjectID']} "
                f"Pos=({item['X']:.2f},"
                f"{item['Y']:.2f},{item['Z']:.2f}) "
                f"Dim=({item['Length']:.2f},"
                f"{item['Width']:.2f},"
                f"{item['Height']:.2f}) "
                f"NearCenter={item['NearestLiDARCenterDistanceM']}"
            )


objects_path = CSV_DIR / (
    "task23_04e5b_groundtruth_object_audit.csv"
)

summary_path = CSV_DIR / (
    "task23_04e5b_groundtruth_frame_summary.csv"
)

def save_csv(path, data):
    if not data:
        return False

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(data[0].keys())
        )
        writer.writeheader()
        writer.writerows(data)

    return path.is_file()


objects_saved = save_csv(objects_path, rows)
summary_saved = save_csv(summary_path, frame_summary)

findings_path = FINDINGS / (
    "task23_04e5b_groundtruth_geometry_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-5B",
        "Scope": "GroundTruth geometry diagnostic audit",
        "FrameSummaries": frame_summary,
        "TotalGroundTruthObjects": len(rows),
        "StationaryNearZeroXCount": sum(
            r["NearZeroX"] for r in rows
            if r["Category"] == "STATIONARY"
        ),
        "KnownPotentialDefect": (
            "ToOSI::toOSIBaseStationary uses "
            "set_z twice; use of this function "
            "in recordings is not yet confirmed."
        ),
        "Limitations": [
            "Nearest object-center distance is diagnostic",
            "Object dimensions and orientation not yet used",
            "Nearest LiDAR point need not belong to the object",
            "Source code revision at recording time unverified",
            "World orientation convention not independently verified",
            "No GroundTruth accuracy metric claimed"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-5B FINAL VERIFICATION ===")
print("Frames examined:", len(frame_summary))
print("GroundTruth objects examined:", len(rows))
print(
    "Stationary objects with near-zero X:",
    sum(
        r["NearZeroX"] for r in rows
        if r["Category"] == "STATIONARY"
    )
)
print("Object audit CSV saved:", objects_saved)
print("Frame summary CSV saved:", summary_saved)
print("Research findings JSON saved:", findings_path.is_file())

if not summary_saved:
    raise RuntimeError("Frame summary was not saved.")

print("\n=== TASK 23.4E-5B COMPLETE ===")
