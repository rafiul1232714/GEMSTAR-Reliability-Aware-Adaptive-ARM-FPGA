
# TASK 11.5X - LIDAR RAY DIAGNOSTICS
# Examine repeated ranges, ray indices and surface IDs.
# No simulation rerun or external libraries required.

import csv
import math
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"
DATA = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

SOURCE = DATA / "task11_lidar_frame150_geometry.csv"

REPORT = FINDINGS / "task11_lidar_ray_diagnostics.txt"
OUTPUT = DATA / "task11_lidar_ray_diagnostics_frame150.csv"

H_RAYS = 251
V_RAYS = 21

points = []

with SOURCE.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):

        ray = int(row["ray_index"])

        points.append({
            "ray": ray,
            "h": ray % H_RAYS,
            "v": ray // H_RAYS,
            "range": float(row["range_m"]),
            "x": float(row["x_ego_m"]),
            "y": float(row["y_ego_m"]),
            "z": float(row["z_ego_m"]),
            "object_id": row["object_id_diagnostic"]
        })

ranges = [p["range"] for p in points]

# Group approximately equal range values.
rounded_ranges = Counter(round(r, 2) for r in ranges)

# Count returns at each vertical scan layer.
layers = defaultdict(list)

for p in points:
    layers[p["v"]].append(p)

lines = [
    "TASK 11.5X - LIDAR RAY DIAGNOSTICS",
    "Frame: 150",
    f"Valid points: {len(points)}",
    f"Unique ray indices: {len(set(p['ray'] for p in points))}",
    f"Minimum range: {min(ranges):.4f} m",
    f"Maximum range: {max(ranges):.4f} m",
    "",
    "MOST COMMON RANGES (rounded to 0.01 m)"
]

for value, count in rounded_ranges.most_common(15):
    lines.append(f"Range {value:.2f} m: {count} points")

lines.append("")
lines.append("VERTICAL LAYER ANALYSIS")

summary_rows = []

for layer in sorted(layers):

    pts = layers[layer]

    rmin = min(p["range"] for p in pts)
    rmax = max(p["range"] for p in pts)
    mean_z = sum(p["z"] for p in pts) / len(pts)

    object_counts = Counter(p["object_id"] for p in pts)
    most_common_id, most_common_count = object_counts.most_common(1)[0]

    lines.append(
        f"Layer {layer:2d}: "
        f"points={len(pts):3d}, "
        f"range=[{rmin:.2f},{rmax:.2f}] m, "
        f"mean Z={mean_z:.3f} m, "
        f"dominant ID={most_common_id} ({most_common_count})"
    )

    summary_rows.append({
        "vertical_layer": layer,
        "point_count": len(pts),
        "min_range_m": rmin,
        "max_range_m": rmax,
        "mean_z_m": mean_z,
        "dominant_object_id": most_common_id,
        "dominant_object_count": most_common_count
    })

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summary_rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(summary_rows)

lines.extend([
    "",
    "INTERPRETATION NOTES",
    "Repeated ranges can occur because many rays",
    "intersect a flat surface or shared geometry.",
    "This diagnostic alone cannot establish a simulator bug.",
    "Check ray-index ordering and the source implementation.",
    "Vehicle detection is not yet confirmed."
])

text = "\n".join(lines)

print("\n" + text)

REPORT.write_text(text + "\n", encoding="utf-8")

print("\nSaved:", OUTPUT)
print("Saved:", REPORT)
print("TASK 11.5X COMPLETED")
