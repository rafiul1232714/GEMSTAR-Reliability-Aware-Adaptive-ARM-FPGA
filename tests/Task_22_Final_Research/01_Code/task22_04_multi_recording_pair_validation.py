import csv
import json
import sys
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_22_Final_Research"

sys.path.insert(0, str(TASK / "01_Code"))

from task22_02_reusable_osi_reader import (
    iter_osi_messages,
    timestamp_ns,
    SensorView,
    GroundTruth,
)

INVENTORY = (
    TASK / "02_CSV_Data" /
    "task22_01_recording_inventory.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"
REFS = TASK / "05_Raw_Data_References"

for directory in (CSV_DIR, FINDINGS, REFS):
    directory.mkdir(parents=True, exist_ok=True)

LIMIT = 100
MAX_PAIRS = 5

KNOWN_NAME = "20261102T180104Z_sv_380_X_806_GEMSTAR.osi"


def pair_key(path):
    name = path.name

    if "_sv_" in name:
        common = name.replace("_sv_", "_PAIR_", 1)
        kind = "SensorView"
    elif "_gt_" in name:
        common = name.replace("_gt_", "_PAIR_", 1)
        kind = "GroundTruth"
    else:
        return None, None

    # Matching requires the same parent directory.
    key = (str(path.parent).lower(), common.lower())
    return key, kind


def load_pairs():
    index = defaultdict(dict)

    with INVENTORY.open(
        newline="", encoding="utf-8-sig"
    ) as handle:
        for row in csv.DictReader(handle):
            path = Path(row["FullPath"])

            if not path.is_file():
                continue

            key, kind = pair_key(path)

            if key and kind:
                index[key][kind] = path

    pairs = [
        entry for entry in index.values()
        if "SensorView" in entry
        and "GroundTruth" in entry
    ]

    # Prefer recordings with meaningful file sizes.
    # This is a selection heuristic, not proof of quality.
    pairs.sort(
        key=lambda p: (
            p["SensorView"].stat().st_size < 100_000,
            p["GroundTruth"].stat().st_size < 100_000,
            str(p["SensorView"]).lower()
        )
    )

    known = [
        p for p in pairs
        if p["SensorView"].name == KNOWN_NAME
    ]

    selected = known[:1]

    # Prefer several different recording directories.
    used_directories = {
        str(p["SensorView"].parent).lower()
        for p in selected
    }

    for pair in pairs:
        if len(selected) >= MAX_PAIRS:
            break

        directory = str(pair["SensorView"].parent).lower()

        if pair not in selected and directory not in used_directories:
            selected.append(pair)
            used_directories.add(directory)

    # Fill remaining slots, if needed.
    for pair in pairs:
        if len(selected) >= MAX_PAIRS:
            break

        if pair not in selected:
            selected.append(pair)

    return pairs, selected


def validate_pair(pair, pair_number):
    sv_path = pair["SensorView"]
    gt_path = pair["GroundTruth"]

    sv_iter = iter_osi_messages(
        sv_path, SensorView, LIMIT
    )
    gt_iter = iter_osi_messages(
        gt_path, GroundTruth, LIMIT
    )

    rows = []
    previous_sv = None
    previous_gt = None

    for sv_item, gt_item in zip_longest(sv_iter, gt_iter):

        # Each iterator yields (frame, message, payload size).
        sv_frame, sv, sv_bytes = (
            sv_item if sv_item is not None
            else (None, None, None)
        )

        gt_frame, gt, gt_bytes = (
            gt_item if gt_item is not None
            else (None, None, None)
        )

        sv_time = timestamp_ns(sv) if sv else None
        gt_time = timestamp_ns(gt) if gt else None

        matched = (
            sv_time is not None
            and gt_time is not None
            and sv_time == gt_time
        )

        sv_nonmonotonic = (
            previous_sv is not None
            and sv_time is not None
            and sv_time <= previous_sv
        )

        gt_nonmonotonic = (
            previous_gt is not None
            and gt_time is not None
            and gt_time <= previous_gt
        )

        if sv_time is not None:
            previous_sv = sv_time

        if gt_time is not None:
            previous_gt = gt_time

        rows.append({
            "PairID": pair_number,
            "ScenarioFolder": str(sv_path.parent),
            "SensorViewFilename": sv_path.name,
            "GroundTruthFilename": gt_path.name,
            "Frame": (
                sv_frame if sv_frame is not None
                else gt_frame
            ),
            "SVPresent": sv is not None,
            "GTPresent": gt is not None,
            "SVTimestampNs": (
                sv_time if sv_time is not None else ""
            ),
            "GTTimestampNs": (
                gt_time if gt_time is not None else ""
            ),
            "AbsTimestampDifferenceMs": (
                abs(sv_time - gt_time) / 1e6
                if sv_time is not None
                and gt_time is not None
                else ""
            ),
            "ExactTimestampMatch": matched,
            "SVNonmonotonic": sv_nonmonotonic,
            "GTNonmonotonic": gt_nonmonotonic,
            "CameraEntries": (
                len(sv.camera_sensor_view) if sv else 0
            ),
            "LiDAREntries": (
                len(sv.lidar_sensor_view) if sv else 0
            ),
            "RadarEntries": (
                len(sv.radar_sensor_view) if sv else 0
            ),
            "GTMovingObjects": (
                len(gt.moving_object) if gt else 0
            ),
            "SVMessageBytes": (
                sv_bytes if sv_bytes is not None else ""
            ),
            "GTMessageBytes": (
                gt_bytes if gt_bytes is not None else ""
            )
        })

    paired_rows = [
        r for r in rows
        if r["SVPresent"] and r["GTPresent"]
    ]

    differences = [
        r["AbsTimestampDifferenceMs"]
        for r in paired_rows
    ]

    summary = {
        "PairID": pair_number,
        "ScenarioFolder": str(sv_path.parent),
        "SensorViewFilename": sv_path.name,
        "GroundTruthFilename": gt_path.name,
        "SensorViewFrames": sum(r["SVPresent"] for r in rows),
        "GroundTruthFrames": sum(r["GTPresent"] for r in rows),
        "PairedFrames": len(paired_rows),
        "ExactTimestampMatches": sum(
            r["ExactTimestampMatch"] for r in rows
        ),
        "TimestampMismatches": sum(
            not r["ExactTimestampMatch"]
            for r in paired_rows
        ),
        "MaxTimestampDifferenceMs": (
            max(differences) if differences else ""
        ),
        "NonmonotonicSVFrames": sum(
            r["SVNonmonotonic"] for r in rows
        ),
        "NonmonotonicGTFrames": sum(
            r["GTNonmonotonic"] for r in rows
        ),
        "CameraEntryFrames": sum(
            r["CameraEntries"] > 0 for r in rows
        ),
        "LiDAREntryFrames": sum(
            r["LiDAREntries"] > 0 for r in rows
        ),
        "RadarEntryFrames": sum(
            r["RadarEntries"] > 0 for r in rows
        ),
        "ValidationStatus": (
            "PASS_MESSAGE_ALIGNMENT"
            if paired_rows
            and len(paired_rows) == len(rows)
            and all(r["ExactTimestampMatch"] for r in rows)
            and not any(r["SVNonmonotonic"] for r in rows)
            and not any(r["GTNonmonotonic"] for r in rows)
            else "REVIEW_REQUIRED"
        )
    }

    return rows, summary


def save_csv(path, rows):
    if not rows:
        return False

    with path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    return path.is_file()


def main():
    print("\n=== TASK 22.4 MULTI-RECORDING PAIR VALIDATION ===")

    if not INVENTORY.is_file():
        raise FileNotFoundError(INVENTORY)

    all_pairs, selected = load_pairs()

    print("Matching filename pairs discovered:", len(all_pairs))
    print("Pairs selected for testing:", len(selected))

    all_frame_rows = []
    summaries = []
    errors = []

    for number, pair in enumerate(selected, 1):
        print(f"\n=== PAIR {number} ===")
        print("SV:", pair["SensorView"].name)
        print("GT:", pair["GroundTruth"].name)

        try:
            frame_rows, summary = validate_pair(
                pair, number
            )

            all_frame_rows.extend(frame_rows)
            summaries.append(summary)

            print(
                "Paired frames:",
                summary["PairedFrames"]
            )
            print(
                "Exact timestamp matches:",
                summary["ExactTimestampMatches"]
            )
            print(
                "Camera/LiDAR/Radar frames:",
                summary["CameraEntryFrames"],
                summary["LiDAREntryFrames"],
                summary["RadarEntryFrames"]
            )
            print("Status:", summary["ValidationStatus"])

        except Exception as exc:
            message = f"Pair {number}: {type(exc).__name__}: {exc}"
            errors.append(message)
            print("ERROR:", message)

    frame_csv = (
        CSV_DIR / "task22_04_pair_frame_validation.csv"
    )

    summary_csv = (
        CSV_DIR / "task22_04_pair_summary.csv"
    )

    frame_saved = save_csv(
        frame_csv, all_frame_rows
    )

    summary_saved = save_csv(
        summary_csv, summaries
    )

    report = {
        "Task": "22.4",
        "MaxMessagesPerFile": LIMIT,
        "MatchingPairsDiscovered": len(all_pairs),
        "PairsSelected": len(selected),
        "PairsValidated": len(summaries),
        "Errors": errors,
        "PairSummaries": summaries,
        "Limitations": [
            "Only the first 100 messages per file were inspected",
            "Matching filenames do not establish scenario equivalence",
            "Matching message timestamps do not independently prove sensor acquisition synchrony",
            "Entry presence is not sensor payload validation",
            "No detection accuracy or hardware energy measured"
        ]
    }

    json_path = (
        FINDINGS / "task22_04_pair_validation.json"
    )

    json_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    reference_path = (
        REFS / "task22_04_selected_recordings.txt"
    )

    reference_path.write_text(
        "\n".join(
            f"Pair {i}: \n"
            f"SV: {pair['SensorView']}\n"
            f"GT: {pair['GroundTruth']}\n"
            for i, pair in enumerate(selected, 1)
        ),
        encoding="utf-8"
    )

    print("\n=== TASK 22.4 FINAL SUMMARY ===")
    print("Pairs validated:", len(summaries))
    print(
        "Pairs passing message alignment:",
        sum(
            s["ValidationStatus"] == "PASS_MESSAGE_ALIGNMENT"
            for s in summaries
        )
    )
    print("Errors:", len(errors))
    print("Frame CSV saved:", frame_saved)
    print("Summary CSV saved:", summary_saved)
    print("JSON saved:", json_path.is_file())
    print("References saved:", reference_path.is_file())

    print("\n=== TASK 22.4 COMPLETE ===")


if __name__ == "__main__":
    main()
