# Task 25.8E - Validation Readiness Matrix

## Objective

Determine which quality validation activities can begin
using the current GEMSTAR software environment and
which require additional evidence or hardware.

This is a readiness assessment, not completed validation.

## G01 - Position accuracy

Software validation can begin now.

Existing measurements contain historical GT-center errors.
However, LiDAR cluster median versus GT-center geometry
and coordinate assumptions must be addressed.

Required: a consistent target-center definition,
independent validation observations, and a justified
accuracy criterion fixed before final evaluation.

## G02 - Valid output coverage

Software validation can begin now.

Existing fallback results contain 168 decisions:
159 provisional and 9 hold classifications.

These are not 159 independently valid perception outputs.

Required: eligible-frame denominator, emitted-output
records, independent validity and fixed coverage criterion.

## G03 - Association integrity

Software validation can begin now.

Existing temporal and spatial associations provide
development evidence, but target identity is provisional.

Required: independent GT identity assignment,
ambiguity handling and prespecified correctness criteria.

## G04 - EKF uncertainty consistency

Software investigation can begin now.

Existing records contain 23 residual comparisons and
four accepted finite Radar NIS values.

Required: innovation and state covariance evidence,
appropriate statistical tests, relevant degrees of
freedom and clear treatment of sample dependence.

## G05 - p99 processing latency

Instrumented software measurement can begin now
without an ARM-FPGA board.

Required: timing boundaries, monotonic-clock timestamps,
processing platform, test workload, p99 calculation method
and a fixed deadline.

The later ARM-FPGA implementation requires separate
platform-specific latency measurements.

Selected-frame spacing does not represent processing latency.

## G06 - Overall output authorization

The gate aggregator can be designed in software now.

However, authorization cannot pass until the required
independent quality and latency evidence is available
and evaluated against prespecified criteria.

Missing evidence must remain UNVERIFIED, never PASS.

## Immediate software research priorities

First, resolve target-coordinate and identity questions.

Second, prepare independent output-validity and
coverage evaluation.

Third, improve EKF covariance diagnostics.

Fourth, instrument CPU processing latency.

Finally, implement and audit fail-closed authorization
once the required acceptance criteria are established.

These activities can be prepared without physical
ARM-FPGA hardware.

## Hardware dependency

Hardware is not needed to define these six gates or to
begin software-based validation.

Later ARM-FPGA measurements are necessary to evaluate
the actual accelerated implementation's latency and
energy consumption.

Software results cannot substitute for hardware energy
measurements.

## Research validity

No numeric quality or latency thresholds were added.

All quality gates remain PENDING / UNVERIFIED.

The current research does not authorize any result
as valid for energy-efficiency benchmarking.

## Next step

Task 25.8F - Consolidate Task 25.8 findings and
record unresolved validation dependencies before
Task 25.9 cross-check and research integration.
