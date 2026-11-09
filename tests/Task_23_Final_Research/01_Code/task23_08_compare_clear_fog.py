from pathlib import Path
import csv
import struct
import statistics
from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\gemstar\Output")
task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")

fog_file = root / "20261103T190206Z_sv_380_X_336_GEMSTARLIDAR23.osi"
clear_file = root / "20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi"

csv_path = task / "02_CSV_Data/task23_08_clear_fog_comparison.csv"
report_path = task / "06_Research_Findings/task23_08_clear_fog_comparison.txt"

C = 299792458.0
MAX_RANGE = 50.0
FRAMES = 10

def read_frames(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    results = []

    with path.open("rb") as stream:
        for index in range(FRAMES):
            header = stream.read(4)
            if not header:
                break
            if len(header) != 4:
                raise RuntimeError("Incomplete OSI frame header")

            size = struct.unpack("<I", header)[0]
            if size <= 0 or size > 100_000_000:
                raise RuntimeError("Invalid OSI frame size")

            payload = stream.read(size)
            if len(payload) != size:
                raise RuntimeError("Incomplete OSI payload")

            message = osi_sensorview_pb2.SensorView()
            message.ParseFromString(payload)

            if len(message.lidar_sensor_view) != 1:
                raise RuntimeError(
                    f"Frame {index+1}: expected one LiDAR SensorView"
                )

            reflections = message.lidar_sensor_view[0].reflection
            distances = [
                C * r.time_of_flight / 2.0
                for r in reflections
            ]
            results.append(distances)

    if len(results) != FRAMES:
        raise RuntimeError(
            f"Expected {FRAMES} frames, got {len(results)}"
        )

    return results

def valid(x):
    return 0 < x <= MAX_RANGE

fog = read_frames(fog_file)
clear = read_frames(clear_file)

rows = []
all_differences = []

for frame_no, (f, c) in enumerate(zip(fog, clear), 1):
    if len(f) != len(c):
        raise RuntimeError("Reflection count mismatch")

    fog_valid = [x for x in f if valid(x)]
    clear_valid = [x for x in c if valid(x)]

    paired = [
        (cv, fv)
        for cv, fv in zip(c, f)
        if valid(cv) and valid(fv)
    ]

    differences = [fv - cv for cv, fv in paired]
    all_differences.extend(differences)

    rows.append({
        "frame": frame_no,
        "total_rays": len(c),
        "clear_valid": len(clear_valid),
        "fog_valid": len(fog_valid),
        "clear_min_m": min(clear_valid) if clear_valid else "",
        "fog_min_m": min(fog_valid) if fog_valid else "",
        "clear_median_m": (
            statistics.median(clear_valid) if clear_valid else ""
        ),
        "fog_median_m": (
            statistics.median(fog_valid) if fog_valid else ""
        ),
        "paired_valid_rays": len(paired),
        "median_fog_minus_clear_m": (
            statistics.median(differences) if differences else ""
        )
    })

csv_path.parent.mkdir(parents=True, exist_ok=True)
report_path.parent.mkdir(parents=True, exist_ok=True)

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

clear_counts = [r["clear_valid"] for r in rows]
fog_counts = [r["fog_valid"] for r in rows]

lines = [
    "=== TASK 23.8 — CLEAR VS FOG LIDAR ===",
    f"Frames per recording: {FRAMES}",
    f"Reflections per frame: {rows[0]['total_rays']}",
    f"Clear valid rays/frame (mean): {statistics.mean(clear_counts):.1f}",
    f"Fog valid rays/frame (mean): {statistics.mean(fog_counts):.1f}",
    f"Clear minimum range/frame (mean): "
    f"{statistics.mean(r['clear_min_m'] for r in rows):.4f} m",
    f"Fog minimum range/frame (mean): "
    f"{statistics.mean(r['fog_min_m'] for r in rows):.4f} m",
    f"Paired valid reflections: {len(all_differences)}"
]

if all_differences:
    lines.append(
        "Median paired (fog - clear) range: "
        f"{statistics.median(all_differences):.6f} m"
    )

lines.extend([
    "",
    "Interpretation:",
    "This is a diagnostic comparison of independently recorded",
    "frames, matched by ray index, not timestamp-synchronized",
    "sensor observations. Geometry, validity, and weather model",
    "effects must be assessed before drawing causal conclusions.",
    "",
    f"CSV: {csv_path}",
    "Status: CLEAR_FOG_COMPARISON_GENERATED"
])

report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
