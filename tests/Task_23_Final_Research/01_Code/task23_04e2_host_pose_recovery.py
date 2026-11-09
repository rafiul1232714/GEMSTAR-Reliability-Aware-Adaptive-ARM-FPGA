import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages,
    SensorView,
    GroundTruth,
    timestamp_ns,
)

MANIFEST = (
    TASK / "05_Raw_Data_References"
    / "task23_01_source_manifest.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

FRAMES = {1, 25, 99}


def object_id(obj):
    if not hasattr(obj, "id"):
        return None
    return int(obj.id.value)


def get_host_id(gt):
    if gt is None:
        return None

    value = int(gt.host_vehicle_id.value)
    return value if value != 0 else None


def get_pose(obj):
    base = obj.base
    position = base.position
    orientation = base.orientation

    return {
        "X": float(position.x),
        "Y": float(position.y),
        "Z": float(position.z),
        "Roll": float(orientation.roll),
        "Pitch": float(orientation.pitch),
        "Yaw": float(orientation.yaw),
    }


def describe_objects(gt):
    return [
        {
            "ID": object_id(obj),
            "Pose": get_pose(obj),
        }
        for obj in gt.moving_object
    ]


print("\n=== TASK 23.4E-2 HOST POSE RECOVERY ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as handle:
    pairs = [
        row for row in csv.DictReader(handle)
        if row["PairID"] in {"1", "2", "3"}
    ]

rows = []
details = []

for pair in pairs:
    pair_id = pair["PairID"]

    sv_path = Path(pair["SensorViewPath"])
    gt_path = Path(pair["GroundTruthPath"])

    print(f"\n=== PAIR {pair_id} ===")

    sv_frames = {
        index: message
        for index, message, _ in iter_osi_messages(
            sv_path, SensorView, 100
        )
        if index in FRAMES
    }

    gt_frames = {
        index: message
        for index, message, _ in iter_osi_messages(
            gt_path, GroundTruth, 100
        )
        if index in FRAMES
    }

    for frame in sorted(FRAMES):
        if frame not in sv_frames or frame not in gt_frames:
            raise RuntimeError(
                f"Missing paired frame: {pair_id}/{frame}"
            )

        sv = sv_frames[frame]
        gt = gt_frames[frame]
        embedded = sv.global_ground_truth

        embedded_host = get_host_id(embedded)
        paired_host = get_host_id(gt)

        embedded_objects = describe_objects(embedded)
        paired_objects = describe_objects(gt)

        embedded_matches = [
            obj for obj in embedded_objects
            if obj["ID"] == embedded_host
        ]

        paired_matches = [
            obj for obj in paired_objects
            if obj["ID"] == embedded_host
        ]

        if len(embedded_matches) == 1:
            source = "SENSORVIEW_EMBEDDED_GROUNDTRUTH"
            pose = embedded_matches[0]["Pose"]
        elif len(paired_matches) == 1:
            source = "PAIRED_GROUNDTRUTH_MATCHED_SV_HOST_ID"
            pose = paired_matches[0]["Pose"]
        else:
            source = "HOST_POSE_NOT_IDENTIFIED"
            pose = {}

        result = {
            "PairID": pair_id,
            "Frame": frame,
            "SVTimestampNs": timestamp_ns(sv),
            "GTTimestampNs": timestamp_ns(gt),
            "EmbeddedHostID": embedded_host,
            "PairedHostID": paired_host,
            "EmbeddedMovingObjects": len(embedded_objects),
            "PairedMovingObjects": len(paired_objects),
            "EmbeddedHostMatches": len(embedded_matches),
            "PairedHostMatches": len(paired_matches),
            "PoseSource": source,
            "X": pose.get("X", ""),
            "Y": pose.get("Y", ""),
            "Z": pose.get("Z", ""),
            "Roll": pose.get("Roll", ""),
            "Pitch": pose.get("Pitch", ""),
            "Yaw": pose.get("Yaw", ""),
        }

        rows.append(result)

        details.append({
            "PairID": pair_id,
            "Frame": frame,
            "EmbeddedGroundTruthObjects": embedded_objects,
            "PairedGroundTruthObjects": paired_objects,
            "SelectedPose": pose,
            "PoseSource": source,
        })

        print(
            f"Frame {frame} | "
            f"EmbeddedHostID={embedded_host} | "
            f"EmbeddedObjects={len(embedded_objects)} | "
            f"PairedObjects={len(paired_objects)}"
        )

        print(
            "Embedded host matches:",
            len(embedded_matches)
        )

        print(
            "Paired host matches:",
            len(paired_matches)
        )

        print("Selected source:", source)
        print("Selected pose:", json.dumps(pose))

csv_path = (
    CSV_DIR / "task23_04e2_host_pose_recovery.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

json_path = (
    FINDINGS / "task23_04e2_host_pose_findings.json"
)

json_path.write_text(
    json.dumps({
        "Task": "23.4E-2",
        "Records": details,
        "Limitations": [
            "This step identifies stored poses only",
            "SensorView embedded pose may be a snapshot",
            "Host coordinate convention remains unverified",
            "Object geometry and point alignment untested",
            "No sensor fusion accuracy measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

recovered = sum(
    row["PoseSource"] != "HOST_POSE_NOT_IDENTIFIED"
    for row in rows
)

print("\n=== TASK 23.4E-2 FINAL VERIFICATION ===")
print("Frame pairs inspected:", len(rows))
print("Host poses recovered:", recovered)
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())

print("\n=== TASK 23.4E-2 COMPLETE ===")
