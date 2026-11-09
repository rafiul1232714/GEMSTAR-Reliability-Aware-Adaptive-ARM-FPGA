Title : Reliability-Aware Multimodal Perception with Adaptive Energy Optimization on Heterogeneous ARM–FPGA Systems

## Project Overview

This research project investigates energy-efficient and reliability-aware multimodal sensor processing for autonomous-driving applications using the GEMSTAR simulation framework and a heterogeneous ARM–FPGA computing platform.

The system integrates Camera, LiDAR, and Radar sensor data to study environmental effects, perception reliability, object association, sensor fusion, and adaptive workload execution.

The primary research objective is to **minimize measured system energy consumption per valid perception result while maintaining predefined perception-quality and real-time latency requirements**.

The project follows a software-first, measurement-driven methodology, beginning with simulation, sensor data analysis, and fusion algorithms before progressing to FPGA acceleration, hardware energy measurement, and live adaptive scheduling.

## Research Objectives

- Develop reproducible Camera–LiDAR–Radar preprocessing and sensor-fusion pipelines.
- Evaluate sensor performance under clear weather, fog, and complex traffic conditions.
- Implement reliability monitoring and failure-aware sensor fusion.
- Develop CPU-based reference processing and object tracking using Extended Kalman Filtering (EKF).
- Investigate FPGA acceleration for computationally demanding Camera and LiDAR processing stages.
- Evaluate fixed-point arithmetic and selective quantization.
- Design an energy-aware scheduler for ARM–FPGA workload distribution.
- Measure real hardware energy consumption, latency, throughput, and perception quality.
- Compare CPU-only, fixed FPGA, and adaptive scheduling approaches under matched workloads.

## Software and Technologies

**Simulation:** GEMSTAR, Unreal Engine, SUMO, Open Simulation Interface (OSI)

**Programming and Data Analysis:** Python, C/C++, MATLAB, NumPy, OpenCV, Protocol Buffers

**Perception:** Camera preprocessing, LiDAR point-cloud processing, Radar analysis, object association, sensor fusion, EKF tracking

**Embedded and FPGA:** ARM processors, FPGA RTL/HLS, AMD Vivado/Vitis, AXI, DMA, fixed-point processing

**Planned Integration:** ROS 2, real-time sensor streaming, hardware power measurement, research dashboard

## Research Progress

### Tasks 01–20: Simulation and Sensor Research

The initial research established the GEMSTAR simulation environment and developed methods for collecting and analyzing Camera, LiDAR, and Radar recordings.

Major activities included:

- GEMSTAR integration with Unreal Engine and SUMO.
- OSI SensorView and GroundTruth data parsing.
- Sensor configuration and recorded-data integrity analysis.
- Camera image preprocessing and MATLAB/Python comparison.
- LiDAR point-cloud reconstruction, filtering, and voxel-based processing experiments.
- Radar geometry analysis and correction of a hard-coded 10 m range limitation to support configurable 50 m operation.
- Sensor quality monitoring, timestamp analysis, and experimental workload-policy evaluation.
- Documentation of remaining calibration, association, and validation limitations.

### Tasks 21–24: Software Preparation and Sensor Fusion

The next research stage covers MATLAB radar analysis, reusable scenario-independent OSI pipelines, preprocessing readiness, and three-sensor object association with EKF-based tracking.

Tasks 21–24 have been reported as completed in the development workflow; their implementation evidence and final verification results are to be consolidated in this repository.

### Tasks 25–29: Reliability and CPU Reference

Implement calibrated sensor health, failure constraints, fusion-quality evaluation, fair CPU benchmarks, workload profiling, numerical-precision analysis, and an offline scheduling model.

### Tasks 30–36: ARM–FPGA Acceleration

Bring up an ARM–FPGA platform, develop data-transfer infrastructure, accelerate selected Camera and LiDAR kernels, and measure actual board-level energy and processing latency.

### Tasks 37–41: Energy-Aware Scheduling

Implement calibrated workload prediction, adaptive CPU–FPGA placement, precision selection, constrained workload control, and supported hardware power-state management.

### Tasks 42–46: Live GEMSTAR Integration

Establish real-time sensor transport, ROS 2 integration, hardware processing, continuous clear-to-fog-to-traffic testing, and live monitoring.

### Tasks 47–50: Final Research Validation

Conduct controlled benchmark comparisons, statistical energy analysis, ablation studies, documentation, and a final system demonstration.

## Expected Research Contributions

1. A reproducible reliability-aware multimodal sensor-processing framework.
2. Experimental evaluation of selected FPGA accelerators for perception preprocessing.
3. A measurement-calibrated adaptive workload scheduler.
4. Comparative evaluation of energy, latency, perception fidelity, and system robustness.
5. A reproducible GEMSTAR-to-ARM–FPGA experimental workflow.

These are research objectives and planned contributions, not claims of results already demonstrated.

## Current Research Status

**Reported progress:** Tasks 01–24  
**Next milestone:** Task 25 — Fusion Reliability and Failure Constraints  
**Hardware measurements:** Pending ARM–FPGA implementation  
**Final energy savings:** Not yet established

## Research Integrity

All energy-efficiency claims will be based on measured hardware results. Comparisons will use matched datasets and consistent perception-quality requirements. Raw recordings, experiment configurations, software revisions, and measurement traces will remain traceable.

## Project Status

Ongoing academic research and development.
