from pathlib import Path
from collections import Counter
import ast
import csv
import json
import os

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

BASE = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
)

DATA = BASE / "C02_V2_EKF_Input_53Frames_V1"

CAMERA = BASE / "Camera_NoVisualizer_V2_2122"

TASK26 = TESTS / "Task_26_Final_Research"

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_5E_camera_ekf_readiness.json"
)

IMAGES = {
    0: "clean_camera_01_frame00000.png",
    530: "clean_camera_02_frame00530.png",
    1060: "clean_camera_03_frame01060.png",
    1591: "clean_camera_04_frame01591.png",
    2121: "clean_camera_05_frame02121.png",
}

def rows(path):
    with path.open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        return list(csv.DictReader(stream))

def discover_python_files():
    roots = [
        TESTS / "Task_24_Final_Research",
        TESTS / "Task_25_Final_Research",
    ]

    skip_dirs = {
        "02_CSV_Data", "04_Plots",
        "05_Raw_Data_References", "08_Processed_Data",
        "__pycache__", ".git", "venv", ".venv",
        "yolo_cpu_env"
    }

    found = []

    for root in roots:
        if not root.is_dir():
            continue

        for directory, dirs, files in os.walk(root):
            dirs[:] = sorted(
                d for d in dirs
                if d not in skip_dirs
            )

            for filename in sorted(files):
                if filename.lower().endswith(".py"):
                    found.append(Path(directory) / filename)

    return found

def inspect_source(path):
    try:
        if path.stat().st_size > 2_000_000:
            return None

        source = path.read_text(
            encoding="utf-8-sig", errors="replace"
        )

        tree = ast.parse(source, filename=str(path))

    except (OSError, SyntaxError, UnicodeError):
        return None

    functions = []

    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            functions.append(node.name)

    filename = path.name.lower()

    terms = (
        "ekf", "kalman", "fusion", "association",
        "radar", "camera", "track"
    )

    filename_matches = [
        term for term in terms if term in filename
    ]

    function_matches = [
        f for f in functions
        if any(term in f.lower() for term in terms)
    ]

    if not filename_matches and not function_matches:
        return None

    score = (
        2 * len(filename_matches)
        + len(function_matches)
    )

    return {
        "path": str(path),
        "score": score,
        "filename_matches": filename_matches,
        "relevant_functions": function_matches,
        "all_top_level_functions": functions[:50],
    }

def main():
    if REPORT.exists():
        raise FileExistsError(
            f"Existing report preserved: {REPORT}"
        )

    selected_path = DATA / "selected_frames.csv"
    ekf_path = DATA / (
        "lidar_radar_camera_ekf_track2_v1.csv"
    )

    for path in (selected_path, ekf_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    selected = rows(selected_path)
    ekf_rows = rows(ekf_path)

    selected_by_frame = {
        int(r["frame"]): r for r in selected
    }

    ekf_by_frame = {
        int(r["frame"]): r for r in ekf_rows
    }

    if len(selected_by_frame) != 53:
        raise RuntimeError("Unexpected selected frame count")

    if len(ekf_by_frame) != len(ekf_rows):
        raise RuntimeError("Duplicate EKF frame IDs")

    camera_frames = {
        frame for frame, name in IMAGES.items()
        if (CAMERA / name).is_file()
    }

    overlap = sorted(
        camera_frames
        & set(ekf_by_frame)
        & set(selected_by_frame)
    )

    if overlap != [0, 530]:
        raise RuntimeError(
            f"Unexpected Camera/EKF overlap: {overlap}"
        )

    print("=== TASK 26.5E CAMERA/EKF READINESS ===")
    print("SELECTED_FRAMES:", len(selected_by_frame))
    print("EKF_RECORDS:", len(ekf_rows))
    print("CAMERA_IMAGES:", len(camera_frames))
    print("CAMERA_EKF_OVERLAP:", len(overlap))
    print("OVERLAP_FRAMES:", overlap)

    print("\n=== MATCHED FRAME DETAILS ===")

    matched_rows = []

    for frame in overlap:
        row = ekf_by_frame[frame]

        details = {
            "frame": frame,
            "time_s": row.get("time_s"),
            "radar_status": row.get("radar_status"),
            "camera_status": row.get("camera_status"),
            "ground_truth_validated":
                row.get("ground_truth_validated"),
            "camera_file": IMAGES[frame],
        }

        matched_rows.append(details)

        for key, value in details.items():
            print(f"FRAME_{frame}_{key.upper()}: {value}")

    print("\n=== EKF STATUS DISTRIBUTIONS ===")

    status_counts = {}

    for field in (
        "camera_status",
        "radar_status",
        "ground_truth_validated",
    ):
        count = Counter(
            row.get(field, "") for row in ekf_rows
        )

        status_counts[field] = dict(count)
        print(field.upper() + ":", dict(count))

    print("\n=== EXISTING PYTHON IMPLEMENTATIONS ===")

    source_files = discover_python_files()

    candidates = []

    for path in source_files:
        result = inspect_source(path)
        if result is not None:
            candidates.append(result)

    candidates.sort(
        key=lambda x: (-x["score"], x["path"])
    )

    print("PYTHON_FILES_INSPECTED:", len(source_files))
    print("RELEVANT_SOURCE_CANDIDATES:", len(candidates))

    for candidate in candidates[:15]:
        print("\nSOURCE:", candidate["path"])
        print("SCORE:", candidate["score"])
        print(
            "FUNCTIONS:",
            candidate["relevant_functions"]
        )

    result = {
        "task": "26.5E",
        "selected_frames": len(selected_by_frame),
        "ekf_records": len(ekf_rows),
        "decoded_camera_frames": sorted(camera_frames),
        "camera_ekf_overlap": overlap,
        "matched_frame_details": matched_rows,
        "ekf_status_counts": status_counts,
        "python_files_inspected": len(source_files),
        "relevant_source_candidates": candidates,
        "limitations": [
            "Archived EKF rows are not executed EKF computations.",
            "Camera frame naming does not independently verify image timestamps.",
            "Matched frame IDs do not prove sensor association.",
            "No integrated Camera/EKF latency is measured.",
            "No ARM, FPGA or board-energy measurement is performed."
        ]
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with REPORT.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)

    print("\nINPUT_FILES_MODIFIED: NO")
    print("INTEGRATED_EKF_EXECUTED: NO")
    print("TASK26_5E_CAMERA_EKF_READINESS_PASS")
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
