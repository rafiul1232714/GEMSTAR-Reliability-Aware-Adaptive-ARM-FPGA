# Task 25 — Preliminary reliability and failure-injection findings

- Task 24 C02 source: `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\C02_V2_EKF_Input_53Frames_V1`
- Reproduced baseline maximum coordinate mismatch: **1.39e-17 m**
- Task 24 GT-center evaluation frames: **23**
- Selected provisional Track 2: **24 samples**
- GT used only after replay, for evaluation.
- All scenarios use the same observation frames/timestamps and EKF equations.
- Radar sigma 2 m/s, LiDAR sigma 0.60 m, Camera sigma minimum 0.05 rad: **uncalibrated experimental assumptions**.
- No full covariance export/NEES, calibrated detection or association precision/recall.
- No real fog/traffic replication or hardware energy/latency measurement.
- GT center and LiDAR visible surface are not equivalent measurement references.
- Failure injections are exploratory software sensitivity experiments, **not a validated safety case**.

## Scenario results

| Scenario | Mean GT-center error (m) | RMSE (m) | Radar accepted | Camera accepted |
|---|---:|---:|---:|---:|
| baseline | 1.628213 | 1.640308 | 4 | 1 |
| radar_dropout | 1.650425 | 1.663593 | 0 | 1 |
| camera_dropout | 1.628205 | 1.640300 | 4 | 0 |
| lidar_every4_dropout | 1.618054 | 1.632332 | 4 | 1 |
| radar_bias_6mps | 1.625637 | 1.645515 | 1 | 1 |
| camera_bias_0p20rad | 1.628205 | 1.640300 | 4 | 0 |
| joint_dropout | 1.601929 | 1.613303 | 4 | 0 |

## Next required for Task 25 completion
1. Verify exported figures, source hashes, replay states and failure scenarios.
2. Validate on independent clear/fog/traffic recordings; current C02 is development-only.
3. Calibrate sensor geometry and uncertainties; test association false positives and missed detections.
4. Predefine perception and p99 latency constraints before claiming acceptable fallback.
5. Document genuine end-to-end CPU cost; hardware power measurement belongs to later tasks.
