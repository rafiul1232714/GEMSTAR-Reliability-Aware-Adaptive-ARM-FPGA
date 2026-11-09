# Task 24.2 ? Sensor Coordinate and Temporal Calibration

## Final Research Report

**Project:** GEMSTAR Camera?LiDAR?Radar energy-aware fusion

**Research status:** Nominal geometry and diagnostic temporal validation completed; physical alignment and independent acquisition synchronization remain unverified.

## 1. Objective

Establish reproducible coordinate conventions, reconstruct measured LiDAR/Radar geometry, develop an initial Camera projection model, and evaluate recording-time consistency before three-sensor association and EKF tracking.

## 2. Raw data and provenance

- **SensorView:** `20261105T231919Z_sv_380_X_372_GEMSTAR.osi`
  - Size: 478214726 bytes
  - SHA-256: `3d4f1c9957b8d26a11d12570212f54e74007f967acb739dc5ff64799326d8e2b`
- **GroundTruth:** `20261105T231919Z_gt_380_X_372_GEMSTAR.osi`
  - Size: 628956 bytes
  - SHA-256: `31cb4c4e113adb7f05c51668922ab8c356d97edbd1ab5af0ea7c2ce2a44dcec9`

Both recordings contain 372 parsed frames. Original files were treated as read-only.

## 3. Nominal sensor geometry

| Sensor | X (m) | Y (m) | Z (m) |
|---|---:|---:|---:|
| Camera | 0.70 | 0.00 | 1.60 |
| Lidar | 2.60 | 0.00 | 0.70 |
| Radar | 2.00 | 0.00 | 0.80 |

Under the documented zero-rotation mounting assumption:

`X_vehicle = X_sensor_UE + mount_X`

`Y_vehicle = -Y_sensor_UE + mount_Y`

`Z_vehicle = Z_sensor_UE + mount_Z`

This is a nominal vehicle-relative OSI transform, not independently calibrated extrinsics.

## 4. LiDAR and Radar reconstruction ? Frame 0

| Measurement | LiDAR | Radar |
|---|---:|---:|
| Total ray slots | 5271 | 100 |
| Diagnostic candidates | 1914 | 32 |
| Near-zero returns | 2510 | 50 |
| No-hit returns | 847 | 18 |

The 0.01 m candidate threshold is provisional. Ray-angle, range and nominal coordinate transforms passed numerical self-consistency checks.

## 5. Camera image and initial projection

- Recorded resolution: **640 ? 480 pixels**.
- Source-verified serialized channel order: **RGB**.
- Recorded horizontal FoV: **90 degrees**.
- Recorded vertical FoV metadata: **90 degrees**.
- Candidate perspective focal lengths: **fx = fy = 320 px**.
- Candidate principal point: **(320, 240) px**.
- Derived conventional vertical FoV: **73.739795 degrees**.
- Actual optical calibration remains unverified.

- LiDAR candidates inside image: **1914/1914**.
- Radar candidates inside image: **32/32**.

Point inclusion in image boundaries does not prove alignment with visual objects. The overlay is diagnostic.

## 6. Recording timestamp analysis

- Paired SensorView/GroundTruth frames: **372**.
- Exact matched logger timestamps: **372/372**.
- Three-sensor message presence: **372/372**.
- Strictly increasing timestamp sequences: **yes**.
- Recording interval transition: **frame 311**.
- Mean interval, frames 1?310: **33.260154 ms**.
- Mean interval, frames 311?371: **333.334059 ms**.
- Mean-interval ratio: **10.0220**.

The cause of the interval change is unknown. Shared logger timestamps do not prove independently synchronized sensor acquisitions.

## 7. Host-pose relationship

- Comparable embedded host poses: **355**.
- Host vehicle identifier: **76895**.
- A near-constant preceding-frame residual was observed:
  - X: approximately **?0.111434 m** in ego-local coordinates.
  - Y: approximately **+0.133235 m**.
  - Z: approximately **?0.826200 m**.
- Missing embedded host pose: **frame 0; frames 356?371**.
- Host absent from separate GT: **frames 356?371**.

The preceding-frame residual is compatible with a systematic origin/centre difference and a frame-index relationship. It does not establish an acquisition delay.

## 8. MATLAB research figures

- `03_Graphs/task24_02C_07B_CF01_common_frame_3d.png`
- `03_Graphs/task24_02C_07B_CF02_common_frame_xy.png`
- `03_Graphs/task24_02C_07B_CF03_common_frame_xz.png`
- `03_Graphs/task24_02C_08G_camera_lidar_radar_overlay_frame000.png`
- `03_Graphs/task24_02D_03_TIME01_timestamps.png`
- `03_Graphs/task24_02D_03_TIME02_frame_intervals.png`
- `03_Graphs/task24_02D_03_TIME03_interval_histogram.png`

## 9. Limitations and scientific safeguards

1. Sensor-to-sensor physical extrinsics are not calibrated.
2. Effective Camera rendering projection requires image-grounded verification.
3. Shared recorder timestamps do not establish independent acquisition synchronization.
4. The apparent one-frame pose relationship is not a proven acquisition delay.
5. GroundTruth host pose disappears after frame 355.
6. Diagnostic ray thresholds are not calibrated sensor validity limits.
7. Single-frame projection is not validated object association or sensor fusion.
8. Recording intervals must not be confused with measured CPU/FPGA processing latency.

## 10. Acceptance and continuation

| Criterion | Assessment |
|---|---|
| Recording integrity | PASS |
| Required CSV and figures | PASS |
| Nominal coordinate consistency | PASS |
| Camera RGB encoding | PASS |
| Recorder timestamp consistency | PASS |
| Physical cross-sensor registration | UNVERIFIED |
| Independent sensor acquisition synchronization | UNVERIFIED |

**Task 24.2 is completed as a reproducible nominal-geometry and temporal-diagnostics stage, with explicitly documented limits.**

Proceed to the next Task 24 subtask using variable timestamp increments, sensor validity masks, and no unsupported synchronization or calibration claims.
