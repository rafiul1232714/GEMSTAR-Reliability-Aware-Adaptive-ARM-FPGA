import csv
import json
from pathlib import Path
from collections import defaultdict

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_22_Final_Research"
)

SOURCE = (
    TASK / "02_CSV_Data" /
    "task22_05b_provenance_evidence.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

KEYWORDS = {
    "Map": [
        "sumo", "map", ".net.xml",
        ".sumocfg", "roadnetwork"
    ],
    "Weather": [
        "fog", "mor", "visibility",
        "weather", "precipitation"
    ],
    "Traffic": [
        "traffic", "vehicle", "route",
        "density", "flow"
    ],
    "Configuration": [
        ".ini", "configuration",
        "config_hash", "sha256"
    ]
}

with SOURCE.open(
    newline="", encoding="utf-8-sig"
) as f:
    rows = list(csv.DictReader(f))

groups = defaultdict(list)

for row in rows:
    groups[row["PairID"]].append(row)

results = []

print("\n=== TASK 22.5C EVIDENCE REVIEW ===")

for pair_id in sorted(groups, key=int):
    records = groups[pair_id]

    print(f"\n=== PAIR {pair_id} ===")
    print("Total matched references:", len(records))

    by_file = defaultdict(list)

    for record in records:
        by_file[record["EvidenceFile"]].append(record)

    print("Distinct evidence files:", len(by_file))

    for file_path, matches in sorted(by_file.items()):

        print("\nSource:", file_path)
        print("References:", len(matches))

        # Inspect at most 2 excerpts per source file
        # to keep terminal output manageable.
        for match in matches[:2]:
            excerpt = match["EvidenceExcerpt"]
            lower = excerpt.lower()

            categories = [
                category
                for category, words in KEYWORDS.items()
                if any(word in lower for word in words)
            ]

            result = {
                "PairID": pair_id,
                "EvidenceFile": file_path,
                "LineNumber": match["LineNumber"],
                "MatchType": match["MatchType"],
                "CandidateCategories": ";".join(categories),
                "Excerpt": excerpt[:500],
                "RuntimeConditionVerified": False
            }

            results.append(result)

            print("Line:", match["LineNumber"])
            print("Possible categories:", categories)
            print("Excerpt:", excerpt[:500])

output_csv = (
    CSV_DIR / "task22_05c_evidence_review.csv"
)

columns = [
    "PairID",
    "EvidenceFile",
    "LineNumber",
    "MatchType",
    "CandidateCategories",
    "Excerpt",
    "RuntimeConditionVerified"
]

with output_csv.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=columns
    )
    writer.writeheader()
    writer.writerows(results)

summary = {
    "Task": "22.5C",
    "TotalOriginalReferences": len(rows),
    "PairsWithReferences": len(groups),
    "ReviewedExcerpts": len(results),
    "VerifiedRuntimeConditions": 0,
    "Interpretation": (
        "Keyword categories are evidence hints only. "
        "A runtime configuration tied to each recording "
        "is required before verification."
    )
}

json_path = (
    FINDINGS / "task22_05c_evidence_review.json"
)

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 22.5C SUMMARY ===")
print("Original evidence matches:", len(rows))
print("Reviewed excerpts:", len(results))
print("Pairs with evidence:", len(groups))
print("Verified runtime conditions:", 0)
print("CSV saved:", output_csv.is_file())
print("JSON saved:", json_path.is_file())

print("\n=== TASK 22.5C COMPLETE ===")
