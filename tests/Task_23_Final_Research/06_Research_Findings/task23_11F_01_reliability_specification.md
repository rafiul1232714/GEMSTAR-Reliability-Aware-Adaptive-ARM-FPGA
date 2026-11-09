# Task 23.11.F.1 - LiDAR Reliability Specification

## Objective

Develop an interpretable LiDAR measurement-availability score
for later reliability-aware sensor fusion and ARM-FPGA scheduling.

## Input evidence

- Clear: 13,819 frames
- Fog MOR 100: 12,386 frames
- Fog MOR 20: 14,597 frames
- Reflection slots per frame: 5,271

## Valid-return definition

A LiDAR reflection is considered positive when:

1. time_of_flight is finite and greater than zero.
2. signal_strength is finite and greater than zero.

## Primary score

R_availability = positive_returns / total_reflection_slots

Score range: 0 to 1.

## Experimental reference scores

Clear: 5090 / 5271 = approximately 0.96566116

Fog MOR 100: 5090 / 5271 = approximately 0.96566116

Fog MOR 20: 0 / 5271 = 0

## Missing-data handling

The algorithm must distinguish:

- Zero positive returns
- Missing LiDAR frame
- Zero reflection slots
- Invalid numerical measurements
- Invalid timestamps

Missing or malformed measurements must not silently receive
a high reliability score.

## Scientific limitations

This score measures positive-return availability.

It does not establish:

- Object detection accuracy
- Tracking accuracy
- Ground-truth agreement
- Physical fog-model accuracy
- Sensor-fusion correctness

The current controlled validation scene produces identical
LiDAR reflection patterns across frames.

## Future research use

The validated availability score will become one input to
the later reliability-aware fusion and ARM-FPGA scheduler.

Energy optimization and sensor-processing decisions will
be evaluated separately against measured performance and
quality constraints.
