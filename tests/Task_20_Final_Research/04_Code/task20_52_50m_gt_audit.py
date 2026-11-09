import csv
import json
import struct
from pathlib import Path
from collections import Counter

from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_20_Final_Research"
)
OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")
PREFIX = "20261102T180104Z"

SV_FILE = OUTPUT / (
    PREFIX + "_sv_380_X_806_GEMSTAR.osi"
)
GT_FILE = OUTPUT / (
    PREFIX + "_gt_380_X_806_GEMSTAR.osi"
)

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

def read_messages(path, cls, limit=100):
    with path.open("rb") as f:
        for index in range(limit):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete frame header")

            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid message size")

            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated message")

            msg = cls()
            msg.ParseFromString(payload)
            yield index, msg

def timestamp_ns(msg):
    return (
        int(msg.timestamp.seconds) * 1_000_000_000
        + int(msg.timestamp.nanos)
    )

print("\n=== TASK 20.52 50M GROUND TRUTH AUDIT ===")
print("SensorView exists:", SV_FILE.exists())
print("GroundTruth exists:", GT_FILE.exists())

if not SV_FILE.exists() or not GT_FILE.exists():
    raise FileNotFoundError(
        "Matching 50m SensorView/GroundTruth files required"
    )

sv_frames = list(read_messages(SV_FILE, SensorView))
gt_frames = list(read_messages(GT_FILE, GroundTruth))

records = []
objects = Counter()
models = Counter()
matched = 0
mismatched = 0
external_entries = 0
external_frames = set()
host_found = 0
return_counts = Counter()

for (si, sv), (gi, gt) in zip(sv_frames, gt_frames):

    if si != gi:
        raise ValueError("Frame indices differ")

    # Exclude frame zero due to identified startup artifacts.
    if si == 0:
        continue

    sv_time = timestamp_ns(sv)
    gt_time = timestamp_ns(gt)

    if sv_time == gt_time:
        matched += 1
    else:
        mismatched += 1

    host_ids = set()

    if sv.HasField("global_ground_truth"):
        nested = sv.global_ground_truth
        if nested.HasField("host_vehicle_id"):
            host_ids.add(int(nested.host_vehicle_id.value))
            host_found += 1

    external_this_frame = 0

    for obj in gt.moving_object:
        obj_id = int(obj.id.value)
        model = str(obj.model_reference)

        objects[obj_id] += 1
        models[model] += 1

        is_host = obj_id in host_ids
        is_helper = "FollowVehicleCamera" in model
        is_external = (
            bool(host_ids)
            and not is_host
            and not is_helper
        )

        if is_external:
            external_entries += 1
            external_this_frame += 1

            if obj.base.HasField("position"):
                pos = obj.base.position
                records.append({
                    "Frame": si,
                    "TimestampNs": gt_time,
                    "ObjectID": obj_id,
                    "ModelReference": model,
                    "X": pos.x,
                    "Y": pos.y,
                    "Z": pos.z
                })

    if external_this_frame:
        external_frames.add(si)

    for view in sv.radar_sensor_view:
        for ref in view.reflection:
            if (
                ref.time_of_flight > 0
                and ref.signal_strength > 0
            ):
                return_counts[si] += 1

summary = {
    "Task": "20.52",
    "SensorViewFramesRead": len(sv_frames),
    "GroundTruthFramesRead": len(gt_frames),
    "FrameZeroExcluded": True,
    "ExactTimestampMatches": matched,
    "TimestampMismatches": mismatched,
    "FramesWithNestedHostID": host_found,
    "ExternalObjectEntries": external_entries,
    "FramesWithExternalObjects": len(external_frames),
    "ExternalUniqueIDs": len({
        row["ObjectID"] for row in records
    }),
    "CandidateRadarReturnsFrames1To99":
        sum(return_counts.values()),
    "ModelReferences": dict(models),
    "ExternalObjectGroundTruthValidated": False,
    "RadarObjectAssociationValidated": False
}

csv_path = DATA / "task20_52_external_gt_50m.csv"
json_path = FINDINGS / "task20_52_50m_gt_audit.json"

columns = [
    "Frame", "TimestampNs", "ObjectID",
    "ModelReference", "X", "Y", "Z"
]

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(records)

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("Exact timestamp matches:", matched)
print("Timestamp mismatches:", mismatched)
print("Frames with host ID:", host_found)
print("External GT entries:", external_entries)
print("Frames containing external objects:",
      len(external_frames))
print("Unique external GT IDs:",
      summary["ExternalUniqueIDs"])
print("Radar candidate returns (frames 1-99):",
      sum(return_counts.values()))

print("\n=== GT MODEL REFERENCES ===")
for name, count in models.most_common(12):
    print(f"{count:5d} | {name}")

print("\n=== TASK 20.52 COMPLETE ===")
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Radar-object association validated:", False)
print("Energy measured:", False)
