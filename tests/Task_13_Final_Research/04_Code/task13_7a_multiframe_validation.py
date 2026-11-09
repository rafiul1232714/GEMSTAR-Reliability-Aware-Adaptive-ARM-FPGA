
# TASK 13.7A - MULTI-FRAME SENSOR VALIDATION
# MOR100 recording: 466 frames
# Read-only input; results stored separately in Task 13.

from pathlib import Path
from collections import defaultdict
import csv
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
SRC = ROOT / "tests" / "Task_11_Final_Research" / "02_CSV_Data"
OUT = ROOT / "tests" / "Task_13_Final_Research" / "02_CSV_Data"
OUT.mkdir(parents=True, exist_ok=True)

TARGET_ID = "76865"
MIN_RANGE = 0.1

FILES = {
    "lidar": SRC / "task11_lidar_measurements.csv",
    "radar": SRC / "task11_radar_measurements.csv",
    "gt": SRC / "task11_groundtruth_objects.csv",
}

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)

counts = defaultdict(lambda: {
    "lidar_valid": 0,
    "radar_valid": 0,
    "gt_objects": 0,
    "target_present": False,
    "time_s": None
})

for row in read_csv(FILES["lidar"]):
    frame = int(row["frame"])
    counts[frame]["time_s"] = float(row["time_s"])

    if (
        float(row["range_m"]) > MIN_RANGE
        and float(row["signal_strength"]) > 0
    ):
        counts[frame]["lidar_valid"] += 1

for row in read_csv(FILES["radar"]):
    frame = int(row["frame"])

    if counts[frame]["time_s"] is None:
        counts[frame]["time_s"] = float(row["time_s"])

    if (
        float(row["range_m"]) > MIN_RANGE
        and float(row["signal_strength"]) > 0
    ):
        counts[frame]["radar_valid"] += 1

for row in read_csv(FILES["gt"]):
    frame = int(row["frame"])
    counts[frame]["gt_objects"] += 1

    if row["object_id"].strip() == TARGET_ID:
        counts[frame]["target_present"] = True

rows = []

for frame, data in sorted(counts.items()):
    rows.append({
        "frame": frame,
        "time_s": data["time_s"],
        "lidar_valid": data["lidar_valid"],
        "radar_valid": data["radar_valid"],
        "gt_objects": data["gt_objects"],
        "target_present": int(data["target_present"]),
    })

if not rows:
    raise RuntimeError("No frames were loaded.")

output = OUT / "task13_7a_multiframe_sensor_summary.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

lidar_counts = [r["lidar_valid"] for r in rows]
radar_counts = [r["radar_valid"] for r in rows]
target_frames = [
    r["frame"] for r in rows if r["target_present"]
]

print("\n===== TASK 13.7A - MULTI-FRAME VALIDATION =====")
print("Total frames:", len(rows))
print("First frame:", rows[0]["frame"])
print("Last frame:", rows[-1]["frame"])
print("Target GT ID:", TARGET_ID)
print("Frames containing target:", len(target_frames))

if target_frames:
    print(
        "Target first/last recorded frame:",
        min(target_frames), max(target_frames)
    )

print("\nLiDAR valid reflections per frame:")
print("  Minimum:", min(lidar_counts))
print("  Median:", statistics.median(lidar_counts))
print("  Maximum:", max(lidar_counts))

print("\nRadar valid candidates per frame:")
print("  Minimum:", min(radar_counts))
print("  Median:", statistics.median(radar_counts))
print("  Maximum:", max(radar_counts))

print("\nSelected frames:")
for r in rows:
    if r["frame"] in (1, 100, 150, 200, 300, 466):
        print(
            f"Frame {r['frame']}: "
            f"t={r['time_s']:.3f}s, "
            f"LiDAR={r['lidar_valid']}, "
            f"Radar={r['radar_valid']}, "
            f"GT objects={r['gt_objects']}, "
            f"target={bool(r['target_present'])}"
        )

print("\nSaved:", output)
print("TASK 13.7A COMPLETED")
