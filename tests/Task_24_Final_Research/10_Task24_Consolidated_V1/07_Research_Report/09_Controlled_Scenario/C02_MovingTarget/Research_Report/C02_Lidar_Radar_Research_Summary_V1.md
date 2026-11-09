# C02 Moving-Target Research Summary — Version 1

## Scope

GEMSTAR controlled moving-target experiment.

Research stage: Task 24.5.4, LiDAR-Radar association and tracking.

This is a two-sensor investigation, not completed Camera-LiDAR-Radar fusion.

## Source recordings

SensorView:
E:\GEMSTAR_Project\gemstar\Output\20261108T154003Z_sv_380_X_4170_GEMSTAR.osi

GroundTruth:
E:\GEMSTAR_Project\gemstar\Output\20261108T154005Z_gt_380_X_4170_GEMSTAR.osi

The raw recordings are external references and are not copied into this research package.

## Processing pipeline

1. Read and reconstruct LiDAR measurements from OSI.
2. Cluster spatial measurements.
3. Associate LiDAR clusters temporally.
4. Reconstruct Radar reflections and Doppler velocity.
5. Match Radar returns to the selected LiDAR cluster surface.
6. Execute LiDAR-only Kalman and Radar-LiDAR EKF filters.
7. Evaluate results using GroundTruth only after estimation.

## Association findings

- 29 nonzero-Doppler Radar returns considered at selected timestamps.
- 29/29 associated with the temporally selected LiDAR cluster surface using the tested 0.75 m spatial gate.
- Diagnostic nearest-point target-label agreement: 29/29.
- Object IDs were not used for the reported association decisions.

These results apply to this selected controlled experiment and do
not establish general-purpose association precision or recall.

## EKF implementations

V1: Fixed LiDAR measurement covariance.

V2: Point-count-adaptive LiDAR covariance.
     Standard deviation factor max(1, 30/N).

V3: Conservative point-count-adaptive covariance.
     Standard deviation factor min(2, max(1, 12/N)).

These covariance models are experimental assumptions, not
independently calibrated sensor-noise models.

All three EKFs use the same Radar association inputs.

## GroundTruth evaluation

Metric: Initial-position-aligned 2D displacement RMSE.

Absolute vehicle-center localization RMSE has not been established.
Time-varying LiDAR surface offsets remain a limitation.

Full sequence, 53 samples:

- EKF V1: 0.981252 m
- EKF V2: 0.934510 m
- EKF V3: 0.950954 m

LiDAR-observed, 49 samples:

- EKF V1: 0.695352 m
- EKF V2: 0.701573 m
- EKF V3: 0.692352 m

Prediction-only, 4 samples:

- EKF V1: 2.614344 m
- EKF V2: 2.354109 m
- EKF V3: 2.471859 m

Full-sequence velocity-vector RMSE, 52 samples:

- EKF V1: 0.391555 m/s
- EKF V2: 0.363241 m/s
- EKF V3: 0.380258 m/s

Prediction-only velocity-vector RMSE, 4 samples:

- EKF V1: 0.749721 m/s
- EKF V2: 0.582877 m/s
- EKF V3: 0.686087 m/s

GroundTruth velocity was approximated by finite differences.

## Key observations

- Radar Doppler measurements improved early radial tracking in C02.
- Sparse LiDAR surface measurements can bias centroid-derived motion.
- V2 improved prediction-only tracking compared with V1.
- V2 slightly worsened LiDAR-observed 2D displacement RMSE.
- V3 slightly improved LiDAR-observed displacement RMSE.
- Both position and velocity error increase when measurements disappear.
- No energy-efficiency or latency improvement has been measured here.

## Limitations

- One controlled moving-target scenario.
- Small sample counts in sparse LiDAR categories.
- Approximate or unvalidated Radar extrinsic geometry.
- Heuristic clustering and track association.
- No independently calibrated sensor covariance.
- V2 and V3 covariance choices explored using the C02 scenario.
- No independent test scenario for generalization.
- No operational full-clutter false-association benchmark.
- Initial-offset-aligned displacement is not absolute center accuracy.
- No full Camera-LiDAR-Radar fusion yet.
- No ARM-FPGA energy measurements in this experiment.

## Research selection

EKF V2 is the leading candidate for future validation based on
the C02 full-sequence and prediction-only results.

EKF V1 and V3 must remain available as comparative baselines.

The observed improvement must be tested on independent scenarios
before claiming a general reliability advantage.

## Figures

01. Initial-aligned target trajectories.
02. 2D displacement tracking error.
03. Velocity-vector error.
04. LiDAR point-count reliability and late-stage tracking error.

The files were generated successfully. Their visual correctness
should also be checked manually before thesis publication.

## Next experiments

1. Validate Camera observations and independent association.
2. Implement and test genuine three-sensor fusion.
3. Evaluate additional clear/fog/traffic scenarios.
4. Calibrate sensor transforms and uncertainty.
5. Compare fusion quality under reproducible matched conditions.
6. Proceed to CPU benchmarking and later ARM-FPGA measurement.

## Reproducibility

See C02_Research_File_Manifest_V1.csv for file inventory,
sizes, and available SHA256 hashes.

Raw OSI recordings are not modified or included in this package.