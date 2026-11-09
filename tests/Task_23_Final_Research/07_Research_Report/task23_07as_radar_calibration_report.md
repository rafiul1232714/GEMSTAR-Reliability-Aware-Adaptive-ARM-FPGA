# Task 23.7AS — Radar Calibration and Displacement Validation

Generated: 2026-11-03T19:14:42

## Objective
Validate controlled geometric range response in the GEMSTAR
radar-only simulation before proceeding to multi-sensor processing.

## Setup
- Unreal Engine / GEMSTAR isolated research validation map
- Radar origin: (1940, -2650, 250) cm
- Radar orientation: (0, 0, 0) degrees
- Four central diagnostic rays: 44, 45, 54, 55
- Nominal calibration cube: 300 cm side length
- Initial cube center X: 2940 cm
- Displaced cube center X: 3140 cm

## Verified results
- Baseline ray 44: 853.407 cm
- Displaced ray 44: 1054.209 cm
- Distance increase: 200.802 cm
- Baseline hit X: 2790.000 cm
- Displaced hit X: 2990.000 cm
- Four central rays satisfy the displacement checks
- Controlled displacement validation: PASS
- Map persistence independently verified during the experiment
- Original map and configuration were restored (per PowerShell output)

## Interpretation
The measured range change is consistent with a 200 cm shift
along world X. Because the rays are slightly angled, their
path-length increase is approximately 200.802 cm rather than
exactly 200 cm.

The initial unchanged-reading investigation was traced to
a map edit that had not persisted. Explicit map saving and an
independent reload fixed the experiment setup.

## Scientific limitations
- Validates a static, idealized simulation geometry
- Does not establish physical Radar sensor accuracy
- Does not measure real Radar noise, false detections or robustness
- Does not establish fog/traffic performance
- Does not measure CPU/FPGA energy or computational latency
- OSI range serialization needs separate end-to-end comparison
  if required for the thesis accuracy claim

## Research evidence
- Baseline log: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\05_Raw_Data_References\task23_07aq_instrumented_runtime.log
- Displaced log: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\05_Raw_Data_References\task23_07ar_final_runtime.log
- Measurement CSV: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\02_CSV_Data\task23_07as_radar_displacement_final.csv
- Comparison graph: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\03_Graphs\task23_07as_radar_displacement.svg
- SHA-256 manifest: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\06_Research_Findings\task23_07as_evidence_hashes.csv

## Outcome
Task 23.7 controlled Radar displacement experiment: PASS.
Next planned sensor calibration: Task 23.8 LiDAR.
