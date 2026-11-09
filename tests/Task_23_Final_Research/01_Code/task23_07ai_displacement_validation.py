from pathlib import Path
from statistics import median
import struct
import csv
import math

from osi3 import osi_sensorview_pb2

TASK = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")
OUTPUT = Path(r"E:\GEMSTAR_Project\gemstar\Output")

BASELINE = OUTPUT / "20261103T155916Z_sv_380_X_2393_GEMSTARADAR.osi"
DISPLACED = OUTPUT / "20261103T161227Z_sv_380_X_2168_GEMSTARADAR.osi"

RAYS = (44, 45, 54, 55)
C = 299792458.0

def read_radar(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    results = {ray: [] for ray in RAYS}
    timestamps = []
    frames = 0
    views = set()
    config_signatures = set()

    with path.open("rb") as f:
        while True:
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError(f"Incomplete header in {path.name}")

            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid message size")

            payload = f.read(size)
            if len(payload) != size:
                raise ValueError(f"Truncated message in {path.name}")

            msg = osi_sensorview_pb2.SensorView()
            msg.ParseFromString(payload)
            frames += 1

            timestamps.append(
                msg.timestamp.seconds + msg.timestamp.nanos * 1e-9
            )

            views.add(len(msg.radar_sensor_view))

            if len(msg.radar_sensor_view) != 1:
                raise ValueError(
                    f"Frame {frames}: expected one Radar view, "
                    f"found {len(msg.radar_sensor_view)}"
                )

            radar = msg.radar_sensor_view[0]
            config_signatures.add(
                radar.view_configuration.SerializeToString()
            )

            for ray in RAYS:
                if ray >= len(radar.reflection):
                    raise ValueError(f"Missing ray {ray}")

                r = radar.reflection[ray]
                distance = C * r.time_of_flight / 2.0

                if not math.isfinite(distance) or distance <= 0:
                    continue

                results[ray].append((
                    distance,
                    r.source_horizontal_angle,
                    r.source_vertical_angle
                ))

    if frames == 0:
        raise ValueError(f"No frames: {path}")

    if len(config_signatures) != 1:
        raise ValueError(
            f"Configuration changed during {path.name}"
        )

    return frames, results, timestamps, config_signatures.pop()

print("\n=== TASK 23.7AI — RADAR DISPLACEMENT VALIDATION ===")

n_a, baseline, t_a, config_a = read_radar(BASELINE)
n_b, moved, t_b, config_b = read_radar(DISPLACED)

print("Baseline frames:", n_a)
print("Displaced frames:", n_b)
print("Configurations identical:", config_a == config_b)

if config_a != config_b:
    raise ValueError("Radar configurations differ between recordings")

rows = []

for ray in RAYS:
    a = baseline[ray]
    b = moved[ray]

    if not a or not b:
        raise ValueError(f"No valid samples for ray {ray}")

    a_range = median(x[0] for x in a)
    b_range = median(x[0] for x in b)

    az_a = median(x[1] for x in a)
    el_a = median(x[2] for x in a)
    az_b = median(x[1] for x in b)
    el_b = median(x[2] for x in b)

    if abs(az_a - az_b) > 1e-5 or abs(el_a - el_b) > 1e-5:
        raise ValueError(f"Beam angles changed for ray {ray}")

    # Assumes the Radar stayed at the same pose,
    # the cube moved +2 m along world +X,
    # and both returns came from the cube's front face.
    expected_change = 2.0 / (
        math.cos(az_a) * math.cos(el_a)
    )

    measured_change = b_range - a_range
    difference = measured_change - expected_change

    rows.append({
        "Ray": ray,
        "BaselineSamples": len(a),
        "MovedSamples": len(b),
        "BaselineRange_m": a_range,
        "MovedRange_m": b_range,
        "MeasuredChange_m": measured_change,
        "ExpectedChange_m": expected_change,
        "Difference_m": difference,
        "AbsoluteDifference_m": abs(difference)
    })

csv_path = TASK / "02_CSV_Data" / "task23_07ai_displacement_comparison.csv"
report_path = TASK / "06_Research_Findings" / "task23_07ai_displacement_report.txt"

csv_path.parent.mkdir(parents=True, exist_ok=True)
report_path.parent.mkdir(parents=True, exist_ok=True)

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

mean_abs = sum(x["AbsoluteDifference_m"] for x in rows) / len(rows)
max_abs = max(x["AbsoluteDifference_m"] for x in rows)

lines = [
    "TASK 23.7AI - RADAR DISPLACEMENT VALIDATION",
    f"Baseline frames: {n_a}",
    f"Displaced frames: {n_b}",
    f"Radar configurations identical: {config_a == config_b}",
    f"Mean absolute displacement residual (m): {mean_abs:.8f}",
    f"Maximum displacement residual (m): {max_abs:.8f}",
    "",
    "PER-RAY RESULTS:"
]

for row in rows:
    line = (
        f"Ray {row['Ray']}: "
        f"baseline={row['BaselineRange_m']:.5f} m, "
        f"moved={row['MovedRange_m']:.5f} m, "
        f"observed change={row['MeasuredChange_m']:.5f} m, "
        f"expected change={row['ExpectedChange_m']:.5f} m, "
        f"residual={row['Difference_m']:.6f} m"
    )
    lines.append(line)
    print(line)

lines.extend([
    "",
    "STATUS: DISPLACEMENT_COMPARISON_COMPLETE",
    "Interpretation is conditional on an unchanged verified Radar pose",
    "and both sets of rays intersecting the intended cube.",
    "GroundTruth identity and independent hit-object confirmation pending.",
    "Deterministic frames are not independent experiments."
])

report_path.write_text("\n".join(lines), encoding="utf-8")

print("\nMean absolute displacement residual:",
      f"{mean_abs:.8f} m")
print("Maximum displacement residual:",
      f"{max_abs:.8f} m")
print("CSV saved:", csv_path)
print("Report saved:", report_path)
print("STATUS: DISPLACEMENT_COMPARISON_COMPLETE")
