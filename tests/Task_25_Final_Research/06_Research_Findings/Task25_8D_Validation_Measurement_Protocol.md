# Task 25.8D - Quality Validation Measurement Protocol

## Objective

Define the measurements necessary to demonstrate
quality-constrained perception on GEMSTAR.

This document is a prospective validation protocol.
It is not a completed measurement campaign.

## G01 - GT-center accuracy

Use frame-matched estimates and independently verified
GroundTruth target identities.

Verify coordinate-frame consistency before measuring
object-center error.

Do not assume a LiDAR cluster median is a vehicle center.

Choose and document the applicable acceptance metric and
limit before evaluating the reserved validation evidence.

Historical GT errors may inform feasibility, but cannot
be used to claim an independently prespecified threshold.

## G02 - Valid-output coverage

Define the denominator before evaluation.

Include eligible frames that produce no output or a withheld
result. Do not calculate coverage using only successful frames.

Distinguish:
- Processing candidate
- Output actually emitted
- Independently valid perception result
- Withheld or unavailable result

The current 159 provisional decisions are not independently
validated perception results.

## G03 - Association integrity

Compare algorithmic track IDs with independently
confirmed GroundTruth object identities.

Do not treat a zero Radar-to-box distance as proof of
correct association.

Retain unresolved, incorrect and ambiguous associations
as distinct evaluation outcomes.

## G04 - EKF uncertainty consistency

Record innovation vectors, innovation covariance and,
where appropriate, state covariance.

Compute NIS or NEES only when the required measurements,
covariance matrices and reference truth are available.

Use appropriate degrees of freedom and statistical tests.

Account for correlated samples and reused source recordings.

Do not treat unavailable NIS values as zero.

## G05 - p99 end-to-end latency

Define the processing boundary, execution platform,
clock source, warm-up policy and run conditions.

Measure time from a clearly defined input-ready event
to a clearly defined output-ready event using a
monotonic clock.

Record per-sample latency and calculate the sample p99
with the quantile method documented.

A deadline must be fixed before final evaluation.

Software replay latency and later ARM-FPGA latency must
be reported separately and compared fairly.

Do not substitute selected-frame spacing for latency.

## G06 - Overall valid-result authorization

No result is authorized solely because the fallback
controller selected NORMAL_CANDIDATE.

Every required hard gate must be independently evaluated
against a prespecified criterion.

Missing evidence means UNVERIFIED, not PASS.

## Evaluation design

Separate development and validation evidence where possible.

Prefer fresh matched runs or a reserved holdout for final
validation. Record scenario identity, frame identity,
software version, configuration hashes and test conditions.

For controlled fault injection, preserve identical base
inputs and report fault changes explicitly.

Report sample dependence and limitations.

## Energy-efficiency evaluation

Energy optimization is allowed only after the required
quality and latency criteria have been satisfied.

Measure total platform energy rather than assuming that
fewer sensor updates automatically save energy.

Report energy per valid perception result, including
the cost of processing and withheld outputs as appropriate
to the defined system boundary.

No hardware energy result is established here.

## Current status

G01-G06: PENDING / UNVERIFIED.

Numerical acceptance limits: not assigned.

Original Task 24 and Task 25 measurements: unchanged.

## Next step

Task 25.8E: establish a traceable validation readiness
matrix identifying which evidence can be collected now
in software and which depends on later instrumentation
or ARM-FPGA measurements.
