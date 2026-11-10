# Task 25.7C - Reliability-Aware Fallback Policy

## Research objective
Define conservative fallback behavior for the GEMSTAR
Camera/LiDAR/Radar fusion pipeline.

## Measurement eligibility
- NEW_PAYLOAD: new observed content, not proven acquisition freshness.
- REPEATED_PAYLOAD: unchanged content; flag, not automatic sensor failure.
- INJECTED_DROPOUT: exclude the removed update.
- REJECTED_BY_NIS: exclude the rejected update.
- NOT_AVAILABLE and NO_UPDATE: no measurement update.
- INSUFFICIENT_RETURNS: exclude Radar update.
- ACCEPTED: estimator-accepted candidate, not proven accuracy.
- EXPERIMENTAL_ACCEPTED: experimental Camera candidate only.
- Missing NIS must never be treated as zero.
- Provisional associations do not establish true target identity.

## Proposed controller states
NORMAL_CANDIDATE:
No explicitly rejected or injected-dropout measurement
in the evaluated replay sample, with an eligible observation.

DEGRADED_CANDIDATE:
One or more updates are excluded or rejected while
other evidence remains available for provisional processing.

HOLD_OR_ALERT:
Insufficient evidence to continue the prescribed update,
or quality authorization cannot be established.

## Quality authorization
All outputs remain UNVERIFIED until independently
established perception-quality and latency constraints
are checked successfully.

Controller mode and quality authorization are separate.
A provisional estimate must not be labeled VALID solely
because the controller selected NORMAL_CANDIDATE.

## Source limitations
- Full-rate health: 2122 frames.
- Fault replay: 7 scenarios, 24 samples each.
- Acquisition timestamps are not independently known.
- Provisional association and uncalibrated uncertainty remain.
- Replay scenarios are not independent experimental runs.
- Do not join full-rate health and replay records by row index.

## Energy considerations
Energy reduction is not established by this fallback policy.
Later hardware benchmarking must measure total energy per
valid perception result under specified quality and latency
constraints.

## Next
Task 25.7D - Python offline fallback-controller implementation.
