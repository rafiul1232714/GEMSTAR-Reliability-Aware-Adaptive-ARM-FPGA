
import csv
import math
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"
DATA = ARCHIVE / "02_CSV_Data"

SOURCE = DATA / "task11_groundtruth_objects.csv"
OUTPUT = DATA / "task11_forward_vehicle_frames.csv"
SUMMARY = ARCHIVE / "06_Research_Findings" / "task11_forward_vehicle_search.txt"

EGO_ID = 76895

# Exploratory LiDAR coverage
MAX_RANGE_M = 20.0
HALF_FOV_RAD = math.radians(45)

frames = defaultdict(list)

with SOURCE.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        frames[int(row["frame"])].append(row)

results = []
checked_frames = 0

for frame, objects in sorted(frames.items()):

    ego_matches = [
        o for o in objects
        if int(o["object_id"]) == EGO_ID
    ]

    if len(ego_matches) != 1:
        continue

    checked_frames += 1
    ego = ego_matches[0]

    ex = float(ego["x_m"])
    ey = float(ego["y_m"])
    yaw = float(ego["yaw_rad"])

    for obj in objects:

        if int(obj["object_id"]) == EGO_ID:
            continue

        name = obj["model_reference"]

        # Exclude the follow camera.
        if not any(s in name for s in (
            "Car", "Truck", "Bus"
        )):
            continue

        dx = float(obj["x_m"]) - ex
        dy = float(obj["y_m"]) - ey

        x = math.cos(yaw)*dx + math.sin(yaw)*dy
        y = -math.sin(yaw)*dx + math.cos(yaw)*dy

        distance = math.hypot(x, y)

        # First-pass center-in-FOV test.
        # Does not account for object dimensions.
        if not (2.0 <= distance <= MAX_RANGE_M):
            continue

        if x <= 0:
            continue

        angle = math.atan2(y, x)

        if abs(angle) > HALF_FOV_RAD:
            continue

        results.append({
            "frame": frame,
            "gt_object_id": int(obj["object_id"]),
            "model_reference": name,
            "x_ego_m": round(x, 3),
            "y_ego_m": round(y, 3),
            "distance_m": round(distance, 3),
            "angle_deg": round(math.degrees(angle), 3)
        })

results.sort(key=lambda r: (
    r["distance_m"],
    r["frame"]
))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
SUMMARY.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "frame", "gt_object_id", "model_reference",
    "x_ego_m", "y_ego_m",
    "distance_m", "angle_deg"
]

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

lines = [
    "TASK 11.5S - FORWARD VEHICLE FRAME SEARCH",
    f"Frames checked: {checked_frames}",
    f"Candidate observations: {len(results)}",
    f"Frames with candidates: {len(set(r['frame'] for r in results))}",
    "Yaw/coordinate convention: provisional",
    "Candidate test: GT center inside approximate LiDAR FOV",
    "",
    "TOP 20 RESULTS"
]

for r in results[:20]:
    lines.append(
        f"Frame {r['frame']} | "
        f"GT {r['gt_object_id']} | "
        f"{r['model_reference']} | "
        f"X={r['x_ego_m']:.2f} m | "
        f"Y={r['y_ego_m']:.2f} m | "
        f"Distance={r['distance_m']:.2f} m | "
        f"Angle={r['angle_deg']:.1f} deg"
    )

text = "\n".join(lines)
print("\n" + text)

SUMMARY.write_text(text + "\n", encoding="utf-8")

print("\nSaved:", OUTPUT)
print("Saved:", SUMMARY)
print("TASK 11.5S COMPLETED")
