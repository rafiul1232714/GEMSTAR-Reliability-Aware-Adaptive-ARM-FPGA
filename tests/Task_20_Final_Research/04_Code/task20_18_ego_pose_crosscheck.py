import csv
import json
import math
import struct
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

LIMIT = 100

def read_frames(path, cls):
    result = {}
    with path.open("rb") as f:
        for index in range(LIMIT):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise RuntimeError("Incomplete header")
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise RuntimeError("Invalid OSI size")
            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError("Truncated OSI record")
            msg = cls()
            msg.ParseFromString(payload)
            stamp = (
                int(msg.timestamp.seconds) * 1_000_000_000
                + int(msg.timestamp.nanos)
            )
            if stamp in result:
                raise RuntimeError("Duplicate timestamp")
            result[stamp] = (index, msg)
    return result

def has_field(message, name):
    return any(
        field.name == name
        for field, _ in message.ListFields()
    )

def pose(obj):
    p = obj.base.position
    o = obj.base.orientation
    return (
        float(p.x), float(p.y), float(p.z),
        float(o.yaw), float(o.pitch), float(o.roll)
    )

rows = []
summaries = []

print("\n=== TASK 20.18 EGO POSE CROSSCHECK ===")

for folder in sorted(RAW.iterdir()):
    if not folder.is_dir():
        continue

    gt_files = list(folder.glob("*_gt_*.osi"))
    sv_files = list(folder.glob("*_sv_*.osi"))

    if len(gt_files) != 1 or len(sv_files) != 1:
        continue

    gt_frames = read_frames(gt_files[0], GroundTruth)
    sv_frames = read_frames(sv_files[0], SensorView)

    counts = {
        "FramesChecked": 0,
        "NestedHostFound": 0,
        "NestedIDMatched": 0,
        "MatchingGTObjectFound": 0,
        "PoseAgreementsWithin1mm1mrad": 0,
        "MissingHost": 0,
        "MissingGTObject": 0
    }

    for stamp, (frame, sv) in sv_frames.items():
        if stamp not in gt_frames:
            continue

        counts["FramesChecked"] += 1
        _, gt = gt_frames[stamp]

        status = "NO_NESTED_HOST"
        host_id = ""
        pos_error = ""
        angle_error = ""
        nested_match = False

        if (has_field(sv, "global_ground_truth")
            and has_field(
                sv.global_ground_truth, "host_vehicle_id"
            )):
            counts["NestedHostFound"] += 1
            host_id = int(
                sv.global_ground_truth.host_vehicle_id.value
            )

            nested = [
                obj for obj in
                sv.global_ground_truth.moving_object
                if int(obj.id.value) == host_id
            ]

            if len(nested) == 1:
                nested_match = True
                counts["NestedIDMatched"] += 1

                candidates = [
                    obj for obj in gt.moving_object
                    if int(obj.id.value) == host_id
                ]

                if len(candidates) == 1:
                    counts["MatchingGTObjectFound"] += 1

                    a = pose(nested[0])
                    b = pose(candidates[0])

                    pos_error = math.sqrt(sum(
                        (a[i]-b[i])**2 for i in range(3)
                    ))

                    angle_error = max(
                        abs(math.atan2(
                            math.sin(a[i]-b[i]),
                            math.cos(a[i]-b[i])
                        ))
                        for i in range(3, 6)
                    )

                    if (pos_error <= 0.001
                        and angle_error <= 0.001):
                        status = "POSE_AGREES"
                        counts[
                            "PoseAgreementsWithin1mm1mrad"
                        ] += 1
                    else:
                        status = "POSE_DIFFERS"
                else:
                    status = "GT_OBJECT_NOT_UNIQUE_OR_MISSING"
                    counts["MissingGTObject"] += 1
            else:
                status = "NESTED_HOST_OBJECT_MISSING"
        else:
            counts["MissingHost"] += 1

        rows.append({
            "Recording": folder.name,
            "Frame": frame,
            "TimestampNs": stamp,
            "HostID": host_id,
            "NestedHostIDMatched": nested_match,
            "PositionErrorM": pos_error,
            "OrientationMaxErrorRad": angle_error,
            "Status": status
        })

    summaries.append({
        "Recording": folder.name,
        **counts
    })

    print(
        f"{folder.name:28s}"
        f" | Checked={counts['FramesChecked']:3d}"
        f" | Host={counts['NestedHostFound']:3d}"
        f" | NestedID={counts['NestedIDMatched']:3d}"
        f" | GTObject={counts['MatchingGTObjectFound']:3d}"
        f" | PoseAgrees="
        f"{counts['PoseAgreementsWithin1mm1mrad']:3d}"
    )

def save_csv(path, data):
    if data:
        with path.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=list(data[0])
            )
            writer.writeheader()
            writer.writerows(data)

detail = DATA / "task20_18_ego_pose_crosscheck.csv"
summary = DATA / "task20_18_ego_pose_summary.csv"
report = FINDINGS / "task20_18_ego_pose_crosscheck.json"

save_csv(detail, rows)
save_csv(summary, summaries)

report.write_text(
    json.dumps(summaries, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.18 COMPLETE ===")
print("Recording pairs checked:", len(summaries))
print("CSV saved:", detail.is_file())
print("Summary saved:", summary.is_file())
print("JSON saved:", report.is_file())
print("Radar detection accuracy validated:", False)
print("Energy measured:", False)
