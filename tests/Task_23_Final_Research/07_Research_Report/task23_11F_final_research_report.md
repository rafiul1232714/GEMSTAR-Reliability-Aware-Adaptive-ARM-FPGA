# Task 23.11.F - Final LiDAR Reliability Research Report

## 1. Research objective

Develop, implement and validate a reproducible LiDAR
positive-return availability metric for controlled
GEMSTAR weather simulations.

This metric is intended as one future input to the
reliability-aware ARM-FPGA scheduling architecture.

## 2. Mathematical definition

R_availability = N_positive / N_total

N_positive counts reflection slots with finite,
positive time_of_flight and signal_strength values.

N_total represents all reflection slots in a frame.

Valid-frame score range: 0 to 1.

The metric is not a calibrated probability of
object-detection correctness.

## 3. Experimental datasets

Clear:
  13,819 frames

Fog MOR 100:
  12,386 frames

Fog MOR 20:
  14,597 frames

Total:
  40,802 frames

All recordings originated from the controlled
GEMSTAR static validation scene.

## 4. Experimental reliability results

| Weather | Positive returns/frame | Slots/frame | Mean score |
|---|---:|---:|---:|
| Clear | 5090 | 5271 | 0.965661165 |
| Fog MOR 100 | 5090 | 5271 | 0.965661165 |
| Fog MOR 20 | 0 | 5271 | 0.000000000 |

The observed availability relationship is:

R_Clear = R_Fog100 > R_Fog20

This ordering was independently checked against
the Task E reference summary.

## 5. Implementation

The reusable Python module is:

01_Code/task23_11F_lidar_reliability.py

The main scoring interface is:

score_lidar_frame(
    lidar_view,
    timestamp,
    previous_timestamp=None
)

Returned fields:

- availability_score
- status
- positive_returns
- total_reflections

## 6. Status handling

VALID:
  Valid measurement with positive returns.

NO_RETURNS:
  Valid measurement with zero positive returns.

MISSING_FRAME:
  No LiDAR sensor view.

EMPTY_FRAME:
  LiDAR view with no reflection slots.

INVALID_TIMESTAMP:
  Timestamp missing, invalid or non-monotonic.

MALFORMED_FRAME:
  Reflection structure is malformed.

Zero availability and an undefined score are
different outcomes.

## 7. Verification performed

- Seven original functional tests passed.
- Nine abnormal-reflection tests passed.
- Ten standard timestamp and availability tests passed.
- Four structural inputs returned MALFORMED_FRAME
  without raising exceptions.
- Five formal malformed-input assertions passed.
- Fifteen initial real-OSI frames passed.
- All 40,802 recorded frames were scored.
- Frame-level CSV integrity checks passed.
- Weather-score ordering checks passed.
- Timestamp ordering was verified.

These tests provide evidence for the tested behaviours,
not proof of all possible input and runtime conditions.

## 8. Generated research artifacts

Python:
  Reusable scoring and validation scripts.

CSV:
  Frame-level availability results.
  Weather-level summary.
  MATLAB-readable weather comparison.

Figures:
  Weather comparison graph.
  Frame-level reliability graph.

Research findings:
  Mathematical specification.
  Validation interpretation.
  Robustness findings.

Evidence:
  SHA256 manifest of 20 Task F files.

## 9. Scientific limitations

The current experiments use a controlled static scene
with identical LiDAR reflection values across frames.

Consequently, the results do not establish:

- Dynamic-scene reliability
- Object-detection accuracy
- Ground-truth object matching accuracy
- Sensor tracking performance
- Real-world fog-model correctness
- Camera and Radar reliability
- Multisensor fusion performance
- CPU versus FPGA energy savings
- End-to-end scheduling effectiveness

Zero positive returns are not universally equivalent
to sensor hardware failure.

## 10. Connection to later research

Task F establishes an interpretable LiDAR
measurement-availability indicator.

Future tasks must evaluate:

- Dynamic driving scenes
- Ground-truth-based perception quality
- Sensor association and tracking
- CPU and FPGA execution costs
- Energy per valid perception result
- Deadline constraints
- Reliability-aware scheduler decisions

The reliability score should support scheduling
decisions, not replace validated perception quality.

## 11. Conclusion

Task 23.11.F established a reusable and tested
LiDAR positive-return availability measurement.

The controlled-weather experiments produced
consistent scoring behaviour across 40,802 frames.

The algorithm now distinguishes valid no-return
measurements from missing and malformed inputs.

The current research supports progression toward
preliminary workload profiling and later sensor-fusion
research, subject to the documented limitations.
