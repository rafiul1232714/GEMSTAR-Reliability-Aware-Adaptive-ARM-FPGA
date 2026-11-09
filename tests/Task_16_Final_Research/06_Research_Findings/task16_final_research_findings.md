# Task 16 — Final Research Findings

## 1. Research Objective

Identify and assess existing research related to
uncertainty-constrained, energy-aware CPU-FPGA scheduling
for Camera-LiDAR-Radar perception.

## 2. Research Inventory

- Literature papers: 20
- Comparison matrix entries: 20
- Priority competing research: 5
- Research areas assessed: 7
- High novelty-risk areas: 5
- Unresolved novelty-risk areas: 2

## 3. Established Research Areas

The preliminary literature inventory covers:

- Multi-sensor fusion and adverse-weather perception
- FPGA sensor-processing acceleration
- CPU-FPGA heterogeneous scheduling
- Energy-aware resource allocation
- Sensor uncertainty estimation
- Mixed-precision computation

These techniques are established research areas.
Their combination does not automatically establish novelty.

## 4. Closest Competing Research

CARMA investigates context-aware FPGA-based sensor fusion.

DyUnS investigates uncertainty-aware task scheduling
for multiprocessor embedded systems.

Both must be considered when developing the thesis.

Other priority studies investigate real-time scheduling,
data freshness and accelerator allocation.

## 5. Candidate Research Contribution

Investigate whether sensor-derived uncertainty and
tracking-quality constraints can improve energy-aware
ARM-FPGA operation placement compared with workload-only
scheduling.

This contribution is PROVISIONAL.

The current evidence is not sufficient to claim that
no previous work has demonstrated the same approach.

## 6. Experimental Design

- Experimental baselines: 4
- Research hypotheses: 4
- Evaluation metrics: 7
- Processing operations selected: 5
- Experimental workflow stages: 8

## 7. Primary Hardware Candidate

LiDAR ROI filtering was selected as the first candidate
for CPU-versus-FPGA acceleration experiments.

Secondary candidates are LiDAR spatial aggregation
and Camera grayscale/gradient preprocessing.

Radar filtering remains optional.

Object association and tracking initially remain on ARM.

## 8. Research Evaluation

The main measurements will include:

- Energy per frame
- End-to-end latency
- Tracking position error
- Deadline-miss rate
- Scheduling overhead
- Hardware transition overhead
- Uncertainty calibration

## 9. Scientific Limitations

- Full-text reviews are incomplete for much of the literature.
- Some bibliographic metadata still requires verification.
- Several comparison fields are not yet established.
- The research-gap claim remains provisional.
- No scheduler performance improvements are demonstrated.
- No ARM-FPGA hardware energy measurements exist yet.
- Real-time and tracking-quality thresholds remain TBD.

## 10. Conclusion

Task 16 has established a structured preliminary
literature review and a testable research direction.

The main candidate contribution is uncertainty-constrained
ARM-FPGA execution scheduling for multi-sensor perception.

Novelty and performance require further verification
and experimental validation.

Status: PRELIMINARY RESEARCH DESIGN COMPLETE.
