import csv
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_22_Final_Research"

SOURCE = (
    TASK / "02_CSV_Data" /
    "task22_04b_deduplicated_pair_summary.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"
REFS = TASK / "05_Raw_Data_References"

for folder in (CSV_DIR, FINDINGS, REFS):
    folder.mkdir(parents=True, exist_ok=True)


def recording_identifier(filename):
    match = re.match(
        r"^(\d{8}T\d{6}Z)_sv_(.+)\.osi$",
        filename,
        flags=re.IGNORECASE,
    )
    if not match:
        return "", ""

    return match.group(1), match.group(2)


def timestamp_from_filename(stamp):
    if not stamp:
        return ""
    try:
        return datetime.strptime(
            stamp, "%Y%m%dT%H%M%SZ"
        ).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return ""


def scenario_hint(directory):
    text = directory.name.lower()

    if text == "output":
        return "UNSPECIFIED_OUTPUT"

    if "fog" in text:
        return "FOG_FOLDER_HINT"

    if "clear" in text:
        return "CLEAR_FOLDER_HINT"

    if "traffic" in text:
        return "TRAFFIC_FOLDER_HINT"

    return "UNCLASSIFIED"


def nearby_configuration_files(directory):
    # Only inspect files directly in the recording directory.
    # Do not assume they were active when OSI was recorded.
    suffixes = {".ini", ".sumocfg", ".json", ".yaml", ".yml"}

    return sorted(
        str(p) for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in suffixes
    )


def as_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


print("\n=== TASK 22.5 SCENARIO PROVENANCE ===")

if not SOURCE.is_file():
    raise FileNotFoundError(SOURCE)

with SOURCE.open(newline="", encoding="utf-8-sig") as f:
    pairs = list(csv.DictReader(f))

records = []
all_config_refs = []

for row in pairs:
    directory = Path(row["ScenarioFolder"])
    sv = directory / row["SensorViewFilename"]
    gt = directory / row["GroundTruthFilename"]

    stamp, run_identifier = recording_identifier(sv.name)
    hints = scenario_hint(directory)

    configs = (
        nearby_configuration_files(directory)
        if directory.is_dir() else []
    )

    all_config_refs.extend(configs)

    entry = {
        "PairID": row["PairID"],
        "RecordingTimestampUTC": timestamp_from_filename(stamp),
        "RunIdentifier": run_identifier,
        "ScenarioFolder": str(directory),
        "ScenarioHint": hints,
        "MapVerified": False,
        "MapName": "UNKNOWN",
        "WeatherVerified": False,
        "WeatherCondition": "UNKNOWN",
        "TrafficVerified": False,
        "TrafficCondition": "UNKNOWN",
        "RuntimeConfigurationVerified": False,
        "NearbyConfigFileCount": len(configs),
        "SVFileExists": sv.is_file(),
        "GTFileExists": gt.is_file(),
        "PairedFramesChecked": as_int(row["PairedFrames"]),
        "TimestampMatches": as_int(
            row["ExactTimestampMatches"]
        ),
        "CameraEntryFrames": as_int(
            row["CameraEntryFrames"]
        ),
        "LiDAREntryFrames": as_int(
            row["LiDAREntryFrames"]
        ),
        "RadarEntryFrames": as_int(
            row["RadarEntryFrames"]
        ),
        "MessageAlignmentStatus": row["ValidationStatus"],
    }

    records.append(entry)

    print(f"\nPair {entry['PairID']}")
    print("Recording:", sv.name)
    print("Directory:", directory)
    print("Scenario hint:", hints)
    print("Map verified:", False)
    print("Weather verified:", False)
    print("Traffic verified:", False)
    print("Nearby configuration files:", len(configs))
    print(
        "Camera/LiDAR/Radar entry frames:",
        entry["CameraEntryFrames"],
        entry["LiDAREntryFrames"],
        entry["RadarEntryFrames"]
    )

csv_path = (
    CSV_DIR / "task22_05_scenario_provenance.csv"
)

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(records[0].keys())
    )
    writer.writeheader()
    writer.writerows(records)

reference_path = (
    REFS / "task22_05_configuration_candidates.txt"
)

reference_path.write_text(
    "\n".join(sorted(set(all_config_refs)))
    if all_config_refs
    else "No nearby configuration candidates found.\n",
    encoding="utf-8"
)

hint_counts = dict(
    Counter(r["ScenarioHint"] for r in records)
)

audit = {
    "Task": "22.5",
    "UniqueRecordingPairs": len(records),
    "ScenarioHintCounts": hint_counts,
    "VerifiedMapCount": sum(
        bool(r["MapVerified"]) for r in records
    ),
    "VerifiedWeatherCount": sum(
        bool(r["WeatherVerified"]) for r in records
    ),
    "VerifiedTrafficCount": sum(
        bool(r["TrafficVerified"]) for r in records
    ),
    "Records": records,
    "Interpretation": (
        "Folder names are scenario hints, not independently "
        "verified simulator runtime configurations."
    ),
    "NextEvidenceRequired": [
        "Recorded SUMO map or route references",
        "Runtime weather settings",
        "Traffic population and scenario configuration",
        "Configuration snapshots or hashes tied to each recording"
    ],
    "Limitations": [
        "No OSI metadata proves map identity in this step",
        "File timestamps are not proof of runtime settings",
        "Nearby configuration files may have changed later",
        "Only deduplicated Task 22.4 sample pairs included",
        "Sensor entry presence is not accuracy validation",
        "No hardware energy measured"
    ]
}

json_path = (
    FINDINGS / "task22_05_provenance_audit.json"
)

json_path.write_text(
    json.dumps(audit, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 22.5 SUMMARY ===")
print("Unique recording pairs:", len(records))
print("Scenario folder hints:", hint_counts)
print("Verified maps:", audit["VerifiedMapCount"])
print("Verified weather conditions:",
      audit["VerifiedWeatherCount"])
print("Verified traffic conditions:",
      audit["VerifiedTrafficCount"])

print("\n=== TASK 22.5 FILE CHECK ===")
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Configuration references saved:",
      reference_path.is_file())

print("\n=== TASK 22.5 COMPLETE ===")
