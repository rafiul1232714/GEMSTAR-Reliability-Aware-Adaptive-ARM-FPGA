# GEMSTAR Task 19 — Consolidated Research Findings

Generated: 2026-10-30T21:25:16.237973+00:00

## 1. Scope

This research evaluates GEMSTAR LiDAR reconstruction,
geometric preprocessing, ground segmentation, voxel
reduction, sensor observability, software scheduling,
timing robustness, quantization and prospective ARM-FPGA
hardware/software partitioning.

The experiments are software investigations. No real
FPGA implementation, board power measurement or
hardware acceleration result is claimed.

## 2. Recordings

| Recording | Selected frames |
| --- | --- |
| baseline_clear | 17 |
| baseline_fog_working_radar | 16 |
| fog_postfix_validation | 15 |

Total cross-recording frames: **48**.

Frames with completed numerical quality evaluation:
**47**.

One low-data frame was excluded from segmentation
quality evaluation.

## 3. Observability monitor

| Provisional state | Frames |
| --- | --- |
| OBSERVABLE | 27 |
| REVIEW | 20 |
| INSUFFICIENT | 1 |

These diagnostic states are not validated sensor
health or failure labels.

## 4. Executed processing policy

| Mode | Frames |
| --- | --- |
| FULL | 22 |
| VOXEL | 25 |
| SKIP | 1 |

Overall processed-frame median baseline/policy
speed ratio: **1.398x**.

Median complete-monitor time:
**0.15245 ms**.

These are PC MATLAB measurements and exclude OSI
decoding, file I/O, hardware transfer and downstream
sensor fusion.

## 5. Processing-quality audit

Evaluated frames: **47**.

Selected-policy diagnostic failures:
**3**.

| Recording | Frame | Observability | Mode | Reference agreement (%) | False-ground count |
| --- | --- | --- | --- | --- | --- |
| baseline_clear | 200 | OBSERVABLE | VOXEL | 95.83 | 41 |
| baseline_fog_working_radar | 50 | OBSERVABLE | VOXEL | 96.57 | 39 |
| baseline_fog_working_radar | 550 | REVIEW | VOXEL | 97.26 | 47 |

Agreement is against full-resolution RANSAC, not
independent road/obstacle ground truth.

## 6. Timing and illustrative deadline

Experimental processing deadline: **3 ms**.

Timing samples: **240**.

Full-reference overall P95:
**3.41720 ms**.

Adaptive-policy overall P95:
**2.91280 ms**.

Full-reference sampled deadline misses:
**35**.

Adaptive-policy sampled deadline misses:
**7**.

These are observed violations of an illustrative
budget, not automotive real-time safety guarantees.

## 7. Quantization

Frame 150; 1,922 ROI points; fixed reference plane.

| Bits | XYZ RMSE (mm) | Changed labels | Reference agreement (%) | Raw storage saving (%) |
| --- | --- | --- | --- | --- |
| 8 | 43.404 | 4 | 99.792 | 87.5 |
| 16 | 0.171 | 0 | 100.000 | 75.0 |

Scales were calibrated on the evaluated frame.
Plane arithmetic was floating-point; these results
do not validate integer-only RANSAC or FPGA behavior.

## 8. Proposed ARM-FPGA architecture

Initial CPU responsibilities:
buffer management, observability monitoring,
scheduling, RANSAC hypotheses and SVD refinement.

Initial candidate FPGA kernel:
fixed-point point-to-plane distance evaluation,
threshold comparison and inlier counting.

The architecture and interface are specifications,
not implemented hardware.

## 9. Limitations

- No independent semantic ground-truth validation.
- No actual ARM-FPGA latency comparison.
- No hardware power or energy measurements.
- No completed RTL functional verification.
- No OSI decoding or transfer time in benchmark.
- Limited repeated timing samples on Windows MATLAB.
- Different simulation recordings may have different
  scenes, configurations or weather conditions.
- Quantization evaluated on one frame.
- Monitoring thresholds are experimental.
- Some scheduler failures occurred in observations
  classified as OBSERVABLE.

## 10. Required next hardware research

1. Verify fixed-point precision across recordings.
2. Implement and verify the first RTL kernel.
3. Establish CPU and FPGA functional equivalence.
4. Integrate data transfer and processing control.
5. Measure end-to-end latency and deadline misses.
6. Measure actual board power and energy per frame.
7. Compare accuracy, resource cost and energy fairly.

## 11. Reproducibility

Artifact files inventoried: **286**.

See `06_Research_Findings/task19_15_artifact_manifest.csv`
for relative paths, file sizes and SHA-256 hashes.

The final illustrated PDF is produced in Task 19.16.
