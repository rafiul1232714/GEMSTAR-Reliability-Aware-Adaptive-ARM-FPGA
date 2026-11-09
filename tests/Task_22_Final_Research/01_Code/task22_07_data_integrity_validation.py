import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_22_Final_Research"
sys.path.insert(0, str(TASK / "01_Code"))

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView, timestamp_ns
)

DATA = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"
GRAPHS = TASK / "03_Graphs"

SOURCE = DATA / "task22_04b_deduplicated_pair_summary.csv"
FRAME_CSV = DATA / "task22_06_frame_metrics.csv"

LIMIT = 100

for folder in (DATA, FINDINGS, GRAPHS):
    folder.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def numeric(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def reflection_audit(path):
    """Audit all radar reflection slots in first 100 messages."""
    counts = Counter()
    frame_details = []

    previous_timestamp = None

    for frame, sv, size in iter_osi_messages(
        path, SensorView, LIMIT
    ):
        ts = timestamp_ns(sv)

        nonmonotonic = (
            previous_timestamp is not None
            and ts <= previous_timestamp
        )
        previous_timestamp = ts

        radar_views = list(sv.radar_sensor_view)
        slots = 0
        tof_positive = 0
        strength_positive = 0
        both_positive = 0
        nonfinite = 0

        for radar in radar_views:
            for reflection in radar.reflection:
                slots += 1
                tof = numeric(reflection.time_of_flight)
                strength = numeric(reflection.signal_strength)

                if tof is None or strength is None:
                    nonfinite += 1
                    continue

                good_tof = tof > 0
                good_strength = strength > 0

                tof_positive += int(good_tof)
                strength_positive += int(good_strength)
                both_positive += int(
                    good_tof and good_strength
                )

        counts["Frames"] += 1
        counts["RadarEntryFrames"] += int(
            len(radar_views) > 0
        )
        counts["RadarReflectionFrames"] += int(
            slots > 0
        )
        counts["PositiveReturnFrames"] += int(
            both_positive > 0
        )
        counts["ReflectionSlots"] += slots
        counts["PositiveTOFSlots"] += tof_positive
        counts["PositiveStrengthSlots"] += strength_positive
        counts["BothPositiveSlots"] += both_positive
        counts["NonfiniteSlots"] += nonfinite
        counts["NonmonotonicFrames"] += int(nonmonotonic)

        frame_details.append({
            "Frame": frame,
            "RadarEntries": len(radar_views),
            "ReflectionSlots": slots,
            "PositiveTOFSlots": tof_positive,
            "PositiveStrengthSlots": strength_positive,
            "BothPositiveSlots": both_positive,
            "NonfiniteSlots": nonfinite,
        })

    return counts, frame_details


print("\n=== TASK 22.7 DATA INTEGRITY VALIDATION ===")

pairs = read_csv(SOURCE)
frame_rows = read_csv(FRAME_CSV)

print("Unique pair records:", len(pairs))
print("Task 22.6 frame rows:", len(frame_rows))

frames_by_pair = defaultdict(list)
for row in frame_rows:
    frames_by_pair[row["PairID"]].append(row)

validation = []
radar_details = []
research_notes = []

for pair in pairs:
    pair_id = pair["PairID"]
    folder = Path(pair["ScenarioFolder"])
    sv_path = folder / pair["SensorViewFilename"]
    rows = frames_by_pair[pair_id]

    print(f"\n=== PAIR {pair_id} ===")
    print("Recording:", sv_path.name)

    if not sv_path.is_file():
        print("ERROR: Source recording missing")
        validation.append({
            "PairID": pair_id,
            "Frames": 0,
            "DuplicateFrameIDs": "",
            "TimestampMismatches": "",
            "NonmonotonicSVTimestamps": "",
            "CameraImageFrames": "",
            "LiDARReflectionFrames": "",
            "RadarEntryFrames": "",
            "RadarReflectionFrames": "",
            "PositiveRadarFrames": "",
            "TotalRadarReflectionSlots": "",
            "PositiveRadarReturnSlots": "",
            "NonfiniteRadarSlots": "",
            "Status": "ERROR_SOURCE_MISSING"
        })
        continue

    frame_ids = [
        row["Frame"] for row in rows
    ]

    duplicate_frames = (
        len(frame_ids) - len(set(frame_ids))
    )

    timestamp_mismatches = sum(
        str(row["TimestampMatch"]).lower()
        not in ("true", "1")
        for row in rows
    )

    timestamps = [
        int(row["SVTimestampNs"])
        for row in sorted(
            rows, key=lambda r: int(r["Frame"])
        )
    ]

    nonmonotonic_sv = sum(
        timestamps[i] <= timestamps[i - 1]
        for i in range(1, len(timestamps))
    )

    camera_frames = sum(
        int(row["CameraImageBytes"]) > 0
        for row in rows
    )

    lidar_frames = sum(
        int(row["LiDARReflectionCount"]) > 0
        for row in rows
    )

    radar_entry_frames = sum(
        int(row["RadarEntries"]) > 0
        for row in rows
    )

    counts, details = reflection_audit(sv_path)

    for detail in details:
        radar_details.append({
            "PairID": pair_id,
            **detail
        })

    structural_pass = (
        len(rows) == counts["Frames"]
        and duplicate_frames == 0
        and timestamp_mismatches == 0
        and nonmonotonic_sv == 0
        and counts["NonmonotonicFrames"] == 0
    )

    complete_sensors = (
        camera_frames == len(rows)
        and lidar_frames == len(rows)
        and counts["PositiveReturnFrames"] == len(rows)
    )

    if not structural_pass:
        status = "FAIL_STRUCTURAL_VALIDATION"
    elif not complete_sensors:
        status = "WARN_INCOMPLETE_SENSOR_DATA"
    elif counts["NonfiniteSlots"] > 0:
        status = "WARN_NONFINITE_RADAR_DATA"
    else:
        status = "PASS_PRELIMINARY_DATA_CHECKS"

    record = {
        "PairID": pair_id,
        "Frames": len(rows),
        "DuplicateFrameIDs": duplicate_frames,
        "TimestampMismatches": timestamp_mismatches,
        "NonmonotonicSVTimestamps": nonmonotonic_sv,
        "CameraImageFrames": camera_frames,
        "LiDARReflectionFrames": lidar_frames,
        "RadarEntryFrames": radar_entry_frames,
        "RadarReflectionFrames": counts["RadarReflectionFrames"],
        "PositiveRadarFrames": counts["PositiveReturnFrames"],
        "TotalRadarReflectionSlots": counts["ReflectionSlots"],
        "PositiveRadarReturnSlots": counts["BothPositiveSlots"],
        "NonfiniteRadarSlots": counts["NonfiniteSlots"],
        "Status": status
    }

    validation.append(record)

    print("Structural integrity:", "PASS" if structural_pass else "FAIL")
    print("Camera image frames:", camera_frames)
    print("LiDAR reflection frames:", lidar_frames)
    print("Radar entry frames:", radar_entry_frames)
    print("Radar reflection frames:", counts["RadarReflectionFrames"])
    print("Radar reflection slots:", counts["ReflectionSlots"])
    print("Slots with positive time_of_flight:",
          counts["PositiveTOFSlots"])
    print("Slots with positive signal_strength:",
          counts["PositiveStrengthSlots"])
    print("Slots with both positive:", counts["BothPositiveSlots"])
    print("Nonfinite reflection slots:", counts["NonfiniteSlots"])
    print("Status:", status)

    if counts["RadarEntryFrames"] > 0 and \
       counts["PositiveReturnFrames"] == 0:
        research_notes.append(
            f"Pair {pair_id}: Radar sensor entries are present "
            f"but no reflections satisfy the two-positive-field "
            f"criterion. Inspect individual fields before "
            f"interpreting these records as valid detections."
        )


validation_csv = DATA / "task22_07_validation_summary.csv"
detail_csv = DATA / "task22_07_radar_reflection_audit.csv"

save_csv(
    validation_csv,
    validation,
    [
        "PairID", "Frames", "DuplicateFrameIDs",
        "TimestampMismatches",
        "NonmonotonicSVTimestamps",
        "CameraImageFrames", "LiDARReflectionFrames",
        "RadarEntryFrames", "RadarReflectionFrames",
        "PositiveRadarFrames", "TotalRadarReflectionSlots",
        "PositiveRadarReturnSlots", "NonfiniteRadarSlots",
        "Status"
    ]
)

save_csv(
    detail_csv,
    radar_details,
    [
        "PairID", "Frame", "RadarEntries",
        "ReflectionSlots", "PositiveTOFSlots",
        "PositiveStrengthSlots", "BothPositiveSlots",
        "NonfiniteSlots"
    ]
)

report = {
    "Task": "22.7",
    "PairsChecked": len(validation),
    "Summary": validation,
    "Findings": research_notes,
    "ValidationScope": (
        "First 100 SensorView frames per recording, "
        "compared with Task 22.6 CSV metrics"
    ),
    "ImportantLimitations": [
        "These are preliminary data-integrity checks",
        "Positive time-of-flight and signal strength are heuristic filters",
        "No image decoding or LiDAR spatial validation",
        "No ground-truth object-association accuracy measured",
        "Recorded-message timing is not CPU/FPGA execution latency",
        "No electrical power or energy measured"
    ]
}

json_path = FINDINGS / "task22_07_validation_findings.json"
json_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

text_path = FINDINGS / "task22_07_research_interpretation.txt"

text_path.write_text(
    "TASK 22.7 - DATA INTEGRITY VALIDATION\n\n"
    + "\n".join(research_notes)
    + "\n\nInterpretation: Preliminary data checks only. "
    + "Do not infer radar detection accuracy or "
    + "hardware energy from these results.\n",
    encoding="utf-8"
)

print("\n=== TASK 22.7 FINAL SUMMARY ===")
print("Pairs checked:", len(validation))
print(
    "Preliminary pass:",
    sum(
        x["Status"] == "PASS_PRELIMINARY_DATA_CHECKS"
        for x in validation
    )
)
print(
    "Sensor-data warnings:",
    sum(
        x["Status"] == "WARN_INCOMPLETE_SENSOR_DATA"
        for x in validation
    )
)
print(
    "Structural failures:",
    sum(
        x["Status"] == "FAIL_STRUCTURAL_VALIDATION"
        for x in validation
    )
)
print("Summary CSV saved:", validation_csv.is_file())
print("Radar audit CSV saved:", detail_csv.is_file())
print("Findings JSON saved:", json_path.is_file())
print("Interpretation saved:", text_path.is_file())
print("\n=== TASK 22.7 COMPLETE ===")
