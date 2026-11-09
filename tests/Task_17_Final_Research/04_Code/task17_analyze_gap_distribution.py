from pathlib import Path
import csv
import statistics

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

SOURCE = BASE / "02_CSV_Data" / "task17_sensor_timestamps.csv"

OUTPUT = (
    BASE / "02_CSV_Data" /
    "task17_timing_gap_distribution.csv"
)

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

intervals = [
    (
        int(r["Frame"]),
        float(r["TimestampSeconds"]),
        float(r["IntervalSeconds"]) * 1000
    )
    for r in rows
    if r["IntervalSeconds"]
]

median_ms = statistics.median(x[2] for x in intervals)
threshold = 2 * median_ms

segments = [
    ("Beginning", 0, 116),
    ("Middle_1", 117, 232),
    ("Middle_2", 233, 348),
    ("End", 349, 465),
]

results = []

for name, start, end in segments:
    part = [
        x for x in intervals
        if start <= x[0] <= end
    ]

    gaps = [x for x in part if x[2] > threshold]

    results.append({
        "Segment": name,
        "StartFrame": start,
        "EndFrame": end,
        "Intervals": len(part),
        "MedianIntervalMs": round(
            statistics.median(x[2] for x in part), 4
        ),
        "MaximumIntervalMs": round(
            max(x[2] for x in part), 4
        ),
        "LongIntervals": len(gaps),
    })

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=results[0].keys()
    )
    writer.writeheader()
    writer.writerows(results)

print("\n=== TASK 17.8A TIMING GAP DISTRIBUTION ===")
print("Investigation threshold (ms):", round(threshold, 4))

for r in results:
    print(
        f'{r["Segment"]}: '
        f'frames={r["StartFrame"]}-{r["EndFrame"]}, '
        f'median={r["MedianIntervalMs"]} ms, '
        f'max={r["MaximumIntervalMs"]} ms, '
        f'long_intervals={r["LongIntervals"]}'
    )

print("\nTotal long intervals:",
      sum(r["LongIntervals"] for r in results))

print("CSV saved:", OUTPUT.exists())
