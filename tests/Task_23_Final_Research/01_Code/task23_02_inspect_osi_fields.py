import csv
import json
import sys
from collections import Counter
from pathlib import Path

from google.protobuf.descriptor import FieldDescriptor

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"
TASK22_CODE = (
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
)

sys.path.insert(0, str(TASK22_CODE))

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

SELECTED_FRAMES = {0, 1, 25, 99}
SCAN_LIMIT = 100


def load_manifest():
    with MANIFEST.open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        return list(csv.DictReader(handle))


PROTOBUF_TYPE_NAMES = {
    FieldDescriptor.TYPE_DOUBLE: "double",
    FieldDescriptor.TYPE_FLOAT: "float",
    FieldDescriptor.TYPE_INT64: "int64",
    FieldDescriptor.TYPE_UINT64: "uint64",
    FieldDescriptor.TYPE_INT32: "int32",
    FieldDescriptor.TYPE_FIXED64: "fixed64",
    FieldDescriptor.TYPE_FIXED32: "fixed32",
    FieldDescriptor.TYPE_BOOL: "bool",
    FieldDescriptor.TYPE_STRING: "string",
    FieldDescriptor.TYPE_BYTES: "bytes",
    FieldDescriptor.TYPE_UINT32: "uint32",
    FieldDescriptor.TYPE_SFIXED32: "sfixed32",
    FieldDescriptor.TYPE_SFIXED64: "sfixed64",
    FieldDescriptor.TYPE_SINT32: "sint32",
    FieldDescriptor.TYPE_SINT64: "sint64",
}
def field_type(field):
    if field.message_type is not None:
        return "message:" + field.message_type.full_name

    if field.enum_type is not None:
        return "enum:" + field.enum_type.full_name

    return PROTOBUF_TYPE_NAMES.get(field.type, str(field.type))


def field_summary(message):
    """Describe fields without serializing large payloads."""
    items = []

    for field, value in message.ListFields():
        repeated = field.is_repeated

        count = len(value) if repeated else 1

        if field.type == FieldDescriptor.TYPE_BYTES:
            byte_count = len(value)
        elif repeated and field.type == FieldDescriptor.TYPE_BYTES:
            byte_count = sum(len(v) for v in value)
        else:
            byte_count = None

        preview = ""

        if not repeated:
            if field.type == FieldDescriptor.TYPE_BYTES:
                preview = value[:12].hex()
            elif field.message_type is None:
                preview = str(value)[:100]

        items.append({
            "Field": field.name,
            "Type": field_type(field),
            "Repeated": repeated,
            "Count": count,
            "Bytes": byte_count,
            "Preview": preview,
        })

    return items


def schema_rows(message, category):
    rows = []

    for field in message.DESCRIPTOR.fields:
        rows.append({
            "Category": category,
            "MessageType": message.DESCRIPTOR.full_name,
            "FieldName": field.name,
            "FieldType": field_type(field),
            "Repeated": field.is_repeated,
        })

    return rows


def sample_reflection(view):
    if not hasattr(view, "reflection"):
        return {
            "ReflectionField": False,
            "Count": 0,
            "FirstSlot": [],
            "FirstPositiveSlot": [],
        }

    reflections = view.reflection

    first_slot = (
        field_summary(reflections[0])
        if len(reflections) else []
    )

    positive = []

    for reflection in reflections:
        tof = getattr(reflection, "time_of_flight", None)
        strength = getattr(reflection, "signal_strength", None)

        if (
            tof is not None
            and strength is not None
            and tof > 0
            and strength > 0
        ):
            positive = field_summary(reflection)
            break

    return {
        "ReflectionField": True,
        "Count": len(reflections),
        "FirstSlot": first_slot,
        "FirstPositiveSlot": positive,
    }


def inspect_pair(pair):
    pair_id = pair["PairID"]
    path = Path(pair["SensorViewPath"])

    if not path.is_file():
        raise FileNotFoundError(path)

    results = []
    schemas = []
    totals = Counter()

    for frame, message, size in iter_osi_messages(
        path, SensorView, SCAN_LIMIT
    ):
        if frame not in SELECTED_FRAMES:
            continue

        cameras = message.camera_sensor_view
        lidars = message.lidar_sensor_view
        radars = message.radar_sensor_view

        image_bytes = sum(
            len(cam.image_data) for cam in cameras
        )

        lidar_count = sum(
            len(view.reflection) for view in lidars
        )

        radar_count = sum(
            len(view.reflection) for view in radars
        )

        sample = {
            "PairID": pair_id,
            "Frame": frame,
            "TimestampNs": timestamp_ns(message),
            "MessageBytes": size,
            "CameraEntries": len(cameras),
            "LiDAREntries": len(lidars),
            "RadarEntries": len(radars),
            "ImageBytes": image_bytes,
            "LiDARReflectionSlots": lidar_count,
            "RadarReflectionSlots": radar_count,
            "CameraFields": (
                field_summary(cameras[0])
                if cameras else []
            ),
            "LiDARFields": (
                field_summary(lidars[0])
                if lidars else []
            ),
            "RadarFields": (
                field_summary(radars[0])
                if radars else []
            ),
            "LiDARReflectionSample": (
                sample_reflection(lidars[0])
                if lidars else {}
            ),
            "RadarReflectionSample": (
                sample_reflection(radars[0])
                if radars else {}
            ),
            "CameraImageHeaderHex": (
                cameras[0].image_data[:16].hex()
                if cameras else ""
            ),
        }

        results.append(sample)

        totals["Samples"] += 1
        totals["CameraSamples"] += int(len(cameras) > 0)
        totals["LiDARSamples"] += int(len(lidars) > 0)
        totals["RadarSamples"] += int(len(radars) > 0)

        if cameras:
            schemas.extend(
                schema_rows(cameras[0], "Camera")
            )

        if lidars:
            schemas.extend(
                schema_rows(lidars[0], "LiDAR")
            )
            if lidars[0].reflection:
                schemas.extend(schema_rows(
                    lidars[0].reflection[0],
                    "LiDARReflection"
                ))

        if radars:
            schemas.extend(
                schema_rows(radars[0], "Radar")
            )
            if radars[0].reflection:
                schemas.extend(schema_rows(
                    radars[0].reflection[0],
                    "RadarReflection"
                ))

    return results, schemas, totals


print("\n=== TASK 23.2 OSI MEASUREMENT INSPECTION ===")

pairs = load_manifest()

all_samples = []
all_schema = []
pair_summaries = []

for pair in pairs:
    print(f"\n=== PAIR {pair['PairID']} ===")
    print("Recording:", pair["SensorViewFilename"])

    samples, schemas, totals = inspect_pair(pair)

    all_samples.extend(samples)
    all_schema.extend(schemas)

    pair_summaries.append({
        "PairID": pair["PairID"],
        "Recording": pair["SensorViewFilename"],
        **dict(totals),
    })

    for sample in samples:
        print(
            f"Frame={sample['Frame']} | "
            f"Camera={sample['CameraEntries']} | "
            f"LiDAR={sample['LiDAREntries']} | "
            f"Radar={sample['RadarEntries']} | "
            f"ImageBytes={sample['ImageBytes']} | "
            f"LiDARSlots={sample['LiDARReflectionSlots']} | "
            f"RadarSlots={sample['RadarReflectionSlots']}"
        )

        if sample["CameraEntries"]:
            print(
                "  Camera image header:",
                sample["CameraImageHeaderHex"]
            )

        if sample["LiDARReflectionSample"]:
            fields = sample[
                "LiDARReflectionSample"
            ].get("FirstSlot", [])
            print(
                "  LiDAR reflection fields:",
                [x["Field"] for x in fields]
            )

        if sample["RadarReflectionSample"]:
            fields = sample[
                "RadarReflectionSample"
            ].get("FirstPositiveSlot", [])
            print(
                "  Positive radar fields:",
                [x["Field"] for x in fields]
            )

# Remove repeated field-schema rows.
unique_schema = {}

for row in all_schema:
    key = (
        row["Category"],
        row["MessageType"],
        row["FieldName"],
    )
    unique_schema[key] = row

schema_path = (
    CSV_DIR / "task23_02_sensor_field_schema.csv"
)

with schema_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "Category",
            "MessageType",
            "FieldName",
            "FieldType",
            "Repeated",
        ],
    )
    writer.writeheader()
    writer.writerows(unique_schema.values())

sample_path = (
    FINDINGS / "task23_02_measurement_samples.json"
)

sample_path.write_text(
    json.dumps({
        "Task": "23.2",
        "FramesSelected": sorted(SELECTED_FRAMES),
        "PairSummaries": pair_summaries,
        "Samples": all_samples,
        "Limitations": [
            "Only four sampled frames per recording",
            "Field presence does not prove payload correctness",
            "Image encoding not yet independently decoded",
            "Sensor coordinate conventions remain unverified",
            "No object association or detection accuracy tested",
        ]
    }, indent=2),
    encoding="utf-8"
)

summary_path = (
    CSV_DIR / "task23_02_sample_summary.csv"
)

summary_rows = [
    {
        key: sample[key]
        for key in (
            "PairID", "Frame", "TimestampNs",
            "MessageBytes", "CameraEntries",
            "LiDAREntries", "RadarEntries",
            "ImageBytes", "LiDARReflectionSlots",
            "RadarReflectionSlots",
            "CameraImageHeaderHex"
        )
    }
    for sample in all_samples
]

with summary_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(summary_rows[0].keys()),
    )
    writer.writeheader()
    writer.writerows(summary_rows)

print("\n=== TASK 23.2 FINAL VERIFICATION ===")
print("Pairs inspected:", len(pairs))
print("Sampled messages:", len(all_samples))
print("Unique schema fields:", len(unique_schema))
print("Schema CSV saved:", schema_path.is_file())
print("Sample CSV saved:", summary_path.is_file())
print("Sample JSON saved:", sample_path.is_file())

print("\n=== TASK 23.2 COMPLETE ===")

