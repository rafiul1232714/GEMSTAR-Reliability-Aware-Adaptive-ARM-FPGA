import csv
import math
from collections import defaultdict
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

osi_csv = TASK / "02_CSV_Data" / (
    "task23_13B_02_radar_calibration_ranges.csv"
)

geometry_csv = TASK / "02_CSV_Data" / (
    "task23_07as_radar_displacement_final.csv"
)

output_csv = TASK / "02_CSV_Data" / (
    "task23_13B_03_radar_serialization_comparison.csv"
)

if output_csv.exists():
    raise RuntimeError("Output CSV already exists")

with osi_csv.open(newline="", encoding="utf-8-sig") as f:
    osi = list(csv.DictReader(f))

with geometry_csv.open(newline="", encoding="utf-8-sig") as f:
    geometry = list(csv.DictReader(f))

expected_rays = {44, 45, 54, 55}
expected_scenarios = {
    "BASELINE_CANDIDATE",
    "DISPLACED_CANDIDATE",
}

if len(osi) != 80:
    raise RuntimeError(f"Expected 80 OSI rows, got {len(osi)}")

if len(geometry) != 4:
    raise RuntimeError("Expected four geometric calibration rays")

groups = defaultdict(list)

for r in osi:
    scenario = r["Scenario"]
    ray = int(r["Ray"])
    frame = int(r["Frame"])

    if scenario not in expected_scenarios:
        raise RuntimeError(f"Unexpected scenario: {scenario}")

    if ray not in expected_rays or frame not in range(10):
        raise RuntimeError("Unexpected ray or frame")

    if r["PositiveReturn"] != "True":
        raise RuntimeError("Non-positive Radar return")

    distance = float(r["RangeM"])
    tof = float(r["TimeOfFlightS"])
    strength = float(r["SignalStrength"])

    if not all(math.isfinite(x) for x in (
        distance, tof, strength
    )):
        raise RuntimeError("Nonfinite Radar measurement")

    if distance <= 0 or tof <= 0 or strength <= 0:
        raise RuntimeError("Non-positive Radar measurement")

    recalculated = 299792458.0 * tof / 2.0

    if abs(recalculated - distance) > 1e-6:
        raise RuntimeError("OSI TOF-to-range inconsistency")

    groups[(scenario, ray)].append((frame, distance))

if len(groups) != 8:
    raise RuntimeError("Expected eight scenario/ray groups")

for key, values in groups.items():
    frames = sorted(frame for frame, _ in values)

    if frames != list(range(10)):
        raise RuntimeError(f"Incomplete frame set: {key}")

rows = []
failures = 0

print("\n=== RADAR SERIALIZATION COMPARISON ===")

for g in geometry:
    ray = int(g["ray"])

    if ray not in expected_rays:
        raise RuntimeError("Unexpected geometric ray")

    baseline_geometry = float(g["baseline_distance_cm"]) / 100
    displaced_geometry = float(g["displaced_distance_cm"]) / 100

    baseline_osi = sum(
        distance for _, distance
        in groups[("BASELINE_CANDIDATE", ray)]
    ) / 10

    displaced_osi = sum(
        distance for _, distance
        in groups[("DISPLACED_CANDIDATE", ray)]
    ) / 10

    geometric_change = displaced_geometry - baseline_geometry
    osi_change = displaced_osi - baseline_osi

    baseline_error = baseline_osi - baseline_geometry
    displaced_error = displaced_osi - displaced_geometry
    change_error = osi_change - geometric_change

    # Diagnostic tolerances for this static experiment.
    passed = (
        abs(baseline_error) <= 0.01
        and abs(displaced_error) <= 0.01
        and abs(change_error) <= 0.002
    )

    failures += int(not passed)

    rows.append({
        "Ray": ray,
        "BaselineGeometryM": baseline_geometry,
        "BaselineOSIM": baseline_osi,
        "BaselineErrorM": baseline_error,
        "DisplacedGeometryM": displaced_geometry,
        "DisplacedOSIM": displaced_osi,
        "DisplacedErrorM": displaced_error,
        "GeometryChangeM": geometric_change,
        "OSIChangeM": osi_change,
        "ChangeErrorM": change_error,
        "Result": "PASS" if passed else "FAIL",
    })

    print(
        f"RAY={ray} "
        f"GEOMETRY_CHANGE_M={geometric_change:.6f} "
        f"OSI_CHANGE_M={osi_change:.6f} "
        f"CHANGE_ERROR_MM={change_error * 1000:.4f} "
        f"RESULT={'PASS' if passed else 'FAIL'}"
    )

if len({r["Ray"] for r in rows}) != 4:
    raise RuntimeError("Duplicate or missing calibration rays")

with output_csv.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV_SAVED={output_csv}")
print(f"RAYS_TESTED={len(rows)}")
print(f"RAYS_PASSED={len(rows) - failures}")
print(f"RAYS_FAILED={failures}")

if failures:
    raise RuntimeError("Radar serialization comparison failed")

print("TASK23_13B_03_RADAR_SERIALIZATION_VALIDATION_PASS")
