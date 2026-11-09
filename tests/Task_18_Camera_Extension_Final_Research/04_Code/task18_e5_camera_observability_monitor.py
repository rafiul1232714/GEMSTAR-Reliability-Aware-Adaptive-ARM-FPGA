import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Camera_Extension_Final_Research"
)

DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"

SOURCE = DATA / "task18_e4_camera_quality_metrics.csv"
OUT = DATA / "task18_e5_camera_observability_results.csv"
SUMMARY = DATA / "task18_e5_observability_summary.csv"
FIGURE = GRAPHS / "task18_e5_camera_observability.png"

assert SOURCE.is_file(), "Task 18.E4 metrics file missing."
GRAPHS.mkdir(parents=True, exist_ok=True)

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    records = list(csv.DictReader(f))

assert records, "No camera measurements found."

features = [
    "Brightness",
    "Contrast",
    "LaplacianVariance",
    "EdgeDensityPercent",
]

# Reference recording: baseline_clear.
# NOTE: Only 4 frames; not a statistically validated
# reference population or independently labeled set.
reference_rows = [
    r for r in records
    if r["Recording"] == "baseline_clear"
]

assert len(reference_rows) >= 2, "Missing clear reference."

reference = {
    key: statistics.median(
        float(r[key]) for r in reference_rows
    )
    for key in features
}

# Provisional, manually selected warning thresholds.
# These are for exploratory comparison only.
thresholds = {
    "BrightnessHigh": reference["Brightness"] + 25.0,
    "ContrastLow": reference["Contrast"] * 0.75,
    "SharpnessLow": reference["LaplacianVariance"] * 0.35,
    "EdgesLow": reference["EdgeDensityPercent"] * 0.60,
}

print("\n=== TASK 18.E5 CAMERA OBSERVABILITY ===")
print("Reference:", "baseline_clear")
print("Reference frames:", len(reference_rows))

print("\n=== REFERENCE MEDIANS ===")
for key, value in reference.items():
    print(f"{key}: {value:.3f}")

print("\n=== PROVISIONAL THRESHOLDS ===")
for key, value in thresholds.items():
    print(f"{key}: {value:.3f}")

results = []

for r in records:
    brightness = float(r["Brightness"])
    contrast = float(r["Contrast"])
    sharpness = float(r["LaplacianVariance"])
    edges = float(r["EdgeDensityPercent"])

    flags = {
        "BrightnessHigh":
            brightness > thresholds["BrightnessHigh"],
        "ContrastLow":
            contrast < thresholds["ContrastLow"],
        "SharpnessLow":
            sharpness < thresholds["SharpnessLow"],
        "EdgesLow":
            edges < thresholds["EdgesLow"],
    }

    warning_count = sum(flags.values())

    # Two or more warning criteria trigger REVIEW.
    state = (
        "REVIEW" if warning_count >= 2
        else "OBSERVABLE"
    )

    row = dict(r)
    row.update({
        "WarningCount": warning_count,
        "CameraState": state,
        "WarningReasons": ";".join(
            k for k, v in flags.items() if v
        ),
    })

    for key, value in flags.items():
        row[key] = int(value)

    results.append(row)

    print(
        f"{r['Recording']:30s} "
        f"| {r['ImageName']:40s} "
        f"| Warnings={warning_count} "
        f"| {state}"
    )

with OUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

groups = defaultdict(list)
for r in results:
    groups[r["Recording"]].append(r)

summary_rows = []

for scenario, group in sorted(groups.items()):
    counts = Counter(r["CameraState"] for r in group)

    summary_rows.append({
        "Recording": scenario,
        "Frames": len(group),
        "Observable": counts["OBSERVABLE"],
        "Review": counts["REVIEW"],
        "MedianWarningCount": statistics.median(
            r["WarningCount"] for r in group
        ),
    })

with SUMMARY.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summary_rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(summary_rows)

# Visualize per-recording monitoring outcomes.
names = [r["Recording"] for r in summary_rows]
observables = [r["Observable"] for r in summary_rows]
reviews = [r["Review"] for r in summary_rows]

fig, axes = plt.subplots(
    2, 1, figsize=(12, 9),
    gridspec_kw={"height_ratios": [1, 1.2]}
)

positions = range(len(names))

axes[0].bar(
    positions, observables, label="OBSERVABLE"
)
axes[0].bar(
    positions, reviews, bottom=observables,
    label="REVIEW"
)
axes[0].set_xticks(list(positions))
axes[0].set_xticklabels(
    names, rotation=20, ha="right"
)
axes[0].set_ylabel("Frame count")
axes[0].set_title("Provisional camera observability states")
axes[0].legend()
axes[0].grid(axis="y", alpha=0.25)

for scenario in names:
    group = groups[scenario]
    xs = list(range(len(group)))
    ys = [r["WarningCount"] for r in group]
    axes[1].plot(
        xs, ys, marker="o", label=scenario
    )

axes[1].axhline(
    2, linestyle="--", color="black",
    label="REVIEW threshold"
)
axes[1].set_xlabel("Sampled frame order within recording")
axes[1].set_ylabel("Number of active warning criteria")
axes[1].set_title("Image-statistics warning counts")
axes[1].set_ylim(-0.3, 4.4)
axes[1].grid(alpha=0.25)
axes[1].legend(fontsize=8)

fig.suptitle(
    "GEMSTAR Camera Observability - Exploratory Monitor"
)
fig.tight_layout()
fig.savefig(FIGURE, dpi=180, bbox_inches="tight")
plt.close(fig)

print("\n=== CAMERA MONITOR SUMMARY ===")

for row in summary_rows:
    print(
        f"{row['Recording']:30s}"
        f"| Frames={row['Frames']}"
        f"| OBSERVABLE={row['Observable']}"
        f"| REVIEW={row['Review']}"
        f"| Median warnings={row['MedianWarningCount']:.1f}"
    )

total = Counter(r["CameraState"] for r in results)

print("\n=== TASK 18.E5 COMPLETE ===")
print("Frames analyzed:", len(results))
print("OBSERVABLE:", total["OBSERVABLE"])
print("REVIEW:", total["REVIEW"])
print("Results CSV saved:", OUT.is_file())
print("Summary CSV saved:", SUMMARY.is_file())
print("Graph saved:", FIGURE.is_file())
print("Graph path:", FIGURE)
print("\nLIMITATION:")
print("Thresholds use only four clear-reference frames.")
print("States are statistical flags, not validated")
print("camera failure or object detection accuracy.")
print("This experiment is exploratory and in-sample.")
