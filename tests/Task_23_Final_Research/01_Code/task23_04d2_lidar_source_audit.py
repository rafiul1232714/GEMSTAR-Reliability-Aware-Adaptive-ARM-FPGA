import csv
import json
import re
from pathlib import Path

GEMSTAR = Path(r"E:\GEMSTAR_Project\gemstar")
TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"
REFERENCES = TASK / "05_Raw_Data_References"

for folder in (CSV_DIR, FINDINGS, REFERENCES):
    folder.mkdir(parents=True, exist_ok=True)

EXTENSIONS = {".cpp", ".h", ".hpp", ".cc", ".cxx"}

# Search the actual GEMSTAR implementation.
# Exclude compiled and generated files.
EXCLUDED = {
    "Binaries",
    "Intermediate",
    "Saved",
    ".git",
    "DerivedDataCache",
    "Output",
    "node_modules",
}

PRIMARY = re.compile(
    r"lidar|laser|raycast|linetrace|"
    r"number_of_rays|field_of_view|time_of_flight",
    re.IGNORECASE
)

GEOMETRY = re.compile(
    r"horizontal|vertical|azimuth|elevation|"
    r"angle|direction|rotation|"
    r"reflection|ray_index|rayindex|"
    r"linspace|fov|trace",
    re.IGNORECASE
)

# Bound the output, but preserve useful context.
MAX_FILE_SIZE = 3_000_000
MAX_MATCHES_PER_FILE = 100
CONTEXT_LINES = 3

print("\n=== TASK 23.4D-2 GEMSTAR SOURCE AUDIT ===")

if not GEMSTAR.is_dir():
    raise RuntimeError(
        f"GEMSTAR source directory missing: {GEMSTAR}"
    )

source_files = []

for path in GEMSTAR.rglob("*"):
    if not path.is_file():
        continue

    if any(part in EXCLUDED for part in path.parts):
        continue

    if path.suffix.lower() not in EXTENSIONS:
        continue

    if path.stat().st_size > MAX_FILE_SIZE:
        continue

    source_files.append(path)

print("C/C++ source files discovered:", len(source_files))

matches = []
file_summary = []
report = []

for path in source_files:
    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()
    except OSError:
        continue

    primary_hits = [
        i for i, line in enumerate(lines)
        if PRIMARY.search(line)
    ]

    if not primary_hits:
        continue

    geometry_hits = [
        i for i, line in enumerate(lines)
        if GEOMETRY.search(line)
    ]

    # Candidate files are ranked by LiDAR-specific
    # references and nearby geometry-related code.
    basename = path.name.lower()

    filename_bonus = (
        20 if "lidar" in basename else 0
    )

    score = (
        len(primary_hits) * 2
        + len(geometry_hits)
        + filename_bonus
    )

    relative_path = str(
        path.relative_to(GEMSTAR)
    )

    file_summary.append({
        "File": relative_path,
        "Score": score,
        "PrimaryMatches": len(primary_hits),
        "GeometryMatches": len(geometry_hits),
    })

    report.append(
        "\n" + "=" * 78
        + f"\nFILE: {relative_path}"
        + f"\nSCORE: {score}"
        + "\n" + "=" * 78
    )

    candidate_lines = sorted(set(
        primary_hits + [
            i for i in geometry_hits
            if any(
                abs(i-j) <= 35
                for j in primary_hits
            )
        ]
    ))

    for index in candidate_lines[:MAX_MATCHES_PER_FILE]:
        start = max(0, index - CONTEXT_LINES)
        end = min(
            len(lines),
            index + CONTEXT_LINES + 1
        )

        matches.append({
            "File": relative_path,
            "Line": index + 1,
            "Text": lines[index].strip()[:300],
            "Kind": (
                "PRIMARY"
                if PRIMARY.search(lines[index])
                else "GEOMETRY_NEAR_LIDAR"
            )
        })

        report.append(
            f"\n--- Match at line {index+1} ---"
        )

        for j in range(start, end):
            report.append(
                f"{j+1:05d}: {lines[j][:250]}"
            )

file_summary.sort(
    key=lambda row: row["Score"],
    reverse=True
)

summary_path = CSV_DIR / (
    "task23_04d2_source_file_ranking.csv"
)

matches_path = CSV_DIR / (
    "task23_04d2_source_matches.csv"
)

report_path = REFERENCES / (
    "task23_04d2_gemstar_source_excerpts.txt"
)

findings_path = FINDINGS / (
    "task23_04d2_source_audit_findings.json"
)

def save_csv(path, rows, fields):
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields
        )
        writer.writeheader()
        writer.writerows(rows)

save_csv(
    summary_path,
    file_summary,
    [
        "File",
        "Score",
        "PrimaryMatches",
        "GeometryMatches"
    ]
)

save_csv(
    matches_path,
    matches,
    ["File", "Line", "Text", "Kind"]
)

report_path.write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4D-2",
        "Purpose": (
            "Locate the actual GEMSTAR LiDAR ray "
            "generation and indexing implementation."
        ),
        "SourceRoot": str(GEMSTAR),
        "SourceFilesScanned": len(source_files),
        "FilesWithMatches": len(file_summary),
        "ExtractedMatchCount": len(matches),
        "TopFiles": file_summary[:15],
        "ScientificStatus": (
            "Source discovery only. Mathematical "
            "beam geometry not yet validated."
        ),
        "RawOSIUnchanged": True,
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TOP GEMSTAR SOURCE FILES ===")

for item in file_summary[:15]:
    print(
        f"Score={item['Score']:4d} | "
        f"Matches={item['PrimaryMatches']:3d} | "
        f"{item['File']}"
    )

print("\n=== SOURCE AUDIT SUMMARY ===")
print("Files scanned:", len(source_files))
print("Files with LiDAR-related matches:", len(file_summary))
print("Source matches extracted:", len(matches))

print("\n=== TASK 23.4D-2 FINAL VERIFICATION ===")
print("File ranking CSV:", summary_path.is_file())
print("Source matches CSV:", matches_path.is_file())
print("Source excerpts TXT:", report_path.is_file())
print("Findings JSON:", findings_path.is_file())

print("\n=== TASK 23.4D-2 COMPLETE ===")
