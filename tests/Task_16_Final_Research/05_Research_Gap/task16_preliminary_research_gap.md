# Task 16 - Preliminary Scientific Research Gap

## 1. Proposed Thesis Title

Uncertainty-Constrained Energy-Aware CPU-FPGA Scheduling
for Multi-Sensor Autonomous Vehicle Perception

## 2. Research Background

Autonomous vehicles use Camera, LiDAR and Radar sensors.

Perception processing requires computational resources.
Sensor quality can vary depending on operating conditions.

ARM CPUs offer flexible execution.
FPGAs offer parallel and specialized hardware processing.

However, assigning more processing to an FPGA does not
automatically improve system-level energy efficiency.

Communication, synchronization, hardware transitions
and scheduling overhead must also be considered.

## 3. Established Research Areas

A. Multi-sensor fusion and adverse-weather robustness
Examples: P003, P004, P008, P009, P010, P013-P017.

B. FPGA acceleration and mixed precision
Examples: P001, P011, P018-P020.

C. CPU-FPGA scheduling and energy management
Examples: P002, P005, P006.

D. Sensor uncertainty estimation
Example: P012.

E. Context-aware FPGA reconfiguration
Priority competing research: CR001 (CARMA).

These categories identify related literature.
They do not establish that a research gap exists.

## 4. Candidate Research Gap

Investigate the joint use of:

1. Sensor reliability.
2. Tracking uncertainty.
3. Real-time deadlines.
4. ARM and FPGA execution costs.
5. Communication and switching overhead.
6. Energy consumption.

The proposed scheduler will use these factors to choose
execution placement for selected perception operations.

The key question is whether uncertainty awareness provides
measurable benefits beyond workload-aware scheduling.

Novelty remains provisional until detailed literature
and competing-system reviews are completed.

## 5. Research Question

Can uncertainty-constrained scheduling improve energy
efficiency and perception robustness in ARM-FPGA
multi-sensor processing compared with fixed and
workload-aware execution strategies?

## 6. Experimental Comparisons

B0: CPU-only.
B1: Fixed CPU-FPGA allocation.
B2: Workload-aware CPU-FPGA scheduling.
B3: Uncertainty-aware CPU-FPGA scheduling.

All strategies must be evaluated on comparable data
and under clearly defined resource constraints.

## 7. Research Hypotheses

H1: B3 reduces energy relative to B2 while satisfying
predefined tracking-quality and deadline constraints.

H2: B2 improves execution efficiency relative to B1.

H3: B3 improves robustness during sensor degradation
relative to B2.

H4: B3 scheduling and transition overhead remain
compatible with real-time requirements.

All hypotheses are untested.

## 8. Evaluation Metrics

M01: Energy per frame.
M02: End-to-end latency.
M03: Tracking position error.
M04: Deadline miss rate.
M05: Scheduling overhead.
M06: Hardware transition overhead.
M07: Uncertainty calibration.

Numerical thresholds are not yet established.

## 9. Experimental Scenarios

Clear road:
Investigate low-uncertainty and lighter workload behavior.

Fog:
Investigate camera degradation and increased reliance
on alternative sensor information.

Heavy traffic:
Investigate computational pressure, deadlines
and concurrent processing opportunities.

Sensor failure:
Investigate reliability changes, safe fallback
and recovery behavior.

These are planned experiments, not completed results.

## 10. Scientific Limitations and Novelty Risks

- CARMA has substantial conceptual overlap.
- Existing work already covers adaptive sensor fusion.
- Existing work already covers CPU-FPGA scheduling.
- Existing work already covers mixed-precision optimization.
- Full-text comparisons are still incomplete.
- Sensor reliability needs calibration.
- GEMSTAR sensor and GT timestamps need validation.
- FPGA energy savings require physical measurements.
- Mixed-precision runtime scheduling is optional scope.

## 11. Evidence Required Before Claiming Novelty

1. Review CARMA's full architecture and experiments.
2. Review the remaining competing research.
3. Identify the closest existing scheduling algorithms.
4. Define the scheduler decision and constraints precisely.
5. Establish reproducible baselines.
6. Demonstrate improvements through controlled experiments.
7. Report negative results and limitations.

## 12. Current Status

Literature database: 20 papers.
Comparison matrix: 20 preliminary entries.
Competing research register: 4 candidates.
Experimental baselines: 4.
Research hypotheses: 4.
Evaluation metrics: 7.

Status: PRELIMINARY RESEARCH GAP - NOT YET VERIFIED.
