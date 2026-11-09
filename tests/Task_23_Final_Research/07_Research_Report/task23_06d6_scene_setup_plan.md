# Task 23.6D-6 — Controlled Validation Scene

Status: PLANNED_NOT_IMPLEMENTED

## Objective
Create an isolated GEMSTAR scene with known reference targets
for Radar and LiDAR measurement validation.

## Initial map candidate
RadarTestMap.umap

## Proposed new map
SensorFusionValidationMap.umap

## Required components
- Radar sensor
- LiDAR sensor
- GroundTruth logger
- Known stationary target
- Known moving target
- Reference position and velocity data

## Verification before recording
1. Confirm original test map loads.
2. Inspect actors in Unreal World Outliner.
3. Verify sensors and logger are present or correctly instantiated.
4. Create a separate map rather than changing original assets.
5. Confirm target position and dimensions.
6. Confirm GroundTruth and SensorView recording.
7. Check actor IDs and timestamps.

## Acceptance criteria
- Reproducible sensor configuration.
- Target reference geometry available.
- Valid Radar and LiDAR OSI payloads.
- GroundTruth target association verified.
- Original GEMSTAR project assets preserved.

## Research limitations
No controlled measurement has been completed yet.
No detection accuracy, latency improvement or energy
saving has been established by this planning step.
