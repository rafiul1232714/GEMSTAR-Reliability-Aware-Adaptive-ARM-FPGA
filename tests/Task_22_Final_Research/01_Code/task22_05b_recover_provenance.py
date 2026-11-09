import csv
import json
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project")
PROJECT = ROOT / "sensor-health-monitor"
TASK = PROJECT / "tests" / "Task_22_Final_Research"

SOURCE = (
    TASK / "02_CSV_Data" /
    "task22_05_scenario_provenance.csv"
)

SEARCH_ROOTS = [
    PROJECT / "tests" / "Task_15_Final_Research",
    ROOT / "gemstar" / "Config",
    PROJECT / "configs",
]

EXTENSIONS = {
    ".csv", ".json", ".txt", ".ini",
    ".yaml", ".yml", ".sumocfg", ".xml"
}

MAX_FILE_BYTES = 2 * 1024 * 1024

KEYWORDS = [
    "fog",
    "weather",
    "sumo",
    "map",
    "traffic",
    "visibility",
    "mor",
    "configuration",
]

OUTPUT = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

OUTPUT.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

with SOURCE.open(
    newline="", encoding="utf-8-sig"
) as f:
    recordings = list(csv.DictReader(f))

print("\n=== TASK 22.5B PROVENANCE RECOVERY ===")

print("Recordings to investigate:", len(recordings))

for folder in SEARCH_ROOTS:
    print("Search directory:", folder)
    print("Exists:", folder.is_dir())

candidates = []

for folder in SEARCH_ROOTS:
    if not folder.is_dir():
        continue

    for path in folder.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in EXTENSIONS:
            continue

        if path.stat().st_size > MAX_FILE_BYTES:
            continue

        candidates.append(path)

print("Candidate evidence files:", len(candidates))

evidence = []

for recording in recordings:
    run_id = recording["RunIdentifier"]
    timestamp = recording["RecordingTimestampUTC"]

    # The run ID may contain generic tokens like GEMSTAR,
    # so use filename stem and recording timestamp as
    # stronger identifiers.
    file_id = (
        run_id.lower()
        if run_id else ""
    )

    sv_filename = ""
    for token in (
        "806", "794", "466", "542"
    ):
        if token in file_id.split("_"):
            sv_filename = token

    print("\nPair:", recording["PairID"])
    print("Run identifier:", run_id)

    count = 0

    for path in candidates:
        try:
            content = path.read_text(
                encoding="utf-8-sig",
                errors="replace"
            )
        except OSError:
            continue

        lines = content.splitlines()

        for line_number, line in enumerate(lines, 1):
            lower = line.lower()

            exact_run_match = (
                bool(file_id) and
                file_id in lower
            )

            recording_token_match = (
                bool(sv_filename) and
                sv_filename in lower.split("_")
            )

            if not exact_run_match and not recording_token_match:
                continue

            context_start = max(0, line_number - 4)
            context_end = min(
                len(lines), line_number + 3
            )

            excerpt = " | ".join(
                lines[context_start:context_end]
            )[:1000]

            evidence.append({
                "PairID": recording["PairID"],
                "RunIdentifier": run_id,
                "EvidenceFile": str(path),
                "LineNumber": line_number,
                "MatchType": (
                    "RUN_ID_EXACT"
                    if exact_run_match
                    else "TOKEN_CANDIDATE"
                ),
                "EvidenceExcerpt": excerpt,
                "MapWeatherTrafficVerified": False,
            })

            count += 1

    print("Evidence matches found:", count)

csv_path = (
    OUTPUT / "task22_05b_provenance_evidence.csv"
)

columns = [
    "PairID",
    "RunIdentifier",
    "EvidenceFile",
    "LineNumber",
    "MatchType",
    "EvidenceExcerpt",
    "MapWeatherTrafficVerified",
]

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=columns
    )
    writer.writeheader()
    writer.writerows(evidence)

summary = {
    "Task": "22.5B",
    "RecordingsInvestigated": len(recordings),
    "CandidateFilesScanned": len(candidates),
    "EvidenceMatches": len(evidence),
    "VerifiedScenarioAssignments": 0,
    "ImportantNote": (
        "Matches are provenance candidates. "
        "Manual review is required before claiming "
        "a verified runtime map, weather or traffic setting."
    ),
}

json_path = (
    FINDINGS / "task22_05b_provenance_recovery.json"
)

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 22.5B RESULTS ===")
print("Recordings investigated:", len(recordings))
print("Candidate files scanned:", len(candidates))
print("Evidence matches found:", len(evidence))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())

print("\n=== TASK 22.5B COMPLETE ===")
