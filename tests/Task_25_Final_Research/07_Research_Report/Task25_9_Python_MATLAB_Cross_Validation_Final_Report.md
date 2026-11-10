# Task 25.9 - Python and MATLAB Cross-Validation

## 1. Research objective

Independently reproduce selected numerical research metrics
using Python and MATLAB and verify source-data integrity.

This is a computational reproducibility study, not physical
validation of sensor fusion or hardware energy efficiency.

## 2. Completed subtasks

- Task 25.9A: Reproducibility inventory
- Task 25.9B: Python numerical reference calculations
- Task 25.9C: MATLAB independent numerical comparison
- Task 25.9D: Dataset integrity and discrepancy audit
- Task 25.9E: Consolidated research report

## 3. Reproducibility inventory

- Original research datasets: 11
- MATLAB scripts: 5
- MATLAB figure files: 24
- MATLAB findings files: 5
- SHA256 dataset integrity checks: 11 passed

The manifest covers selected source datasets used for
numerical research verification.

## 4. Numerical agreement

Python and MATLAB independently calculated 18 metrics.

- Integer/count metrics requiring exact agreement: 11
- Floating-point metrics: 7
- Metrics passed after correction: 18
- Metrics failed after correction: 0
- Absolute comparison tolerance: 1e-10
- Relative comparison tolerance: 1e-9

Floating-point tolerances apply only to computational
agreement; they are not perception acceptance limits.

## 5. Detailed numerical comparison

| Metric | Python | MATLAB | Absolute difference |
|---|---:|---:|---:|
| fallback_total | 168 | 168 | 0 |
| fallback_normal | 143 | 143 | 0 |
| fallback_degraded | 16 | 16 | 0 |
| fallback_hold | 9 | 9 | 0 |
| association_lidar_matched | 74 | 74 | 0 |
| association_radar_provisional | 65 | 65 | 0 |
| association_lidar_mean_distance_m | 0.0946882432432433 | 0.0946882432432433 | 0 |
| association_radar_mean_gap_m | 0.0440801538461538 | 0.0440801538461538 | 0 |
| ekf_gt_rows | 23 | 23 | 0 |
| ekf_lidar_mean_signed_residual_x_m | -1.62352233650936 | -1.62352233650936 | 0 |
| ekf_radar_mean_signed_residual_x_m | -1.60128294772754 | -1.60128294772754 | 2.22044604925031e-16 |
| ekf_lidar_mean_sigma_x_m | 0.555641037945769 | 0.555641037945769 | 0 |
| ekf_radar_mean_sigma_x_m | 0.552601266164852 | 0.552601266164851 | 1.11022302462516e-16 |
| radar_nis_rows | 24 | 24 | 0 |
| radar_nis_finite_accepted | 4 | 4 | 0 |
| radar_nis_mean_accepted | 0.570677354389672 | 0.570677354389672 | 0 |
| quality_gate_total | 6 | 6 | 0 |
| quality_gate_authorized | 0 | 0 | 0 |

## 6. Maximum numerical discrepancy

Maximum absolute difference after correction:

2.2204460492503101E-16

The remaining difference is consistent with normal
floating-point rounding.
## 7. Initial comparison failure and resolution

The initial MATLAB comparison passed 11 count metrics
and failed seven floating-point metrics.

The original mismatch was consistent with converting
numeric MATLAB columns into strings and then parsing
those shortened strings back into numeric values.

The analysis was corrected to preserve existing numeric
columns as double values.

The original MATLAB script and failed comparison CSV
were archived before the corrected rerun.

No numerical tolerance was relaxed to obtain agreement.

## 8. Dataset integrity

The 11 original datasets in the reproducibility manifest
were verified using SHA256.

Their recorded row counts were independently audited
during Task 25.9D.

The original research measurements were not edited
as part of the numerical correction.

## 9. Scientific interpretation

The cross-language agreement establishes that Python
and MATLAB reproduce the selected numerical summaries.

It does not establish:

- Correct physical sensor coordinate calibration
- Verified LiDAR/Radar/Camera target identity
- Validated EKF covariance calibration
- Perception-quality threshold compliance
- p99 processing latency compliance
- Real-time ARM-FPGA reliability
- Hardware energy savings

The repeated fault scenarios are not independent
experimental recordings.

The LiDAR cluster median is not a verified vehicle center.

Radar spatial associations remain provisional.

Only four accepted finite Radar NIS values are
available in the original selected-frame source.

## 10. Quality authorization

QUALITY_AUTHORIZATION: UNVERIFIED

VALIDATED_QUALITY_GATES: 0

ENERGY_SAVINGS_CLAIMED: NO

Computational agreement is not equivalent to
validated perception quality.

## 11. Next research stage

Task 25.10 will consolidate research Tasks 25.1 through
25.9, verify required outputs and archive the completed
Task 25 research package.

GitHub upload is permitted only after final consolidation,
source integrity checks and archive review.

No future Task 26-50 folders are created at this stage.
