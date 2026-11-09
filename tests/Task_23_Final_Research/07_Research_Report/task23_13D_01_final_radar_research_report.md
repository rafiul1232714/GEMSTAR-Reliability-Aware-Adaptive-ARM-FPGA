# Task 23.13 — Radar OSI Range Serialization Readiness

Generated: 2026-11-06T01:07:13

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
20261103T164111Z_sv_380_X_1352_GEMSTARADAR.osi

Displaced candidate:
20261103T181207Z_sv_380_X_1062_GEMSTARADAR.osi

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

| Ray | Baseline geometry (m) | Baseline OSI (m) | Displaced geometry (m) | Displaced OSI (m) | Change error (mm) | Result |
|---|---:|---:|---:|---:|---:|---|
| 44 | 8.534070 | 8.536549 | 10.542090 | 10.545149 | 0.579953 | PASS |
| 45 | 8.534070 | 8.536549 | 10.542090 | 10.545149 | 0.579953 | PASS |
| 54 | 8.534070 | 8.536549 | 10.542090 | 10.545149 | 0.579953 | PASS |
| 55 | 8.534070 | 8.536549 | 10.542090 | 10.545149 | 0.579953 | PASS |

Maximum absolute displacement difference: 0.579953 mm.

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
