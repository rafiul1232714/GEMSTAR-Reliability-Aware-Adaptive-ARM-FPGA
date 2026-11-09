from pathlib import Path
import struct
import csv
import statistics
from osi3 import osi_sensorview_pb2

task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")
output = Path(r"E:\GEMSTAR_Project\gemstar\Output")

baseline = output / "20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi"
displaced = output / "20261103T191205Z_sv_380_X_604_GEMSTARLIDARDISPLACED23.osi"

csv_file = task / "02_CSV_Data/task23_08_lidar_displacement_rays.csv"
report = task / "06_Research_Findings/task23_08_lidar_displacement_validation.txt"
graph = task / "03_Graphs/task23_08_lidar_displacement.svg"

C = 299792458.0
FRAME_LIMIT = 10

# Known cube front-face axial distances, measured in metres.
BASE_X = 8.50
MOVED_X = 10.50
RATIO = MOVED_X / BASE_X

def load_recording(path):
    if not path.exists():
        raise FileNotFoundError(path)

    frames = []

    with path.open("rb") as stream:
        for index in range(FRAME_LIMIT):
            header = stream.read(4)
            if len(header) != 4:
                raise RuntimeError(
                    f"Missing frame {index+1}: {path.name}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size < 100_000_000:
                raise RuntimeError("Invalid OSI frame length")

            data = stream.read(size)

            if len(data) != size:
                raise RuntimeError("Truncated OSI payload")

            sensor = osi_sensorview_pb2.SensorView()
            sensor.ParseFromString(data)

            if len(sensor.lidar_sensor_view) != 1:
                raise RuntimeError(
                    f"Expected one LiDAR view in frame {index+1}"
                )

            reflections = sensor.lidar_sensor_view[0].reflection

            distances = [
                C * r.time_of_flight / 2.0
                for r in reflections
            ]

            frames.append(distances)

    return frames

print("\n=== TASK 23.8 — LIDAR DISPLACEMENT VALIDATION ===")

a = load_recording(baseline)
b = load_recording(displaced)

ray_count = len(a[0])

if not all(len(frame) == ray_count for frame in a+b):
    raise RuntimeError("Inconsistent LiDAR ray counts")

print(f"Baseline frames: {len(a)}")
print(f"Displaced frames: {len(b)}")
print(f"Rays per frame: {ray_count}")

rows = []
candidates = []
matched = []

for ray in range(ray_count):
    baseline_values = [frame[ray] for frame in a]
    displaced_values = [frame[ray] for frame in b]

    baseline_m = statistics.median(baseline_values)
    displaced_m = statistics.median(displaced_values)

    # Initial selection uses baseline geometry only.
    # These are candidate cube-front-face rays, not
    # independently verified actor identities.
    candidate = 8.48 <= baseline_m <= 8.85

    valid = (
        0 < baseline_m <= 50 and
        0 < displaced_m <= 50
    )

    change = displaced_m - baseline_m
    expected = baseline_m * RATIO
    error = displaced_m - expected

    # A 5 cm geometric tolerance is a test criterion,
    # not a claim about physical sensor accuracy.
    geometry_match = (
        candidate and valid and
        abs(error) <= 0.05
    )

    record = {
        "ray_index": ray,
        "baseline_m": round(baseline_m, 6),
        "displaced_m": round(displaced_m, 6),
        "change_m": round(change, 6),
        "expected_displaced_m": round(expected, 6),
        "geometry_error_m": round(error, 6),
        "candidate_front_face": int(candidate),
        "geometry_match": int(geometry_match),
    }

    rows.append(record)

    if candidate:
        candidates.append(record)

    if geometry_match:
        matched.append(record)

csv_file.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)
graph.parent.mkdir(parents=True, exist_ok=True)

with csv_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

if matched:
    changes = [r["change_m"] for r in matched]
    errors = [abs(r["geometry_error_m"]) for r in matched]

    median_change = statistics.median(changes)
    median_error = statistics.median(errors)
else:
    median_change = None
    median_error = None

print(f"Baseline geometric candidates: {len(candidates)}")
print(f"Matching displaced rays: {len(matched)}")

if median_change is not None:
    print(f"Median matched range increase: {median_change:.4f} m")
    print(f"Median absolute geometric error: {median_error:.4f} m")

# Require substantial matching evidence, rather than
# declaring success because a single ray happens to match.
pass_status = (
    len(candidates) >= 10 and
    len(matched) >= 10 and
    len(matched) / len(candidates) >= 0.70
)

status = (
    "LIDAR_DISPLACEMENT_PASS"
    if pass_status else
    "LIDAR_DISPLACEMENT_REQUIRES_INVESTIGATION"
)

print("\n=== SAMPLE MATCHING RAYS ===")

for r in matched[:12]:
    print(
        f"Ray {r['ray_index']}: "
        f"{r['baseline_m']:.4f} -> "
        f"{r['displaced_m']:.4f} m; "
        f"change={r['change_m']:.4f} m; "
        f"error={r['geometry_error_m']:.4f} m"
    )

if candidates:
    print("\n=== FIRST BASELINE CANDIDATES ===")
    for r in candidates[:8]:
        print(
            f"Ray {r['ray_index']}: "
            f"baseline={r['baseline_m']:.4f}, "
            f"displaced={r['displaced_m']:.4f}, "
            f"match={bool(r['geometry_match'])}"
        )

# Simple evidence graph using matching-ray medians.
if matched:
    base_median = statistics.median(
        r["baseline_m"] for r in matched
    )
    moved_median = statistics.median(
        r["displaced_m"] for r in matched
    )

    max_range = 13
    scale = 400 / max_range

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="680" height="290">',
        '<rect width="680" height="290" fill="white"/>',
        '<text x="25" y="32" font-size="20" font-family="Arial">LiDAR target displacement</text>',
        '<text x="25" y="57" font-size="13" font-family="Arial">Median of geometry-matching rays</text>'
    ]

    for label, value, y, color in [
        ("Baseline", base_median, 100, "#3378bb"),
        ("Displaced", moved_median, 170, "#26976f")
    ]:
        bar_width = value * scale
        svg.append(
            f'<text x="25" y="{y+23}" font-size="14" font-family="Arial">{label}</text>'
        )
        svg.append(
            f'<rect x="145" y="{y}" width="{bar_width:.2f}" height="34" fill="{color}"/>'
        )
        svg.append(
            f'<text x="{155+bar_width:.2f}" y="{y+23}" font-size="14" font-family="Arial">{value:.4f} m</text>'
        )

    svg.append("</svg>")
    graph.write_text("\n".join(svg), encoding="utf-8")

lines = [
    "TASK 23.8 - LIDAR CONTROLLED DISPLACEMENT",
    f"Baseline OSI: {baseline}",
    f"Displaced OSI: {displaced}",
    f"Frames per condition: {FRAME_LIMIT}",
    f"Rays per frame: {ray_count}",
    f"Baseline candidates: {len(candidates)}",
    f"Matching displaced rays: {len(matched)}",
    f"Median range increase: {median_change}",
    f"Median absolute geometric error: {median_error}",
    f"Status: {status}",
    "",
    "Method:",
    "Compare median distance by identical ray index.",
    "Candidate selection is based on baseline geometry.",
    "Expected moved range = baseline range * (10.5 / 8.5).",
    "A matching ray has absolute range error <= 0.05 m.",
    "",
    "Limitations:",
    "Candidate ray identity is inferred from geometry.",
    "The two recordings are not time-synchronized.",
    "This validates controlled simulated range response only.",
    "It does not establish real-world LiDAR accuracy.",
    "",
    f"CSV: {csv_file}",
    f"Graph: {graph if matched else 'Not generated'}",
]

report.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n=== FINAL VALIDATION ===")
print(f"Status: {status}")
print(f"CSV: {csv_file}")
print(f"Report: {report}")

if matched:
    print(f"Graph: {graph}")
