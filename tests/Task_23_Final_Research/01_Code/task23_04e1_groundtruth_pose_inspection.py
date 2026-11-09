import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(0, str(
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
))

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

CSV_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

FRAMES = {1, 25, 99}
LIMIT = 100


def message_summary(message, depth=0):
    """Extract small protobuf samples without dumping arrays."""
    if depth >= 5:
        return {"note": "depth limit"}

    result = {}

    for field, value in message.ListFields():
        if field.is_repeated:
            result[field.name] = {
                "count": len(value),
                "first": (
                    message_summary(value[0], depth + 1)
                    if len(value) and field.message_type
                    else None
                )
            }

        elif field.message_type:
            result[field.name] = message_summary(
                value, depth + 1
            )

        elif field.type == field.TYPE_BYTES:
            result[field.name] = {
                "bytes": len(value)
            }

        else:
            result[field.name] = value

    return result


def extract_pose(obj):
    if not hasattr(obj, "base"):
        return {}

    base = obj.base

    if not hasattr(base, "position"):
        return {}

    pos = base.position

    result = {
        "X": float(pos.x),
        "Y": float(pos.y),
        "Z": float(pos.z)
    }

    if hasattr(base, "orientation"):
        rot = base.orientation
        result.update({
            "Roll": float(rot.roll),
            "Pitch": float(rot.pitch),
            "Yaw": float(rot.yaw)
        })

    return result


def get_id(obj):
    if hasattr(obj, "id"):
        return int(obj.id.value)
    return None


def host_id(gt):
    if hasattr(gt, "host_vehicle_id"):
        value = int(gt.host_vehicle_id.value)
        return value if value != 0 else None
    return None


print("\n=== TASK 23.4E-1 GROUNDTRUTH POSE INSPECTION ===")

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

    sv_iter = iter_osi_messages(
        sv_path, SensorView, LIMIT
    )

    gt_iter = iter_osi_messages(
        gt_path, GroundTruth, LIMIT
    )

    found = 0

    for sv_item, gt_item in zip(sv_iter, gt_iter):
        sv_frame, sv, sv_bytes = sv_item
        gt_frame, gt, gt_bytes = gt_item

        if sv_frame != gt_frame:
            raise RuntimeError(
                f"Frame indices differ: "
                f"{sv_frame} != {gt_frame}"
            )

        if sv_frame not in FRAMES:
            continue

        found += 1

        gt_host = host_id(gt)

        sv_gt = getattr(
            sv, "global_ground_truth", None
        )

        sv_host = (
            host_id(sv_gt)
            if sv_gt is not None
            else None
        )

        moving = list(gt.moving_object)

        host_matches = [
            obj for obj in moving
            if get_id(obj) == gt_host
        ]

        host_pose = (
            extract_pose(host_matches[0])
            if host_matches else {}
        )

        lidar_config = {}

        if sv.lidar_sensor_view:
            lidar_config = message_summary(
                sv.lidar_sensor_view[0].view_configuration
            )

        sample_objects = []

        for obj in moving[:5]:
            sample_objects.append({
                "ID": get_id(obj),
                "Pose": extract_pose(obj),
                "Structure": message_summary(
                    obj, depth=3
                )
            })

        row = {
            "PairID": pair_id,
            "Frame": sv_frame,
            "SVTimestampNs": timestamp_ns(sv),
            "GTTimestampNs": timestamp_ns(gt),
            "SVHostID": sv_host,
            "GTHostID": gt_host,
            "MovingObjectCount": len(moving),
            "HostFoundInGT": bool(host_matches),
            "HostX": host_pose.get("X", ""),
            "HostY": host_pose.get("Y", ""),
            "HostZ": host_pose.get("Z", ""),
            "HostRoll": host_pose.get("Roll", ""),
            "HostPitch": host_pose.get("Pitch", ""),
            "HostYaw": host_pose.get("Yaw", ""),
        }

        rows.append(row)

        details.append({
            "PairID": pair_id,
            "Frame": sv_frame,
            "GroundTruthDeclaredFields": [
                field.name for field in gt.DESCRIPTOR.fields
            ],
            "HostVehicleID": gt_host,
            "SensorViewHostID": sv_host,
            "HostPose": host_pose,
            "LiDARConfiguration": lidar_config,
            "FirstFiveMovingObjects": sample_objects,
        })

        print(
            f"Frame {sv_frame} | "
            f"MovingObjects={len(moving)} | "
            f"GT_HostID={gt_host} | "
            f"SV_HostID={sv_host} | "
            f"HostInGT={bool(host_matches)}"
        )

        print(
            "Host pose:",
            json.dumps(host_pose)
        )

        if sv_frame == 1:
            print(
                "GroundTruth fields:",
                [f.name for f in gt.DESCRIPTOR.fields]
            )
            print(
                "First moving object:",
                json.dumps(
                    sample_objects[0]
                    if sample_objects else {},
                    indent=2
                )[:2500]
            )

    if found != len(FRAMES):
        raise RuntimeError(
            f"Pair {pair_id}: expected 3 sampled "
            f"frames, got {found}"
        )

csv_path = (
    CSV_DIR / "task23_04e1_host_pose_summary.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

json_path = (
    FINDINGS /
    "task23_04e1_groundtruth_structure.json"
)

json_path.write_text(
    json.dumps({
        "Task": "23.4E-1",
        "SampledFrames": sorted(FRAMES),
        "Records": details,
        "ScientificLimitations": [
            "This step inspects stored poses only",
            "Coordinate transforms are not yet applied",
            "Unreal-to-OSI axis conventions not yet verified",
            "Host ID may be absent from paired GroundTruth",
            "Object association is not yet validated",
            "No point-cloud accuracy claim"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4E-1 FINAL VERIFICATION ===")
print("Pairs inspected:", len(pairs))
print("Frame pairs inspected:", len(rows))
print(
    "Host objects found:",
    sum(int(row["HostFoundInGT"]) for row in rows)
)
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())

print("\n=== TASK 23.4E-1 COMPLETE ===")
