import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

task = Path(sys.argv[1])

source = task / "02_CSV_Data" / "task23_11F_04B_frame_reliability.csv"
output = task / "03_Graphs" / "task23_11F_07B_frame_reliability.png"

if output.exists():
    raise RuntimeError(f"Output already exists: {output}")

expected = {
    "Clear": 13819,
    "Fog100": 12386,
    "Fog20": 14597,
}

samples = {name: ([], []) for name in expected}
counts = {name: 0 for name in expected}
minimums = {name: math.inf for name in expected}
maximums = {name: -math.inf for name in expected}

with source.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        name = row["weather"]

        if name not in expected:
            raise RuntimeError(f"Unexpected weather: {name}")

        index = int(row["frame_index"])
        score = float(row["availability_score"])

        if index != counts[name]:
            raise RuntimeError(f"Frame sequence error: {name}")

        if not math.isfinite(score) or not 0 <= score <= 1:
            raise RuntimeError(f"Invalid score: {name}")

        minimums[name] = min(minimums[name], score)
        maximums[name] = max(maximums[name], score)

        # Keep a manageable number of points for the graph.
        stride = max(1, expected[name] // 500)

        if index % stride == 0 or index == expected[name] - 1:
            progress = 100 * index / (expected[name] - 1)
            samples[name][0].append(progress)
            samples[name][1].append(score * 100)

        counts[name] += 1

if counts != expected:
    raise RuntimeError(f"Unexpected frame counts: {counts}")

fig, ax = plt.subplots(figsize=(10, 5.5))

labels = {
    "Clear": "Clear",
    "Fog100": "Fog MOR 100",
    "Fog20": "Fog MOR 20",
}

for name in expected:
    x, y = samples[name]

    ax.plot(
        x, y,
        linewidth=2,
        label=labels[name]
    )

    print(
        f"{name}: FRAMES={counts[name]} "
        f"MIN={minimums[name]:.9f} "
        f"MAX={maximums[name]:.9f}"
    )

ax.set_xlabel("Progress within each recording (%)")
ax.set_ylabel("Positive-return availability (%)")
ax.set_title("Frame-level LiDAR Return Availability")
ax.set_xlim(0, 100)
ax.set_ylim(-5, 105)
ax.grid(alpha=0.25)
ax.legend(loc="center right")

fig.text(
    0.5, 0.015,
    "Static controlled scene; horizontal trends do not establish tracking performance",
    ha="center",
    fontsize=9
)

fig.tight_layout(rect=[0, 0.045, 1, 1])

fig.savefig(output, dpi=200, bbox_inches="tight")
plt.close(fig)

if not output.is_file() or output.stat().st_size == 0:
    raise RuntimeError("Graph was not generated correctly")

print(f"TOTAL_FRAMES={sum(counts.values())}")
print(f"GRAPH={output}")
print("TASK23_11F_07B_FRAME_GRAPH_PASS")
