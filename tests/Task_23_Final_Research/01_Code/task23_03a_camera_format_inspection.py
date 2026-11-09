import csv
import json
import sys
from pathlib import Path
from google.protobuf.descriptor import FieldDescriptor

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(0, str(
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
))

from task22_02_reusable_osi_reader import (
    iter_osi_messages,
    SensorView,
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

CSV_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

SELECTED_FRAMES = {1, 25, 99}
PAIR_IDS = {"1", "2", "3"}

def field_value(value):
    if isinstance(value, bytes):
        return {
            "bytes": len(value),
            "header_hex": value[:16].hex()
        }

    if isinstance(value, (int, float, str, bool)):
        return value

    return str(value)[:160]


def inspect_message(message, depth=0):
    """Inspect populated protobuf fields without dumping payloads."""
    if depth > 3:
        return {"note": "depth_limit"}

    result = {}

    for descriptor, value in message.ListFields():
        name = descriptor.name

        if descriptor.is_repeated:
            item = {"count": len(value)}

            if (
                len(value) > 0
                and descriptor.type == FieldDescriptor.TYPE_MESSAGE
            ):
                item["first_element"] = inspect_message(
                    value[0], depth + 1
                )

            result[name] = item

        elif descriptor.type == FieldDescriptor.TYPE_MESSAGE:
            result[name] = inspect_message(
                value, depth + 1
            )

        else:
            result[name] = field_value(value)

    return result


def declared_fields(message):
    return [
        {
            "name": f.name,
            "type_number": f.type,
            "repeated": bool(f.is_repeated),
            "message_type": (
                f.message_type.full_name
                if f.message_type else ""
            )
        }
        for f in message.DESCRIPTOR.fields
    ]


def candidate_layouts(byte_count):
    resolutions = [
        (320, 240),
        (640, 480),
        (800, 600),
        (1024, 768),
        (1280, 720),
        (1920, 1080),
    ]

    results = []

    for width, height in resolutions:
        for channels in (1, 3, 4):
            if width * height * channels == byte_count:
                results.append({
                    "width": width,
                    "height": height,
                    "channels": channels,
                    "bytes_per_channel": 1,
                    "status": "SIZE_ONLY_NOT_VERIFIED"
                })

    return results


print("\n=== TASK 23.3A CAMERA FORMAT INSPECTION ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as f:
    pairs = [
        row for row in csv.DictReader(f)
        if row["PairID"] in PAIR_IDS
    ]

samples = []
details = []

for pair in pairs:
    pair_id = pair["PairID"]
    path = Path(pair["SensorViewPath"])

    print(f"\n=== PAIR {pair_id} ===")
    print("Recording:", path.name)

    if not path.is_file():
        raise FileNotFoundError(path)

    for frame, message, message_bytes in iter_osi_messages(
        path, SensorView, 100
    ):
        if frame not in SELECTED_FRAMES:
            continue

        cameras = list(message.camera_sensor_view)

        if not cameras:
            print(f"Frame {frame}: camera absent")
            continue

        camera = cameras[0]
        payload = camera.image_data
        byte_count = len(payload)

        sample = {
            "PairID": pair_id,
            "Frame": frame,
            "ImageBytes": byte_count,
            "HeaderHex": payload[:16].hex(),
            "CandidateLayouts": candidate_layouts(
                byte_count
            )
        }

        samples.append(sample)

        details.append({
            "PairID": pair_id,
            "Frame": frame,
            "CameraDeclaredFields": declared_fields(camera),
            "CameraPopulatedFields": inspect_message(camera),
            "SensorViewPopulatedFields": inspect_message(
                message, depth=2
            ),
            "CandidateLayouts": sample["CandidateLayouts"]
        })

        print(
            f"Frame={frame} | "
            f"ImageBytes={byte_count} | "
            f"Header={sample['HeaderHex']}"
        )

        print(
            "Candidate layouts (size only):",
            [
                (x["width"], x["height"], x["channels"])
                for x in sample["CandidateLayouts"]
            ]
        )

        if frame == 1:
            print(
                "Declared camera fields:",
                [f["name"] for f in declared_fields(camera)]
            )
            print(
                "Populated camera fields:",
                list(inspect_message(camera).keys())
            )

csv_path = (
    CSV_DIR / "task23_03a_camera_format_candidates.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "PairID", "Frame", "ImageBytes", "HeaderHex",
            "CandidateLayouts"
        ]
    )
    writer.writeheader()

    for row in samples:
        writer.writerow({
            **row,
            "CandidateLayouts": json.dumps(
                row["CandidateLayouts"]
            )
        })

json_path = (
    FINDINGS / "task23_03a_camera_structure.json"
)

json_path.write_text(
    json.dumps({
        "Task": "23.3A",
        "Purpose": "Camera encoding and shape investigation",
        "Samples": samples,
        "ConfigurationInspection": details,
        "Interpretation": (
            "Matching byte counts provide candidate layouts, "
            "not proof of image width, height, channel count, "
            "color order or row stride."
        )
    }, indent=2),
    encoding="utf-8"
)

text_path = (
    FINDINGS / "task23_03a_camera_findings.txt"
)

lines = [
    "TASK 23.3A CAMERA FORMAT INVESTIGATION",
    "",
    f"Recording pairs inspected: {len(pairs)}",
    f"Camera samples inspected: {len(samples)}",
    "",
    "Image interpretation is pending confirmation",
    "of actual dimensions, channel order and layout.",
    "",
    "A matching byte count does not prove pixel format.",
    "Current configuration files may not match the",
    "configuration active at recording time."
]

text_path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8"
)

print("\n=== TASK 23.3A FINAL VERIFICATION ===")
print("Recording pairs:", len(pairs))
print("Camera samples:", len(samples))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Findings saved:", text_path.is_file())
print("\n=== TASK 23.3A COMPLETE ===")
