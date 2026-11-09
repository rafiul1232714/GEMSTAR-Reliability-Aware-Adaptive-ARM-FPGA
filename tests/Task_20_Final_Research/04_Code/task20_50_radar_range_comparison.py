import csv
import json
import math
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_20_Final_Research")
DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"
FINDINGS = BASE / "06_Research_Findings"

for folder in (DATA, GRAPHS, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

OLD = DATA / "task20_28_radar_world_points.csv"
NEW = DATA / "task20_49_50m_radar_returns.csv"

def read_ranges(path, column, scenario=None):
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if scenario is not None:
        rows = [
            row for row in rows
            if row["Recording"] == scenario
        ]

    values = []
    near_zero = 0

    for row in rows:
        value = float(row[column])
        if not math.isfinite(value) or value < 0:
            continue
        if value < 0.001:
            near_zero += 1
        values.append(value)

    return values, near_zero

old, old_near_zero = read_ranges(
    OLD, "RangeM", "baseline_clear"
)
new, new_near_zero = read_ranges(NEW, "RangeM")

if not old or not new:
    raise ValueError("Missing usable radar returns")

# Both datasets represent 100 inspected frames.
# Task 20.28 omitted the first frame because host pose
# was unavailable. This affects the old counts.
FRAME_WINDOW = 100

def summarize(label, values, near_zero):
    return {
        "Dataset": label,
        "InspectedFrameWindow": FRAME_WINDOW,
        "Returns": len(values),
        "ReturnsPerInspectedFrame": len(values) / FRAME_WINDOW,
        "MinRangeM": min(values),
        "MedianRangeM": median(values),
        "MaxRangeM": max(values),
        "Beyond10m": sum(x > 10 for x in values),
        "Beyond20m": sum(x > 20 for x in values),
        "Beyond30m": sum(x > 30 for x in values),
        "Beyond40m": sum(x > 40 for x in values),
        "NearZeroUnder1mm": near_zero
    }

results = [
    summarize("Original 10m - baseline_clear", old, old_near_zero),
    summarize("Corrected 50m - 20261102T180104Z", new, new_near_zero)
]

print("\n=== TASK 20.50 RADAR COMPARISON ===")

for item in results:
    print("\n", item["Dataset"])
    print(" Candidate returns:", item["Returns"])
    print(" Returns per inspected frame:",
          round(item["ReturnsPerInspectedFrame"], 2))
    print(" Median range:",
          round(item["MedianRangeM"], 4), "m")
    print(" Maximum range:",
          round(item["MaxRangeM"], 4), "m")
    print(" Returns beyond 10m:", item["Beyond10m"])
    print(" Near-zero (<1mm):", item["NearZeroUnder1mm"])

summary_path = DATA / "task20_50_10m_vs_50m_summary.csv"

with summary_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

# Distribution comparison, using the same bin boundaries.
bins = list(range(0, 55, 5))

fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(
    [old, new],
    bins=bins,
    label=["Original 10 m", "Corrected 50 m"],
    alpha=0.7
)
ax.set_xlabel("Measured radar range (m)")
ax.set_ylabel("Candidate returns")
ax.set_title("GEMSTAR radar range distribution comparison")
ax.legend()
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()

plot_path = GRAPHS / "task20_50_radar_range_comparison.png"
fig.savefig(plot_path, dpi=180)
plt.close(fig)

report = {
    "Task": "20.50",
    "OriginalDataset": "task20_28 baseline_clear",
    "CorrectedDataset": "task20_49 50m recording",
    "Results": results,
    "OriginalDatasetExcludesFrameZero": True,
    "ComparisonIsPaired": False,
    "IdenticalSceneStateVerified": False,
    "NearZeroReturnQualityValidated": False,
    "RadarDetectionAccuracyValidated": False,
    "HardwareEnergyMeasured": False,
    "Interpretation": (
        "Descriptive comparison of two different "
        "recordings. Changes in counts cannot be "
        "attributed exclusively to radar range."
    )
}

report_path = FINDINGS / "task20_50_range_comparison.json"
report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.50 COMPLETE ===")
print("Summary CSV saved:", summary_path.is_file())
print("Comparison plot saved:", plot_path.is_file())
print("Research report saved:", report_path.is_file())
print("Paired controlled comparison:", False)
print("Radar accuracy validated:", False)
print("Energy measured:", False)
