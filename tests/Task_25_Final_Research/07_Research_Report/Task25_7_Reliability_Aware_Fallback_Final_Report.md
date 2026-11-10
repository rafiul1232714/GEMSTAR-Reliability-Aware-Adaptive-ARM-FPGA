# Task 25.7 - Reliability-Aware Fallback Final Research Report

## 1. Research objective

Develop and audit an offline reliability-aware fallback policy
for GEMSTAR Camera/LiDAR/Radar perception.

The policy determines measurement eligibility and provisional
processing modes under controlled fault scenarios.

The controller is not yet a real-time scheduler, independently
validated perception controller or hardware energy optimizer.

## 2. Research inputs

- 2,122-frame sensor-health audit
- Seven controlled fault-replay scenarios
- 168 total replay samples
- Association-reliability diagnostics
- EKF uncertainty and Radar NIS diagnostics
- Offline BEV geometric validation
- 21 machine-readable fallback-policy rules

The original Task 24 recordings and measurements remain unchanged.

## 3. Controller design

Three provisional modes were implemented:

NORMAL_CANDIDATE:
LiDAR is available and no explicitly excluded sensor update
is identified by the evaluated replay policy.

DEGRADED_CANDIDATE:
LiDAR remains available, but an additional sensor update is
excluded due to an injected dropout, rejection or insufficient
returns.

HOLD_OR_ALERT:
LiDAR is unavailable under the conservative policy.
Authorization of a new valid perception result is withheld.

These modes describe policy classifications only.

## 4. Verified numerical results

- Policy rules: 21
- Scenarios: 7
- Replay decisions: 168
- Normal candidate: 143
- Degraded candidate: 16
- Hold or alert: 9

## 5. Scenario breakdown

| Scenario | Normal | Degraded | Hold |
|---|---:|---:|---:|
| baseline | 23 | 1 | 0 |
| camera_bias_0p20rad | 22 | 2 | 0 |
| camera_dropout | 22 | 2 | 0 |
| joint_dropout | 19 | 1 | 4 |
| lidar_every4_dropout | 18 | 1 | 5 |
| radar_bias_6mps | 20 | 4 | 0 |
| radar_dropout | 19 | 5 | 0 |

## 6. Independent decision audit

The independently implemented audit verified:

- 504 measurement-action assignments
- 168 controller-mode decisions
- 168 output-permission decisions
- 168 UNVERIFIED quality-authorization flags
- 21 scenario-summary checks
- Zero identified audit discrepancies

This demonstrates internal consistency with the recorded
policy rules, not correctness against real-world safety
requirements.

## 7. MATLAB visualization evidence

Figure 1:
task25_68_matlab_fallback_scenario_comparison

Figure 2:
task25_69_matlab_fallback_decision_timeline

Each figure was exported as a 300 DPI PNG and vector PDF.

These are offline replay classifications, not real-time
sensor acquisition timelines.

## 8. Sensor reliability limitations

Sensor payload repetition is not equivalent to proven failure.

Acquisition age is unknown for the full-rate recording.

Radar association is provisional and does not independently
validate object identity.

The reported EKF uncertainty exhibits systematic
ground-truth residual inconsistencies.

Camera-bearing updates remain experimental.

The fallback controller does not independently rerun the
EKF with alternative measurements.

No validated Radar-only or Camera-only substitute has
been established for the unavailable-LiDAR condition.

## 9. Quality authorization

QUALITY_AUTHORIZATION = UNVERIFIED for every replay sample.

The policy does not demonstrate compliance with predefined
perception-accuracy or p99-latency requirements.

A NORMAL_CANDIDATE mode must not be interpreted as an
independently validated accurate or safe perception result.

## 10. Energy-efficiency limitations

No hardware power or total system energy was measured.

No energy-saving percentage is claimed.

Future optimization must minimize measured total energy per
valid perception result under fixed perception-quality
and p99 latency constraints.

## 11. Research conclusion

The offline fallback controller implements the documented
status-to-action policy consistently for the seven replay
scenarios.

Nine replay samples trigger HOLD_OR_ALERT because the
recorded LiDAR measurement is unavailable.

The controller provides a reproducible baseline for
future quality-constrained and energy-aware scheduling.

It does not yet demonstrate perception safety, real-time
performance or hardware energy efficiency.

## 12. Next research task

Task 25.8 - Define and audit hard perception-quality
and latency constraints before authorizing fallback output.

Original datasets remain immutable. Task 25 is not ready
for final GitHub archiving until all remaining stages
are completed.
