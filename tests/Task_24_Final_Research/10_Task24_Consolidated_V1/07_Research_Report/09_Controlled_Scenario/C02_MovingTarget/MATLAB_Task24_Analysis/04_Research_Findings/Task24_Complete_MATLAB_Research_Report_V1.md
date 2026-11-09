# Task 24 — Complete MATLAB Research Findings

## 1. Research scope

Exploratory Camera-LiDAR-Radar association and EKF tracking using one clean V2 GEMSTAR recording. Ground Truth is evaluation-only.

## 2. Experimental evidence

- Ground Truth recording: 2122 frames.
- Sampled measurement frames: 53.
- Provisional Track 2 observations: 24.
- Valid GT-center comparisons: 23.
- Radar EKF accepted updates: 4.
- Experimental Camera-bearing updates: 1.
- Generated MATLAB figures: 30 of 30 found.

## 3. Position accuracy

| Estimator | Mean GT-center error (m) |
|---|---:|
| LiDAR-only | 1.650417 |
| LiDAR-Radar | 1.628205 |
| Three-sensor | 1.628213 |

Mean Radar error reduction: 0.022212 m (1.346%).

Radar-improved frames: 11; worsened: 6; approximately unchanged: 6.

## 4. Velocity comparison — provisional

LiDAR mean 2D velocity error: 1.504483 m/s.

LiDAR-Radar mean 2D velocity error: 1.465717 m/s.

These errors use the exported actor velocity and must not be presented as validated physical velocity performance.

## 5. Ground Truth exporter findings

- Reported dimensions use world-axis-aligned bounding-box half-extents rather than full physical dimensions.
- Exported actor velocity components were not converted from Unreal cm/s to OSI m/s in the examined source.
- Nonzero actor speeds are approximately twice position-derived speeds during many active-motion samples.
- Full-rate audit found 883 zero-actor-velocity samples despite finite-difference center motion.
- The root cause of the velocity discrepancy is unresolved; no correction factor is authorized.

## 6. Figure-by-figure interpretation

### Figure 01 — Raw sensor measurement availability

**Finding:** Both LiDAR and Radar return data throughout the sampled recording; startup counts differ.

**Limitation:** Counts do not measure probability of detection or accuracy.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_01.png`

**Present:** true

### Figure 02 — LiDAR filtering and clustering

**Finding:** Filtering reduces LiDAR points substantially; candidate count changes over time.

**Limitation:** Clustering depends on selected filtering and grid parameters.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_02.png`

**Present:** true

### Figure 03 — LiDAR temporal track trajectories

**Finding:** Track 2 is moving while Track 7 is approximately stationary in the selected scene.

**Limitation:** Tracks are provisional and not full-rate validated.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_03.png`

**Present:** true

### Figure 04 — Radar association coverage

**Finding:** Provisional Radar associations are concentrated early for Track 2.

**Limitation:** Geometric associations are not independently calibrated.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_04.png`

**Present:** true

### Figure 05 — Radar and LiDAR velocity consistency

**Finding:** Five Doppler and LiDAR velocity comparisons have substantial magnitude disagreement.

**Limitation:** Radar and LiDAR may observe different surfaces.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_05.png`

**Present:** true

### Figure 06 — Matched three-estimator position errors

**Finding:** Radar gives a small average center-reference improvement; Camera does not.

**Limitation:** One development sequence with 23 matched GT comparisons.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_06.png`

**Present:** true

### Figure 07 — GT center and EKF trajectories

**Finding:** Three estimators follow similar trajectories with a systematic GT-center displacement.

**Limitation:** GT center differs from the LiDAR observation reference.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_07.png`

**Present:** true

### Figure 08 — Signed longitudinal and lateral bias

**Finding:** Longitudinal reference-point bias dominates much of the position error.

**Limitation:** Reference-point effect is unresolved.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_08.png`

**Present:** true

### Figure 09 — Radar position-error contribution

**Finding:** Radar improvements are concentrated around particular updates and are not universal.

**Limitation:** The improvement is descriptive, not a causal guarantee.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_09.png`

**Present:** true

### Figure 10 — Camera update contribution

**Finding:** One Camera bearing update changes position only slightly.

**Limitation:** One low-confidence Camera hypothesis; uncalibrated projection.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_10.png`

**Present:** true

### Figure 11 — Position-error empirical distributions

**Finding:** Radar slightly reduces the upper portion of the observed error distribution.

**Limitation:** Temporal samples are correlated.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_11.png`

**Present:** true

### Figure 12 — GT bounding-box dimensions and reference effects

**Finding:** Reported GT dimensions vary with target yaw; exporter uses AABB half-extents.

**Limitation:** GT exporter does not supply physical heading-aligned full dimensions.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_12.png`

**Present:** true

### Figure 13 — 3D LiDAR point cloud

**Finding:** Measured LiDAR geometry is visible; object identity is not proven by the plot.

**Limitation:** LiDAR data is a sparse sampled subset.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_13.png`

**Present:** true

### Figure 14 — 3D Radar return geometry

**Finding:** Radar returns exist at frame 530 but do not associate with Track 2.

**Limitation:** No Track 2 Radar association at the displayed frame.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_14.png`

**Present:** true

### Figure 15 — Nominal Camera-LiDAR projection

**Finding:** 56 nominally projected LiDAR points overlap a low-confidence Camera hypothesis.

**Limitation:** Nominal camera intrinsics and extrinsics only.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_15.png`

**Present:** true

### Figure 16 — Combined LiDAR-Radar scene

**Finding:** Frame 530 supports LiDAR and Track 7 Radar matches, not a full three-sensor match for Track 2.

**Limitation:** Associations remain provisional.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_16.png`

**Present:** true

### Figure 17 — Track 2 position through space and time

**Finding:** Track 2 Radar support varies substantially over time.

**Limitation:** Time is the vertical axis, not physical elevation.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_17.png`

**Present:** true

### Figure 18 — Three-frame LiDAR-Radar comparison

**Finding:** Scene geometry changes across frames 245, 530 and 816.

**Limitation:** Only three snapshots are presented.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_18.png`

**Present:** true

### Figure 19 — EKF velocity state comparison

**Finding:** Radar updates noticeably influence the early longitudinal velocity state.

**Limitation:** Velocity states are not validated by the figure alone.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_19.png`

**Present:** true

### Figure 20 — Radar measured versus predicted velocity

**Finding:** Measured Radar velocity and EKF prediction disagree in magnitude.

**Limitation:** Measurement-model uncertainty remains uncalibrated.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_20.png`

**Present:** true

### Figure 21 — Radar innovation NIS gating

**Finding:** Four accepted Radar updates meet the exploratory NIS gate.

**Limitation:** Exploratory NIS gate 9; no full consistency test.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_21.png`

**Present:** true

### Figure 22 — EKF reported X uncertainty

**Finding:** Reported uncertainty decreases after initialization but is not calibrated against object-center GT.

**Limitation:** Only reported X marginal standard deviation is available.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_22.png`

**Present:** true

### Figure 23 — Estimator position separation

**Finding:** Radar shifts position by at most about 17 cm; Camera by about 1.74 cm.

**Limitation:** Estimator separation is not an accuracy metric.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_23.png`

**Present:** true

### Figure 24 — Radar update effectiveness

**Finding:** Four accepted Radar updates reduce center-reference error at their update frames.

**Limitation:** Radar measurements are not consistently beneficial.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_24.png`

**Present:** true

### Figure 25 — Local target LiDAR-Radar association

**Finding:** Local 3D views show 14, 0 and 2 Track 2 Radar matches at frames 245, 530 and 816.

**Limitation:** LiDAR bounding boxes are not verified physical vehicle boxes.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_25.png`

**Present:** true

### Figure 26 — Camera-LiDAR target depth compatibility

**Finding:** Depth clustering supports Camera-LiDAR geometric compatibility, not confirmed class or identity.

**Limitation:** Low detector confidence; mixed object/background depths possible.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_26_V2.png`

**Present:** true

### Figure 27 — Sensor support and update timeline

**Finding:** Track 2 availability is distinct from sensor-wide availability; one Camera hypothesis is accepted experimentally.

**Limitation:** Absence of Track 2 is not evidence of sensor failure.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_27.png`

**Present:** true

### Figure 28 — GT-center residual versus X uncertainty

**Finding:** GT-center X residual exceeds reported X sigma, but these refer to different target points.

**Limitation:** Not an NEES or valid covariance coverage test.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_28.png`

**Present:** true

### Figure 29 — GT actor velocity versus EKF states

**Finding:** Exported GT actor velocity switches between zero and values above position-derived speed.

**Limitation:** GT velocity export exhibits systematic inconsistencies.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_29.png`

**Present:** true

### Figure 30 — Velocity-error and GT-reference disagreement

**Finding:** GT velocity-reference disagreement limits physical interpretation of EKF velocity RMSE.

**Limitation:** Actor velocity, AABB center and time sampling references are not reconciled.

**File:** `E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget\MATLAB_Task24_Analysis\01_Graphs\Task24_Figure_30.png`

**Present:** true

## 7. Research validity and limitations

- Single development recording; no independent scenario replication.
- 23 evaluated frames are temporally correlated.
- Track 2 matched GT object 76897 as nearest candidate in all 23 audited frames; physical correspondence remains subject to observation bias.
- LiDAR cluster position and GT geometric center are different measurement references.
- Camera projection and sensor noise are not independently calibrated.
- No three-sensor Camera-LiDAR-Radar association was confirmed at frame 530.
- Full-state covariance consistency and NEES were not established.
- No energy, latency, FPGA acceleration, or full-rate deployment performance is established.

## 8. Implications for Task 25

Task 25 should distinguish sensor availability, target observability, association confidence, measurement validity, and estimator uncertainty. Reliability thresholds need independent validation rather than tuning to this development recording.

## 9. Conclusions

An experimental three-sensor fusion workflow has been demonstrated. Radar provides a small mean improvement in GT-center position error for this recording. Camera produced one accepted exploratory update without demonstrated accuracy benefit. Geometry and velocity-export issues must be accounted for in subsequent validation.
