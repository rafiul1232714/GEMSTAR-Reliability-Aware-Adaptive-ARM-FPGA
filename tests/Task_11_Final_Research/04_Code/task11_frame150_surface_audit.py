
# TASK 11.5V - FRAME 150 SURFACE AUDIT
# Research diagnostic, not an object detector.

import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"
DATA = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

SOURCE = DATA / "task11_lidar_frame150_geometry.csv"
OUTPUT = DATA / "task11_frame150_surface_audit.csv"
REPORT = FINDINGS / "task11_frame150_surface_audit.txt"

TARGET_X = 5.48
TARGET_Y = 2.18
WINDOW_X = 2.5
WINDOW_Y = 2.0

groups = defaultdict(list)

with SOURCE.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        obj = row["object_id_diagnostic"]

        groups[obj].append({
            "x": float(row["x_ego_m"]),
            "y": float(row["y_ego_m"]),
            "z": float(row["z_ego_m"]),
            "r": float(row["range_m"])
        })

results = []

for obj, points in groups.items():

    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    zs = [p["z"] for p in points]

    positive = sum(
        abs(p["x"] - TARGET_X) <= WINDOW_X
        and abs(p["y"] - TARGET_Y) <= WINDOW_Y
        for p in points
    )

    negative = sum(
        abs(p["x"] - TARGET_X) <= WINDOW_X
        and abs(p["y"] + TARGET_Y) <= WINDOW_Y
        for p in points
    )

    results.append({
        "diagnostic_id": obj,
        "total_points": len(points),
        "positive_y_count": positive,
        "negative_y_count": negative,
        "mean_x": sum(xs) / len(xs),
        "mean_y": sum(ys) / len(ys),
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
        "min_range": min(p["r"] for p in points)
    })

results.sort(
    key=lambda x: x["total_points"],
    reverse=True
)

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

lines = [
    "TASK 11.5V - FRAME 150 SURFACE AUDIT",
    "Ground Truth target: vehicle 76865",
    "Target coordinates are provisional.",
    "",
    "SIMULATOR SURFACE GROUPS",
    ""
]

for r in results:
    lines.append(
        f"ID {r['diagnostic_id']} | "
        f"Points {r['total_points']} | "
        f"+Y window {r['positive_y_count']} | "
        f"-Y window {r['negative_y_count']} | "
        f"X [{r['min_x']:.2f}, {r['max_x']:.2f}] | "
        f"Y [{r['min_y']:.2f}, {r['max_y']:.2f}] | "
        f"Z [{r['min_z']:.2f}, {r['max_z']:.2f}] | "
        f"MinRange {r['min_range']:.2f}"
    )

lines.extend([
    "",
    "Interpretation:",
    "These groups are simulator diagnostic IDs.",
    "They are not predicted vehicle labels.",
    "Bounding ranges and counts are not proof of alignment.",
    "Coordinate conventions require independent validation."
])

report = "\n".join(lines)

print("\n" + report)
REPORT.write_text(report + "\n", encoding="utf-8")

print("\nSaved:", OUTPUT)
print("Saved:", REPORT)
print("TASK 11.5V COMPLETED")
