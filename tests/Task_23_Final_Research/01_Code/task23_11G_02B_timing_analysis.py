import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

task = Path(sys.argv[1])

source = task / "02_CSV_Data" / "task23_11G_02A_raw_timing_distribution.csv"
summary = task / "02_CSV_Data" / "task23_11G_02B_timing_statistics.csv"
figure = task / "03_Graphs" / "task23_11G_02B_timing_distribution.png"

for path in (summary, figure):
    if path.exists():
        raise RuntimeError(f"Output already exists: {path}")

def percentile(values, percent):
    values = sorted(values)
    position = (len(values) - 1) * percent / 100
    lo = int(position)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)

groups = defaultdict(list)
rounds = defaultdict(list)

with source.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        name = row["weather"]
        number = int(row["round"])
        repetition = int(row["repetition"])
        duration = float(row["duration_us"])

        if name not in {"Clear", "Fog100", "Fog20"}:
            raise RuntimeError("Unexpected weather condition")

        if number not in (1, 2, 3):
            raise RuntimeError("Unexpected round")

        if repetition < 1 or repetition > 200:
            raise RuntimeError("Unexpected repetition")

        if not math.isfinite(duration) or duration <= 0:
            raise RuntimeError("Invalid execution time")

        groups[name].append(duration)
        rounds[(name, number)].append((repetition, duration))

for name in ("Clear", "Fog100", "Fog20"):
    if len(groups[name]) != 600:
        raise RuntimeError(f"{name}: expected 600 measurements")

    for number in (1, 2, 3):
        measurements = rounds[(name, number)]

        if len(measurements) != 200:
            raise RuntimeError("Expected 200 samples per round")

        indices = sorted(index for index, _ in measurements)

        if indices != list(range(1, 201)):
            raise RuntimeError("Missing or duplicate repetitions")

results = []

for name in ("Clear", "Fog100", "Fog20"):
    values = groups[name]

    mean = statistics.mean(values)
    median = statistics.median(values)
    std = statistics.stdev(values)
    p95 = percentile(values, 95)
    p99 = percentile(values, 99)

    round_means = [
        statistics.mean(
            duration for _, duration in rounds[(name, n)]
        )
        for n in (1, 2, 3)
    ]

    round_mean_range = max(round_means) - min(round_means)

    results.append([
        name,
        len(values),
        f"{mean:.3f}",
        f"{median:.3f}",
        f"{p95:.3f}",
        f"{p99:.3f}",
        f"{std:.3f}",
        f"{min(values):.3f}",
        f"{max(values):.3f}",
        f"{round_mean_range:.3f}"
    ])

    print(
        f"{name}: N={len(values)} "
        f"MEAN_US={mean:.3f} "
        f"P50_US={median:.3f} "
        f"P95_US={p95:.3f} "
        f"P99_US={p99:.3f} "
        f"STD_US={std:.3f}"
    )

with summary.open("x", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "weather",
        "samples",
        "mean_us",
        "p50_us",
        "p95_us",
        "p99_us",
        "std_us",
        "min_us",
        "max_us",
        "round_mean_range_us"
    ])
    writer.writerows(results)

fig, ax = plt.subplots(figsize=(9, 5.5))

ax.boxplot(
    [groups[name] for name in ("Clear", "Fog100", "Fog20")],
    tick_labels=["Clear", "Fog MOR 100", "Fog MOR 20"],
    showfliers=True
)

ax.set_title("LiDAR Scoring Execution-Time Distribution")
ax.set_ylabel("Execution time per scoring call (microseconds)")
ax.set_xlabel("Controlled weather condition")
ax.grid(axis="y", alpha=0.25)

fig.text(
    0.5, 0.015,
    "Python on PC; 600 repeated calls per fixed frame, not ARM-FPGA timing",
    ha="center",
    fontsize=9
)

fig.tight_layout(rect=[0, 0.045, 1, 1])

try:
    fig.savefig(figure, dpi=200, bbox_inches="tight")
finally:
    plt.close(fig)

if not figure.is_file() or figure.stat().st_size == 0:
    raise RuntimeError("Timing graph missing or empty")

print("TOTAL_MEASUREMENTS=1800")
print(f"SUMMARY_CSV={summary}")
print(f"GRAPH={figure}")
print("TASK23_11G_02B_TIMING_ANALYSIS_PASS")
