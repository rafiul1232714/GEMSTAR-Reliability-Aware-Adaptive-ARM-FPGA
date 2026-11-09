# Task 23.14 — Coordinate-Frame and Timestamp Readiness

## Objective

Evaluate existing GEMSTAR Camera, LiDAR and Radar coordinate-frame
metadata, mounting geometry and timestamp evidence before Task 24
three-sensor association and EKF tracking.

This task is a readiness audit, not an independent calibration
certificate or proof of simultaneous sensor acquisition.

## 1. Camera intrinsic sanity check

Image resolution: 640 x 480 pixels.
Configured horizontal FoV: 90 degrees.

Nominal pinhole intrinsic parameters:
- fx = 320 pixels
- fy = 320 pixels
- cx = 320 pixels
- cy = 240 pixels
- Derived vertical FoV = 73.739795 degrees

Assumptions:
- Perspective projection
- Square pixels
- Centered principal point
- Negligible lens distortion

Existing cube-width validation:
- 8.5 m: measured 112 px, predicted 112.941 px
- 10.5 m: measured 92 px, predicted 91.429 px

Both checks passed the exploratory 3-pixel tolerance.

Limitations:
- This is not an independent camera calibration.
- Pixel-level reprojection accuracy is not established.
- Camera optical-axis and Unreal-to-OSI axis conventions require
  explicit validation before cross-sensor pixel projection.

## 2. Original three-sensor mounting configuration

Original configuration:
task23_07ad_original.ini

All three sensors use Mount=SensorPlatform_1.

Configured positions in vehicle-relative Unreal coordinates,
converted from centimetres to metres:

Camera: X=0.70, Y=0.00, Z=1.60
LiDAR:  X=2.60, Y=0.00, Z=0.70
Radar:  X=2.00, Y=0.00, Z=0.80

Configured roll, pitch and yaw are zero for all three sensors.

Calculated relative translations and separations:

Camera -> LiDAR:
  delta=(+1.90, 0.00, -0.90) m
  separation=2.102380 m

Camera -> Radar:
  delta=(+1.30, 0.00, -0.80) m
  separation=1.526434 m

Radar -> LiDAR:
  delta=(+0.60, 0.00, -0.10) m
  separation=0.608276 m

These are configuration-based calculations, not independently
measured extrinsic calibration results.

## 3. Mounting implementation findings

Camera mounting source:
- CameraSensor.cpp applies SensorConfiguration.Offset using
  SetActorRelativeTransform().
- CameraSensorManager.cpp requests the named mount and invokes
  UpdateTransformAfterAttachment().
- VehicleManager.cpp resolves configured names to vehicle instances
  and uses AttachToActor(... SnapToTarget ...).
- GemstarSimulationSubsystem.cpp caches pending mounting requests
  and retries their resolution.

Mounting success and final effective pose have not been independently
verified against a runtime ground-truth pose in this audit.

## 4. Incompatible experiment configurations

Task 23.12 Camera configuration:
- Camera mounted to SensorPlatform_1 at (0.70, 0.00, 1.60) m.
- LiDAR has no named mount and is configured at
  (19.40, -26.50, 2.50) m.
- Radar remains mounted to SensorPlatform_1.

Therefore, Task 23.12 results must not be treated as proof of
simultaneous three-sensor alignment using the original configuration.

Task 23.9 camera cube calibration used a different Camera mounting
arrangement and cannot independently validate the Task 23.12
vehicle-relative extrinsic pose.

## 5. Radar-LiDAR spatial evidence

Existing nearest-point overlay results support exploratory
spatial consistency for some sampled frames.

However:
- ObjectAssociationVerified is False.
- Some nearest-neighbour P95 distances are large.
- Object-to-object correspondence has not been validated.
- No external spatial accuracy metric has been established.

Nearest-point overlap must not be reported as association accuracy.

## 6. Timestamp validation

Radar-LiDAR sampled records: 15.
Shared SensorView containers: 15/15.
SensorView-GroundTruth equal timestamps: 15/15.
Independent acquisition timing verified: 0.

Timestamp progression:
- 9/9 sampled steps strictly increasing.
- Minimum step: 27.894 ms.
- Maximum step: 38.361 ms.
- Mean step: 32.803 ms.

Camera timing from separate recordings:

- Clear: 10 frames, mean interval 36.865 ms.
- Fog MOR100: 10 frames, mean interval 39.425 ms.
- Fog MOR20: 10 frames, mean interval 33.509 ms.

Camera frame intervals are not cross-sensor timestamp differences.

## 7. Readiness conclusions

SUPPORTED:
- Nominal Camera intrinsics agree with two controlled cube-width
  measurements.
- Original configurations define consistent three-sensor
  relative translations.
- Radar and LiDAR share SensorView container timestamps in
  the audited samples.
- Sampled SensorView and GroundTruth timestamps match exactly.
- Sampled timestamp steps increase monotonically.

NOT YET VERIFIED:
- Actual Camera-to-Radar/LiDAR pixel reprojection errors.
- Independent three-sensor sensor-acquisition synchronization.
- Successful effective named-mount pose for every recording.
- Camera-LiDAR-Radar object-level correspondence.
- Object tracking or EKF fusion accuracy.

## 8. Conditions before Task 24 association and EKF fusion

1. Use one explicit, consistent vehicle-frame convention.
2. Verify actual mounted sensor poses for the chosen recordings.
3. Implement and validate Unreal/OSI/Camera optical-axis conversion.
4. Distinguish container timestamps from acquisition timestamps.
5. Use matched same-run measurements when testing temporal fusion.
6. Reject or flag missing, delayed or inconsistent measurements.
7. Evaluate object correspondence against appropriate ground truth.
8. Preserve raw OSI data and source manifests.

## 9. Evidence references

- 01_Code/task23_14B_03F_camera_intrinsic_sanity_check.py
- 02_CSV_Data/task23_14B_03F_camera_intrinsic_sanity_check.csv
- 02_CSV_Data/task23_05d1_radar_lidar_alignment.csv
- 02_CSV_Data/task23_05d2_radar_lidar_timestamps.csv
- 02_CSV_Data/task23_05d2_timestamp_progression.csv
- 02_CSV_Data/task23_12C_01_camera_timing_audit.csv
- 04_Configurations/task23_07ad_original.ini
- 04_Configurations/task23_12_camera_clear.ini
- 06_Research_Findings/task23_14B_04G_mount_transform_source_evidence.txt

## Final assessment

Task 23.14 readiness audit: COMPLETED WITH DOCUMENTED LIMITATIONS.

Full three-sensor calibration and independent synchronization:
NOT YET DEMONSTRATED.
