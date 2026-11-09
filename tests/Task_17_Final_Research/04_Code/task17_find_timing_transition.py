from pathlib import Path
import csv
import statistics

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_17_Final_Research"
)

SOURCE = BASE / "02_CSV_Data" / "task17_sensor_timestamps.csv"
OUTPUT = BASE / "02_CSV_Data" / "task17_timing_transition.csv"

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

valid = [
    (int(r["Frame"]), float(r["TimestampSeconds"]),
     float(r["IntervalSeconds"]) * 1000, r)
    for r in rows if r["IntervalSeconds"]
]

median_ms = statistics.median(x[2] for x in valid)
threshold_ms = 2 * median_ms

long_intervals = [x for x in valid if x[2] > threshold_ms]

if not long_intervals:
    raise RuntimeError("No long intervals found")

first = long_intervals[0]
last = long_intervals[-1]

first_frame = first[0]

context = [
    x for x in valid
    if first_frame - 8 <= x[0] <= first_frame + 12
]

output_rows = []

for frame, timestamp, interval_ms, original in context:
    output_rows.append({
        "Frame": frame,
        "TimestampSeconds": timestamp,
        "IntervalMilliseconds": round(interval_ms, 6),
        "LongInterval": interval_ms > threshold_ms,
        "CameraEntries": original["CameraEntries"],
        "LiDAREntries": original["LiDAREntries"],
        "RadarEntries": original["RadarEntries"],
    })

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=output_rows[0].keys())
    writer.writeheader()
    writer.writerows(output_rows)

print("\n=== TASK 17.8B TIMING TRANSITION ===")
print("First long-interval frame:", first[0])
print("First long-interval timestamp (s):", round(first[1], 6))
print("First long interval (ms):", round(first[2], 4))
print("Last long-interval frame:", last[0])
print("Last long-interval timestamp (s):", round(last[1], 6))

print("\n=== FRAMES AROUND TRANSITION ===")
for r in output_rows:
    print(
        f'Frame {r["Frame"]:3d} | '
        f'Time {r["TimestampSeconds"]:9.4f}s | '
        f'Interval {r["IntervalMilliseconds"]:8.3f}ms | '
        f'Long={r["LongInterval"]} | '
        f'C/L/R={r["CameraEntries"]}/'
        f'{r["LiDAREntries"]}/{r["RadarEntries"]}'
    )

print("\nCSV saved:", OUTPUT.exists())
