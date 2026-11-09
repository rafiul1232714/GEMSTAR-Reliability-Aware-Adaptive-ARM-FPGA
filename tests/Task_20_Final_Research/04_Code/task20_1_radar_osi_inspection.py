import csv
import json
import struct
from collections import Counter
from pathlib import Path

from google.protobuf.descriptor import FieldDescriptor
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

MAX_FRAMES = 5

def read_messages(path):
    with path.open("rb") as f:
        for index in range(MAX_FRAMES):
            header = f.read(4)

            if len(header) == 0:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]

            if not (0 < size < 100_000_000):
                raise ValueError(
                    f"Invalid message size: {size}"
                )

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Truncated OSI message")

            msg = SensorView()
            msg.ParseFromString(payload)

            yield index, msg

def inspect_fields(message, prefix="", depth=0):
    """
    Show populated protobuf fields.
    Do not print binary payloads.
    Inspect the first element of repeated messages.
    """
    records = []

    if depth > 6:
        return records

    for field, value in message.ListFields():
        name = prefix + field.name

        if field.is_repeated:
            records.append({
                "Field": name,
                "Type": "REPEATED",
                "Value": str(len(value))
            })

            if (
                len(value) > 0
                and field.type == FieldDescriptor.TYPE_MESSAGE
            ):
                records.extend(inspect_fields(
                    value[0],
                    name + "[0].",
                    depth + 1
                ))

        elif field.type == FieldDescriptor.TYPE_MESSAGE:
            records.append({
                "Field": name,
                "Type": "MESSAGE",
                "Value": str(value.ByteSize())
            })

            records.extend(inspect_fields(
                value, name + ".", depth + 1
            ))

        elif field.type == FieldDescriptor.TYPE_BYTES:
            records.append({
                "Field": name,
                "Type": "BYTES",
                "Value": str(len(value))
            })

        else:
            records.append({
                "Field": name,
                "Type": "VALUE",
                "Value": str(value)[:120]
            })

    return records

def main():
    print("\n=== TASK 20.1 RADAR OSI INSPECTION ===")

    files = sorted(RAW.rglob("*_sv_*.osi"))

    print("SensorView recordings found:", len(files))

    if not files:
        raise RuntimeError("No SensorView recordings found")

    rows = []
    all_field_names = Counter()
    field_examples = {}
    field_sources = {}

    for path in files:
        scenario = path.parent.name

        frame_count = 0
        radar_views = 0
        nonempty_radar = 0
        max_size = 0
        first_fields = None
        status = "OK"

        try:
            for frame_index, msg in read_messages(path):
                frame_count += 1

                for radar in msg.radar_sensor_view:
                    radar_views += 1

                    size = radar.ByteSize()
                    max_size = max(max_size, size)

                    fields = inspect_fields(radar)

                    if first_fields is None:
                        first_fields = fields

                    for item in fields:
                        name = item["Field"]
                        all_field_names[name] += 1

                        field_examples.setdefault(
                            name, item["Value"]
                        )
                        field_sources.setdefault(
                            name, scenario
                        )

                    # Nonempty message indicates fields are
                    # populated, not necessarily detections.
                    if size > 0:
                        nonempty_radar += 1

        except Exception as exc:
            status = "ERROR: " + str(exc)[:150]

        row = {
            "Recording": scenario,
            "File": path.name,
            "FramesChecked": frame_count,
            "RadarViews": radar_views,
            "NonemptyRadarMessages": nonempty_radar,
            "LargestRadarMessageBytes": max_size,
            "Status": status
        }

        rows.append(row)

        print("\nRecording:", scenario)
        print("Frames checked:", frame_count)
        print("Radar SensorViews:", radar_views)
        print("Largest radar message:", max_size, "bytes")
        print("Status:", status)

        if first_fields:
            print("First radar message fields:")

            for field in first_fields[:45]:
                print(
                    " ",
                    field["Field"],
                    "|",
                    field["Type"],
                    "|",
                    field["Value"]
                )

        else:
            print("No populated radar fields found.")

    inventory_file = (
        DATA / "task20_1_radar_recording_inventory.csv"
    )

    with inventory_file.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    field_rows = []

    for name in sorted(all_field_names):
        field_rows.append({
            "Field": name,
            "ObservedCount": all_field_names[name],
            "ExampleValue": field_examples[name],
            "ExampleRecording": field_sources[name],
        })

    fields_file = (
        DATA / "task20_1_radar_populated_fields.csv"
    )

    if field_rows:
        with fields_file.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=list(field_rows[0])
            )
            writer.writeheader()
            writer.writerows(field_rows)

    summary = {
        "Task": "20.1",
        "RecordingsFound": len(files),
        "FramesChecked": sum(
            r["FramesChecked"] for r in rows
        ),
        "RadarViewsFound": sum(
            r["RadarViews"] for r in rows
        ),
        "PopulatedRadarFieldPaths": len(field_rows),
        "NoRadarDetectionSemanticsAssumed": True,
        "EnergyMeasured": False,
        "GroundTruthAccuracyMeasured": False
    }

    summary_file = (
        FINDINGS / "task20_1_radar_inspection_summary.json"
    )

    summary_file.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )

    print("\n=== TASK 20.1 COMPLETE ===")
    print("Recordings:", len(files))
    print("Frames checked:", summary["FramesChecked"])
    print("Radar views:", summary["RadarViewsFound"])
    print("Field paths:", len(field_rows))
    print("Inventory saved:", inventory_file.is_file())
    print("Fields CSV saved:", fields_file.is_file())
    print("Summary JSON saved:", summary_file.is_file())

    print("\nIMPORTANT:")
    print("Radar view presence is not proof of detections.")
    print("Range, velocity, angle and IDs must be")
    print("confirmed from actual populated fields.")
    print("No hardware energy or accuracy measured.")

if __name__ == "__main__":
    main()
