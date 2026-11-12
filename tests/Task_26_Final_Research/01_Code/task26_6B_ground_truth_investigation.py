from pathlib import Path
from collections import Counter
import os
import csv
import json
import re

PROJECT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
)

TESTS = PROJECT / "tests"

TASK26 = TESTS / "Task_26_Final_Research"

C02 = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
)

C02_DATA = C02 / "C02_V2_EKF_Input_53Frames_V1"

INVENTORY = (
    TASK26 / "02_CSV_Data"
    / "task26_6B_ground_truth_candidate_inventory.csv"
)

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_6B_ground_truth_investigation.json"
)

SKIP_DIRS = {
    ".git", ".venv", "venv", "env",
    "node_modules", "__pycache__",
    "yolo_cpu_env", ".pytest_cache",
    "site-packages", "build", "dist",
}

SOURCE_EXTENSIONS = {
    ".csv", ".json", ".osi", ".txt",
    ".xml", ".xosc", ".mat", ".npy",
    ".npz", ".parquet",
}

CSV_HEADER_LIMIT = 65536

GT_FILENAME = re.compile(
    r"ground.?truth|(?:^|[_\-.])gt(?:[_\-.]|$)"
    r"|truth|reference.?trajectory"
    r"|reference.?track",
    re.IGNORECASE,
)

POSSIBLE_REFERENCE = re.compile(
    r"trajectory|object.?state|validation|"
    r"ego.?pose|target.?pose|tracking.?accuracy",
    re.IGNORECASE,
)

GT_COLUMN = re.compile(
    r"ground.?truth|(^|_)gt(_|$)|true_"
    r"|reference_(x|y|z|position|velocity)"
    r"|truth_(x|y|z|position|velocity)",
    re.IGNORECASE,
)

def csv_header(path):
    try:
        with path.open(
            "r",
            newline="",
            encoding="utf-8-sig",
            errors="replace",
        ) as stream:
            header = stream.readline(CSV_HEADER_LIMIT)

        if not header:
            return []

        return next(csv.reader([header]))

    except (OSError, UnicodeError, csv.Error):
        return []

def main():
    if INVENTORY.exists() or REPORT.exists():
        raise FileExistsError(
            "Task 26.6B results already exist; "
            "preserving previous research outputs."
        )

    if not TESTS.is_dir():
        raise FileNotFoundError(TESTS)

    selected_file = C02_DATA / "selected_frames.csv"

    if not selected_file.is_file():
        raise FileNotFoundError(selected_file)

    with selected_file.open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        selected = list(csv.DictReader(stream))

    selected_frames = {
        int(row["frame"]) for row in selected
    }

    if len(selected) != 53 or len(selected_frames) != 53:
        raise RuntimeError(
            "C02 expected 53 unique selected frames."
        )

    candidates = []
    scanned_files = 0
    osi_files = 0
    gt_osi_files = 0
    strong_candidates = 0
    c02_candidates = 0
    scan_limit = 250000

    for directory, dirs, files in os.walk(TESTS):
        dirs[:] = sorted(
            d for d in dirs
            if d not in SKIP_DIRS
            and not d.startswith(".")
        )

        folder = Path(directory)

        for filename in sorted(files):
            scanned_files += 1

            if scanned_files > scan_limit:
                raise RuntimeError(
                    "Scan exceeded safety file-count limit."
                )

            path = folder / filename
            extension = path.suffix.lower()

            if extension not in SOURCE_EXTENSIONS:
                continue

            try:
                size = path.stat().st_size
            except OSError:
                continue

            if extension == ".osi":
                osi_files += 1

            relative = str(path.relative_to(TESTS))

            filename_gt = bool(
                GT_FILENAME.search(path.stem)
            )

            filename_reference = bool(
                POSSIBLE_REFERENCE.search(path.stem)
            )

            columns = (
                csv_header(path)
                if extension == ".csv"
                else []
            )

            matching_columns = [
                column
                for column in columns
                if GT_COLUMN.search(column)
            ]

            gt_osi = (
                extension == ".osi"
                and filename_gt
            )

            if gt_osi:
                gt_osi_files += 1

            score = 0

            if filename_gt:
                score += 4

            if matching_columns:
                score += 5

            if filename_reference:
                score += 1

            if gt_osi:
                score += 2

            if score == 0:
                continue

            in_c02 = (
                path == C02
                or C02 in path.parents
            )

            if in_c02:
                c02_candidates += 1
                score += 2

            if score >= 4:
                strong_candidates += 1

            if score >= 5:
                classification = "HIGH_PRIORITY"
            elif score >= 2:
                classification = "MEDIUM_PRIORITY"
            else:
                classification = "REVIEW_ONLY"

            candidates.append({
                "priority": classification,
                "score": score,
                "source_path": str(path),
                "relative_path": relative,
                "extension": extension,
                "size_bytes": size,
                "in_C02_scenario": in_c02,
                "filename_gt_indicator": filename_gt,
                "gt_related_columns": (
                    "|".join(matching_columns[:30])
                ),
                "csv_header": (
                    "|".join(columns[:40])
                ),
            })

    candidates.sort(
        key=lambda x: (
            -x["score"],
            not x["in_C02_scenario"],
            x["relative_path"],
        )
    )

    # Focused check of the existing C02 data.
    # These are feature/estimate fields, not assumed GT.
    focus_files = [
        "selected_frames.csv",
        "lidar_temporal_tracks_v1.csv",
        "lidar_radar_camera_ekf_track2_v1.csv",
        "radar_returns.csv",
        "lidar_points.csv",
    ]

    focused_headers = {}

    for filename in focus_files:
        path = C02_DATA / filename

        focused_headers[filename] = (
            csv_header(path)
            if path.is_file()
            else None
        )

    INVENTORY.parent.mkdir(
        parents=True, exist_ok=True
    )
    REPORT.parent.mkdir(
        parents=True, exist_ok=True
    )

    fields = [
        "priority", "score", "source_path",
        "relative_path", "extension",
        "size_bytes", "in_C02_scenario",
        "filename_gt_indicator",
        "gt_related_columns", "csv_header",
    ]

    with INVENTORY.open(
        "x", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fields
        )
        writer.writeheader()
        writer.writerows(candidates)

    report = {
        "task": "26.6B",
        "investigation_type": (
            "Filename, CSV header and metadata audit"
        ),
        "scope": str(TESTS),
        "selected_C02_frames": len(selected_frames),
        "scanned_files": scanned_files,
        "osi_files_under_tests": osi_files,
        "filename_indicated_gt_osi_files": gt_osi_files,
        "candidate_files": len(candidates),
        "strong_candidates": strong_candidates,
        "c02_candidate_files": c02_candidates,
        "focused_C02_headers": focused_headers,
        "top_candidates": candidates[:50],
        "limitations": [
            "A GT-labelled filename is not proof of correct object ground truth.",
            "OSI file contents have not been decoded.",
            "CSV files were inspected by header, not fully interpreted.",
            "Files outside the tests folder were not searched.",
            "Matching timestamps and coordinate systems are not yet established.",
            "No position RMSE, detection recall or tracking accuracy was calculated.",
            "Historical Task 15 to Task 25 data were not modified."
        ],
        "ground_truth_ready_for_accuracy_comparison": False,
    }

    with REPORT.open(
        "x", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, indent=2)

    print("=== TASK 26.6B GROUND-TRUTH INVESTIGATION ===")

    print("SCOPE:", TESTS)
    print("SELECTED_C02_FRAMES:", len(selected_frames))
    print("FILES_SCANNED:", scanned_files)
    print("OSI_FILES_FOUND:", osi_files)
    print("GT_NAMED_OSI_FILES:", gt_osi_files)
    print("GROUND_TRUTH_CANDIDATES:", len(candidates))
    print("STRONG_CANDIDATES:", strong_candidates)
    print("C02_CANDIDATE_FILES:", c02_candidates)

    print("\n=== TOP GROUND-TRUTH CANDIDATES ===")

    for item in candidates[:25]:
        print(
            "PRIORITY=", item["priority"],
            "SCORE=", item["score"]
        )
        print("PATH=", item["source_path"])

        if item["gt_related_columns"]:
            print(
                "GT_COLUMNS=",
                item["gt_related_columns"]
            )

    print("\n=== C02 EXISTING CSV HEADERS ===")

    for filename, columns in focused_headers.items():
        print("FILE:", filename)
        print(
            "COLUMNS:",
            ", ".join(columns)
            if columns else "NOT_FOUND"
        )

    print("\n=== RESEARCH INTERPRETATION ===")

    print("GROUND_TRUTH_MATCH_VERIFIED: NO")
    print("POSITION_RMSE_CALCULATED: NO")
    print("DETECTION_ACCURACY_CALCULATED: NO")
    print("ORIGINAL_SOURCE_FILES_MODIFIED: NO")

    print(
        "TASK26_6B_GROUND_TRUTH_INVENTORY_PASS"
    )

    print("INVENTORY:", INVENTORY)
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
