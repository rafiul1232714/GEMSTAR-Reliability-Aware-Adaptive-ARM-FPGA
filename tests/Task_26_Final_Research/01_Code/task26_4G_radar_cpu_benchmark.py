from pathlib import Path
from collections import defaultdict
import ast
import csv
import hashlib
import math
import statistics
import time
import json

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
T23 = ROOT / "Task_23_Final_Research"
T26 = ROOT / "Task_26_Final_Research"

SOURCE = T23 / "01_Code" / "task23_13C_01_radar_robustness_tests.py"
DATA = T23 / "02_CSV_Data" / "task23_05c1_radar_measurements.csv"

TIMING = T26 / "02_CSV_Data" / "task26_4G_radar_cpu_timing.csv"
SUMMARY = T26 / "02_CSV_Data" / "task26_4G_radar_cpu_summary.csv"
REPORT = T26 / "06_Research_Findings" / "task26_4G_radar_cpu_report.json"

WARMUP = 10
REPEATS = 100

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest().upper()

def percentile(values, p):
    v = sorted(values)
    index = (len(v)-1)*p
    low = math.floor(index)
    high = math.ceil(index)
    return v[low] + (v[high]-v[low])*(index-low)

def load_radar_processor():
    text = SOURCE.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=str(SOURCE))

    functions = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "preprocess_radar_return"
    ]

    constants = [
        n for n in tree.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "C"
    ]

    if len(functions) != 1 or len(constants) != 1:
        raise RuntimeError("Unexpected original Radar source")

    C = ast.literal_eval(constants[0].value)
    if not math.isclose(C, 299792458.0):
        raise RuntimeError("Unexpected speed-of-light constant")

    code = ast.get_source_segment(text, functions[0])
    if not code:
        raise RuntimeError("Original function extraction failed")

    namespace = {"math": math, "C": C}
    exec(compile(code, str(SOURCE), "exec"), namespace)

    return namespace["preprocess_radar_return"]

def main():
    for path in (TIMING, SUMMARY, REPORT):
        if path.exists():
            raise FileExistsError(
                f"Existing output must be preserved: {path}"
            )

    for path in (SOURCE, DATA):
        if not path.is_file():
            raise FileNotFoundError(path)

    processor = load_radar_processor()

    groups = defaultdict(list)
    total_rows = 0
    valid_rows = 0
    invalid_rows = 0
    max_range_difference = 0.0

    with DATA.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {
            "PairID", "Frame", "TimeOfFlightS",
            "SignalStrength", "PositiveReturn", "RangeM"
        }

        if not required.issubset(reader.fieldnames or []):
            raise RuntimeError("Unexpected Radar CSV columns")

        for row in reader:
            total_rows += 1

            tof = float(row["TimeOfFlightS"])
            strength = float(row["SignalStrength"])
            expected_valid = row["PositiveReturn"].strip().lower() == "true"

            accepted = False
            result = None

            try:
                result = processor(tof, strength)
                accepted = result["status"] == "VALID"
            except (ValueError, TypeError):
                pass

            if accepted != expected_valid:
                raise RuntimeError(
                    f"Radar acceptance mismatch at CSV row {total_rows}"
                )

            if not accepted:
                invalid_rows += 1
                continue

            expected_range = float(row["RangeM"])
            actual_range = result["range_m"]
            difference = abs(actual_range - expected_range)

            if not math.isclose(
                actual_range, expected_range,
                rel_tol=1e-8, abs_tol=1e-6
            ):
                raise RuntimeError(
                    f"Radar range mismatch at row {total_rows}: "
                    f"expected={expected_range}, actual={actual_range}"
                )

            max_range_difference = max(
                max_range_difference, difference
            )

            valid_rows += 1
            key = (row["PairID"], int(row["Frame"]))
            groups[key].append((tof, strength))

    if not groups or not valid_rows:
        raise RuntimeError("No valid Radar measurements found")

    timing_rows = []
    summary_rows = []

    for (pair, frame), samples in sorted(groups.items()):

        def run_batch():
            for tof, strength in samples:
                processor(tof, strength)

        for _ in range(WARMUP):
            run_batch()

        durations = []

        for repeat in range(1, REPEATS+1):
            start = time.perf_counter_ns()
            run_batch()
            duration = (time.perf_counter_ns()-start)/1e6
            durations.append(duration)

            timing_rows.append({
                "pair_id": pair,
                "frame": frame,
                "repeat": repeat,
                "returns_processed": len(samples),
                "batch_elapsed_ms": duration,
                "average_ms_per_return": duration/len(samples),
            })

        summary_rows.append({
            "pair_id": pair,
            "frame": frame,
            "returns_processed": len(samples),
            "median_ms": statistics.median(durations),
            "p95_ms": percentile(durations, 0.95),
            "p99_ms": percentile(durations, 0.99),
            "mean_ms": statistics.mean(durations),
            "median_ms_per_return":
                statistics.median(durations)/len(samples),
        })

        print(
            f"PAIR={pair} FRAME={frame} "
            f"RETURNS={len(samples)} "
            f"MEDIAN_BATCH_MS={statistics.median(durations):.6f} "
            f"P99_BATCH_MS={percentile(durations,0.99):.6f}"
        )

    for path, rows in (
        (TIMING, timing_rows),
        (SUMMARY, summary_rows),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(rows[0])
            )
            writer.writeheader()
            writer.writerows(rows)

    report = {
        "task": "26.4G",
        "source_sha256": sha256(SOURCE),
        "data_sha256": sha256(DATA),
        "input_rows": total_rows,
        "valid_returns": valid_rows,
        "invalid_returns": invalid_rows,
        "frame_groups": len(groups),
        "timing_rows": len(timing_rows),
        "maximum_range_difference_m": max_range_difference,
        "original_function_used": True,
        "reference_validation": "PASS",
        "warmup_batches_per_frame": WARMUP,
        "timed_batches_per_frame": REPEATS,
        "csv_parsing_timed": False,
        "invalid_returns_timed": False,
        "radar_lidar_association_timed": False,
        "energy_measured": False,
        "latency_type": "Complete valid-return batch",
        "per_return_metric": "Batch time divided by return count",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print("=== TASK 26.4G RADAR CPU BENCHMARK ===")
    print("INPUT_ROWS:", total_rows)
    print("VALID_RETURNS:", valid_rows)
    print("INVALID_RETURNS:", invalid_rows)
    print("FRAME_GROUPS:", len(groups))
    print("TIMING_ROWS:", len(timing_rows))
    print("REFERENCE_VALIDATION: PASS")
    print("ASSOCIATION_INCLUDED: NO")
    print("ENERGY_MEASURED: NO")
    print("TASK26_4G_RADAR_CPU_BENCHMARK_PASS")
    print("TIMING:", TIMING)
    print("SUMMARY:", SUMMARY)
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
