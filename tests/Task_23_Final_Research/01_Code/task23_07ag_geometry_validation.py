import csv
import math
from pathlib import Path
from collections import defaultdict

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

input_csv = TASK / "02_CSV_Data" / "task23_07af_radar_range_measurements.csv"
output_csv = TASK / "02_CSV_Data" / "task23_07ag_geometric_comparison.csv"
report_file = TASK / "06_Research_Findings" / "task23_07ag_radar_geometry_report.txt"

# Assumed geometry from the calibration configuration.
# All coordinates are in metres.
radar_origin = (19.4, -26.5, 2.5)
cube_center = (29.4, -26.5, 2.5)
cube_half_size = 1.5

box_min = tuple(c - cube_half_size for c in cube_center)
box_max = tuple(c + cube_half_size for c in cube_center)

def ray_box_distance(origin, direction, low, high):
    t_near = -float("inf")
    t_far = float("inf")

    for i in range(3):
        o = origin[i]
        d = direction[i]

        if abs(d) < 1e-12:
            if o < low[i] or o > high[i]:
                return None
            continue

        a = (low[i] - o) / d
        b = (high[i] - o) / d

        t_near = max(t_near, min(a, b))
        t_far = min(t_far, max(a, b))

        if t_near > t_far:
            return None

    if t_far < 0:
        return None

    return max(0.0, t_near)

if not input_csv.exists():
    raise FileNotFoundError(input_csv)

results = []
errors = []
by_ray = defaultdict(list)
frames = set()

with input_csv.open(newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        az = float(row["Azimuth_rad"])
        el = float(row["Elevation_rad"])
        measured = float(row["Range_m"])

        # Unit direction in Unreal's assumed +X-forward frame.
        direction = (
            math.cos(el) * math.cos(az),
            math.cos(el) * math.sin(az),
            math.sin(el)
        )

        expected = ray_box_distance(
            radar_origin, direction, box_min, box_max
        )

        if expected is None:
            continue

        if measured <= 0:
            continue

        range_difference = measured - expected

        results.append({
            "Frame": row["Frame"],
            "RayIndex": row["RayIndex"],
            "MeasuredRange_m": f"{measured:.8f}",
            "ExpectedCubeIntersection_m": f"{expected:.8f}",
            "Difference_m": f"{range_difference:.8f}",
            "AbsoluteDifference_m": f"{abs(range_difference):.8f}"
        })

        frames.add(row["Frame"])
        errors.append(abs(range_difference))
        by_ray[row["RayIndex"]].append(range_difference)

if not results:
    raise RuntimeError(
        "No valid ray-to-cube comparison records found."
    )

output_csv.parent.mkdir(parents=True, exist_ok=True)
report_file.parent.mkdir(parents=True, exist_ok=True)

with output_csv.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

mae = sum(errors) / len(errors)
max_error = max(errors)

lines = [
    "TASK 23.7AG - RADAR GEOMETRIC COMPARISON",
    f"Compared records: {len(results)}",
    f"Unique frames: {len(frames)}",
    f"Mean absolute difference (m): {mae:.8f}",
    f"Maximum absolute difference (m): {max_error:.8f}",
    "",
    "PER-RAY RESULTS:"
]

for ray_id, values in sorted(by_ray.items(), key=lambda x: int(x[0])):
    mean_diff = sum(values) / len(values)
    lines.append(
        f"Ray {ray_id}: samples={len(values)}, "
        f"mean difference={mean_diff:.8f} m"
    )

lines += [
    "",
    "ASSUMPTIONS:",
    "Radar world origin: (19.4,-26.5,2.5) m",
    "Radar orientation: +X forward, zero rotation",
    "Cube center: (29.4,-26.5,2.5) m",
    "Cube dimensions: 3 x 3 x 3 m",
    "Cube is axis-aligned.",
    "No occluding geometry is present.",
    "",
    "STATUS: CONDITIONAL_GEOMETRY_CONSISTENCY",
    "This is not independent sensor accuracy validation.",
    "Radar runtime pose and hit actor identity remain unverified.",
    "Repeated frames are not independent trials."
]

report_file.write_text("\n".join(lines), encoding="utf-8")

print("\n=== TASK 23.7AG — CORRECTED GEOMETRIC COMPARISON ===")
print("Compared records:", len(results))
print("Unique frames:", len(frames))
print(f"Mean absolute difference: {mae:.8f} m")
print(f"Maximum absolute difference: {max_error:.8f} m")

for line in lines[6:]:
    if line.startswith("Ray "):
        print(line)

print("\nCSV saved:", output_csv)
print("Report saved:", report_file)
print("STATUS: CONDITIONAL_GEOMETRY_CONSISTENCY")
