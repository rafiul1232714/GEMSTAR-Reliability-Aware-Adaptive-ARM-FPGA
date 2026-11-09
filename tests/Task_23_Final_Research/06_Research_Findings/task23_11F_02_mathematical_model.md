# Task 23.11.F.2 - Mathematical LiDAR Availability Model

## Purpose

Define a reproducible LiDAR availability indicator for the
GEMSTAR controlled-weather experiment.

## Inputs per frame

N_total:
    Number of LiDAR reflection slots.

N_positive:
    Number of reflections with finite positive
    time_of_flight and finite positive signal_strength.

timestamp:
    OSI SensorView frame timestamp.

frame_present:
    Whether a LiDAR SensorView is available.

## Primary mathematical score

R_availability = N_positive / N_total

Applicable only when the frame and timestamp are valid
and N_total > 0.

Range: 0 <= R_availability <= 1.

The metric measures positive-return availability only.

## Valid-return rule

A reflection counts as positive when:

- time_of_flight is finite
- time_of_flight > 0
- signal_strength is finite
- signal_strength > 0

## Frame status

VALID:
    Frame and timestamp valid, positive returns > 0.

NO_RETURNS:
    Frame and timestamp valid, positive returns = 0.

MISSING_FRAME:
    No LiDAR view is available.

EMPTY_FRAME:
    LiDAR view exists but contains zero reflection slots.

INVALID_TIMESTAMP:
    Timestamp missing, nonfinite, negative or non-monotonic
    relative to the previous accepted frame timestamp.

## Score behaviour

VALID:
    Calculate N_positive / N_total.

NO_RETURNS:
    Return score = 0.

MISSING_FRAME:
    Return score = None.

EMPTY_FRAME:
    Return score = None.

INVALID_TIMESTAMP:
    Return score = None.

A zero score and an undefined score must remain distinguishable.

## Reference measurements

Clear:
    N_positive = 5090
    N_total = 5271

Fog MOR 100:
    N_positive = 5090
    N_total = 5271

Fog MOR 20:
    N_positive = 0
    N_total = 5271

## Scientific constraints

The availability score does not prove detection accuracy,
tracking quality, calibration quality or physical sensor
reliability.

The current controlled scene has identical LiDAR reflection
values across frames.

No additional arbitrary weighting coefficients will be
introduced at this stage.

## F.3 implementation requirements

Implement a reusable Python scoring function.

Return:
- availability_score
- status
- positive_returns
- total_reflections

Validate input values and provide explicit handling for
missing frames, empty frames and invalid timestamps.

## Acceptance criteria

- Mathematical formula documented.
- Score range defined.
- Missing-data behaviour defined.
- Zero returns distinguished from missing data.
- Reference measurements included.
- Limitations documented.

## Amendment after Task 23.11.F.6

MALFORMED_FRAME:
    The reflection collection or individual reflection
    structure is malformed.

    availability_score = None

    This status is distinct from NO_RETURNS.

The original mathematical score remains unchanged.
This amendment documents the hardened implementation.
