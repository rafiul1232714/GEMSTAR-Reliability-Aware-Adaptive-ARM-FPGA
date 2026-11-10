# Task 25.3 - Controlled Sensor Fault Research

## 1. Experimental scope

- Recording: GEMSTAR C02 clean V2
- Seven controlled replay scenarios
- 24 tracking observations per scenario
- Same selected frame identifiers across scenarios
- Results describe the existing offline estimator replay

## 2. Tracking error comparison

| Scenario | GT samples | Mean error (m) | RMSE (m) | Delta mean (m) |
|---|---:|---:|---:|---:|
| baseline | 23 | 1.628213 | 1.640308 | 0.000000 |
| radar_dropout | 23 | 1.650425 | 1.663593 | +0.022212 |
| camera_dropout | 23 | 1.628205 | 1.640300 | -0.000008 |
| lidar_every4_dropout | 23 | 1.618054 | 1.632332 | -0.010159 |
| radar_bias_6mps | 23 | 1.625637 | 1.645515 | -0.002576 |
| camera_bias_0p20rad | 23 | 1.628205 | 1.640300 | -0.000008 |
| joint_dropout | 23 | 1.601929 | 1.613303 | -0.026284 |

GT evaluation counts identical across scenarios: True

## 3. Fault injection verification

| Scenario | LiDAR dropped | Radar accepted | Radar rejected | Camera accepted | Camera rejected |
|---|---:|---:|---:|---:|---:|
| baseline | 0 | 4 | 0 | 1 | 0 |
| radar_dropout | 0 | 0 | 0 | 1 | 0 |
| camera_dropout | 0 | 4 | 0 | 0 | 0 |
| lidar_every4_dropout | 5 | 4 | 0 | 1 | 0 |
| radar_bias_6mps | 0 | 1 | 3 | 1 | 0 |
| camera_bias_0p20rad | 0 | 4 | 0 | 0 | 1 |
| joint_dropout | 4 | 4 | 0 | 0 | 0 |

All seven replay scenarios passed the previously executed fault-consistency audit.

## 4. Research interpretation

- Radar dropout increased mean GT-center error in this replay.
- Camera dropout and camera bias produced very small or rounded-zero changes.
- Periodic LiDAR dropout and joint dropout showed numerically lower mean errors.
- Lower error under dropout is not evidence that failures improve perception.
- Rejected biased updates demonstrate gate behavior, not a complete robustness guarantee.

## 5. Limitations

- Only one controlled recording and a small selected tracking set were evaluated.
- Matched frames from one trajectory are temporally dependent.
- Sensor associations and geometry are partly provisional.
- Independent sensor acquisition age is unknown.
- Existing full-rate repetition diagnostics are not equivalent to fault injection.
- No statistical significance or generalization across recordings is established.
- No predefined perception-quality threshold has yet been validated.
- No ARM-FPGA energy or hardware performance improvement is demonstrated.

## 6. MATLAB figures

- task25_27_matlab_fault_tracking_error.png / .pdf
- task25_28_matlab_fault_responses.png / .pdf

## 7. Next research requirements

- Define accuracy and tail-latency acceptance constraints before final pass/fail judgments.
- Investigate association reliability and filter consistency.
- Validate against additional controlled recordings where possible.
- Preserve matched comparisons for subsequent CPU and hardware benchmarks.

TASK25_03E_REPORT_PASS
