# Task 23.11.F.5C - Reliability Validation Findings

## Objective

Evaluate whether the LiDAR availability-scoring algorithm
produces consistent, interpretable results across controlled
Clear and Fog simulations.

## Input evidence

The following GEMSTAR SensorView recordings were evaluated:

- Clear: 13,819 frames
- Fog MOR 100: 12,386 frames
- Fog MOR 20: 14,597 frames

Total analyzed frames: 40,802.

## Reliability metric

R_availability = N_positive / N_total

A positive reflection requires:

- Finite positive time_of_flight
- Finite positive signal_strength

The score is between 0 and 1 for valid, nonempty frames.

## Experimental results

| Condition | Mean availability | Status |
|---|---:|---|
| Clear | 0.965661165 | VALID |
| Fog MOR 100 | 0.965661165 | VALID |
| Fog MOR 20 | 0.000000000 | NO_RETURNS |

## Validation checks

1. All 40,802 frames were processed by the scoring module.
2. Frame-level CSV counts matched Task E reference measurements.
3. Frame timestamps increased strictly within each recording.
4. Clear and Fog MOR 100 scores were equal within tolerance.
5. Fog MOR 20 scores were zero.
6. The weather-score ordering test passed.

## Scientific interpretation

The metric measures positive LiDAR return availability
within a recorded SensorView frame.

The experimental ordering is:

R_Clear = R_Fog100 > R_Fog20

Fog MOR 20 completely invalidated the positive returns
in this controlled validation scene.

The observation is consistent with the inspected
reflectivity-dependent distance-cutoff weather model.

## Scientific limitations

- Return availability is not object-detection accuracy.
- The score is not a calibrated probability of correctness.
- A positive return can still represent noise or an incorrect
  measurement.
- A zero return can result from weather, geometry, sensor
  limitations or the absence of a detectable reflection.
- The controlled scene contains identical LiDAR reflection
  patterns across frames.
- The experiments do not validate dynamic traffic,
  ego-motion or changing sensor viewpoints.
- Real-world fog attenuation has not been validated.
- Camera and Radar reliability have not been evaluated here.
- No claim about multisensor fusion accuracy is supported.
- Hardware energy savings are not established by this metric.

## Missing-data distinction

The scoring module distinguishes:

VALID:
    The frame exists and contains positive returns.

NO_RETURNS:
    The frame exists but contains zero positive returns.

MISSING_FRAME:
    No LiDAR measurement is available.

EMPTY_FRAME:
    The measurement contains no reflection slots.

INVALID_TIMESTAMP:
    Timestamp validity requirements are not satisfied.

Undefined availability scores must remain distinguishable
from numerical zero scores.

## Relevance to the future scheduler

The validated availability score can be used as one input
to a future reliability-aware scheduler.

The scheduler must additionally consider:

- Perception quality constraints
- Validated sensor-fusion performance
- Execution deadlines
- Measured processing energy
- Sensor and processing availability

A high availability score alone must never justify
relaxing a perception-quality constraint.

## Conclusion

Task F.5 confirms consistency of the LiDAR
measurement-availability scoring algorithm with the
controlled GEMSTAR weather experiment.

Further dynamic-scene, sensor-specific and
ground-truth-based validation is necessary before
interpreting this metric as operational sensor reliability.
