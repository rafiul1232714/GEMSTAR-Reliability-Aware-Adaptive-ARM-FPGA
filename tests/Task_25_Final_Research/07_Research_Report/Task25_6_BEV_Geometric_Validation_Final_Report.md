# Task 25.6 - Offline BEV Geometric Validation

## Research scope

This task evaluates provisional bird's-eye-view geometry for the
C02 V2 GEMSTAR Camera/LiDAR/Radar experiment.

This is an offline geometric diagnostic. It is not a validated
deep-learning BEV perception system or a hardware energy benchmark.

## Source provenance

The assessment uses Task 24 C02 V2 source code, archived configuration,
LiDAR temporal tracks, Radar associations and GroundTruth evaluation.

The archived C02 V2 configuration SHA-256 is:

1982F8C80901BB7C90EBB5B4808E999EEDE0FC41F98AB24B523C729948728290

The same archived configuration hash was previously audited in Task 25.2.

## Coordinate construction

GroundTruth target coordinates are translated relative to the ego
position and rotated by the negative ego yaw.

LiDAR extraction reconstructs points from range, pitch and yaw,
then applies nominal sensor translation (2.60, 0, 0.70) meters.

Radar extraction reconstructs returns from range, pitch and yaw,
then applies nominal sensor translation (2.00, 0, 0.80) meters.

The archived C02 V2 configuration specifies corresponding mounting
positions in centimeters:

LiDAR: X=260, Y=0, Z=70.
Radar: X=200, Y=0, Z=80.

Both sensor configurations specify zero mounting roll, pitch and yaw.
The hard-coded translations and nominal orientation assumptions
therefore agree with the archived configuration.

This agreement is source-level consistency evidence, not independent
validation of GEMSTAR/OSI coordinate conventions or runtime extrinsics.

## LiDAR tracking and Radar association

LiDAR track coordinates originate from cluster median X/Y/Z
measurements. They are not verified vehicle geometric centers.

Temporal tracking uses provisional greedy nearest predicted-position
association.

Radar coordinates originate from vehicle-labeled XYZ measurements.
Radar returns are associated with LiDAR cluster bounding boxes using
a spatial gate. A zero box gap is not proof of object identity.

## BEV observations

The coordinate audit contains 59 rows across frames 41, 530 and 816:
three GT centers, six LiDAR track observations and fifty Radar returns.

The provisional LiDAR Track 2 to GT-center separations are
approximately:

- Frame 41: 1.725 m
- Frame 530: 1.698 m
- Frame 816: 1.471 m

Using the archived relative vehicle yaw and half-length to estimate
the rear-face location, the LiDAR Track 2 longitudinal coordinate
extends approximately:

- Frame 41: 0.642 m beyond the provisional rear-face position
- Frame 530: 0.615 m beyond the provisional rear-face position
- Frame 816: 0.428 m beyond the provisional rear-face position

These are diagnostic comparisons under assumed coordinate compatibility.
They do not establish a corrected object center or calibration error.

## MATLAB figures

- task25_51_matlab_bev_three_frames.png and .pdf
- task25_52_matlab_bev_geometry_offsets.png and .pdf

These figures are stored in Task_25_Final_Research/04_Plots.

## Reliability and uncertainty limitations

1. LiDAR cluster median is not equivalent to a GroundTruth object center.
2. LiDAR/Radar association remains provisional.
3. Sensor-coordinate conventions have not been independently validated.
4. Runtime sensor extrinsics are not independently measured.
5. Three selected BEV frames are not a comprehensive calibration sample.
6. Repeated sensor payloads may affect apparent observation freshness.
7. No post-hoc center correction was applied.
8. No hardware energy reduction is demonstrated by this task.

## Conclusion

Task 25.6 establishes a documented offline BEV diagnostic with
reproducible figures, selected coordinate observations, source-code
provenance and matching nominal sensor mounting translations.

The approximately 1.6 m systematic LiDAR-to-GT X discrepancy cannot
be attributed to disagreement between the extraction script's
mounting translations and the archived configuration.

A surface/cluster-median versus GT-center representation mismatch
is plausible but does not fully account for the provisional
three-frame rear-face comparisons.

The BEV is therefore retained as a diagnostic visualization,
not certified as geometrically calibrated perception.

## Next research stage

Task 25.7: reliability-aware sensor fallback using independently
audited sensor health, association confidence, uncertainty and
perception-quality constraints.

Do not infer hardware energy savings before measured ARM-FPGA
benchmarks and matched validation.
