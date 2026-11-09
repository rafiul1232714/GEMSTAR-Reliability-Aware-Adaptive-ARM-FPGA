import csv
import json
import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

def read_messages(path, limit=100):
    with path.open("rb") as f:
        for frame in range(limit):
            header = f.read(4)
            if not header:
                break

            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI size")

            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Incomplete OSI message")

            msg = SensorView()
            msg.ParseFromString(payload)
            yield frame, msg

def present(msg, name):
    return any(
        field.name == name
        for field, _ in msg.ListFields()
    )

rows = []
summaries = []

print("\n=== TASK 20.17 EGO POSE AVAILABILITY ===")

for path in sorted(RAW.rglob("*_sv_*.osi")):
    scenario = path.parent.name

    frames = 0
    nested_gt = 0
    host_ids = 0
    host_data = 0
    nested_host_ids = 0
    nested_moving = 0
    pose_entries = 0
    example = None

    for frame, sv in read_messages(path):
        frames += 1

        has_gt = present(sv, "global_ground_truth")
        has_host_id = present(sv, "host_vehicle_id")
        has_host_data = present(sv, "host_vehicle_data")

        nested_gt += int(has_gt)
        host_ids += int(has_host_id)
        host_data += int(has_host_data)

        gt_host = False
        moving_count = 0
        found_pose = False

        if has_gt:
            gt = sv.global_ground_truth
            gt_host = present(gt, "host_vehicle_id")
            moving_count = len(gt.moving_object)

            for obj in gt.moving_object:
                base_fields = {
                    field.name
                    for field, _ in obj.base.ListFields()
                }

                if (
                    "position" in base_fields
                    and "orientation" in base_fields
                ):
                    found_pose = True

                    if example is None:
                        example = {
                            "Frame": frame,
                            "ObjectID": str(obj.id.value),
                            "Position": {
                                "x": obj.base.position.x,
                                "y": obj.base.position.y,
                                "z": obj.base.position.z
                            },
                            "Orientation": {
                                "yaw": obj.base.orientation.yaw,
                                "pitch": obj.base.orientation.pitch,
                                "roll": obj.base.orientation.roll
                            },
                        }

        nested_host_ids += int(gt_host)
        nested_moving += moving_count
        pose_entries += int(found_pose)

        rows.append({
            "Recording": scenario,
            "Frame": frame,
            "HasNestedGT": int(has_gt),
            "HasTopLevelHostID": int(has_host_id),
            "HasHostVehicleData": int(has_host_data),
            "HasNestedHostID": int(gt_host),
            "NestedMovingObjects": moving_count,
            "HasNestedPose": int(found_pose),
        })

    summary = {
        "Recording": scenario,
        "Frames": frames,
        "NestedGTFrames": nested_gt,
        "TopLevelHostIDFrames": host_ids,
        "HostVehicleDataFrames": host_data,
        "NestedHostIDFrames": nested_host_ids,
        "NestedMovingObjectEntries": nested_moving,
        "NestedPoseFrames": pose_entries,
        "Example": example
    }

    summaries.append(summary)

    print(
        f"{scenario:28s}"
        f" | Frames={frames:3d}"
        f" | NestedGT={nested_gt:3d}"
        f" | NestedHostID={nested_host_ids:3d}"
        f" | NestedPose={pose_entries:3d}"
    )

    if example:
        print("  Example pose:", example)

csv_path = DATA / "task20_17_ego_pose_availability.csv"
summary_path = FINDINGS / "task20_17_ego_pose_summary.json"

if rows:
    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

summary_path.write_text(
    json.dumps(summaries, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.17 COMPLETE ===")
print("Recordings:", len(summaries))
print("Frames inspected:", len(rows))
print(
    "Frames containing nested poses:",
    sum(s["NestedPoseFrames"] for s in summaries)
)
print("CSV saved:", csv_path.is_file())
print("JSON saved:", summary_path.is_file())
print("Energy measured:", False)
print("Radar accuracy validated:", False)
