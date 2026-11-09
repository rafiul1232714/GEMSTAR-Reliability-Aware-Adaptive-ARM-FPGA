# Task 24.3.9 — Object Extraction Dataset Decision

## Status
Visual inspection completed for frames 2, 172, 311 and 355.

## Evidence

- All 372 frames were extracted and checked.
- LiDAR candidate returns: 823254.
- Radar candidate returns: 24161.
- LiDAR exact repeated frame pairs: 148.
- Radar exact repeated frame pairs: 57.
- All-zero Radar Doppler frames: 149.
- Frame 1 contains 58 Radar returns above the provisional
  absolute radial-speed review threshold.
- Nominal geometry and logger timestamps do not establish
  independently verified physical calibration or synchronization.

## Object extraction findings

1. Initial LiDAR voxel clusters were dominated by large,
   horizontally extended structures.
2. A near-horizontal RANSAC plane explained 84.49% to 100%
   of the tested LiDAR ROI points.
3. Only four above-plane clusters were retained across the
   four selected frames.
4. Exact LiDAR-Radar proximity did not confirm physical
   object correspondence.
5. Of 60 elevated Radar candidate returns, 31 mapped outside
   the nominal LiDAR field of view.
6. The remaining 29 mapped to LiDAR no-hit directions,
   with no candidate in the inspected 3x3 ray neighborhoods.
7. All 269 tested Radar candidate positions projected inside
   the nominal Camera image boundaries.
8. Camera overlays visually show roadways, roadside structures,
   vegetation and a visible vehicle in frame 311.
9. The visible vehicle in frame 311 did not produce a retained
   above-plane LiDAR cluster under the tested procedure.
10. Original Camera frames contain orange/yellow curved
    graphics whose simulator-side origin requires investigation.

## Interpretation limits

- Simulator-side LiDAR object IDs are diagnostic metadata only.
- No privileged object IDs may enter fusion features.
- Camera visibility is not Camera detection.
- Radar proximity is not object correspondence.
- RANSAC plane inliers are not confirmed road labels.
- Neither object-detection accuracy nor tracking performance
  has been established.
- Energy savings have not been measured.

## Research decision

KEEP the original 372-frame dataset as a baseline for sensor
freshness, timing, measurement-quality and scheduling studies.

REQUIRE an additional controlled GEMSTAR scene before claiming
validated three-sensor object association or EKF tracking.

## Controlled recording requirements

- Reproducible scenario and fixed sensor configurations.
- At least one clearly visible target vehicle at known
  approximate positions and distances.
- Capture Camera, LiDAR, Radar and separately held GT data.
- Investigate and, where possible, disable Camera-visible
  debug/ray graphics.
- Confirm sensor coverage and object-level measurement support.
- Record clear and fog conditions for later reliability testing.
- Preserve original OSI files and verify frame pairs and hashes.
- Separate GT evaluation from sensor-only detection and fusion.

## Exit criteria for Task 24.3

- Preserve the full validated sensor measurement dataset.
- Preserve all MATLAB and Camera overlay figures.
- Document nominal calibration and synchronization limitations.
- Document failed or ambiguous object-extraction experiments.
- Define a controlled-recording validation plan.
- Consolidate Task 24.3 findings and reproducible code.

## Next development stage

Proceed with controlled-scenario validation before making
object-detection or EKF-accuracy claims.

An EKF implementation may be tested separately on synthetic
measurements, but such results must not be presented as
validated three-sensor perception from this recording.