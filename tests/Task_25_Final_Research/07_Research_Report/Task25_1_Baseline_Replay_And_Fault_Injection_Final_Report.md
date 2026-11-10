# Task 25.1 - Baseline Replay and Controlled Fault Injection

## 1. Objective

Establish a reproducible historical baseline for controlled
Camera, LiDAR and Radar fault-replay investigations.

This document consolidates existing research evidence.
It does not represent a new experiment or replay run.

## 2. Evidence provenance

Source CSV: task25_replay_samples.csv

- Recorded replay rows: 168
- SHA256: 16190327DD2346C81E86D239BF78B1A20877FA2B14EA092D6A8F7FFA96516596
- Source columns: scenario, sample, frame, time_s, lidar_used, lidar_cluster_points, radar_status, radar_nis, camera_status, camera_nis, lidar_only_x_m, lidar_only_y_m, lidar_radar_x_m, lidar_radar_y_m, fusion_x_m, fusion_y_m, fusion_std_x_m

Source CSV: task25_fault_summary.csv

- Recorded scenario-summary rows: 7
- SHA256: 86EE768D8E59B117DB9C4D440267373FD456A7520AC42AE32AD20DB394B787F0
- Source columns: scenario, samples, gt_evaluation_samples, mean_gt_center_error_m, rmse_gt_center_m, max_gt_center_error_m, lidar_measurement_used, radar_updates_accepted, radar_nis_rejected, camera_updates_accepted

Both files matched their existing Task 25.9A
SHA256 inventory before this report was generated.

## 3. Scenario replay inventory

Scenario grouping status: VERIFIED_7_GROUPS_24_ROWS_EACH

| Scenario | Replay rows |
|---|---:|
| baseline | 24 |
| camera_bias_0p20rad | 24 |
| camera_dropout | 24 |
| joint_dropout | 24 |
| lidar_every4_dropout | 24 |
| radar_bias_6mps | 24 |
| radar_dropout | 24 |

These observations are controlled replay entries
derived from related underlying evidence.

They must not be described as independent recordings.

## 4. Baseline and fault-injection interpretation

The existing research package contains a baseline
and controlled fault scenarios used to investigate
the behavior of the perception and fallback pipeline.

The associated scenario-summary CSV is the authoritative
source for its recorded numerical results.

A scenario with a lower historical GT error is not,
by itself, evidence that the system is more robust.

Results may depend on selection, missing outputs,
association conventions and object-center definitions.

## 5. Reproducibility

The original replay CSV and summary CSV were preserved.

Task 25.9 separately demonstrated computational agreement
between Python and MATLAB for selected research metrics.

That numerical agreement does not independently establish
physical sensor correctness.

## 6. Limitations

- Historical replay data do not establish live execution
- Sensor acquisition age is not independently known
- Target association and GT-center alignment remain provisional
- No p99 processing-latency compliance has been demonstrated
- No measured hardware energy reduction has been demonstrated
- Perception-quality authorization remains UNVERIFIED

## 7. Relationship to later research stages

Task 25.2 investigates recorded sensor-health evidence.

Task 25.3 analyzes controlled fault outcomes.

Tasks 25.4-25.6 investigate association, EKF uncertainty
and BEV geometry.

Task 25.7 implements conservative fallback classification.

Task 25.8 defines quality and latency validation gates.

Task 25.9 establishes selected computational reproducibility.

## 8. Final research status

HISTORICAL_REPLAY_EVIDENCE: PRESENT

SOURCE_HASHES_VERIFIED: 2

NEW_EXPERIMENTS_PERFORMED: NO

QUALITY_AUTHORIZATION: UNVERIFIED

ENERGY_SAVINGS_CLAIMED: NO

This closes the missing retrospective documentation for
Task 25.1, not the outstanding perception-quality validation.
