import csv
import hashlib
import math
from pathlib import Path
from datetime import datetime

ROOT = Path(r"E:\GEMSTAR_Project")
TASK = ROOT / "sensor-health-monitor" / "tests" / "Task_23_Final_Research"
OUTPUT = ROOT / "gemstar" / "Output"

REPORT = TASK / "07_Research_Report" / (
    "task23_13D_01_final_radar_research_report.md"
)

MANIFEST = TASK / "05_Raw_Data_References" / (
    "task23_13D_01_radar_evidence_manifest.csv"
)

COMPARISON = TASK / "02_CSV_Data" / (
    "task23_13B_03_radar_serialization_comparison.csv"
)

ROBUSTNESS = TASK / "02_CSV_Data" / (
    "task23_13C_01_radar_robustness_tests.csv"
)

SAMPLES = TASK / "02_CSV_Data" / (
    "task23_13B_02_radar_calibration_ranges.csv"
)

GEOMETRY = TASK / "02_CSV_Data" / (
    "task23_07as_radar_displacement_final.csv"
)

PLOT = TASK / "03_Graphs" / (
    "task23_13C_02_radar_serialization_comparison.png"
)

if REPORT.exists() or MANIFEST.exists():
    raise RuntimeError("Final report or manifest already exists")

required = [COMPARISON, ROBUSTNESS, SAMPLES, GEOMETRY, PLOT]

with COMPARISON.open(newline="", encoding="utf-8-sig") as f:
    comparisons = list(csv.DictReader(f))

with ROBUSTNESS.open(newline="", encoding="utf-8-sig") as f:
    tests = list(csv.DictReader(f))

with SAMPLES.open(newline="", encoding="utf-8-sig") as f:
    samples = list(csv.DictReader(f))

if len(comparisons) != 4:
    raise RuntimeError("Expected four Radar comparison rows")

if sorted(int(r["Ray"]) for r in comparisons) != [44, 45, 54, 55]:
    raise RuntimeError("Incorrect Radar ray indices")

if any(r["Result"] != "PASS" for r in comparisons):
    raise RuntimeError("Failed Radar comparison detected")

if len(tests) != 12 or any(r["Result"] != "PASS" for r in tests):
    raise RuntimeError("Radar robustness acceptance failed")

if len(samples) != 80:
    raise RuntimeError("Expected 80 sampled Radar reflections")

if any(r["PositiveReturn"] != "True" for r in samples):
    raise RuntimeError("Non-positive return in calibration sample")

raw_names = [
    "20261103T164111Z_sv_380_X_1352_GEMSTARADAR.osi",
    "20261103T164111Z_gt_380_X_1352_GEMSTARADAR.osi",
    "20261103T181207Z_sv_380_X_1062_GEMSTARADAR.osi",
    "20261103T181207Z_gt_380_X_1062_GEMSTARADAR.osi",
]

raw_files = [OUTPUT / name for name in raw_names]
required.extend(raw_files)

logs = [
    TASK / "05_Raw_Data_References" / "task23_07aq_instrumented_runtime.log",
    TASK / "05_Raw_Data_References" / "task23_07ar_final_runtime.log",
]

required.extend(logs)

code_files = sorted((TASK / "01_Code").glob("task23_13*.py"))
required.extend(code_files)

if len(code_files) < 4:
    raise RuntimeError("Missing Task 23.13 Python scripts")

for path in required:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Missing or empty evidence: {path}")

comparison_lines = [
    "| Ray | Baseline geometry (m) | Baseline OSI (m) | "
    "Displaced geometry (m) | Displaced OSI (m) | "
    "Change error (mm) | Result |",
    "|---|---:|---:|---:|---:|---:|---|",
]

for r in sorted(comparisons, key=lambda x: int(x["Ray"])):
    error_mm = float(r["ChangeErrorM"]) * 1000
    if not math.isfinite(error_mm) or abs(error_mm) > 2.0:
        raise RuntimeError("Invalid displacement comparison")

    comparison_lines.append(
        f'| {r["Ray"]} | '
        f'{float(r["BaselineGeometryM"]):.6f} | '
        f'{float(r["BaselineOSIM"]):.6f} | '
        f'{float(r["DisplacedGeometryM"]):.6f} | '
        f'{float(r["DisplacedOSIM"]):.6f} | '
        f'{error_mm:.6f} | {r["Result"]} |'
    )

max_error_mm = max(
    abs(float(r["ChangeErrorM"]) * 1000)
    for r in comparisons
)

report = f"""# Task 23.13 — Radar OSI Range Serialization Readiness

Generated: {datetime.now().isoformat(timespec='seconds')}

## 1. Objective

Validate that controlled target-distance changes measured by the
GEMSTAR Radar simulation are preserved in recorded OSI Radar reflections
and recoverable using Python time-of-flight decoding.

This is a static simulator validation, not physical Radar calibration.

## 2. Experimental setup

- Research scene: GEMSTAR static Radar calibration arena
- Radar origin: (1940, -2650, 250) cm
- Radar orientation: (0, 0, 0) degrees
- Calibration target: 300 cm cube
- Baseline cube center X: 2940 cm
- Displaced cube center X: 3140 cm
- Cube displacement: 200 cm
- Diagnostic Radar rays: 44, 45, 54, 55

Prior independent geometric calibration:
02_CSV_Data/task23_07as_radar_displacement_final.csv

## 3. Source recordings

Baseline candidate:
{raw_names[0]}

Displaced candidate:
{raw_names[2]}

The runs were associated with their calibration conditions by
runtime timestamps and measured ray distances.

Both recordings were decoded read-only.
Their corresponding GroundTruth files were retained as evidence.
GroundTruth objects were not used to establish detection accuracy.

## 4. OSI decoding method

- Parse four-byte little-endian length-prefixed OSI SensorView messages
- Access radar_sensor_view[0].reflection
- Inspect rays 44, 45, 54 and 55
- Require finite, positive time_of_flight and signal_strength
- Compute range using R = 299792458 * TOF / 2 (meters)
- Inspect the first 10 frames of both recordings

Total inspected: 80 positive Radar reflection samples.

The complete recordings were not exhaustively decoded in this subtask.

## 5. Geometric versus OSI comparison

{chr(10).join(comparison_lines)}

Maximum absolute displacement difference: {max_error_mm:.6f} mm.

Independent geometric displacement: 2.008020 m.
Decoded OSI displacement: approximately 2.008600 m.

The difference was below the preselected diagnostic
displacement tolerance of 2 mm.

Absolute range differences were checked against a 10 mm
diagnostic tolerance.

These tolerances are experiment acceptance criteria,
not manufacturer Radar accuracy specifications.

## 6. Robustness validation

12 standalone Radar preprocessing tests completed; all passed.

Valid cases:
- Baseline TOF and signal strength
- Displaced TOF and signal strength

Invalid cases:
- Zero and negative TOF
- Zero and negative signal strength
- NaN and infinite values
- Missing TOF
- String and Boolean TOF

The test function raises an exception on invalid inputs.
Integration into scheduler sensor-health status handling
remains future work.

## 7. Research visualization

03_Graphs/task23_13C_02_radar_serialization_comparison.png

The figure compares measured geometric and OSI ranges and
shows displacement differences for all four rays.

## 8. Scientific interpretation

PASS: Controlled Radar geometric displacement previously verified.

PASS: Positive Radar reflections recovered from both OSI recordings.

PASS: Time-of-flight values decode to plausible metric ranges.

PASS: All four rays satisfy geometric-versus-OSI diagnostic tolerances.

PASS: 12 standalone invalid-input robustness tests.

The results support correct Radar range serialization for this
specific controlled, static scene and sampled frame window.

## 9. Limitations

1. The validation uses simulated Radar, not physical hardware.
2. The target is a static idealized calibration cube.
3. Only four central rays and the first ten frames per recording
   were examined for this comparison.
4. Repeated equal returns are not independent dynamic trials.
5. The small absolute range offset has not been fully explained.
6. No physical noise, occlusion, clutter, multipath, or detection
   probability measurements were established.
7. No traffic-scene object association or tracking was validated.
8. No ARM-FPGA power consumption, energy, or p99 latency was measured.
9. OSI GroundTruth files were archived as references, not used to
   assert detection correctness.

## 10. Relation to thesis objective

Task 23.13 establishes an OSI Radar-range decoding baseline for the
future CPU/FPGA preprocessing and reliability-aware fusion pipeline.

Task 23.14 will address cross-sensor coordinate frames and timestamps.
Task 23.15 will define unified Camera/LiDAR/Radar preprocessing.
Task 23.16 will consolidate final Task 23 acceptance evidence.

Full dynamic-object fusion and EKF tracking belong to Task 24.

## 11. Evidence archive

- 01_Code: decoding, comparison, robustness and plotting scripts
- 02_CSV_Data: per-ray and sampled measurements
- 03_Graphs: Radar serialization comparison PNG
- 05_Raw_Data_References: original logs and OSI references
- 06_Research_Findings: prior geometric calibration evidence
- 07_Research_Report: this report

A separate manifest records evidence paths, file sizes and SHA-256 hashes.
Original raw OSI files are not copied or modified.

## 12. Conclusion

Task 23.13 completed within its stated static Radar
serialization-readiness scope, subject to the limitations above.
"""

with REPORT.open("x", encoding="utf-8") as f:
    f.write(report)

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

evidence_paths = list(dict.fromkeys(required + [REPORT]))

records = []

for path in evidence_paths:
    records.append({
        "Category": "RAW_OSI" if path in raw_files else "RESEARCH",
        "FileName": path.name,
        "FullPath": str(path),
        "SizeBytes": path.stat().st_size,
        "SHA256": sha256_file(path),
    })

with MANIFEST.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)

if REPORT.stat().st_size < 3000:
    raise RuntimeError("Report unexpectedly short")

print(f"REPORT_SAVED={REPORT}")
print(f"REPORT_BYTES={REPORT.stat().st_size}")
print(f"MANIFEST_SAVED={MANIFEST}")
print(f"EVIDENCE_FILES={len(records)}")
print(f"RAW_OSI_FILES={len(raw_files)}")
print(f"RADAR_RAYS_PASSED={len(comparisons)}")
print(f"ROBUSTNESS_TESTS_PASSED={len(tests)}")
print(f"MAX_DISPLACEMENT_ERROR_MM={max_error_mm:.6f}")
print("TASK23_13D_01_FINAL_RADAR_RESEARCH_PASS")
