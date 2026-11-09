import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

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

CSV_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

SAMPLE_FRAMES = {0, 1, 10, 25, 50, 75, 99}
FRAME_LIMIT = 100


def summarize_message(message, depth=0):
    """Describe populated fields without large payload dumps."""
    if depth > 4:
        return {"note": "depth_limit"}

    result = {}

    for field, value in message.ListFields():
        if field.is_repeated:
            entry = {"count": len(value)}

            if (
                len(value) > 0
                and field.message_type is not None
            ):
                entry["first"] = summarize_message(
                    value[0], depth + 1
                )

            result[field.name] = entry

        elif field.message_type is not None:
            result[field.name] = summarize_message(
                value, depth + 1
            )

        elif isinstance(value, bytes):
            result[field.name] = {
                "byte_count": len(value)
            }

        else:
            result[field.name] = value

    return result


def describe_schema(message):
    return [
        {
            "name": field.name,
            "number": field.number,
            "type": field.type,
            "repeated": bool(field.is_repeated),
            "message_type": (
                field.message_type.full_name
                if field.message_type else ""
            ),
        }
        for field in message.DESCRIPTOR.fields
    ]


def stats(values):
    if not values:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None
        }

    array = np.asarray(values, dtype=np.float64)

    return {
        "count": int(array.size),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "mean": float(array.mean())
    }


def inspect_reflections(reflections):
    valid = 0
    positive_tof = 0
    positive_strength = 0
    nonfinite = 0

    valid_tof = []
    valid_strength = []
    object_ids = set()

    for reflection in reflections:
        tof = float(
            getattr(reflection, "time_of_flight", 0.0)
        )

        strength = float(
            getattr(reflection, "signal_strength", 0.0)
        )

        if not (
            math.isfinite(tof)
            and math.isfinite(strength)
        ):
            nonfinite += 1
            continue

        if tof > 0:
            positive_tof += 1

        if strength > 0:
            positive_strength += 1

        if tof > 0 and strength > 0:
            valid += 1
            valid_tof.append(tof)
            valid_strength.append(strength)

            if hasattr(reflection, "object_id"):
                object_ids.add(
                    str(reflection.object_id.value)
                )

    return {
        "ReflectionSlots": len(reflections),
        "PositiveTOF": positive_tof,
        "PositiveStrength": positive_strength,
        "BothPositive": valid,
        "NonfiniteTOFOrStrength": nonfinite,
        "TOFStatistics": stats(valid_tof),
        "StrengthStatistics": stats(valid_strength),
        "DistinctObjectIDs": len(object_ids),
    }


print("\n=== TASK 23.4A LIDAR CONFIGURATION AUDIT ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as handle:
    pairs = list(csv.DictReader(handle))

rows = []
details = []

for pair in pairs:
    pair_id = pair["PairID"]
    source = Path(pair["SensorViewPath"])

    print(f"\n=== PAIR {pair_id} ===")
    print("Recording:", source.name)

    found_frames = 0

    for frame, message, size in iter_osi_messages(
        source, SensorView, FRAME_LIMIT
    ):
        if frame not in SAMPLE_FRAMES:
            continue

        found_frames += 1

        views = list(message.lidar_sensor_view)

        if not views:
            print(
                f"Frame {frame}: LiDAR entry absent"
            )

            rows.append({
                "PairID": pair_id,
                "Frame": frame,
                "LiDAREntries": 0,
                "ReflectionSlots": 0,
                "PositiveTOF": 0,
                "PositiveStrength": 0,
                "BothPositive": 0,
                "NonfiniteTOFOrStrength": 0,
                "DistinctObjectIDs": 0,
                "MinPositiveTOF": "",
                "MaxPositiveTOF": "",
                "MeanPositiveStrength": ""
            })

            continue

        view = views[0]
        result = inspect_reflections(
            view.reflection
        )

        tof_stats = result["TOFStatistics"]
        strength_stats = result[
            "StrengthStatistics"
        ]

        rows.append({
            "PairID": pair_id,
            "Frame": frame,
            "LiDAREntries": len(views),
            "ReflectionSlots": result[
                "ReflectionSlots"
            ],
            "PositiveTOF": result[
                "PositiveTOF"
            ],
            "PositiveStrength": result[
                "PositiveStrength"
            ],
            "BothPositive": result[
                "BothPositive"
            ],
            "NonfiniteTOFOrStrength": result[
                "NonfiniteTOFOrStrength"
            ],
            "DistinctObjectIDs": result[
                "DistinctObjectIDs"
            ],
            "MinPositiveTOF": (
                tof_stats["minimum"]
                if tof_stats["minimum"] is not None
                else ""
            ),
            "MaxPositiveTOF": (
                tof_stats["maximum"]
                if tof_stats["maximum"] is not None
                else ""
            ),
            "MeanPositiveStrength": (
                strength_stats["mean"]
                if strength_stats["mean"] is not None
                else ""
            )
        })

        print(
            f"Frame={frame} | "
            f"Slots={result['ReflectionSlots']} | "
            f"PositiveTOF={result['PositiveTOF']} | "
            f"BothPositive={result['BothPositive']} | "
            f"Nonfinite={result['NonfiniteTOFOrStrength']}"
        )

        if frame == 1:
            config = summarize_message(
                view.view_configuration
            )

            print("\nLiDAR configuration:")
            print(json.dumps(
                config, indent=2, default=str
            ))

            print(
                "\nDeclared LiDAR fields:",
                [x["name"] for x in describe_schema(view)]
            )

            if view.reflection:
                first = view.reflection[0]

                print(
                    "\nDeclared reflection fields:",
                    [
                        x["name"]
                        for x in describe_schema(first)
                    ]
                )

                print(
                    "\nFirst reflection:",
                    json.dumps(
                        summarize_message(first),
                        indent=2,
                        default=str
                    )
                )

            details.append({
                "PairID": pair_id,
                "Configuration": config,
                "LiDARSchema": describe_schema(view),
                "ReflectionSchema": (
                    describe_schema(
                        view.reflection[0]
                    )
                    if view.reflection else []
                ),
                "FirstReflection": (
                    summarize_message(
                        view.reflection[0]
                    )
                    if view.reflection else {}
                ),
                "Frame1Statistics": result
            })

    if found_frames != len(SAMPLE_FRAMES):
        raise RuntimeError(
            f"Pair {pair_id}: expected "
            f"{len(SAMPLE_FRAMES)} sampled frames, "
            f"found {found_frames}"
        )

csv_path = (
    CSV_DIR / "task23_04a_lidar_validity_audit.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

json_path = (
    FINDINGS /
    "task23_04a_lidar_configuration_findings.json"
)

json_path.write_text(
    json.dumps({
        "Task": "23.4A",
        "SampleFrames": sorted(SAMPLE_FRAMES),
        "Configurations": details,
        "ValidityDefinition": (
            "Finite positive time_of_flight and "
            "signal_strength. This is preliminary "
            "screening, not physical correctness."
        ),
        "Limitations": [
            "Only seven frames inspected per recording",
            "Reflection slots are not necessarily valid points",
            "Time-of-flight units not yet verified",
            "Scan angles and coordinate system unverified",
            "Object IDs are simulator metadata, not detections",
            "No distance or 3D point reconstruction yet",
            "No FPGA energy measurements"
        ]
    }, indent=2, default=str),
    encoding="utf-8"
)

print("\n=== TASK 23.4A SUMMARY ===")

for pair in pairs:
    pair_rows = [
        r for r in rows
        if r["PairID"] == pair["PairID"]
    ]

    total_slots = sum(
        int(r["ReflectionSlots"])
        for r in pair_rows
    )

    positive = sum(
        int(r["BothPositive"])
        for r in pair_rows
    )

    print(
        f"Pair {pair['PairID']} | "
        f"SampledFrames={len(pair_rows)} | "
        f"TotalSlots={total_slots} | "
        f"BothPositive={positive}"
    )

print("\n=== TASK 23.4A FINAL VERIFICATION ===")
print("Recording pairs:", len(pairs))
print("Sampled frames:", len(rows))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())

print("\n=== TASK 23.4A COMPLETE ===")
