# Task 24.1 - Initial Dataset Readiness Report

## Dataset

SensorView:
20261105T231919Z_sv_380_X_372_GEMSTAR.osi

GroundTruth:
20261105T231919Z_gt_380_X_372_GEMSTAR.osi

Source directory:
E:\GEMSTAR_Project\gemstar\Output

These files are provisionally paired based on filename identity
and the sampled internal timestamp agreement.

## Dataset inventory

- 40 SensorView files found.
- 40 GroundTruth files found.
- 40 provisional one-to-one filename-based pairs identified.
- Candidate selected: 372_GEMSTAR.

## Three-sensor readiness

First 100 SensorView frames:

- Camera nonempty frames: 100/100.
- Camera image bytes: 921600 per sampled frame.
- LiDAR positive-TOF frames: 100/100.
- Radar positive-TOF frames: 100/100.
- LiDAR positive TOF counts: 2025 to 4424.
- Radar positive TOF counts: 53 to 82.

Positive TOF values are not equivalent to confirmed object detections.

## Container timestamp analysis

- SensorView and GroundTruth index pairs compared: 100.
- Exact recorded container timestamp matches: 100.
- Mean absolute timestamp difference: 0 ms.
- Maximum absolute timestamp difference: 0 ms.
- Mean SensorView container interval: 33.786 ms.
- Maximum SensorView container interval: 94.130 ms.

These results do not independently validate individual Camera,
LiDAR or Radar acquisition timestamps.

## GroundTruth object analysis

- GroundTruth frames checked: 100.
- Frames containing moving objects: 100.
- Unique moving-object IDs: 5.

GroundTruth IDs:
76865, 76868, 76870, 76895, 77191.

## Motion continuity findings

Object 77191 contains two diagnostic discontinuity flags:

Frame 0 to 1:
- Displacement: 35.180 m
- Time interval: 0.061111 s
- Implied speed: 575.675 m/s

Frame 1 to 2:
- Displacement: 8.796 m
- Time interval: 0.094130 s
- Implied speed: 93.445 m/s

Diagnostic threshold: 50 m/s.

The source of these discontinuities is not yet established.
Do not silently remove or alter GroundTruth data.

## Research readiness assessment

The dataset is suitable for further investigation of real
three-sensor preprocessing, time alignment, coordinate geometry,
object association and tracking.

Object-level Camera-LiDAR-Radar association and EKF tracking
have not yet been validated.

## Next step

Task 24.2:
Temporal and coordinate compatibility.

Required:
- Confirm the relevant sensor mounting configurations.
- Validate sensor-to-world and world-to-sensor transformations.
- Validate Camera projection using matched recorded evidence.
- Establish defensible observation-level temporal alignment.
- Verify meaningful object-level sensor observations.