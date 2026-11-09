import csv
import json
import math
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
)

MANIFEST = (
    TASK / "05_Raw_Data_References"
    / "task23_01_source_manifest.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

for folder in (CSV_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

FRAMES = (0, 1, 25, 99)
LIMIT = 100


def field_summary(message, depth=0):
    """Inspect present protobuf fields without dumping bulk data."""
    if depth >= 4:
        return {"note": "depth limit"}

    result = {}

    for descriptor, value in message.ListFields():
        name = descriptor.name

        if descriptor.is_repeated:
            item = {
                "count": len(value)
            }

            if (
                len(value) > 0
                and descriptor.message_type is not None
            ):
                item["first"] = field_summary(
                    value[0], depth + 1
                )

            result[name] = item

        elif descriptor.message_type is not None:
            result[name] = field_summary(
                value, depth + 1
            )

        elif descriptor.type == descriptor.TYPE_BYTES:
            result[name] = {"byte_count": len(value)}

        else:
            result[name] = value

    return result


def finite_positive(value):
    return math.isfinite(value) and value > 0.0


def save_csv(path, rows, columns):
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as handle:
    manifest = list(csv.DictReader(handle))

rows = []
details = []

print("\n=== TASK 23.5A RADAR CONFIGURATION AUDIT ===")

for pair in manifest:
    pair_id = int(pair["PairID"])

    sv_path = Path(pair["SensorViewPath"])

    if not sv_path.is_file():
        raise FileNotFoundError(sv_path)

    print(f"\n=== PAIR {pair_id} ===")

    found = set()

    for frame, sv, size in iter_osi_messages(
        sv_path,
        SensorView,
        LIMIT
    ):
        if frame not in FRAMES:
            continue

        found.add(frame)

        radar_views = list(sv.radar_sensor_view)

        for sensor_index, radar in enumerate(radar_views):
            reflections = radar.reflection

            positive_tof = sum(
                finite_positive(float(r.time_of_flight))
                for r in reflections
            )

            positive_strength = sum(
                finite_positive(float(r.signal_strength))
                for r in reflections
            )

            positive_both = sum(
                finite_positive(float(r.time_of_flight))
                and finite_positive(float(r.signal_strength))
                for r in reflections
            )

            sample = next(
                (
                    r for r in reflections
                    if finite_positive(
                        float(r.time_of_flight)
                    )
                ),
                reflections[0] if len(reflections) else None
            )

            row = {
                "PairID": pair_id,
                "Frame": frame,
                "SensorIndex": sensor_index,
                "SensorViewMessageBytes": size,
                "RadarEntryCount": len(radar_views),
                "ReflectionSlots": len(reflections),
                "PositiveTimeOfFlight": positive_tof,
                "PositiveSignalStrength": positive_strength,
                "PositiveBoth": positive_both,
            }

            rows.append(row)

            details.append({
                "PairID": pair_id,
                "Frame": frame,
                "SensorIndex": sensor_index,
                "ViewConfiguration": field_summary(
                    radar.view_configuration
                ),
                "RadarPresentFields": [
                    field.name
                    for field, _ in radar.ListFields()
                ],
                "ReflectionFieldNames": [
                    field.name
                    for field in (
                        reflections[0].DESCRIPTOR.fields
                        if len(reflections) else []
                    )
                ],
                "RepresentativeReflection": (
                    field_summary(sample)
                    if sample is not None else {}
                ),
            })

            print(
                f"Frame {frame:02d} | "
                f"RadarSlots={len(reflections)} | "
                f"PositiveTOF={positive_tof} | "
                f"PositiveStrength={positive_strength} | "
                f"PositiveBoth={positive_both}"
            )

        if not radar_views:
            print(
                f"Frame {frame:02d} | "
                "No Radar sensor entry"
            )

    missing = sorted(set(FRAMES) - found)

    if missing:
        raise RuntimeError(
            f"Pair {pair_id}: missing frames {missing}"
        )

csv_path = CSV_DIR / (
    "task23_05a_radar_raw_measurement_summary.csv"
)

json_path = FINDINGS / (
    "task23_05a_radar_configuration_findings.json"
)

save_csv(
    csv_path,
    rows,
    [
        "PairID",
        "Frame",
        "SensorIndex",
        "SensorViewMessageBytes",
        "RadarEntryCount",
        "ReflectionSlots",
        "PositiveTimeOfFlight",
        "PositiveSignalStrength",
        "PositiveBoth",
    ]
)

json_path.write_text(
    json.dumps({
        "Task": "23.5A",
        "Scope": (
            "Radar configuration, protobuf fields, "
            "and preliminary raw reflection counts"
        ),
        "SampledFrames": sorted(FRAMES),
        "Records": details,
        "ScientificStatus": "RAW_RADAR_INSPECTION",
        "Limitations": [
            "Positive TOF is not proof of a correct detection",
            "Radar noise and weather effects not validated",
            "No range reconstruction performed yet",
            "No velocity or Doppler conversion performed yet",
            "No object-level accuracy claimed",
            "No hardware power or latency measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5A FINAL VERIFICATION ===")
print("Recording pairs examined:", len(manifest))
print("Radar entries inspected:", len(rows))
print(
    "Total reflection slots:",
    sum(r["ReflectionSlots"] for r in rows)
)
print(
    "Total positive TOF:",
    sum(r["PositiveTimeOfFlight"] for r in rows)
)
print(
    "Total positive TOF and strength:",
    sum(r["PositiveBoth"] for r in rows)
)
print("Summary CSV saved:", csv_path.is_file())
print("Configuration JSON saved:", json_path.is_file())

print("\n=== TASK 23.5A COMPLETE ===")

