
from pathlib import Path
import csv
from collections import Counter, defaultdict

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

DATA = (
    ROOT / "tests"
    / "Task_11_Final_Research"
    / "02_CSV_Data"
)

LIDAR = DATA / "task11_lidar_measurements.csv"
GT = DATA / "task11_groundtruth_objects.csv"

OUTPUT = DATA / "task11_vehicle_frame_candidates.csv"

# Ground Truth object IDs and classes are used only
# for choosing candidate frames, not for detection.

gt_objects = defaultdict(list)

with GT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        frame = int(row["frame"])

        if "Car" in row["model_reference"] or \
           "Truck" in row["model_reference"] or \
           "Bus" in row["model_reference"]:

            gt_objects[frame].append(row)

# Count reflections per simulator object ID and frame.
counts = defaultdict(Counter)

with LIDAR.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        frame = int(row["frame"])
        object_id = row["object_id_diagnostic"]

        if object_id:
            counts[frame][object_id] += 1

rows = []

for frame, objects in gt_objects.items():
    for obj in objects:

        object_id = obj["object_id"]

        rows.append([
            frame,
            object_id,
            obj["model_reference"],
            counts[frame].get(object_id, 0),
            obj["x_m"],
            obj["y_m"]
        ])

rows.sort(key=lambda r: int(r[3]), reverse=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "frame",
        "gt_object_id",
        "vehicle_type",
        "lidar_reflections_matching_gt_id",
        "gt_x_m",
        "gt_y_m"
    ])

    writer.writerows(rows)

print("TASK 11.5H - VEHICLE FRAME SEARCH")
print("\nTop 15 candidates:")

for row in rows[:15]:
    print(
        f"Frame {row[0]} | "
        f"GT ID {row[1]} | "
        f"{row[2]} | "
        f"LiDAR reflections {row[3]}"
    )

print("\nSaved:", OUTPUT)
print("TASK 11.5H COMPLETED")
