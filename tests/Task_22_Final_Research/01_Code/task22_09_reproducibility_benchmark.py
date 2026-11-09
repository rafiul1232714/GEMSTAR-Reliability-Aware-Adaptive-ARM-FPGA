import csv
import json
import hashlib
import statistics
import time
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_22_Final_Research"

DATA = TASK / "08_Processed_Data"
BENCH = TASK / "09_Benchmark_Results"
GRAPHS = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

for folder in (BENCH, GRAPHS, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

SOURCE = DATA / "task22_08_all_frames.csv"
CANDIDATES = DATA / "task22_08_fusion_ready_candidates.csv"

TRIALS = 5
REPEATS = 1000
REPRO_RUNS = 3

FIELDS = [
    "StructuralPass",
    "TimestampMatched",
    "CameraAvailable",
    "LiDARAvailable",
    "RadarAvailable",
    "StartupFrameExcluded"
]


def load_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def candidate_key(row):
    return (int(row["PairID"]), int(row["Frame"]))


def python_filter(records):
    result = []

    for row in records:
        valid = (
            row[0] == 1
            and row[1] == 1
            and row[2] == 1
            and row[3] == 1
            and row[4] == 1
            and row[5] == 0
        )

        result.append(valid)

    return result


def numpy_filter(matrix):
    return (
        (matrix[:, 0] == 1)
        & (matrix[:, 1] == 1)
        & (matrix[:, 2] == 1)
        & (matrix[:, 3] == 1)
        & (matrix[:, 4] == 1)
        & (matrix[:, 5] == 0)
    )


def digest_keys(keys):
    normalized = sorted(keys)

    content = "\n".join(
        f"{pair},{frame}"
        for pair, frame in normalized
    )

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


print("\n=== TASK 22.9 REPRODUCIBILITY BENCHMARK ===")

if not SOURCE.is_file():
    raise FileNotFoundError(SOURCE)

if not CANDIDATES.is_file():
    raise FileNotFoundError(CANDIDATES)

rows = load_csv(SOURCE)
expected_rows = load_csv(CANDIDATES)

records = [
    tuple(int(row[field]) for field in FIELDS)
    for row in rows
]

matrix = np.asarray(records, dtype=np.int64)

expected_keys = sorted(
    candidate_key(row) for row in expected_rows
)

assert len(rows) == 400, "Unexpected input frame count"
assert len(expected_keys) == 297, "Unexpected candidate count"

print("Input frames:", len(rows))
print("Expected candidate frames:", len(expected_keys))
print("Python version:", platform.python_version())
print("NumPy version:", np.__version__)

# ------------------------------------------------
# 1. Independent correctness check
# ------------------------------------------------

py_result = python_filter(records)
np_result = numpy_filter(matrix)

assert py_result == np_result.tolist(), (
    "Python and NumPy eligibility decisions differ"
)

actual_keys = sorted(
    candidate_key(row)
    for row, eligible in zip(rows, py_result)
    if eligible
)

assert actual_keys == expected_keys, (
    "Calculated candidates do not match Task 22.8"
)

print("\n=== CORRECTNESS VALIDATION ===")
print("Python candidates:", sum(py_result))
print("NumPy candidates:", int(np.sum(np_result)))
print("Candidate identities match:", True)

# ------------------------------------------------
# 2. Reproducibility: independent CSV reads
# ------------------------------------------------

repro_rows = []

for run in range(1, REPRO_RUNS + 1):

    fresh_rows = load_csv(SOURCE)

    fresh_records = [
        tuple(int(row[field]) for field in FIELDS)
        for row in fresh_rows
    ]

    flags = python_filter(fresh_records)

    keys = [
        candidate_key(row)
        for row, eligible in zip(fresh_rows, flags)
        if eligible
    ]

    same = sorted(keys) == expected_keys

    repro_rows.append({
        "Run": run,
        "InputFrames": len(fresh_rows),
        "Candidates": len(keys),
        "CandidateSHA256": digest_keys(keys),
        "MatchesExpected": same
    })

    print(
        f"Run {run}: "
        f"{len(keys)} candidates, "
        f"identical={same}"
    )

assert all(
    record["MatchesExpected"] for record in repro_rows
), "Reproducibility check failed"

assert len({
    record["CandidateSHA256"] for record in repro_rows
}) == 1, "Reproducibility hashes differ"

# ------------------------------------------------
# 3. Timing benchmark
# ------------------------------------------------

# Warm up both functions before measurement.
for _ in range(100):
    python_filter(records)
    numpy_filter(matrix)

trial_rows = []

methods = [
    ("Python_loop", lambda: python_filter(records)),
    ("NumPy_vectorized", lambda: numpy_filter(matrix))
]

for trial in range(1, TRIALS + 1):
    # Alternate measurement order to reduce order bias.
    selected = methods if trial % 2 else methods[::-1]

    for name, function in selected:

        start = time.perf_counter()

        for _ in range(REPEATS):
            function()

        elapsed_ms = (
            (time.perf_counter() - start)
            * 1000.0 / REPEATS
        )

        trial_rows.append({
            "Trial": trial,
            "Method": name,
            "InputFrames": len(rows),
            "RepeatedExecutions": REPEATS,
            "TimePerPassMs": elapsed_ms
        })

        print(
            f"Trial {trial} | {name}: "
            f"{elapsed_ms:.6f} ms/pass"
        )

summary_rows = []

for name, _ in methods:
    values = [
        row["TimePerPassMs"]
        for row in trial_rows
        if row["Method"] == name
    ]

    summary_rows.append({
        "Method": name,
        "InputFrames": len(rows),
        "MedianTimeMs": statistics.median(values),
        "MinTimeMs": min(values),
        "MaxTimeMs": max(values),
        "Trials": TRIALS,
        "ExecutionsPerTrial": REPEATS
    })

# ------------------------------------------------
# 4. Save research tables
# ------------------------------------------------

repro_path = BENCH / "task22_09_reproducibility.csv"
trials_path = BENCH / "task22_09_benchmark_trials.csv"
summary_path = BENCH / "task22_09_benchmark_summary.csv"

save_csv(
    repro_path, repro_rows,
    [
        "Run", "InputFrames", "Candidates",
        "CandidateSHA256", "MatchesExpected"
    ]
)

save_csv(
    trials_path, trial_rows,
    [
        "Trial", "Method", "InputFrames",
        "RepeatedExecutions", "TimePerPassMs"
    ]
)

save_csv(
    summary_path, summary_rows,
    [
        "Method", "InputFrames", "MedianTimeMs",
        "MinTimeMs", "MaxTimeMs",
        "Trials", "ExecutionsPerTrial"
    ]
)

# ------------------------------------------------
# 5. Generate research plots
# ------------------------------------------------

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(9, 5))

names = [r["Method"] for r in summary_rows]
times = [r["MedianTimeMs"] for r in summary_rows]

ax.bar(names, times)
ax.set_ylabel("Median execution time (ms/pass)")
ax.set_title("Task 22.9 - CPU Eligibility Benchmark")
ax.grid(axis="y", alpha=0.3)

fig.tight_layout()

graph1 = (
    GRAPHS / "task22_09_cpu_benchmark.png"
)

fig.savefig(graph1, dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 5))

for name, _ in methods:
    records_for_method = [
        r for r in trial_rows
        if r["Method"] == name
    ]

    ax.plot(
        [r["Trial"] for r in records_for_method],
        [r["TimePerPassMs"] for r in records_for_method],
        marker="o",
        label=name
    )

ax.set_xlabel("Benchmark trial")
ax.set_ylabel("Execution time (ms/pass)")
ax.set_title("Task 22.9 - Benchmark Repeatability")
ax.legend()
ax.grid(alpha=0.3)

fig.tight_layout()

graph2 = (
    GRAPHS / "task22_09_benchmark_trials.png"
)

fig.savefig(graph2, dpi=200)
plt.close(fig)

# ------------------------------------------------
# 6. Save research interpretation
# ------------------------------------------------

report = {
    "Task": "22.9",
    "PythonVersion": platform.python_version(),
    "NumPyVersion": np.__version__,
    "InputFrames": len(rows),
    "ExpectedCandidates": len(expected_keys),
    "ReproducibilityRuns": REPRO_RUNS,
    "ReproducibilityPassed": True,
    "PythonNumPyCorrectnessPassed": True,
    "Trials": TRIALS,
    "RepetitionsPerTrial": REPEATS,
    "Benchmarks": summary_rows,
    "Scope": (
        "Eligibility-filter computation using "
        "preloaded 400-frame tabular data"
    ),
    "Limitations": [
        "Measured on host CPU, not target ARM processor",
        "No FPGA implementation tested",
        "Input parsing and disk I/O excluded from timing",
        "Only 400 frames analyzed",
        "Wall-clock timing is not electrical energy",
        "No power measurement",
        "Software eligibility is not perception accuracy",
        "Results are not fusion-kernel benchmarks"
    ]
}

json_path = (
    FINDINGS / "task22_09_benchmark_findings.json"
)

json_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

environment_path = (
    BENCH / "task22_09_environment.txt"
)

environment_path.write_text(
    f"Python: {sys.version}\n"
    f"NumPy: {np.__version__}\n"
    f"Platform: {platform.platform()}\n"
    f"Processor: {platform.processor()}\n"
    f"Input frames: {len(rows)}\n"
    f"Trials: {TRIALS}\n"
    f"Repetitions per trial: {REPEATS}\n"
    f"Input loading excluded from timing: yes\n"
    f"Hardware power measured: no\n",
    encoding="utf-8"
)

print("\n=== TASK 22.9 BENCHMARK SUMMARY ===")

for row in summary_rows:
    print(
        f"{row['Method']}: "
        f"median={row['MedianTimeMs']:.6f} ms, "
        f"min={row['MinTimeMs']:.6f} ms, "
        f"max={row['MaxTimeMs']:.6f} ms"
    )

print("\n=== TASK 22.9 FINAL VERIFICATION ===")

print("Reproducibility passed:", True)
print("Python/NumPy correctness passed:", True)
print("Reproducibility CSV:", repro_path.is_file())
print("Benchmark trials CSV:", trials_path.is_file())
print("Benchmark summary CSV:", summary_path.is_file())
print("Benchmark graph 1:", graph1.is_file())
print("Benchmark graph 2:", graph2.is_file())
print("Findings JSON:", json_path.is_file())
print("Environment TXT:", environment_path.is_file())

print("\n=== TASK 22.9 COMPLETE ===")
