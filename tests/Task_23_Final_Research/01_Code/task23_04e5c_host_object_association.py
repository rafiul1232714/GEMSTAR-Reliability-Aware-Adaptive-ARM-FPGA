import csv
import json
import math
from collections import defaultdict
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

POSE_CSV = CSV_DIR / "task23_04e2_host_pose_recovery.csv"
OBJECT_CSV = CSV_DIR / "task23_04e5b_groundtruth_object_audit.csv"

POSITION_TOLERANCE_M = 0.05
YAW_TOLERANCE_RAD = math.radians(2.0)


def load_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def xyz(row, names):
    return [float(row[name]) for name in names]


def distance(a, b):
    return math.sqrt(sum(
        (x - y) ** 2 for x, y in zip(a, b)
    ))


def wrapped_angle_difference(a, b):
    return abs(math.atan2(
        math.sin(a - b),
        math.cos(a - b)
    ))


poses = load_csv(POSE_CSV)
objects = load_csv(OBJECT_CSV)

by_frame = defaultdict(list)

for obj in objects:
    key = (
        int(obj["PairID"]),
        int(obj["Frame"])
    )
    by_frame[key].append(obj)

output_rows = []
frame_results = []

print("\n=== TASK 23.4E-5C HOST OBJECT ASSOCIATION ===")

for pose in poses:
    pair = int(pose["PairID"])
    frame = int(pose["Frame"])
    key = (pair, frame)

    host_position = xyz(
        pose, ("X", "Y", "Z")
    )
    host_yaw = float(pose["Yaw"])

    candidates = []

    for obj in by_frame[key]:
        object_position = xyz(
            obj, ("X", "Y", "Z")
        )

        position_error = distance(
            host_position, object_position
        )

        yaw_error = wrapped_angle_difference(
            host_yaw, float(obj["Yaw"])
        )

        length = float(obj["Length"])
        width = float(obj["Width"])
        height = float(obj["Height"])

        unusually_large = (
            max(length, width, height) >= 8.0
        )

        # Position-only candidate, not final
        # proof of actor identity.
        near_host = (
            position_error <= POSITION_TOLERANCE_M
        )

        angle_consistent = (
            yaw_error <= YAW_TOLERANCE_RAD
        )

        record = {
            "PairID": pair,
            "Frame": frame,
            "ObjectID": obj["ObjectID"],
            "Category": obj["Category"],
            "PositionDifferenceM": position_error,
            "YawDifferenceDeg": math.degrees(yaw_error),
            "LengthM": length,
            "WidthM": width,
            "HeightM": height,
            "UnusuallyLarge": unusually_large,
            "NearHostPosition": near_host,
            "HostYawConsistent": angle_consistent,
            "HostCandidate": (
                near_host and angle_consistent
            )
        }

        output_rows.append(record)
        candidates.append(record)

    candidates.sort(
        key=lambda r: r["PositionDifferenceM"]
    )

    matched = [
        item for item in candidates
        if item["HostCandidate"]
    ]

    status = (
        "UNIQUE_CANDIDATE" if len(matched) == 1
        else "NO_CANDIDATE" if len(matched) == 0
        else "AMBIGUOUS"
    )

    chosen = (
        matched[0]["ObjectID"]
        if len(matched) == 1 else ""
    )

    frame_results.append({
        "PairID": pair,
        "Frame": frame,
        "GroundTruthObjects": len(candidates),
        "HostCandidates": len(matched),
        "CandidateHostObjectID": chosen,
        "AssociationStatus": status,
        "HostPoseSource": pose["PoseSource"]
    })

    print(
        f"\nPair {pair} | Frame {frame:02d} | "
        f"Status={status} | "
        f"HostCandidateID={chosen}"
    )

    for item in candidates[:3]:
        print(
            f"  Object {item['ObjectID']} | "
            f"PositionError="
            f"{item['PositionDifferenceM']:.6f} m | "
            f"YawError="
            f"{item['YawDifferenceDeg']:.3f} deg | "
            f"Large={item['UnusuallyLarge']}"
        )


def save_csv(filename, rows):
    path = CSV_DIR / filename

    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    return path


object_output = save_csv(
    "task23_04e5c_object_association.csv",
    output_rows
)

frame_output = save_csv(
    "task23_04e5c_host_association_summary.csv",
    frame_results
)

unique_count = sum(
    row["AssociationStatus"] == "UNIQUE_CANDIDATE"
    for row in frame_results
)

large_count = sum(
    row["UnusuallyLarge"]
    for row in output_rows
)

findings_path = FINDINGS / (
    "task23_04e5c_host_association_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4E-5C",
        "PositionToleranceM": POSITION_TOLERANCE_M,
        "YawToleranceDeg": math.degrees(
            YAW_TOLERANCE_RAD
        ),
        "FrameResults": frame_results,
        "UniqueHostCandidates": unique_count,
        "UnusuallyLargeObjectEntries": large_count,
        "AssociationMethod": (
            "Position and yaw consistency; "
            "not definitive actor identity verification"
        ),
        "Limitations": [
            "Matching position and yaw does not prove ID identity",
            "Object centers may be bounding-box centers",
            "Large objects are flagged, not automatically invalid",
            "No point-to-surface accuracy measured",
            "Stationary GroundTruth objects absent in samples"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-5C FINAL VERIFICATION ===")
print("Frames analyzed:", len(frame_results))
print("Object entries analyzed:", len(output_rows))
print("Unique host candidates:", unique_count)
print("Unusually large object entries:", large_count)
print("Object association CSV:", object_output.is_file())
print("Frame summary CSV:", frame_output.is_file())
print("Research JSON:", findings_path.is_file())

print("\n=== TASK 23.4E-5C COMPLETE ===")
