# Task 23.11 - Final Research Consolidation

## 1. Research objective

Establish and validate the controlled LiDAR preprocessing,
measurement-availability scoring, and preliminary
software workload characterization required for
subsequent GEMSTAR sensor-fusion research.

## 2. Completed work

A. Dataset audit
   Controlled source recording and evidence audit.

B. OSI integrity
   Framing, data integrity and timestamp checks.

C. LiDAR preprocessing
   Controlled preprocessing validation.

D. Clear reference
   Clear-weather reference measurements.

E. Controlled weather
   Clear, Fog MOR 100 and Fog MOR 20 experiments.

F. LiDAR reliability
   Scoring algorithm, validation, robustness tests,
   plots, MATLAB CSV and final research report.

G. Preliminary profiling
   Development-PC scoring latency measurements,
   timing distributions and research findings.

H. Final consolidation
   Artifact audit, scientific readiness assessment,
   final reporting and evidence manifest.

## 3. Controlled experiment

Weather        Frames       Positive returns / slots
Clear          13819        5090 / 5271
Fog MOR 100    12386        5090 / 5271
Fog MOR 20     14597        0 / 5271

Total recorded frames evaluated: 40802.

## 4. LiDAR availability

R_availability = positive_returns / reflection_slots

Measured mean scores:

Clear:       0.965661165
Fog MOR 100: 0.965661165
Fog MOR 20:  0.000000000

These values measure positive-return availability,
not object-detection correctness.

## 5. Robustness

The scoring implementation distinguishes:

VALID
NO_RETURNS
MISSING_FRAME
EMPTY_FRAME
INVALID_TIMESTAMP
MALFORMED_FRAME

Functional, numerical edge-case, timestamp and
selected malformed-input tests passed.

## 6. Preliminary scoring workload

Measured on the development PC using Python.

Weather       Mean us       P99 us
Clear         925.187       1256.396
Fog MOR 100   932.944       1365.312
Fog MOR 20    890.777       1073.268

G.2 collected 1800 timing measurements using
three fixed frames and repeated scoring calls.

Disk I/O and protobuf decoding were excluded
from the timed operations.

These measurements are not an ARM, FPGA,
energy or end-to-end latency benchmark.

## 7. Artifacts

The research folder contains:

01_Code
02_CSV_Data
03_Graphs
04_Configurations
05_Raw_Data_References
06_Research_Findings
07_Research_Report

H.1 catalogued 457 files using its supported
artifact extensions before H.2 and H.3.

The final evidence manifest inventories the
selected research files and their SHA256 hashes.

Large raw OSI recordings remain at their
original GEMSTAR output locations.

## 8. Scientific limitations

- Controlled LiDAR reflection patterns were static.
- Dynamic perception accuracy remains unvalidated.
- Positive-return availability is not detection accuracy.
- Real-world fog-model validity is not established.
- Three-sensor association and EKF tracking are not
  established by this Task 23.11 experiment.
- CPU versus FPGA energy efficiency is not measured.
- No hard real-time latency guarantee is established.
- Camera and Radar preprocessing readiness must be
  assessed separately against the broader Task 23 scope.

## 9. Transition to future roadmap work

The selected research roadmap places three-sensor
association and EKF tracking fusion in Task 24.

Fusion reliability is developed further in Task 25.

Formal CPU benchmarking belongs to Task 26.

ARM-FPGA bring-up and hardware energy measurements
belong to their later roadmap tasks.

Any outstanding Task 23 preprocessing prerequisites
must be reviewed before starting Task 24.

## 10. Conclusion

Task 23.11 established a validated controlled-scene
LiDAR availability and preliminary workload foundation.

The completed work is suitable for reproducible
research handover subject to the stated limitations.

Completion of Task 23.11 does not independently
establish completion of every broader Task 23
camera, LiDAR and Radar prerequisite.
