# Task 23.15 — Unified Three-Sensor Preprocessing Readiness

## 1. Objective

Develop a common software interface for Camera, LiDAR and Radar
preprocessing using validated Task 23 algorithms.

Preserve timestamp metadata, coordinate-frame conventions,
sensor-specific quality indicators and invalid-data handling.

No original GEMSTAR recordings or experimental source files
were modified during adapter implementation.

## 2. Unified architecture

Camera input
    -> Camera preprocessing adapter
    -> SensorMeasurement

LiDAR input
    -> LiDAR return-availability adapter
    -> SensorMeasurement

Radar input
    -> Radar range preprocessing adapter
    -> SensorMeasurement

SensorMeasurement objects
    -> Timestamp bundle evaluation
    -> Preliminary status and timing readiness

Separate coordinate adapter:
    Sensor-local Unreal points
    -> Zero-rotation axis conversion
    -> Vehicle-relative OSI points

This architecture does not yet establish an operational
recorded-OSI end-to-end processing pipeline.

## 3. Common interface

Module:
01_Code/task23_15_unified_preprocessing.py

The common SensorMeasurement structure contains:

- Sensor identity
- Timestamp in nanoseconds
- Coordinate-frame label
- Processing status
- Sensor-specific quality data
- Processed measurement data

Interface validation:
14/14 tests passed.

## 4. Camera preprocessing

Adapter:
01_Code/task23_15_camera_adapter.py

Reuses:
task23_12C_06_camera_cpu_preprocessing.py

Supported features include:

- Grayscale image conversion
- Edge-map generation
- Mean luminance
- Contrast standard deviation
- Edge density
- Laplacian variance
- Mean saturation
- Region-of-interest validation

Synthetic Camera integration:
7/7 tests passed.

Adapter output matched the original preprocessing
function for the tested synthetic BGR image.

Camera quality metrics must not be interpreted
as object-detection accuracy.

## 5. LiDAR preprocessing

Adapter:
01_Code/task23_15_lidar_adapter.py

Reuses the original score_lidar_frame function.

Preserves statuses including:

- VALID
- NO_RETURNS
- EMPTY_FRAME
- MISSING_FRAME
- MALFORMED_FRAME
- INVALID_TIMESTAMP

LiDAR return-availability integration:
9/9 tests passed.

The positive-return ratio indicates measurement
availability, not object-detection accuracy.

LiDAR full 3D reconstruction has not yet been
integrated into the end-to-end preprocessing adapter.

## 6. Radar preprocessing

Adapter:
01_Code/task23_15_radar_adapter.py

Reuses the original preprocess_radar_return function.

Radar range equation:
range = speed_of_light * time_of_flight / 2

Existing calibration samples:

- Baseline: 8.536549 m
- Displaced: 10.545149 m

Radar integration:
13/13 tests passed.

The implementation rejects invalid time-of-flight
and signal-strength measurements.

Radar 3D reconstruction and object association
are not yet integrated into an end-to-end pipeline.

## 7. Coordinate conversion

Adapter:
01_Code/task23_15_coordinate_adapter.py

Source convention verified in LiDAR and Radar scripts:

reflect_y = [1, -1, 1]

For tested zero-rotation configurations:

vehicle_osi = sensor_unreal * reflect_y
              + mounting_translation_osi

Numerical validation:

- LiDAR axis convention passed
- Radar axis convention passed
- Seven coordinate adapter checks passed

Nonzero mounting rotations are explicitly rejected.

Limitations:

- Mount translations must already be in OSI metres.
- Effective runtime mounting poses are not independently verified.
- No measured Camera-to-LiDAR/Radar reprojection accuracy.
- No general nonzero-rotation extrinsic transformation.

## 8. Timestamp and missing-sensor handling

Module:
01_Code/task23_15_timestamp_bundle.py

Synthetic validation:
12/12 tests passed.

Supported checks include:

- Exact container timestamp equality
- Missing sensor detection
- Stale measurement detection
- Future timestamp detection
- No-return status preservation
- Invalid timestamp tolerance rejection

The preliminary ready_for_fusion flag checks only
timestamp alignment and measurement validity.

It is NOT proof of full fusion readiness.

Independent acquisition synchronization:
NOT VERIFIED.

Same-run provenance:
NOT VERIFIED.

## 9. Combined software integration

Synthetic Camera-LiDAR-Radar integration:
12/12 tests passed.

Validated behaviors:

- Camera feature extraction
- LiDAR return-availability scoring
- Radar range decoding
- Common SensorMeasurement interface
- Container timestamp matching
- Zero-rotation coordinate conversion
- Missing Radar handling
- Stale Radar handling
- LiDAR no-return handling

This is a synthetic software test, not proof of
real simultaneous three-sensor acquisition.

## 10. Historical evidence acceptance

Required files found: 13/13.
Missing or empty required files: 0.

Historical CSV row counts:

- Camera intrinsic calibration: 2
- Radar-LiDAR alignment: 6
- Radar-LiDAR timestamps: 15
- Camera timestamps: 30
- Task 23.14 readiness summary: 8

All five expected count checks passed.

These checks confirm file presence and expected
row counts, not complete raw-dataset integrity.

## 11. Outstanding acceptance requirements

The following have NOT been demonstrated:

1. Independent Camera-LiDAR-Radar acquisition synchronization.
2. Measured cross-sensor reprojection accuracy.
3. Recorded-OSI end-to-end unified preprocessing.
4. Verified runtime extrinsics for all three sensors.
5. Ground-truth object association.
6. Dynamic object tracking and EKF fusion accuracy.
7. Hardware energy efficiency or latency improvement.

These limitations must not be presented as completed validation.

## 12. Requirements before accepting Task 24 fusion

- Use matched recordings from the same GEMSTAR run.
- Establish sensor-time or simulation-time semantics.
- Quantify and handle timing offsets.
- Confirm effective runtime sensor poses.
- Validate Camera projection and optical-axis conventions.
- Measure cross-sensor reprojection residuals.
- Validate object correspondences against ground truth.
- Reject stale, missing or malformed measurements.
- Keep quality metrics distinct from fusion accuracy.

## 13. Final research assessment

Task 23.15:
UNIFIED SOFTWARE PREPROCESSING READINESS COMPLETED
WITH DOCUMENTED LIMITATIONS.

Validated:
Function-level adapters, synthetic integration,
coordinate convention and timestamp status handling.

Not yet validated:
Recorded-OSI end-to-end operation, independent
three-sensor synchronization or cross-sensor reprojection.

Next roadmap task:
Task 23.16 — Final Task 23 evidence acceptance and archive.
