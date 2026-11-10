# Task 25.8 - Hard Perception-Quality Constraints

## 1. Research objective

Define and audit the requirements for authorizing
reliable GEMSTAR Camera/LiDAR/Radar perception outputs.

The intended optimization objective is minimum measured
total system energy per valid perception result, subject
to hard perception-quality and p99 latency requirements.

Task 25.8 defines the validation framework.
It does not establish successful compliance.

## 2. Completed research components

- 25.8A: Existing quality-evidence inventory
- 25.8B: Six hard quality-gate definitions
- 25.8C: Quality-gate evidence audit
- 25.8D: Validation measurement protocol
- 25.8E: Software and hardware readiness assessment
- 25.8F: Consolidated research report

## 3. Historical measurement evidence

Seven related controlled fault scenarios contain
23 GroundTruth evaluation samples each.

There are 161 scenario-evaluation entries in total.
They are not 161 independent recordings.

The existing fallback controller generated
168 policy classifications:

- NORMAL_CANDIDATE: 143
- DEGRADED_CANDIDATE: 16
- HOLD_OR_ALERT: 9

All 168 classifications remain UNVERIFIED with respect
to perception-quality authorization.

The controller currently classifies recorded conditions.
It does not rerun the EKF or independently validate
replacement perception outputs.

## 4. Quality-gate evidence matrix

| Gate | Evidence status | Next validation activity |
|---|---|---|
| G01 - GT_CENTER_ACCURACY | EVIDENCE_AVAILABLE_THRESHOLD_UNSET | Verify coordinate conventions and object-center reference |
| G02 - VALID_OUTPUT_COVERAGE | PARTIAL_EVIDENCE | Define eligible-frame denominator and instrument emitted versus withheld outputs |
| G03 - ASSOCIATION_INTEGRITY | PARTIAL_EVIDENCE | Build independently verified track-to-GT identity evaluation |
| G04 - UNCERTAINTY_CONSISTENCY | PARTIAL_EVIDENCE | Instrument innovation vectors and covariance matrices |
| G05 - P99_PROCESSING_LATENCY | NOT_MEASURED | Define timing boundaries and instrument CPU replay using a monotonic clock |
| G06 - OVERALL_VALID_RESULT | INSUFFICIENT_FOR_AUTHORIZATION | Implement a fail-closed gate aggregator with UNVERIFIED handling |

## 5. Accuracy and geometry limitations

Historical GT-center errors have been measured.

However, the LiDAR track coordinate represents a
cluster median rather than a verified object center.

Nominal LiDAR and Radar mounting translations match
the archived C02 V2 configuration.

Full coordinate-frame and object-center calibration
remain unverified.

Historical measurements must not be used to
retroactively choose convenient acceptance thresholds.

## 6. Association and uncertainty limitations

LiDAR temporal and Radar spatial associations are
provisional, not independently verified target identities.

The existing uncertainty investigation identified
systematic GT residual discrepancies.

Only four accepted finite Radar NIS values are available
from the original selected-frame source.

Full calibrated covariance consistency has not been shown.

## 7. Freshness and timing limitations

The full-rate recording contains 2,122 frames.

Independent sensor acquisition age is unknown throughout.

Repeated payloads are evidence of unchanged content,
not automatically failed or overdue sensors.

The selected-frame spacing must not be interpreted
as end-to-end processing latency.

The current fault-replay records do not contain measured
per-decision processing latency.

No p99 latency compliance claim is permitted.

## 8. Required future validation

G01 requires frame-matched GT-center accuracy using
independently verified geometry and a prespecified limit.

G02 requires a defined denominator and independent
validity labels for emitted and withheld results.

G03 requires independently verified target identities
and a prespecified association acceptance criterion.

G04 requires sufficient covariance, innovation and
reference-truth evidence for appropriate statistical tests.

G05 requires instrumented end-to-end processing latency,
documented timing boundaries and a fixed deadline.

G06 requires every applicable hard gate to pass before
valid-result authorization is granted.

## 9. Software and hardware execution

Software validation can begin without physical
ARM-FPGA hardware.

CPU timing instrumentation can also begin now.

Actual ARM-FPGA latency and energy efficiency must be
measured later on the corresponding hardware.

Software results cannot substitute for hardware
energy consumption measurements.

## 10. Authorization and interpretation

QUALITY_AUTHORIZATION: UNVERIFIED

VALIDATED_GATE_PASSES: 0

NUMERIC_ACCEPTANCE_LIMITS_ASSIGNED: 0

ENERGY_SAVINGS_CLAIMED: NO

These findings indicate missing validation evidence,
not six demonstrated performance failures.

No fallback result is authorized as independently
valid by Task 25.8.

## 11. Next stage

Task 25.9 will independently cross-check Python
and MATLAB analysis outputs, source schemas,
sample counts and recorded numerical conclusions.

Task 25.10 will consolidate and archive Task 25
after all required verification checks pass.

Future validation experiments must maintain clear
source provenance, matched comparisons and immutable
historical input measurements.
