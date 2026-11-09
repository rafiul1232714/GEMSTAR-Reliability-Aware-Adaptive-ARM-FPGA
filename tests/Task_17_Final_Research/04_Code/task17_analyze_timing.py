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

SOURCE = BASE / "02_CSV_Data" / "task17_sensor_timestamps.csv"
STATS = BASE / "02_CSV_Data" / "task17_timing_statistics.csv"
GAPS = BASE / "02_CSV_Data" / "task17_timing_gap_events.csv"
GRAPH = BASE / "01_Graphs" / "task17_sensor_timestamp_intervals.png"

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

frames = [int(r["Frame"]) for r in rows]
times = [float(r["TimestampSeconds"]) for r in rows]
intervals = [
    (int(r["Frame"]), float(r["IntervalSeconds"]))
    for r in rows
    if r["IntervalSeconds"]
]

values = [dt for _, dt in intervals]

# Descriptive threshold only:
# intervals > 2x median are flagged for investigation.
median_interval = statistics.median(values)
threshold = 2 * median_interval

gap_events = [
    {
        "Frame": frame,
        "TimestampSeconds": f"{times[frame]:.9f}",
        "IntervalSeconds": f"{dt:.9f}",
        "IntervalMilliseconds": f"{dt * 1000:.3f}",
        "ThresholdMilliseconds": f"{threshold * 1000:.3f}",
        "Interpretation": "LONG_INTERVAL_REQUIRES_INVESTIGATION",
    }
    for frame, dt in intervals
    if dt > threshold
]

metrics = {
    "Frames": len(frames),
    "Intervals": len(values),
    "FirstTimestampSeconds": times[0],
    "LastTimestampSeconds": times[-1],
    "RecordingSpanSeconds": times[-1] - times[0],
    "MinimumIntervalMs": min(values) * 1000,
    "MedianIntervalMs": median_interval * 1000,
    "MeanIntervalMs": statistics.mean(values) * 1000,
    "MaximumIntervalMs": max(values) * 1000,
    "IntervalStdDevMs": statistics.stdev(values) * 1000,
    "LongIntervalThresholdMs": threshold * 1000,
    "LongIntervalCount": len(gap_events),
    "NonPositiveIntervalCount": sum(x <= 0 for x in values),
}

STATS.parent.mkdir(parents=True, exist_ok=True)
GRAPH.parent.mkdir(parents=True, exist_ok=True)

with STATS.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Metric", "Value"])
    writer.writerows(metrics.items())

with GAPS.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Frame",
            "TimestampSeconds",
            "IntervalSeconds",
            "IntervalMilliseconds",
            "ThresholdMilliseconds",
            "Interpretation",
        ],
    )
    writer.writeheader()
    writer.writerows(gap_events)

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(
    [frame for frame, _ in intervals],
    [dt * 1000 for _, dt in intervals],
    linewidth=1,
)

ax.axhline(
    threshold * 1000,
    linestyle="--",
    label="2 x median interval (investigation threshold)",
)

ax.set_title("Task 17 - GEMSTAR SensorView Timestamp Intervals")
ax.set_xlabel("Frame index")
ax.set_ylabel("Interval between SensorView messages (ms)")
ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()
fig.savefig(GRAPH, dpi=200)
plt.close(fig)

print("\n=== TASK 17.3B TIMING ANALYSIS ===")
print("Frames:", metrics["Frames"])
print("Median interval (ms):", round(metrics["MedianIntervalMs"], 4))
print("Mean interval (ms):", round(metrics["MeanIntervalMs"], 4))
print("Maximum interval (ms):", round(metrics["MaximumIntervalMs"], 4))
print("Investigation threshold (ms):", round(metrics["LongIntervalThresholdMs"], 4))
print("Long intervals:", metrics["LongIntervalCount"])
print("Statistics saved:", STATS.exists())
print("Gap events saved:", GAPS.exists())
print("Graph saved:", GRAPH.exists())
