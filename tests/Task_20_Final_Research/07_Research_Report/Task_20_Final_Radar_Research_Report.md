# Task 20 — GEMSTAR Automotive Radar Research

## 1. Research objective

Investigate and validate radar data generation, processing,
coordinate reconstruction, configuration and ground-truth
comparison using the GEMSTAR simulation platform.

## 2. Technical environment

- DLR GEMSTAR simulation platform
- Unreal Engine 5.8
- SUMO traffic simulation
- C++ radar implementation
- Python OSI parsing and analysis
- NumPy and Matplotlib-based diagnostics
- OSI SensorView and GroundTruth recordings

## 3. Original radar investigation

The original radar implementation used a 10 m tracing range.

Evidence:
- C++ source inspection
- Runtime diagnostic: 10.000 m
- Original maximum observed return: approximately 9.99 m

## 4. Radar configuration correction

A configurable radar range was implemented by modifying:

- SensorConfigurationData.h
- RadarSensorManager.cpp
- SimpleRadar.cpp
- DefaultGemstar.ini

The experimental configuration used Range=50.

The Unreal Editor build succeeded and the runtime configuration
diagnostic confirmed 50.000 m.

## 5. Experimental comparison

Original 10 m recording:
- Candidate returns: 2,957
- Median return range: approximately 5.9114 m
- Maximum return range: approximately 9.9814 m

Corrected 50 m recording:
- Candidate returns: 5,696 in the first 100 frames
- Median return range: approximately 8.5541 m
- Maximum return range: approximately 49.9283 m
- Candidate returns beyond 10 m: 2,687

The recordings were not paired under verified identical
simulation states. Differences in return counts cannot be
attributed solely to the radar-range correction.

## 6. Startup artifact

Fifty near-zero candidate returns occurred exclusively in
frame 0 of the corrected recording.

Frame 0 was excluded from subsequent external-object analysis.
The exact origin of these near-zero observations is unresolved.

## 7. Ground-truth audit

For the corrected recording, frames 1-99 showed:

- 99 matching SensorView/GroundTruth timestamp labels
- 112 external moving-object observations
- 3 unique external moving-object IDs
- 5 centre observations inside the 50 m range and FoV

Matching timestamps do not independently resolve the possible
difference between simulator pose-sampling instants.

## 8. External-vehicle association

Investigated target:
- Model: BP_Large_Car_C
- Object ID: 76765
- Frames: 95-99

Under the doubled GT-box interpretation:
- 10 predicted ray-box intersections
- Ray 44: five positive radar returns around 41.2556 m
- Ray 54: five intersections with no valid return
- Predicted box entry distances: approximately 24.89-27.51 m

The measured return range did not agree with the predicted
vehicle surface intersection. Consequently, those positive
returns cannot be independently attributed to the vehicle.

## 9. Verified achievements

- Identified the original radar-range configuration limitation
- Implemented a configurable range correction
- Successfully compiled the modified GEMSTAR modules
- Verified a 50 m runtime configuration
- Demonstrated recorded radar returns beyond 10 m
- Created reproducible processing and diagnostic artifacts

## 10. Limitations

- External-object detection accuracy remains unverified
- Actual Unreal collision-mesh hit identity is unavailable
- Bounding-box dimension semantics require further validation
- Radar-to-world transform needs independent validation
- Pose-sampling timing uncertainty remains
- No CPU-versus-FPGA power or energy measurements were made

## 11. Research conclusion

The configurable radar-range correction is supported by
C++ source inspection, successful compilation, runtime logs
and recorded radar measurements.

The corrected radar extends measured returns from below
10 m to almost 50 m.

This establishes a simulator engineering improvement, not
a validated external-object detection rate or a measured
hardware energy-efficiency improvement.

## 12. Future research

- Controlled vehicle-target scenes
- Ray-hit actor identification
- Independent collision and world-coordinate verification
- Radar processing optimization in Python, MATLAB and C++
- Sensor fusion with Camera and LiDAR
- Later CPU-FPGA benchmarking of latency, energy and quality
