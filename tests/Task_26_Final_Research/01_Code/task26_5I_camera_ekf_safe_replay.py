from pathlib import Path
import ast
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

BASE = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
)

ORIGINAL_DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

ORIGINAL_SCRIPT = BASE / "C02_V2_Track2_Camera_EKF_V1.py"

TASK26 = TESTS / "Task_26_Final_Research"

SANDBOX = (
    TASK26 / "03_Configurations"
    / "Task26_5I_EKF_Sandbox"
)

SANDBOX_DATA = SANDBOX / "Input_Output"

SANDBOX_SCRIPT = (
    SANDBOX / "camera_ekf_sandbox_replay.py"
)

OUTPUT_NAME = "lidar_radar_camera_ekf_track2_v1.csv"

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_5I_camera_ekf_safe_replay_report.json"
)

INPUT_NAMES = [
    "lidar_temporal_tracks_v1.csv",
    "radar_track_matches_v1.csv",
    "camera_bearing_track2_frame530_v1.csv",
    "lidar_radar_ekf_track2_v1.csv",
]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(
            lambda: stream.read(1048576), b""
        ):
            h.update(block)
    return h.hexdigest()

def read_csv(path):
    with path.open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        return list(csv.DictReader(stream))

def compare_values(original, replay):
    if original == replay:
        return True, 0.0

    try:
        a = float(original)
        b = float(replay)
    except (ValueError, TypeError):
        return False, None

    if math.isnan(a) and math.isnan(b):
        return True, 0.0

    if not (math.isfinite(a) and math.isfinite(b)):
        return a == b, None

    difference = abs(a - b)

    return math.isclose(
        a, b, rel_tol=1e-10, abs_tol=1e-9
    ), difference

def main():
    print("=== TASK 26.5I SAFE EKF REPLAY ===")

    if REPORT.exists():
        raise FileExistsError(
            f"Existing report preserved: {REPORT}"
        )

    if SANDBOX.exists():
        raise FileExistsError(
            f"Existing sandbox preserved: {SANDBOX}"
        )

    originals = [
        ORIGINAL_SCRIPT,
        ORIGINAL_DIR / OUTPUT_NAME,
    ] + [
        ORIGINAL_DIR / name
        for name in INPUT_NAMES
    ]

    for path in originals:
        if not path.is_file():
            raise FileNotFoundError(path)

    hashes_before = {
        str(path): sha256(path)
        for path in originals
    }

    source = ORIGINAL_SCRIPT.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(
        source, filename=str(ORIGINAL_SCRIPT)
    )

    # Confirm original input/output directory assignment.
    dir_assignments = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "DIR"
            for target in node.targets
        )
    ]

    if len(dir_assignments) != 1:
        raise RuntimeError(
            "Unexpected DIR assignment structure"
        )

    # Verify the original script has only the expected
    # direct file-opening calls. No historical script
    # is imported or executed.
    open_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "open"
            ):
                open_calls.append(node)

    if len(open_calls) != 2:
        raise RuntimeError(
            "Unexpected source file-opening pattern"
        )

    write_calls = []

    for node in open_calls:
        modes = [
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant)
            and isinstance(arg.value, str)
        ]

        if "x" in modes:
            write_calls.append(node)

    if len(write_calls) != 1:
        raise RuntimeError(
            "Unexpected output-writing pattern"
        )

    expected_assignment = (
        'DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"'
    )

    pattern = (
        r'(?m)^DIR\s*=\s*BASE\s*/\s*'
        r'"C02_V2_EKF_Input_53Frames_V1"\s*$'
    )

    replacement = (
        "DIR = Path("
        + repr(str(SANDBOX_DATA))
        + ")"
    )

    patched_source, replacements = re.subn(
        pattern,
        lambda _: replacement,
        source
    )

    if replacements != 1:
        raise RuntimeError(
            "Cannot safely redirect original EKF output"
        )

    # Prepare isolated copies. Never modify Task 24.
    SANDBOX_DATA.mkdir(
        parents=True, exist_ok=False
    )

    for name in INPUT_NAMES:
        shutil.copy2(
            ORIGINAL_DIR / name,
            SANDBOX_DATA / name
        )

    SANDBOX_SCRIPT.write_text(
        patched_source,
        encoding="utf-8"
    )

    sandbox_input_hashes = {
        name: sha256(SANDBOX_DATA / name)
        for name in INPUT_NAMES
    }

    for name in INPUT_NAMES:
        if (
            sandbox_input_hashes[name]
            != hashes_before[str(ORIGINAL_DIR / name)]
        ):
            raise RuntimeError(
                f"Sandbox input changed: {name}"
            )

    print("SANDBOX_CREATED: YES")
    print("INPUT_COPIES_VERIFIED: YES")
    print("ORIGINAL_DIR_REDIRECTED: YES")

    # Run original calculations from the redirected copy.
    # subprocess time is NOT recorded as CPU EKF latency.
    result = subprocess.run(
        [sys.executable, str(SANDBOX_SCRIPT)],
        cwd=str(SANDBOX),
        capture_output=True,
        text=True,
        timeout=120
    )

    print("=== ORIGINAL EKF REPLAY OUTPUT ===")
    print(result.stdout)

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            f"Sandbox EKF exited with {result.returncode}"
        )

    replay_path = SANDBOX_DATA / OUTPUT_NAME
    archived_path = ORIGINAL_DIR / OUTPUT_NAME

    if not replay_path.is_file():
        raise RuntimeError(
            "Sandbox EKF produced no output CSV"
        )

    archived = read_csv(archived_path)
    replayed = read_csv(replay_path)

    if len(archived) != 24 or len(replayed) != 24:
        raise RuntimeError(
            "Expected exactly 24 EKF records"
        )

    if not archived:
        raise RuntimeError("Empty archived EKF CSV")

    if list(archived[0]) != list(replayed[0]):
        raise RuntimeError(
            "Archived and replay CSV columns differ"
        )

    mismatches = []
    max_numeric_difference = 0.0

    for index, (old, new) in enumerate(
        zip(archived, replayed)
    ):
        if old["frame"] != new["frame"]:
            raise RuntimeError(
                f"Frame order mismatch at row {index}"
            )

        for field in old:
            equal, difference = compare_values(
                old[field], new[field]
            )

            if difference is not None:
                max_numeric_difference = max(
                    max_numeric_difference, difference
                )

            if not equal:
                mismatches.append({
                    "row": index,
                    "frame": old["frame"],
                    "field": field,
                    "archived": old[field],
                    "replayed": new[field]
                })

    hashes_after = {
        str(path): sha256(path)
        for path in originals
    }

    originals_unchanged = (
        hashes_before == hashes_after
    )

    sandbox_inputs_unchanged = all(
        sha256(SANDBOX_DATA / name)
        == sandbox_input_hashes[name]
        for name in INPUT_NAMES
    )

    print("=== NUMERICAL VERIFICATION ===")
    print("ARCHIVED_ROWS:", len(archived))
    print("REPLAY_ROWS:", len(replayed))
    print("MISMATCH_COUNT:", len(mismatches))
    print(
        "MAX_NUMERIC_DIFFERENCE:",
        f"{max_numeric_difference:.12g}"
    )

    print(
        "ORIGINAL_SOURCE_AND_DATA_UNCHANGED:",
        originals_unchanged
    )

    print(
        "SANDBOX_INPUTS_UNCHANGED:",
        sandbox_inputs_unchanged
    )

    print(
        "CAMERA_UPDATE_POLICY:",
        "ORIGINAL_EXPERIMENTAL_NIS_GATE"
    )

    print("GROUND_TRUTH_VALIDATED: NO")
    print("INTEGRATED_CPU_LATENCY_MEASURED: NO")
    print("ENERGY_MEASURED: NO")

    report = {
        "task": "26.5I",
        "replay_type": (
            "Sandbox reproduction of the original "
            "Task 24 Camera-assisted EKF"
        ),
        "original_source": str(ORIGINAL_SCRIPT),
        "sandbox_source": str(SANDBOX_SCRIPT),
        "sandbox_output": str(replay_path),
        "archived_rows": len(archived),
        "replay_rows": len(replayed),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:30],
        "max_numeric_difference": (
            max_numeric_difference
        ),
        "original_files_unchanged": (
            originals_unchanged
        ),
        "sandbox_inputs_unchanged": (
            sandbox_inputs_unchanged
        ),
        "source_hashes_before": hashes_before,
        "source_hashes_after": hashes_after,
        "camera_update_policy": (
            "Original experimental NIS gate, "
            "without authorization-field enforcement"
        ),
        "ground_truth_validated": False,
        "integrated_cpu_latency_measured": False,
        "energy_measured": False
    }

    REPORT.parent.mkdir(
        parents=True, exist_ok=True
    )

    with REPORT.open(
        "x", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, indent=2)

    if (
        mismatches
        or not originals_unchanged
        or not sandbox_inputs_unchanged
    ):
        raise RuntimeError(
            "EKF verification failed. Review report."
        )

    print("TASK26_5I_SAFE_EKF_REPLAY_PASS")
    print("REPORT:", REPORT)
    print("SANDBOX_OUTPUT:", replay_path)

if __name__ == "__main__":
    main()
