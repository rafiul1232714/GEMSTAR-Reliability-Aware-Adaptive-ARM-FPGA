# Task 26 — Final CPU Benchmark and Quality Evidence Report

**Project:** GEMSTAR reliability-aware, energy-adaptive Camera/LiDAR/Radar processing for future ARM–FPGA implementation

**Report status:** CPU baseline and diagnostic quality evidence; not final system validation.

## 1. Executive summary

- Original recorded CPU timing observations: **6,025**.
- Comparable timing groups: **184**.
- Hashed research files in Task 26.8A manifest: **114**.
- Original benchmark datasets were not rerun or modified during report generation.
- No ARM–FPGA hardware energy savings have been measured.
- Full-pipeline accuracy and p99 latency constraints remain unverified.

## 2. Objective and scope

The long-term objective is to minimize measured total system energy per valid perception result while satisfying independently evaluated perception quality and a predeclared p99 latency constraint.

Task 26 establishes CPU-based reference timings for selected software components and a partial processing pipeline. It does not measure a complete end-to-end real-time perception system.

## 3. CPU measurement methodology

Timing results originate from repeated execution of stored test inputs on the development CPU. Workload groups use different timing units, sample counts and input sizes.

The development machine is reported as using an AMD Ryzen AI 7 450 CPU with 8 cores and 16 threads. These timings should not be transferred directly to a future ARM processor.

Statistics include sample mean, median, sample standard deviation, coefficient of variation, interpolated p95/p99 and Tukey 1.5-IQR outlier counts.

## 4. CPU runtime repeatability

| Workload | Groups | Timings | Median of group medians (ms) | Max group p99 (ms) | Median within-group CV | Outlier rate |
|---|---:|---:|---:|---:|---:|---:|
| EKF | 2 | 200 | 5.485225 | 10.413307 | 6.379% | 13.500% |
| Camera | 6 | 600 | 1.815050 | 4.249605 | 11.371% | 9.833% |
| LiDAR | 106 | 2650 | 0.460500 | 1.717220 | 3.163% | 9.774% |
| Radar | 12 | 1200 | 0.008825 | 0.041704 | 16.222% | 9.333% |
| YOLO11s | 5 | 50 | 43.746050 | 51.676415 | 5.262% | 4.000% |
| Partial_LiDAR_Radar | 53 | 1325 | 0.794900 | 1.831704 | 12.735% | 10.340% |

**Interpretation:** These medians and p99 values describe different workload sizes. They must not be summed or interpreted as a shared end-to-end frame deadline.

### Important timing findings

- YOLO11s CPU inference is the largest measured standalone workload in this study.
- Radar batches have high relative timing variation and an observed 0.617 ms outlier.
- The Radar pooled median of 0.0108 ms differs from the median of its group medians (0.008825 ms), because the aggregation methods are different.
- The partial pipeline contains LiDAR filtering, LiDAR clustering and Radar validation only.
- All observed outliers were retained.

## 5. Ground-truth position diagnostics

Matching C02 moving-target GT/EKF frames: **23**. The evaluation target is OSI object ID **76897**.

| EKF configuration | Diagnostic object-center position RMSE (m) |
|---|---:|
| lidar_only | 1.663585 |
| radar_assisted | 1.640300 |
| camera_experimental | 1.640308 |

Radar assistance reduced the diagnostic GT-center RMSE by **1.3997%** over this small matched evaluation set.

This does not demonstrate a general sensor-fusion accuracy improvement.

The experimental Camera update at frame 530 was not authorized for validated operation.

## 6. Surface-versus-center geometry

- Radar mean GT-center distance: **1.628205 m**.
- Radar mean approximate GT-rear-face distance: **0.639567 m**.
- Reported OSI target length: **1.173327–2.168729 m**.
- Original surface diagnostic reads `GroundTruth.moving_object.base.dimension`.
- The reported dimensions vary with target orientation in the observed sequence.
- The rear-face point is a constructed approximation, not a verified LiDAR-hit position.

A difference in distance to two reference points must not be reported as a reduction in algorithmic localization error.

## 7. Perception-quality limitations

1. GT world-to-ego transformation is mathematically consistent but was explicitly labelled preliminary in the original diagnostic.
2. Target association uses the known GT ID for evaluation only.
3. Ground-truth velocity integrity flagged six samples with zero reported actor velocity during inferred motion.
4. Camera acceptance at frame 530 is experimental and unauthorized.
5. YOLO inference timing does not establish detection accuracy or reliable perception quality.
6. No full-pipeline validated detection, tracking, precision/recall or three-sensor quality guarantee has been established.

## 8. Repeatability limitations

- Workloads process different input sizes and have different timing units.
- Repeated measurements of the same stored input are not independent driving scenarios.
- Per-group p99 is descriptive, not a certified worst-case execution time.
- Ten-sample YOLO groups and 25-sample LiDAR/integrated groups give limited tail-latency evidence.
- No confidence interval establishes a hard real-time guarantee.
- CPU timings were measured on the development host, not an ARM–FPGA board.

## 9. Requirements for Tasks 27–36

Before claiming an optimization:

1. Use matched inputs and unchanged ground-truth evaluation references.
2. Define the exact processing scope and timing boundaries for each candidate.
3. Validate object identity, association, detection quality and tracking quality.
4. Select quality thresholds before optimizing, based on defensible requirements and validation data.
5. Specify latency deadlines and an appropriate p99 evaluation protocol.
6. Benchmark software and FPGA candidates under matched workloads and accounting rules.
7. Measure total ARM–FPGA board/system power during actual operation, including data movement and idle overhead.
8. Calculate measured joules per valid perception result, with confidence bounds.
9. Reject candidates violating quality or deadline constraints.

## 10. Task 26 completion interpretation

**Completed:** CPU component profiling, partial LiDAR–Radar sequential timing, diagnostic GT comparison, statistical repeatability and research archive checks.

**Not established:** validated full three-sensor accuracy, hard real-time feasibility, complete end-to-end latency, ARM–FPGA energy savings.

## 11. Provenance

Primary timing sources: `task26_3B_ekf_cpu_timing.csv`, `task26_4B_camera_cpu_timing.csv`, `task26_4D_lidar_cpu_timing.csv`, `task26_4G_radar_cpu_timing.csv`, `task26_4J_yolo_cpu_timing.csv`, `task26_5C_integrated_cpu_timing.csv`.

Quality source: `task26_6C_ekf_position_error_summary.csv`.

Repeatability sources: `task26_7B_repeatability_by_group.csv` and `task26_7B_repeatability_by_workload.csv`.

Archive record: `task26_8A_research_file_manifest.csv`.

The Task 26.8A manifest predates this report and this generator script. They must be accounted for in Task 26.8C.

---

*Research report generated from archived diagnostic and benchmark data. No claims of measured energy efficiency are made.*
