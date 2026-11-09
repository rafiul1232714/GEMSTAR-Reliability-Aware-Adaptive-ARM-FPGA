# Task 23.8 — Final LiDAR Calibration Report

Generated: 2026-11-03T20:19:06

## 1. Research objective
Validate LiDAR range response to a controlled 2 m target displacement
in the isolated GEMSTAR simulation environment.

## 2. Experimental configuration
- Sensor: GEMSTAR SimpleLidar
- LiDAR origin: (1940, -2650, 250) cm
- Orientation: (0, 0, 0) degrees
- Horizontal rays: 251
- Vertical rays: 21
- Total rays per scan: 5271
- Configured range: 50 m
- Validation target: cube with 300 cm sides
- Baseline target center X: 2940 cm
- Displaced target center X: 3140 cm
- Baseline target front face X: 2790 cm
- Displaced target front face X: 2990 cm

## 3. Experimental datasets
- Preliminary fog recording: 20261103T190206Z_sv_380_X_336_GEMSTARLIDAR23.osi
- Clear baseline: 20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi
- Clear displaced: 20261103T191205Z_sv_380_X_604_GEMSTARLIDARDISPLACED23.osi
- Ten frames per recording were used in displacement analysis.

## 4. Results
- Baseline geometric candidates: 1071
- Matching rays: 765
- Unmatched candidates: 306
- Matching proportion: 71.43%
- Median matched range increase: 2.013944 m
- Median absolute geometry error among matched rays: 0.000000 m
- Maximum absolute geometry error among matched rays: 0.000001 m
- Controlled displacement status: PASS

## 5. Interpretation
The matched LiDAR rays responded to the controlled target displacement
in a manner consistent with the expected simulated geometry.

The measured median path-length increase is approximately 2.014 m,
rather than exactly 2 m, because the rays intersect the front face
at different angles.

The baseline candidate selection used range proximity, rather than
independently verified object identity.

## 6. Limitations
- Not all candidate rays met the displacement criterion.
- Candidate rays can hit other surfaces or become occluded.
- Geometric matching was evaluated only on the selected ray subset.
- Near-zero error in that subset is not an independent accuracy metric.
- Recordings were made separately and are not synchronized.
- The clear/fog comparison showed no observed change in ranges or
  positive-range counts in the tested frames; intensity and weather
  degradation require separate investigation.
- This is simulated geometric validation, not physical LiDAR calibration.
- CPU/FPGA energy and processing latency were not measured here.

## 7. Reproducibility evidence
- Ray comparison CSV: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\02_CSV_Data\task23_08_lidar_displacement_rays.csv
- Displacement graph: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\03_Graphs\task23_08_lidar_displacement.svg
- Source-file hash manifest: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\05_Raw_Data_References\task23_08_final_evidence_manifest.csv
- Original validation map was restored after acquisition, according
  to the experiment's PowerShell verification output.

## 8. Conclusion
Task 23.8 controlled LiDAR geometric displacement validation: PASS.

Next task: Task 23.9 Camera calibration and validation.
