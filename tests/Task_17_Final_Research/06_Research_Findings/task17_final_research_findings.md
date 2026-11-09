# TASK 17 — FINAL RESEARCH FINDINGS

## Research topic
GEMSTAR Camera–LiDAR–Radar Timestamp Synchronization
and Sensor Coordinate Validation

## 1. Research objective

Validate recorded-message timing, GroundTruth alignment,
sensor mounting stability and geometric transformation
consistency before implementing multi-sensor fusion.

## 2. Dataset

Recording:
20261027T224313Z_sv_380_X_466_GEMSTAR.osi

GroundTruth:
20261027T224313Z_gt_380_X_466_GEMSTAR.osi

Scenario folder: fog_mor100
Total SensorView frames: 466
Total GroundTruth frames: 466

Both files were verified against Task 15 SHA-256 records.

## 3. Timestamp synchronization

Compared frames: 466
Exact recorded timestamp matches: 466
Timestamp mismatches: 0
Maximum difference: 0 ms
Mean difference: 0 ms

Conclusion:
GroundTruth and SensorView message timestamps are exactly
aligned frame-by-frame in this recording.

Limitation:
This does not independently establish simultaneous acquisition
times for Camera, LiDAR and Radar.

## 4. Timing irregularities

Overall median interval: approximately 32.9931 ms
Long-interval investigation threshold: 65.9862 ms
Flagged intervals: 42

High-rate segment:
Frames 0–423
Frames: 424
Median interval: 32.8011 ms
Approximate rate: 30.487 Hz

Low-rate segment:
Frames 424–465
Frames: 42
Median interval: 333.3335 ms
Approximate rate: 3.000 Hz

First flagged interval:
Frame 424
Timestamp: approximately 14.371461 seconds

Conclusion:
The recording exhibits two distinct message-timing regimes.

The reason for this transition has not been established.
These recorded intervals are not measurements of CPU or FPGA
processing latency.

## 5. Sensor mounting positions

Camera: (0.7, 0, 1.6) m
LiDAR: (2.6, 0, 0.7) m
Radar: (2.0, 0, 0.8) m

Camera–LiDAR distance: 2.1024 m
Camera–Radar distance: 1.5264 m
LiDAR–Radar distance: 0.6083 m

All three configurations were stable across all 466
SensorView messages.

## 6. GEMSTAR configuration comparison

Current DefaultGemstar.ini:

Camera: (70, 0, 160) cm
LiDAR: (260, 0, 70) cm
Radar: (200, 0, 80) cm

All three positions agree numerically with the selected
OSI recording after centimeters-to-meters conversion.

Historical backup configurations contain a different
Radar location and mounting assignment.

The exact historical INI file used to generate the
recording has not been independently established.

## 7. Transformation validation

Three 4x4 homogeneous transformation matrices were
constructed using the recorded mounting poses.

Numerical checks:
- Sensor-origin transformation: passed
- Transformation inverse consistency: passed
- Rotation orthogonality: passed
- Rotation determinant: passed

These tests demonstrate internal mathematical consistency.

They do not independently verify coordinate-axis conventions
or the physical accuracy of projected sensor measurements.

## 8. MATLAB cross-validation

MATLAB reproduced:
- 466 exact GT–SensorView timestamp matches
- 0 ms maximum timestamp difference
- Approximately 32.9931 ms overall median interval
- 42 flagged long intervals
- Three sensor mounting positions
- Three transformation matrices
- Three relative sensor distances

Python and MATLAB numerical results agree.

## 9. Remaining limitations

L01: Independent sensor acquisition times are unverified.

L02: Source-level OSI/Unreal coordinate-axis conversion
has not yet been fully inspected.

L03: Sensor-to-object geometric projection has not been
validated against known ground-truth object positions.

L04: Cause of the abrupt recorded-message timing change
at frame 424 remains unknown.

L05: Historical simulation configuration provenance
is not completely established.

L06: Presence of sensor entries does not by itself prove
that all payloads are physically correct or properly calibrated.

## 10. Implications for future research

Task 18:
Use validated recording references for Camera processing.
Keep timestamp regime labels in all exported results.

Tasks 19–20:
Develop LiDAR and Radar processing using the documented
sensor mounting configuration.

Tasks 21–23:
Validate spatial projections and cross-sensor associations
before making tracking-accuracy or uncertainty claims.

Hardware phase:
Measure CPU/FPGA processing latency independently of
simulation timestamp intervals.

All experiments must distinguish observed data,
verified transformations, assumptions and limitations.

## 11. Research status

Task 17 achieved:
- Verified dataset integrity
- Recorded-message timestamp alignment
- Sensor mounting stability
- Configuration consistency
- Numerical transformation validation
- MATLAB/Python cross-validation
- Timing-regime characterization

Coordinate-frame conventions and timing-transition cause
remain open validation items.
