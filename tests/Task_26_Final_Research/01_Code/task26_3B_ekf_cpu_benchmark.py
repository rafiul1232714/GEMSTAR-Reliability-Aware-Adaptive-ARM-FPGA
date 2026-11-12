from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests"
)

TASK26 = ROOT / "Task_26_Final_Research"

CONFIG = (
    TASK26
    / "03_Configurations"
    / "Task26_2F_CPU_Benchmark_Config.json"
)

HASH_MANIFEST = (
    TASK26
    / "05_Raw_Data_References"
    / "Task26_2F_Code_Input_SHA256.csv"
)

C02_INPUT = (
    ROOT
    / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
    / "C02_V2_EKF_Input_53Frames_V1"
)

OUTPUT_CSV = (
    TASK26
    / "02_CSV_Data"
    / "task26_3B_ekf_cpu_timing.csv"
)

OUTPUT_JSON = (
    TASK26
    / "06_Research_Findings"
    / "task26_3B_ekf_cpu_benchmark_summary.json"
)

WARMUP_RUNS = 20
TIMED_RUNS = 100


def percentile(values, percent):
    values = sorted(values)
    pos = (len(values) - 1) * percent / 100.0
    lower = math.floor(pos)
    upper = math.ceil(pos)

    return (
        values[lower]
        + (values[upper] - values[lower])
        * (pos - lower)
    )


def file_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest().upper()


def main():
    print("=== TASK 26.3B CPU EKF BENCHMARK ===")

    # Never overwrite existing benchmark outputs.
    if OUTPUT_CSV.exists() or OUTPUT_JSON.exists():
        raise FileExistsError(
            "Benchmark output already exists. "
            "Preserving previous measurements."
        )

    # Load frozen benchmark configuration.
    with CONFIG.open("r", encoding="utf-8-sig") as handle:
        config = json.load(handle)

    source = Path(config["SourceScripts"]["FaultReplay"])

    if not source.is_file():
        raise FileNotFoundError(
            f"Task 25 replay source missing: {source}"
        )

    with HASH_MANIFEST.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as handle:
        records = list(csv.DictReader(handle))

    expected_hashes = [
        row["SHA256"].upper()
        for row in records
        if row["Role"] == "FaultReplay"
    ]

    if len(expected_hashes) != 1:
        raise RuntimeError(
            "Expected one frozen FaultReplay SHA256 record"
        )

    actual_hash = file_sha256(source)

    if actual_hash != expected_hashes[0]:
        raise RuntimeError(
            "Task 25 replay script differs from frozen reference"
        )

    print("SOURCE_SHA256_VERIFIED: YES")

    # Import Task 25 without running its command-line main().
    spec = importlib.util.spec_from_file_location(
        "task25_frozen_replay",
        str(source)
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Task 25 module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    # Load precomputed observations OUTSIDE the timed region.
    (
        tracks,
        radar,
        camera,
        reference,
        camera_reference,
        gt_centers,
        input_hashes
    ) = module.load_inputs(C02_INPUT)

    print("SOURCE_INPUTS_LOADED: YES")

    if len(tracks) != 24:
        raise RuntimeError(
            f"Expected 24 Track 2 observations, got {len(tracks)}"
        )

    # Validate that replay matches the frozen Task 24 reference.
    baseline = module.replay(
        tracks, radar, camera, "baseline"
    )

    max_difference = module.validate_baseline(
        baseline,
        reference,
        camera_reference
    )

    scenarios = list(module.SCENARIOS)

    if len(scenarios) != 7:
        raise RuntimeError(
            f"Expected 7 scenarios, got {len(scenarios)}"
        )

    # Check every workload before recording timing results.
    for scenario in scenarios:
        rows = module.replay(
            tracks, radar, camera, scenario
        )

        if len(rows) != 24:
            raise RuntimeError(
                f"Unexpected observation count: {scenario}"
            )

    def execute(workload):
        if workload == "baseline":
            return module.replay(
                tracks, radar, camera, "baseline"
            )

        if workload == "seven_scenarios":
            output = []

            for scenario in scenarios:
                output.extend(
                    module.replay(
                        tracks, radar, camera, scenario
                    )
                )

            return output

        raise ValueError(f"Unknown workload: {workload}")

    measurements = []
    summaries = []

    for workload in ("baseline", "seven_scenarios"):

        # Warm up CPU execution without recording timing.
        for _ in range(WARMUP_RUNS):
            execute(workload)

        durations_ms = []
        observation_count = 0

        for repeat_index in range(TIMED_RUNS):
            start_ns = time.perf_counter_ns()

            result = execute(workload)

            elapsed_ns = time.perf_counter_ns() - start_ns

            if not result:
                raise RuntimeError("Empty benchmark output")

            observation_count = len(result)
            elapsed_ms = elapsed_ns / 1_000_000.0

            durations_ms.append(elapsed_ms)

            measurements.append({
                "workload": workload,
                "repeat": repeat_index + 1,
                "observations": observation_count,
                "elapsed_ms": elapsed_ms,
                "ms_per_observation":
                    elapsed_ms / observation_count
            })

        summary = {
            "workload": workload,
            "observations_per_run": observation_count,
            "warmup_runs": WARMUP_RUNS,
            "timed_runs": TIMED_RUNS,
            "mean_ms": statistics.mean(durations_ms),
            "median_ms": statistics.median(durations_ms),
            "p95_ms": percentile(durations_ms, 95),
            "p99_ms": percentile(durations_ms, 99),
            "min_ms": min(durations_ms),
            "max_ms": max(durations_ms),
            "median_ms_per_observation":
                statistics.median(durations_ms)
                / observation_count
        }

        summaries.append(summary)

    OUTPUT_CSV.parent.mkdir(
        parents=True, exist_ok=True
    )

    OUTPUT_JSON.parent.mkdir(
        parents=True, exist_ok=True
    )

    report = {
        "task": "26.3B",
        "benchmark_type": "isolated_EKF_replay",
        "source_script": str(source),
        "source_sha256": actual_hash,
        "input_directory": str(C02_INPUT),
        "python_version": sys.version,
        "baseline_max_difference_m": max_difference,
        "osi_parsing_timed": False,
        "csv_loading_timed": False,
        "camera_inference_timed": False,
        "file_writing_timed": False,
        "groundtruth_in_timed_execution": False,
        "energy_measured": False,
        "arm_board_measured": False,
        "complete_pipeline_measured": False,
        "results": summaries
    }

    with OUTPUT_CSV.open(
        "x",
        newline="",
        encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(measurements[0].keys())
        )
        writer.writeheader()
        writer.writerows(measurements)

    with OUTPUT_JSON.open(
        "x",
        encoding="utf-8"
    ) as handle:
        json.dump(report, handle, indent=2)

    print("BASELINE_VALIDATION_MAX_DIFF_M:", max_difference)
    print("TRACK_OBSERVATIONS:", len(tracks))
    print("FAULT_SCENARIOS:", len(scenarios))

    for summary in summaries:
        print()
        print("WORKLOAD:", summary["workload"])
        print(
            "OBSERVATIONS:",
            summary["observations_per_run"]
        )
        print(
            "MEDIAN_MS:",
            round(summary["median_ms"], 6)
        )
        print(
            "P95_MS:",
            round(summary["p95_ms"], 6)
        )
        print(
            "P99_MS:",
            round(summary["p99_ms"], 6)
        )
        print(
            "MEDIAN_MS_PER_OBSERVATION:",
            round(
                summary["median_ms_per_observation"],
                6
            )
        )

    print()
    print("CPU_ONLY_ISOLATED_EKF: YES")
    print("END_TO_END_PIPELINE_MEASURED: NO")
    print("ENERGY_MEASURED: NO")
    print("TASK26_3B_EKF_CPU_BENCHMARK_PASS")
    print("CSV:", OUTPUT_CSV)
    print("REPORT:", OUTPUT_JSON)


if __name__ == "__main__":
    main()
