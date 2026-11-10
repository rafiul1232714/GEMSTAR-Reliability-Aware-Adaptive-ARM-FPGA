# Task 25.2 — Sensor Health and Freshness Research

## 1. Dataset

Scenario: C02 clean V2 moving-target experiment.
SensorView recording: 2,122 frames.
Sensors: Camera, LiDAR, Radar.

## 2. Validated findings

| Sensor | Changed | Repeated | Max unchanged (s) |
|---|---:|---:|---:|
| Camera | 2121 | 0 | 0.000 |
| LiDAR | 633 | 1488 | 17.669 |
| Radar | 286 | 1835 | 22.265 |

All counts exclude the first observation, for which
there is no preceding frame to compare.

The full-rate health table passed an independent
frame-alignment, timestamp, status and duration check.

Reflection-level boundary checks confirmed that
LiDAR and Radar measurements themselves repeat
during the investigated long unchanged intervals.

## 3. Interpretation

Exact payload repetition is observed, but the
independent measurement acquisition time is unknown.
An advancing SensorView timestamp does not prove
that a new sensor acquisition occurred.

Repeated measurements must not be treated as
independent new observations by the fusion estimator.

## 4. Configuration evidence

The original and archived C02 V2 INI configurations
have identical SHA256 hashes:

1982F8C80901BB7C90EBB5B4808E999EEDE0FC41F98AB24B523C729948728290

The preserved configuration includes all three
sensor inputs and clear weather with weather effects
disabled. Effective per-sensor acquisition rates
and exact runtime provenance are not fully verified.

## 5. Limitations

- Repetition is not proof of a sensor hardware fault.
- Independent sensor acquisition age is unknown.
- Effective sensor update rates are not established.
- Camera payload changes do not prove detection quality.
- Sensor associations remain partly provisional.
- No energy savings or hardware acceleration are
  demonstrated by Task 25.2.
- Full-rate payload checks do not mean the EKF was
  evaluated on all 2,122 frames.

## 6. Implications for Task 25.3

Use controlled fault injection and matched comparisons.
Track stale/repeated observations separately from
intentional measurement dropout.
Preserve quality constraints and record every
accepted or rejected EKF update.

## 7. Evidence

- task25_12_c02_fullrate_freshness.csv
- task25_13_repetition_runs.csv
- task25_15_reflection_boundary_audit.csv
- task25_19_c02_v2_config_hashes.csv
- task25_20_c02_sensor_health_fullrate.csv
- task25_21_sensor_health_validation.txt

TASK25_02_06B_COMPLETE
