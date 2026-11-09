from pathlib import Path
import csv
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

CSV_DIR = BASE / "02_CSV_Data"
GRAPH_DIR = BASE / "01_Graphs"

SV_FILE = CSV_DIR / "task17_sensor_timestamps.csv"
GT_FILE = CSV_DIR / "task17_groundtruth_timestamps.csv"

OUT_CSV = CSV_DIR / "task17_gt_sv_alignment.csv"
OUT_STATS = CSV_DIR / "task17_alignment_statistics.csv"
OUT_GRAPH = GRAPH_DIR / "task17_gt_sv_alignment.png"

def load_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

sv = load_csv(SV_FILE)
gt = load_csv(GT_FILE)

if len(sv) != len(gt):
    raise RuntimeError(
        f"Frame count mismatch: SV={len(sv)}, GT={len(gt)}"
    )

results = []

for sv_row, gt_row in zip(sv, gt):
    sv_frame = int(sv_row["Frame"])
    gt_frame = int(gt_row["Frame"])

    if sv_frame != gt_frame:
        raise RuntimeError(
            f"Frame index mismatch: SV={sv_frame}, GT={gt_frame}"
        )

    sv_time = float(sv_row["TimestampSeconds"])
    gt_time = float(gt_row["TimestampSeconds"])

    difference_ms = (sv_time - gt_time) * 1000

    results.append({
        "Frame": sv_frame,
        "SVTimestampSeconds": f"{sv_time:.9f}",
        "GTTimestampSeconds": f"{gt_time:.9f}",
        "DifferenceMilliseconds": f"{difference_ms:.9f}",
        "AbsoluteDifferenceMilliseconds": f"{abs(difference_ms):.9f}",
        "ExactMatch": abs(difference_ms) < 0.000001
    })

with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

differences = [
    float(r["AbsoluteDifferenceMilliseconds"])
    for r in results
]

exact_matches = sum(
    r["ExactMatch"] for r in results
)

statistics_rows = [
    ["SensorViewFrames", len(sv)],
    ["GroundTruthFrames", len(gt)],
    ["ComparedFrames", len(results)],
    ["ExactTimestampMatches", exact_matches],
    ["MaximumAbsoluteDifferenceMs", max(differences)],
    ["MeanAbsoluteDifferenceMs", statistics.mean(differences)],
    ["TimestampMismatchCount", len(results) - exact_matches],
]

with OUT_STATS.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value"])
    writer.writerows(statistics_rows)

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    [int(r["Frame"]) for r in results],
    [
        float(r["DifferenceMilliseconds"])
        for r in results
    ],
    linewidth=1.2
)

ax.set_title(
    "Task 17 - GroundTruth vs SensorView Timestamp Difference"
)
ax.set_xlabel("Frame index")
ax.set_ylabel("SV - GT timestamp difference (ms)")
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUT_GRAPH, dpi=200)
plt.close(fig)

print("\n=== TASK 17.4B SYNCHRONIZATION VALIDATION ===")
print("Compared frames:", len(results))
print("Exact timestamp matches:", exact_matches)
print("Timestamp mismatches:", len(results) - exact_matches)
print("Maximum difference (ms):", max(differences))
print("Mean difference (ms):", statistics.mean(differences))
print("Alignment CSV saved:", OUT_CSV.exists())
print("Statistics CSV saved:", OUT_STATS.exists())
print("Alignment graph saved:", OUT_GRAPH.exists())
