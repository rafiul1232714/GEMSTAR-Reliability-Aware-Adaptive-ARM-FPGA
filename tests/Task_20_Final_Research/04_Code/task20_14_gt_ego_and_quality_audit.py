import csv
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

LIMIT = 100

def read_messages(path):
    with path.open("rb") as f:
        for frame in range(LIMIT):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete OSI header")
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI size")
            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated message")
            msg = GroundTruth()
            msg.ParseFromString(payload)
            yield frame, msg

def populated_fields(message):
    return {f.name: value for f, value in message.ListFields()}

def enum_description(message, field_name):
    field = message.DESCRIPTOR.fields_by_name.get(field_name)
    if field is None:
        return ""
    value = getattr(message, field_name)
    enum = field.enum_type
    if enum is None:
        return str(value)
    found = enum.values_by_number.get(int(value))
    return found.name if found else str(value)

def save_csv(path, rows):
    if not rows:
        return False
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return True

print("\n=== TASK 20.14 GT EGO AND QUALITY AUDIT ===")

files = sorted(RAW.rglob("*_gt_*.osi"))
rows = []
summaries = []
ego_metadata = []
sample_objects = []

for path in files:
    scenario = path.parent.name
    classes = Counter()
    unusual_count = 0
    seen_ids = defaultdict(set)
    first_frame_ego = None
    frames = 0

    for frame, gt in read_messages(path):
        frames += 1
        gt_fields = populated_fields(gt)

        # Record explicit GT ego/host fields if present,
        # without guessing that any object is ego.
        ego_fields = {
            key: str(value).replace("\n", " ")[:250]
            for key, value in gt_fields.items()
            if ("host" in key.lower()
                or "ego" in key.lower())
        }

        ego_metadata.append({
            "Recording": scenario,
            "Frame": frame,
            "EgoOrHostFields": json.dumps(ego_fields)
        })

        if frame == 0:
            first_frame_ego = ego_fields

        for kind, objects in (
            ("MOVING", gt.moving_object),
            ("STATIONARY", gt.stationary_object)
        ):
            for obj in objects:
                obj_id = str(obj.id.value)
                base = obj.base
                d = base.dimension
                p = base.position
                typename = enum_description(obj, "type")
                vehicle_class = ""

                if kind == "MOVING" and hasattr(
                    obj, "vehicle_classification"
                ):
                    vehicle_class = enum_description(
                        obj.vehicle_classification, "type"
                    )

                dims = [
                    float(d.length),
                    float(d.width),
                    float(d.height)
                ]

                unusual = (
                    not all(math.isfinite(x) for x in dims)
                    or any(x <= 0 or x > 20 for x in dims)
                    or (
                        kind == "MOVING"
                        and all(x >= 9 for x in dims)
                    )
                )

                if unusual:
                    unusual_count += 1

                key = (kind, typename, vehicle_class)
                classes[key] += 1
                seen_ids[obj_id].add(kind)

                row = {
                    "Recording": scenario,
                    "Frame": frame,
                    "TimestampNs": (
                        int(gt.timestamp.seconds)*1_000_000_000
                        + int(gt.timestamp.nanos)
                    ),
                    "Kind": kind,
                    "ID": obj_id,
                    "ObjectType": typename,
                    "VehicleClass": vehicle_class,
                    "X": float(p.x),
                    "Y": float(p.y),
                    "Z": float(p.z),
                    "Length": dims[0],
                    "Width": dims[1],
                    "Height": dims[2],
                    "UnusualDimensions": int(unusual),
                    "PotentialEgo": "UNVERIFIED",
                }
                rows.append(row)

                if frame == 0 and len(sample_objects) < 150:
                    sample_objects.append(row)

    summaries.append({
        "Recording": scenario,
        "Frames": frames,
        "UniqueIDs": len(seen_ids),
        "UnusualDimensionEntries": unusual_count,
        "ExplicitEgoFieldsFirstFrame":
            json.dumps(first_frame_ego or {}),
        "ClassCounts": json.dumps({
            "/".join(k): v for k, v in classes.items()
        }),
    })

    print("\nRecording:", scenario)
    print("Frames:", frames)
    print("Unique IDs:", len(seen_ids))
    print("Unusual dimension entries:", unusual_count)
    print("GT ego/host fields:", first_frame_ego or "NONE")
    print("Object types / classes:")
    for key, count in classes.most_common(8):
        print(" ", "/".join(key), ":", count)

    if frames:
        first_objects = [
            r for r in rows
            if r["Recording"] == scenario
            and r["Frame"] == 0
        ]
        print("First-frame object examples:")
        for obj in first_objects[:6]:
            print(
                f"  ID={obj['ID']} "
                f"Kind={obj['Kind']} "
                f"Type={obj['ObjectType']} "
                f"Class={obj['VehicleClass']} "
                f"XYZ=({obj['X']:.2f},"
                f"{obj['Y']:.2f},{obj['Z']:.2f}) "
                f"Dimensions=({obj['Length']:.2f},"
                f"{obj['Width']:.2f},"
                f"{obj['Height']:.2f})"
            )

object_file = DATA / "task20_14_gt_classified_objects.csv"
summary_file = DATA / "task20_14_gt_object_quality_summary.csv"
ego_file = DATA / "task20_14_gt_ego_metadata.csv"

save_csv(object_file, rows)
save_csv(summary_file, summaries)
save_csv(ego_file, ego_metadata)

report = {
    "Task": "20.14",
    "GTFiles": len(files),
    "ObjectEntries": len(rows),
    "UnusualDimensionEntries": sum(
        r["UnusualDimensionEntries"] for r in summaries
    ),
    "ExplicitEgoMetadataSample": {
        r["Recording"]: json.loads(
            r["ExplicitEgoFieldsFirstFrame"]
        )
        for r in summaries
    },
    "EgoIdentityVerified": False,
    "GTObjectClassificationAudited": True,
    "RadarObjectAssociationsVerified": False,
    "DetectionAccuracyMeasured": False,
    "EnergyMeasured": False
}

report_file = FINDINGS / "task20_14_gt_quality_audit.json"
report_file.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.14 COMPLETE ===")
print("Ground-truth files:", len(files))
print("Object entries:", len(rows))
print(
    "Unusual dimension entries:",
    report["UnusualDimensionEntries"]
)
print("Object CSV saved:", object_file.is_file())
print("Summary CSV saved:", summary_file.is_file())
print("Ego metadata CSV saved:", ego_file.is_file())
print("Research JSON saved:", report_file.is_file())
print("Ego identity verified:", False)
print("Radar associations verified:", False)
print("Energy measured:", False)
