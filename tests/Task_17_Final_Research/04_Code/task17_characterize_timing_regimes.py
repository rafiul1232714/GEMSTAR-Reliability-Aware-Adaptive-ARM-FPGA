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
SUMMARY = BASE / "02_CSV_Data" / "task17_timing_regime_summary.csv"
DETAILS = BASE / "02_CSV_Data" / "task17_timing_regime_frames.csv"
GRAPH = BASE / "01_Graphs" / "task17_timing_regime_transition.png"

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    original = list(csv.DictReader(f))

rows = []
for r in original:
    frame = int(r["Frame"])
    rows.append({
        "Frame": frame,
        "Regime": "HIGH_RATE" if frame < 424 else "LOW_RATE",
        "TimestampSeconds": float(r["TimestampSeconds"]),
        "IntervalMs": (
            float(r["IntervalSeconds"]) * 1000
            if r["IntervalSeconds"] else None
        ),
        "CameraEntries": int(r["CameraEntries"]),
        "LiDAREntries": int(r["LiDAREntries"]),
        "RadarEntries": int(r["RadarEntries"])
    })

summary = []

for regime in ["HIGH_RATE", "LOW_RATE"]:
    selected = [r for r in rows if r["Regime"] == regime]
    intervals = [
        r["IntervalMs"] for r in selected
        if r["IntervalMs"] is not None
    ]

    # For the low-rate segment, interval for frame 424
    # is the transition into the new regime.
    record = {
        "Regime": regime,
        "StartFrame": selected[0]["Frame"],
        "EndFrame": selected[-1]["Frame"],
        "Frames": len(selected),
        "MedianIntervalMs": statistics.median(intervals),
        "MeanIntervalMs": statistics.mean(intervals),
        "MinIntervalMs": min(intervals),
        "MaxIntervalMs": max(intervals),
        "ApproxRateHz": 1000 / statistics.median(intervals),
        "CameraMissingFrames": sum(
            r["CameraEntries"] != 1 for r in selected
        ),
        "LiDARMissingFrames": sum(
            r["LiDAREntries"] != 1 for r in selected
        ),
        "RadarMissingFrames": sum(
            r["RadarEntries"] != 1 for r in selected
        ),
    }

    summary.append(record)

with SUMMARY.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=summary[0].keys())
    writer.writeheader()
    writer.writerows(summary)

with DETAILS.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

fig, ax = plt.subplots(figsize=(12, 5))

valid = [r for r in rows if r["IntervalMs"] is not None]
ax.plot(
    [r["Frame"] for r in valid],
    [r["IntervalMs"] for r in valid],
    linewidth=1.2
)

ax.axvline(
    424,
    linestyle="--",
    label="First long interval: frame 424"
)

ax.set_title("Task 17 - GEMSTAR Recorded Timing Regime Change")
ax.set_xlabel("Frame index")
ax.set_ylabel("Recorded message interval (ms)")
ax.grid(True, alpha=0.3)
ax.legend()

fig.tight_layout()
fig.savefig(GRAPH, dpi=200)
plt.close(fig)

print("\n=== TASK 17.8C TIMING REGIMES ===")

for r in summary:
    print(
        f'{r["Regime"]}: '
        f'frames={r["Frames"]}, '
        f'median={r["MedianIntervalMs"]:.4f} ms, '
        f'rate={r["ApproxRateHz"]:.3f} Hz, '
        f'missing C/L/R='
        f'{r["CameraMissingFrames"]}/'
        f'{r["LiDARMissingFrames"]}/'
        f'{r["RadarMissingFrames"]}'
    )

print("Summary CSV saved:", SUMMARY.exists())
print("Frame CSV saved:", DETAILS.exists())
print("Graph saved:", GRAPH.exists())
