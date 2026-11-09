# Task 23.9 — Camera Calibration Research Report

Generated: 2026-11-03T21:09:45

## Objective
Validate RGB camera recording and the simulated perspective
response to a controlled 2 m target displacement.

## Setup
- Simulator: GEMSTAR / Unreal Engine
- Resolution: 640 x 480
- Image payload: raw RGB, 921600 bytes per frame
- Camera position: (1940, -2650, 250) cm
- Horizontal field of view: 90 degrees
- Cube side length: 300 cm
- Baseline target front-face distance: 8.50 m
- Displaced target front-face distance: 10.50 m

## Recorded measurements
- Baseline front-face width: 112 pixels
- Displaced front-face width: 92 pixels
- Measured width ratio: 0.821429
- Ideal pinhole ratio: 0.809524
- Measured width reduction: 17.86%
- Expected width reduction: 19.05%
- Absolute ratio deviation: 0.011905

## Validation
Result: PASS — controlled simulated perspective consistency.

The automatic rectangles were visually checked against the
calibration target. This test uses a screening tolerance of
0.03 absolute width ratio, not an independently established
camera-accuracy specification.

## Important limitations
- The apparent cube edges are identified using image gradients.
- Only a limited sample of captured frames was compared.
- Pixel boundaries and antialiasing introduce measurement uncertainty.
- Weather-mode consistency is NOT validated: a previous runtime
  log showed Fog despite the calibration INI requesting Clear.
- This experiment does not establish physical camera calibration.
- No CPU/FPGA energy or latency measurements were performed.
- Original map restoration was confirmed in the recording logs.

## Evidence
- Measurements CSV: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\02_CSV_Data\task23_09_camera_auto_measurements.csv
- Annotated image: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\03_Graphs\task23_09_auto_detected_cubes.png
- Evidence manifest: E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research\05_Raw_Data_References\task23_09_final_camera_manifest.csv
- Baseline OSI: E:\GEMSTAR_Project\gemstar\Output\20261103T194105Z_sv_380_X_55_GEMSTARCAMERACLEAR23.osi
- Displaced OSI: E:\GEMSTAR_Project\gemstar\Output\20261103T195644Z_sv_380_X_769_GEMSTARCAMERADISPLACED23.osi

## Conclusion
Task 23.9 RGB payload and controlled geometric response: PASS.
Weather-effect behavior remains a documented follow-up.

Next: review remaining Task 23 research requirements before
Task 24 camera-LiDAR-radar association and fusion.
