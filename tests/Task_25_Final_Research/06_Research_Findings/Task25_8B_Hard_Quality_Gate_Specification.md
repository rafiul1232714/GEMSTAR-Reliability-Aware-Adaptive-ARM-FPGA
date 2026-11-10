# Task 25.8B - Hard Perception-Quality Gate Specification

## Purpose

Define the evidence and acceptance requirements needed
before GEMSTAR fallback outputs may be called valid.

This step specifies evaluation requirements.
It does not establish numerical performance limits.

## Current research evidence

Seven offline fault scenarios have historical GT error
measurements. Each includes 23 GT evaluation samples.

These scenario results share underlying experimental
measurements and are not independent trials.

Task 25.7 produced 168 deterministic policy classifications.
Those classifications are not independently validated
perception outputs.

## Hard gate requirements

G01: GT-center position accuracy must satisfy a
prespecified and justified acceptance limit.

G02: Valid-output coverage must meet a defined minimum.
Coverage must use an explicit evaluation denominator
and must not ignore withheld or missing outputs.

G03: Association correctness must be supported by
independent identity or geometric validation.

G04: EKF uncertainty consistency must be evaluated using
appropriate residual or covariance-based evidence.

G05: End-to-end p99 processing latency must be measured
and compared against a prespecified deadline.

G06: Overall valid-result authorization requires every
applicable hard gate to pass.

## Current authorization

All gates are UNVERIFIED.

No GT-error threshold is automatically inferred from
the observed baseline or fault-scenario errors.

No numerical latency limit is invented.

The historical source reports include references to
measurement acceptance criteria. These must be inspected
before treating any statement as a binding perception gate.

## Important research limitations

LiDAR track locations are cluster medians and are not
verified object geometric centers.

Sensor mounting translations agree with the archived
C02 V2 configuration, but full geometric calibration
remains unverified.

Association is provisional.

Radar NIS has only four finite accepted source values.

Acquisition age is not independently known.

The current fallback controller does not recompute EKF
outputs under its decisions.

## Energy optimization principle

Only processing configurations that satisfy the applicable
perception-quality and latency gates may participate
in comparisons of energy per valid result.

No energy savings are claimed.

## Next

Task 25.8C - Audit the available evidence against these
gates, explicitly distinguishing unavailable measurements,
unverified thresholds and genuine test failures.
