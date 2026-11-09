import csv
import json
import hashlib
from pathlib import Path
from collections import defaultdict

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_22_Final_Research"
)

SOURCE = TASK / "02_CSV_Data" / "task22_04_pair_summary.csv"
OUT = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

with SOURCE.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

groups = defaultdict(list)

for row in rows:
    key = (
        row["SensorViewFilename"].lower(),
        row["GroundTruthFilename"].lower()
    )
    groups[key].append(row)

suspected = [
    group for group in groups.values()
    if len(group) > 1
]

print("\n=== TASK 22.4B DUPLICATE AUDIT ===")
print("Previously tested pairs:", len(rows))
print("Unique filename-pair identities:", len(groups))
print("Repeated filename-pair groups:", len(suspected))

audits = []
confirmed_duplicate_pair_ids = set()

for group in suspected:
    print("\n=== REPEATED RECORDING GROUP ===")

    fingerprints = []

    for row in group:
        directory = Path(row["ScenarioFolder"])
        sv = directory / row["SensorViewFilename"]
        gt = directory / row["GroundTruthFilename"]

        item = {
            "PairID": row["PairID"],
            "ScenarioFolder": str(directory),
            "SensorViewFilename": sv.name,
            "GroundTruthFilename": gt.name,
            "SensorViewExists": sv.is_file(),
            "GroundTruthExists": gt.is_file(),
            "SensorViewSHA256": "",
            "GroundTruthSHA256": ""
        }

        if sv.is_file() and gt.is_file():
            item["SensorViewSHA256"] = sha256(sv)
            item["GroundTruthSHA256"] = sha256(gt)

            fingerprints.append((
                item["SensorViewSHA256"],
                item["GroundTruthSHA256"]
            ))

        audits.append(item)

        print("Pair:", item["PairID"])
        print("Folder:", directory)
        print("SV exists:", item["SensorViewExists"])
        print("GT exists:", item["GroundTruthExists"])
        print("SV SHA256:", item["SensorViewSHA256"])
        print("GT SHA256:", item["GroundTruthSHA256"])

    all_identical = (
        len(fingerprints) == len(group)
        and len(set(fingerprints)) == 1
    )

    print("Identical SV+GT content:", all_identical)

    if all_identical:
        # Keep one representative of identical content.
        for row in group[1:]:
            confirmed_duplicate_pair_ids.add(row["PairID"])

cleaned = [
    row for row in rows
    if row["PairID"] not in confirmed_duplicate_pair_ids
]

clean_path = OUT / "task22_04b_deduplicated_pair_summary.csv"

with clean_path.open("w", newline="", encoding="utf-8") as f:
    if rows:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(cleaned)

audit_path = FINDINGS / "task22_04b_duplicate_audit.json"

audit_path.write_text(
    json.dumps({
        "Task": "22.4B",
        "PreviouslyTestedPairs": len(rows),
        "UniqueFilenamePairIdentities": len(groups),
        "SuspectedRepeatedGroups": len(suspected),
        "ConfirmedDuplicateEntriesExcluded": len(
            confirmed_duplicate_pair_ids
        ),
        "RetainedEntries": len(cleaned),
        "AuditedRecords": audits,
        "Limitations": [
            "SHA256 was computed only for repeated filename pairs",
            "Distinct filenames do not guarantee distinct content",
            "Distinct recordings do not establish distinct maps",
            "No full-dataset metadata verification performed"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 22.4B RESULTS ===")
print("Original selected entries:", len(rows))
print("Confirmed duplicate entries excluded:",
      len(confirmed_duplicate_pair_ids))
print("Retained entries:", len(cleaned))
print("Deduplicated CSV saved:", clean_path.is_file())
print("Audit JSON saved:", audit_path.is_file())
print("\n=== TASK 22.4B COMPLETE ===")
