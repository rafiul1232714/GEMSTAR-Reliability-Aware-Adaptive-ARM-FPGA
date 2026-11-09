import csv
import hashlib
import platform
import sys
import time
import statistics
from pathlib import Path

import numpy as np

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_21_Final_Research"

SOURCE = (
    ROOT / "tests" / "Task_20_Final_Research"
    / "02_CSV_Data" / "task20_49_50m_radar_returns.csv"
)

BENCH = TASK / "05_Benchmark_Results"
FINDINGS = TASK / "06_Research_Findings"

BENCH.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

NFRAMES = 99
BATCH = 100
TRIALS = 5

print("\n=== TASK 21.8 PYTHON / MATLAB BENCHMARK ===")

# Read the same original CSV that was imported into MATLAB.
frames, ranges, signals = [], [], []

with SOURCE.open(newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        frames.append(float(row["Frame"]))
        ranges.append(float(row["RangeM"]))
        signals.append(float(row["SignalStrength"]))

frames = np.asarray(frames, dtype=np.float64)
ranges = np.asarray(ranges, dtype=np.float64)
signals = np.asarray(signals, dtype=np.float64)

print("Input rows:", len(frames))
print("Python:", sys.version.split()[0])
print("NumPy:", np.__version__)
print("Computer:", platform.node())
print("Processor:", platform.processor())

def vectorized(repeats):
    for _ in range(repeats):
        valid = (
            np.isfinite(frames)
            & np.isfinite(ranges)
            & np.isfinite(signals)
            & (frames >= 1)
            & (frames <= NFRAMES)
            & (frames == np.floor(frames))
            & (ranges > 0)
            & (ranges <= 50.01)
        )

        f = frames[valid].astype(np.int64)
        r = ranges[valid]

        counts = np.bincount(f, minlength=100)[1:100]
        beyond = np.bincount(
            f,
            weights=(r > 10).astype(np.float64),
            minlength=100
        )[1:100]

        sums = np.bincount(
            f, weights=r, minlength=100
        )[1:100]

    return counts, beyond, sums

def python_loop(repeats):
    for _ in range(repeats):
        counts = np.zeros(NFRAMES, dtype=np.int64)
        beyond = np.zeros(NFRAMES, dtype=np.float64)
        sums = np.zeros(NFRAMES, dtype=np.float64)

        for f, r, s in zip(frames, ranges, signals):
            if not (
                np.isfinite(f)
                and np.isfinite(r)
                and np.isfinite(s)
                and 1 <= f <= NFRAMES
                and f == int(f)
                and 0 < r <= 50.01
            ):
                continue

            i = int(f) - 1
            counts[i] += 1
            beyond[i] += float(r > 10)
            sums[i] += r

    return counts, beyond, sums

# Verify both Python implementations agree.
a = vectorized(1)
b = python_loop(1)

assert np.array_equal(a[0], b[0])
assert np.array_equal(a[1], b[1])
assert np.allclose(a[2], b[2], rtol=0, atol=1e-7)

assert int(a[0].sum()) == 5614
assert int(a[1].sum()) == 2655

print("Correctness validation: PASSED")
print("Candidate returns:", int(a[0].sum()))
print("Returns beyond 10m:", int(a[1].sum()))

# Warm up both methods.
vectorized(3)
python_loop(3)

def benchmark(func):
    results = []
    for trial in range(TRIALS):
        start = time.perf_counter()
        output = func(BATCH)
        elapsed = time.perf_counter() - start
        assert len(output[0]) == NFRAMES
        ms = elapsed * 1000 / BATCH
        results.append(ms)
        print(f"  Trial {trial + 1}: {ms:.6f} ms")
    return results

print("\nNumPy vectorized:")
vector_times = benchmark(vectorized)

print("\nPython loop:")
loop_times = benchmark(python_loop)

results = {
    "NumPy vectorized": vector_times,
    "Python loop": loop_times,
}

trial_path = BENCH / "task21_08_python_trials.csv"

with trial_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Trial", "NumPyMs", "PythonLoopMs"])
    for i in range(TRIALS):
        writer.writerow([
            i + 1, vector_times[i], loop_times[i]
        ])

summary_path = BENCH / "task21_08_language_comparison.csv"
matlab_path = BENCH / "task21_07_cpu_benchmark_summary.csv"

summary_rows = []

for name, times in results.items():
    summary_rows.append([
        name,
        statistics.median(times),
        min(times),
        max(times),
        "Python"
    ])

# Add actual MATLAB values from Task 21.7, rather than
# typing or assuming their measured times.
if matlab_path.is_file():
    with matlab_path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        for row in csv.DictReader(f):
            summary_rows.append([
                row["Method"],
                float(row["MedianMsPerDataset"]),
                float(row["MinimumMsPerDataset"]),
                float(row["MaximumMsPerDataset"]),
                "MATLAB"
            ])
else:
    print("WARNING: MATLAB benchmark CSV missing")

with summary_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.writer(f)
    writer.writerow([
        "Method", "MedianMsPerDataset",
        "MinimumMsPerDataset", "MaximumMsPerDataset",
        "Language"
    ])
    writer.writerows(summary_rows)

digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

environment = (
    f"Task 21.8 benchmark\n"
    f"Computer: {platform.node()}\n"
    f"OS: {platform.platform()}\n"
    f"Processor: {platform.processor()}\n"
    f"Python: {sys.version}\n"
    f"NumPy: {np.__version__}\n"
    f"Input: {SOURCE}\n"
    f"Input SHA256: {digest}\n"
    f"Frames: 1-99\n"
    f"Repetitions: {BATCH}\n"
    f"Trials: {TRIALS}\n"
    f"Timing: perf_counter, excluding CSV loading\n"
    f"MATLAB and Python use different runtimes and "
    f"measurement APIs.\n"
    f"Results are exploratory, not controlled "
    f"cross-language energy benchmarks.\n"
)

env_path = BENCH / "task21_08_python_environment.txt"
env_path.write_text(environment, encoding="utf-8")

finding_path = FINDINGS / "task21_08_python_matlab_findings.txt"

finding_path.write_text(
    "TASK 21.8 - PYTHON VS MATLAB\n\n"
    "Identical source CSV and intended processing operations.\n"
    "Correctness validation: PASSED\n"
    "Dataset contains 5614 valid returns after frame 0.\n"
    "No OSI decoding or disk I/O included in timing.\n"
    "MATLAB and Python timings have different runtime overhead.\n"
    "No electrical energy or FPGA performance measured.\n"
    "Differences do not establish whole-pipeline performance.\n",
    encoding="utf-8"
)

print("\n=== TASK 21.8 BENCHMARK SUMMARY ===")
for name, times in results.items():
    print(
        f"{name}: "
        f"median={statistics.median(times):.6f} ms, "
        f"min={min(times):.6f} ms, "
        f"max={max(times):.6f} ms"
    )

print("\n=== TASK 21.8 FILE CHECK ===")
for path in [
    trial_path, summary_path, env_path, finding_path
]:
    print(f"{path.name}: {path.is_file()}")

print("\n=== TASK 21.8 COMPLETE ===")
