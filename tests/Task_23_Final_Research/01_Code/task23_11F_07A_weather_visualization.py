import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

task = Path(sys.argv[1])

source = (
    task / "02_CSV_Data" /
    "task23_11F_04B_reliability_summary.csv"
)

figure = (
    task / "03_Graphs" /
    "task23_11F_07A_weather_reliability.png"
)

matlab_csv = (
    task / "02_CSV_Data" /
    "task23_11F_07A_matlab_weather_reliability.csv"
)

for output in (figure, matlab_csv):
    if output.exists():
        raise RuntimeError(f"Output already exists: {output}")

with source.open(encoding="utf-8-sig", newline="") as f:
    records = list(csv.DictReader(f))

rows = {row["weather"]: row for row in records}

expected = ["Clear", "Fog100", "Fog20"]

if len(records) != 3 or set(rows) != set(expected):
    raise RuntimeError("Unexpected weather summary")

labels = ["Clear", "Fog MOR 100", "Fog MOR 20"]
scores = []
frames = []

for name in expected:
    score = float(rows[name]["mean_score"])
    count = int(rows[name]["frames"])

    if not math.isfinite(score) or not 0 <= score <= 1:
        raise RuntimeError(f"Invalid score for {name}")

    scores.append(score)
    frames.append(count)

if frames != [13819, 12386, 14597]:
    raise RuntimeError("Unexpected frame counts")

fig, ax = plt.subplots(figsize=(9, 5.5))

bars = ax.bar(
    labels,
    [score * 100 for score in scores],
    width=0.55
)

ax.set_ylabel("Positive-return availability (%)")
ax.set_xlabel("Controlled GEMSTAR weather condition")
ax.set_title("LiDAR Return Availability Across Weather Conditions")
ax.set_ylim(0, 110)
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)

for bar, score in zip(bars, scores):
    ax.annotate(
        f"{score * 100:.3f}%",
        (
            bar.get_x() + bar.get_width() / 2,
            bar.get_height()
        ),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center"
    )

fig.text(
    0.5, 0.015,
    "Controlled static scene; availability is not detection accuracy",
    ha="center", fontsize=9
)

fig.tight_layout(rect=[0, 0.045, 1, 1])

try:
    fig.savefig(figure, dpi=200, bbox_inches="tight")
finally:
    plt.close(fig)

try:
    with matlab_csv.open(
        "x", encoding="utf-8", newline=""
    ) as f:
        writer = csv.writer(f)

        writer.writerow([
            "weather_code",
            "frame_count",
            "mean_availability",
            "mean_availability_percent"
        ])

        for i, (count, score) in enumerate(zip(frames, scores), 1):
            writer.writerow([
                i,
                count,
                f"{score:.12f}",
                f"{score * 100:.9f}"
            ])
except Exception:
    if matlab_csv.exists():
        matlab_csv.unlink()
    if figure.exists():
        figure.unlink()
    raise

print("WEATHER_CODES=1:Clear,2:Fog100,3:Fog20")

for name, count, score in zip(expected, frames, scores):
    print(
        f"{name}: FRAMES={count} "
        f"AVAILABILITY={score:.9f}"
    )

print(f"GRAPH={figure}")
print(f"MATLAB_CSV={matlab_csv}")
print("TASK23_11F_07A_VISUALIZATION_PASS")
