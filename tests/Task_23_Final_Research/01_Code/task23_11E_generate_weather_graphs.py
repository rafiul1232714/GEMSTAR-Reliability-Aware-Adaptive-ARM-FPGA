import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

task = Path(sys.argv[1])
csv_path = task / "02_CSV_Data" / "task23_11E_three_weather_comparison.csv"
graph_dir = task / "03_Graphs"

if not csv_path.is_file():
    raise RuntimeError("Comparison CSV missing")

with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 3:
    raise RuntimeError("Expected exactly three weather conditions")

expected = {"Clear", "Fog100", "Fog20"}

if {r["Weather"] for r in rows} != expected:
    raise RuntimeError("Unexpected weather conditions")

rows.sort(key=lambda r: ["Clear", "Fog100", "Fog20"].index(r["Weather"]))

labels = ["Clear", "Fog MOR 100", "Fog MOR 20"]
coverage = [float(r["CoveragePercent"]) for r in rows]
positive = [int(r["PositiveReturnsPerFrame"]) for r in rows]
slots = [int(r["ReflectionSlotsPerFrame"]) for r in rows]
invalid = [s - p for s, p in zip(slots, positive)]

output1 = graph_dir / "task23_11E_lidar_coverage_by_weather.png"
output2 = graph_dir / "task23_11E_positive_vs_invalid_returns.png"

for output in (output1, output2):
    if output.exists():
        raise RuntimeError(f"Refusing to overwrite: {output}")

graph_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(9, 5.5))
bars = ax.bar(labels, coverage)
ax.set_ylim(0, 105)
ax.set_ylabel("Positive-return coverage (%)")
ax.set_title("GEMSTAR LiDAR Return Coverage Under Controlled Weather")
ax.bar_label(bars, fmt="%.2f%%", padding=4)
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(output1, dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 5.5))
x = range(len(labels))

ax.bar(x, positive, label="Positive returns")
ax.bar(x, invalid, bottom=positive, label="Invalid returns")

ax.set_xticks(list(x), labels)
ax.set_ylabel("Reflection slots per frame")
ax.set_title("GEMSTAR LiDAR Positive and Invalid Returns")
ax.legend()
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)

fig.tight_layout()
fig.savefig(output2, dpi=200)
plt.close(fig)

for output in (output1, output2):
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"Graph verification failed: {output}")

    print(f"GRAPH_SAVED={output}")
    print(f"FILE_BYTES={output.stat().st_size}")

print("TASK23_11E_WEATHER_GRAPHS_SAVED")
