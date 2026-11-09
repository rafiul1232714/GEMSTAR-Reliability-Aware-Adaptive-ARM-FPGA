import csv
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

SOURCE = (
    TASK / "02_CSV_Data"
    / "task23_11D_clear_lidar_frame_metrics.csv"
)

GRAPHS = TASK / "03_Graphs"
REPORT = (
    TASK / "06_Research_Findings"
    / "task23_11D_range_variability.txt"
)

GRAPHS.mkdir(parents=True, exist_ok=True)

with SOURCE.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

frames = [int(r["Frame"]) for r in rows]
coverage = [float(r["CoveragePct"]) for r in rows]
min_range = [float(r["MinRangeM"]) for r in rows]
median_range = [float(r["MedianRangeM"]) for r in rows]
max_range = [float(r["MaxRangeM"]) for r in rows]

interval_frames = [
    int(r["Frame"]) for r in rows if r["IntervalMS"]
]
intervals = [
    float(r["IntervalMS"])
    for r in rows if r["IntervalMS"]
]

# Graph 1: Coverage
plt.figure(figsize=(10, 4))
plt.plot(frames, coverage)
plt.xlabel("Frame")
plt.ylabel("Accepted return coverage (%)")
plt.title("Task 23.11.D - Clear LiDAR Coverage")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    GRAPHS / "task23_11D_clear_coverage.png",
    dpi=160
)
plt.close()

# Graph 2: Range variation
plt.figure(figsize=(10, 5))
plt.plot(frames, min_range, label="Minimum range")
plt.plot(frames, median_range, label="Median range")
plt.plot(frames, max_range, label="Maximum range")
plt.xlabel("Frame")
plt.ylabel("Range (m)")
plt.title("Task 23.11.D - Clear LiDAR Range Variation")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    GRAPHS / "task23_11D_clear_ranges.png",
    dpi=160
)
plt.close()

# Graph 3: Timestamp intervals
plt.figure(figsize=(10, 4))
plt.plot(interval_frames, intervals)
plt.xlabel("Frame")
plt.ylabel("Time since previous frame (ms)")
plt.title("Task 23.11.D - LiDAR Timestamp Intervals")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(
    GRAPHS / "task23_11D_timestamp_intervals.png",
    dpi=160
)
plt.close()

lines = [
    "TASK 23.11.D - CLEAR LIDAR RANGE VARIABILITY",
    f"Frames: {len(rows)}",
    f"Unique coverage values: {len(set(coverage))}",
    f"Unique median range values: {len(set(median_range))}",
    f"Minimum median range: {min(median_range):.9f} m",
    f"Maximum median range: {max(median_range):.9f} m",
    f"Median range standard deviation: {statistics.pstdev(median_range):.9f} m",
    f"Minimum range standard deviation: {statistics.pstdev(min_range):.9f} m",
    f"Maximum range standard deviation: {statistics.pstdev(max_range):.9f} m",
    "",
    "Note: Constant summary statistics do not prove identical raw rays.",
    "Note: Detection accuracy and physical geometry remain unverified.",
]

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n".join(lines))
print("\nGraphs saved:")
for name in [
    "task23_11D_clear_coverage.png",
    "task23_11D_clear_ranges.png",
    "task23_11D_timestamp_intervals.png"
]:
    print(GRAPHS / name)
