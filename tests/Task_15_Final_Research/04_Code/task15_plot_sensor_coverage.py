from pathlib import Path
import csv
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_15_Final_Research"
)

CSV_FILE = (
    BASE / "02_CSV_Data"
    / "task15_sensor_coverage_percentages.csv"
)

OUTPUT = (
    BASE / "01_Graphs"
    / "task15_sensor_coverage.png"
)

with CSV_FILE.open(
    newline="", encoding="utf-8-sig"
) as f:
    rows = list(csv.DictReader(f))

labels = [
    row["Recording"].split("_sv_")[1].replace(
        "_GEMSTAR.osi", ""
    )
    for row in rows
]

camera = [
    float(row["CameraCoveragePct"]) for row in rows
]
lidar = [
    float(row["LiDARCoveragePct"]) for row in rows
]
radar = [
    float(row["RadarCoveragePct"]) for row in rows
]

x = np.arange(len(rows))
width = 0.25

fig, ax = plt.subplots(figsize=(16, 7))

ax.bar(x - width, camera, width, label="Camera")
ax.bar(x, lidar, width, label="LiDAR")
ax.bar(x + width, radar, width, label="Radar")

ax.set_xlabel("GEMSTAR Recording Identifier")
ax.set_ylabel("Frames with Nonempty Sensor Payload (%)")
ax.set_title(
    "Task 15 — GEMSTAR Camera, LiDAR and Radar Payload Coverage"
)

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=65, ha="right")
ax.set_ylim(0, 110)

ax.legend()
ax.grid(axis="y", alpha=0.25)

fig.tight_layout()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT, dpi=200)
plt.close(fig)

print("Graph saved:", OUTPUT)
print("Recordings plotted:", len(rows))