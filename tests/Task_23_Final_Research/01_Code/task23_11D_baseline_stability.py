import csv
import statistics
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

SOURCE = (
    TASK / "02_CSV_Data"
    / "task23_11D_clear_lidar_frame_metrics.csv"
)

REPORT = (
    TASK / "06_Research_Findings"
    / "task23_11D_baseline_stability.txt"
)

with SOURCE.open(newline="", encoding="utf-8-sig") as file:
    rows = list(csv.DictReader(file))

if len(rows) != 573:
    raise RuntimeError(
        f"Expected 573 frames, found {len(rows)}"
    )

coverage = [
    float(row["CoveragePct"])
    for row in rows
]

returns = [
    int(row["ScreenedReturns"])
    for row in rows
]

median_ranges = [
    float(row["MedianRangeM"])
    for row in rows
    if row["MedianRangeM"]
]

intervals = [
    float(row["IntervalMS"])
    for row in rows
    if row["IntervalMS"]
]

first = rows[0]
steady = rows[1:]

steady_coverage = [
    float(row["CoveragePct"])
    for row in steady
]

unique_counts = sorted(set(returns))

lines = [
    "TASK 23.11.D - CLEAR BASELINE STABILITY",
    f"Frames: {len(rows)}",
    f"Unique accepted-return counts: {len(unique_counts)}",
    f"Minimum accepted returns/frame: {min(returns)}",
    f"Maximum accepted returns/frame: {max(returns)}",
    f"Mean coverage: {statistics.mean(coverage):.6f} %",
    f"Coverage standard deviation: {statistics.pstdev(coverage):.6f}",
    f"Minimum coverage: {min(coverage):.6f} %",
    f"Maximum coverage: {max(coverage):.6f} %",
    f"First-frame coverage: {float(first['CoveragePct']):.6f} %",
    f"Frames 2-573 mean coverage: {statistics.mean(steady_coverage):.6f} %",
    f"First-frame median range: {first['MedianRangeM']} m",
    f"Mean of frame median ranges: {statistics.mean(median_ranges):.6f} m",
    f"Minimum timestamp interval: {min(intervals):.6f} ms",
    f"Median timestamp interval: {statistics.median(intervals):.6f} ms",
    f"Maximum timestamp interval: {max(intervals):.6f} ms",
    f"Timestamp interval standard deviation: {statistics.pstdev(intervals):.6f} ms",
    "Note: Frames 2-573 are an analysis grouping, not proven steady state.",
]

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n".join(lines))
print("\nReport:", REPORT)
