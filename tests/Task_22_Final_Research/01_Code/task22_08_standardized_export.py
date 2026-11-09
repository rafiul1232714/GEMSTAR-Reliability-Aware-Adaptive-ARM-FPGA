import csv
import json
from collections import Counter
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_22_Final_Research"
)

SOURCE_DIR = TASK / "02_CSV_Data"
OUTPUT_DIR = TASK / "08_Processed_Data"
FINDINGS_DIR = TASK / "06_Research_Findings"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS_DIR.mkdir(parents=True, exist_ok=True)

FRAME_SOURCE = SOURCE_DIR / "task22_06_frame_metrics.csv"
QUALITY_SOURCE = SOURCE_DIR / "task22_07_validation_summary.csv"
PAIR_SOURCE = (
    SOURCE_DIR /
    "task22_04b_deduplicated_pair_summary.csv"
)

def read_rows(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))


def integer(value):
    return int(value) if str(value).strip() else 0


def save_rows(path, rows, columns):
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


print("\n=== TASK 22.8 STANDARDIZED DATA EXPORT ===")

frames = read_rows(FRAME_SOURCE)
quality = read_rows(QUALITY_SOURCE)
pairs = read_rows(PAIR_SOURCE)

quality_by_id = {
    row["PairID"]: row
    for row in quality
}

pairs_by_id = {
    row["PairID"]: row
    for row in pairs
}

if not frames or not quality or not pairs:
    raise ValueError("A required source table is empty")

if len(quality_by_id) != len(quality):
    raise ValueError("Duplicate PairID in validation summary")

if len(pairs_by_id) != len(pairs):
    raise ValueError("Duplicate PairID in pair summary")

columns = [
    "PairID",
    "RecordingID",
    "Frame",
    "TimestampNs",
    "TimestampSeconds",
    "CameraEntries",
    "CameraImageBytes",
    "LiDAREntries",
    "LiDARReflections",
    "RadarEntries",
    "RadarReflectionSlots",
    "PositiveRadarReturns",
    "GTMovingObjects",
    "TimestampMatched",
    "StructuralPass",
    "CameraAvailable",
    "LiDARAvailable",
    "RadarAvailable",
    "StartupFrameExcluded",
    "FusionCandidate",
    "QualityStatus"
]

standardized = []
candidates = []
seen_frames = set()

for source in frames:
    pair_id = source["PairID"]

    if pair_id not in quality_by_id:
        raise ValueError(
            f"Missing validation record for pair {pair_id}"
        )

    if pair_id not in pairs_by_id:
        raise ValueError(
            f"Missing recording source for pair {pair_id}"
        )

    check = quality_by_id[pair_id]
    pair = pairs_by_id[pair_id]

    frame = integer(source["Frame"])

    key = (pair_id, frame)

    if key in seen_frames:
        raise ValueError(f"Duplicate frame key: {key}")

    seen_frames.add(key)

    timestamp_ns = integer(source["SVTimestampNs"])

    camera_entries = integer(source["CameraEntries"])
    camera_bytes = integer(source["CameraImageBytes"])

    lidar_entries = integer(source["LiDAREntries"])
    lidar_reflections = integer(
        source["LiDARReflectionCount"]
    )

    radar_entries = integer(source["RadarEntries"])
    radar_slots = integer(source["RadarReflectionCount"])
    positive_radar = integer(source["PositiveRadarReturns"])

    timestamp_matched = (
        source["TimestampMatch"].strip().lower()
        in ("true", "1")
    )

    structural_pass = (
        check["Status"] != "FAIL_STRUCTURAL_VALIDATION"
        and check["Status"] != "ERROR_SOURCE_MISSING"
        and integer(check["DuplicateFrameIDs"]) == 0
        and integer(check["TimestampMismatches"]) == 0
        and integer(check["NonmonotonicSVTimestamps"]) == 0
    )

    camera_available = (
        camera_entries > 0 and camera_bytes > 0
    )

    lidar_available = (
        lidar_entries > 0 and lidar_reflections > 0
    )

    radar_available = (
        radar_entries > 0 and positive_radar > 0
    )

    startup_excluded = frame == 0

    fusion_candidate = (
        structural_pass
        and timestamp_matched
        and camera_available
        and lidar_available
        and radar_available
        and not startup_excluded
    )

    gt_objects = source["GTMovingObjects"].strip()

    record = {
        "PairID": pair_id,
        "RecordingID": pair["SensorViewFilename"],
        "Frame": frame,
        "TimestampNs": timestamp_ns,
        "TimestampSeconds": timestamp_ns / 1e9,
        "CameraEntries": camera_entries,
        "CameraImageBytes": camera_bytes,
        "LiDAREntries": lidar_entries,
        "LiDARReflections": lidar_reflections,
        "RadarEntries": radar_entries,
        "RadarReflectionSlots": radar_slots,
        "PositiveRadarReturns": positive_radar,
        "GTMovingObjects": (
            integer(gt_objects) if gt_objects else ""
        ),
        "TimestampMatched": int(timestamp_matched),
        "StructuralPass": int(structural_pass),
        "CameraAvailable": int(camera_available),
        "LiDARAvailable": int(lidar_available),
        "RadarAvailable": int(radar_available),
        "StartupFrameExcluded": int(startup_excluded),
        "FusionCandidate": int(fusion_candidate),
        "QualityStatus": check["Status"]
    }

    standardized.append(record)

    if fusion_candidate:
        candidates.append(record)

standardized.sort(
    key=lambda r: (int(r["PairID"]), r["Frame"])
)

candidates.sort(
    key=lambda r: (int(r["PairID"]), r["Frame"])
)

all_path = (
    OUTPUT_DIR / "task22_08_all_frames.csv"
)

candidate_path = (
    OUTPUT_DIR / "task22_08_fusion_ready_candidates.csv"
)

summary_path = (
    OUTPUT_DIR / "task22_08_dataset_summary.csv"
)

save_rows(all_path, standardized, columns)
save_rows(candidate_path, candidates, columns)

summary_rows = []

for pair_id in sorted(pairs_by_id, key=int):

    selected = [
        r for r in standardized if r["PairID"] == pair_id
    ]

    eligible = [
        r for r in selected if r["FusionCandidate"] == 1
    ]

    row = {
        "PairID": pair_id,
        "Recording": pairs_by_id[pair_id][
            "SensorViewFilename"
        ],
        "FramesExported": len(selected),
        "TimestampMatchedFrames": sum(
            r["TimestampMatched"] for r in selected
        ),
        "CameraAvailableFrames": sum(
            r["CameraAvailable"] for r in selected
        ),
        "LiDARAvailableFrames": sum(
            r["LiDARAvailable"] for r in selected
        ),
        "RadarAvailableFrames": sum(
            r["RadarAvailable"] for r in selected
        ),
        "StartupFramesExcluded": sum(
            r["StartupFrameExcluded"] for r in selected
        ),
        "FusionCandidateFrames": len(eligible),
        "QualityStatus": quality_by_id[pair_id]["Status"]
    }

    summary_rows.append(row)

summary_columns = [
    "PairID", "Recording", "FramesExported",
    "TimestampMatchedFrames",
    "CameraAvailableFrames",
    "LiDARAvailableFrames",
    "RadarAvailableFrames",
    "StartupFramesExcluded",
    "FusionCandidateFrames",
    "QualityStatus"
]

save_rows(summary_path, summary_rows, summary_columns)

metadata = {
    "Task": "22.8",
    "DatasetType": "Preliminary per-frame sensor availability",
    "OriginalFrameRows": len(frames),
    "ExportedFrameRows": len(standardized),
    "CandidateFrames": len(candidates),
    "UniqueRecordings": len(summary_rows),
    "SourceFiles": [
        str(FRAME_SOURCE),
        str(QUALITY_SOURCE),
        str(PAIR_SOURCE)
    ],
    "CandidateRules": {
        "StructuralPass": True,
        "TimestampMatched": True,
        "CameraImageBytesPositive": True,
        "LiDARReflectionCountPositive": True,
        "RadarPositiveReturnCountPositive": True,
        "ExcludeFrameZero": True
    },
    "Units": {
        "TimestampNs": "nanoseconds",
        "TimestampSeconds": "seconds",
        "CameraImageBytes": "bytes",
        "LiDARReflections": "count",
        "RadarReflectionSlots": "count",
        "PositiveRadarReturns": "count"
    },
    "Limitations": [
        "CSV contains per-frame metadata, not raw sensor arrays",
        "Camera image bytes are not decoded pixels",
        "LiDAR counts are not calibrated point clouds",
        "Radar positive returns use a heuristic validity rule",
        "Frame zero is excluded conservatively in all recordings",
        "GT object count is not GT association accuracy",
        "FusionCandidate is not proof of geometric fusion readiness",
        "Scenario weather/map/traffic identities remain unverified",
        "No FPGA latency or power measurements"
    ]
}

metadata_path = (
    OUTPUT_DIR / "task22_08_dataset_metadata.json"
)

metadata_path.write_text(
    json.dumps(metadata, indent=2),
    encoding="utf-8"
)

finding_path = (
    FINDINGS_DIR / "task22_08_export_findings.txt"
)

finding_lines = [
    "TASK 22.8 - STANDARDIZED DATASET EXPORT",
    "",
    f"Original inspected frames: {len(frames)}",
    f"Exported frames: {len(standardized)}",
    f"Preliminary fusion candidates: {len(candidates)}",
    "",
    "PER-RECORDING RESULTS",
]

for row in summary_rows:
    finding_lines.append(
        f"Pair {row['PairID']}: "
        f"{row['FusionCandidateFrames']} candidates / "
        f"{row['FramesExported']} inspected frames; "
        f"status={row['QualityStatus']}"
    )

finding_lines.extend([
    "",
    "INTERPRETATION",
    "Candidate eligibility is based on preliminary",
    "sensor data presence and message alignment only.",
    "Further calibration, sensor decoding, GT association",
    "and perception-quality validation are required.",
])

finding_path.write_text(
    "\n".join(finding_lines) + "\n",
    encoding="utf-8"
)

print("\n=== STANDARDIZED DATASET SUMMARY ===")
print("Original frame rows:", len(frames))
print("Exported frame rows:", len(standardized))
print("Preliminary fusion candidates:", len(candidates))

for row in summary_rows:
    print(
        f"Pair {row['PairID']}: "
        f"{row['FusionCandidateFrames']} candidate frames "
        f"/ {row['FramesExported']} total"
    )

print("\n=== TASK 22.8 FILE VERIFICATION ===")
print("All-frame CSV:", all_path.is_file())
print("Candidate CSV:", candidate_path.is_file())
print("Summary CSV:", summary_path.is_file())
print("Metadata JSON:", metadata_path.is_file())
print("Findings TXT:", finding_path.is_file())

print("\n=== TASK 22.8A COMPLETE ===")
