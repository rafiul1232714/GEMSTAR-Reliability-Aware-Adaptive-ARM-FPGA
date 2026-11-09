# Task 24.2.B - MATLAB GroundTruth Research Analysis

## 1. Objective

Analyze recorded GroundTruth motion before developing
Camera-LiDAR-Radar object association and EKF tracking.

This analysis concerns simulator GroundTruth, not fused
sensor estimates.

## 2. Source and reproducibility

GroundTruth recording:
20261105T231919Z_gt_380_X_372_GEMSTAR.osi

SensorView recording:
20261105T231919Z_sv_380_X_372_GEMSTAR.osi

Dataset:
02_CSV_Data/task24_02B_04_gt_trajectories_100frames.csv

MATLAB script:
01_Code/task24_02B_05_matlab_gt_visualization.m

The first 100 GroundTruth frames were analyzed.

Total object observations: 327.
Physical-vehicle candidate observations: 227.
Camera-support-actor observations: 100.

## 3. GroundTruth object classification

| ID | Model | Observations | Classification |
|---|---|---:|---|
| 76895 | BP_Small_Car_C | 100 | Vehicle candidate |
| 76870 | BP_Truck_C | 73 | Vehicle candidate |
| 76868 | BP_Bus_C | 43 | Vehicle candidate |
| 76865 | BP_Large_Car_C | 11 | Vehicle candidate |
| 77191 | FollowVehicleCamera | 100 | Simulation support actor |

Model names support candidate classification.
Physical target eligibility still requires appropriate
validation for tracking evaluation.

## 4. GT-01: Vehicle XY trajectories

Figure:
03_Graphs/task24_02B_05_GT01_vehicle_xy_trajectories.png

Method:
Plot recorded world X and Y positions for four vehicle
candidates, preserving their object IDs and timestamps.

Interpretation:
The plotted trajectories occupy different regions of the
GEMSTAR world. Each vehicle provides a candidate trajectory
for later object-level tracking evaluation.

Limitation:
These are simulator GroundTruth positions. They do not
demonstrate that any particular sensor detected the objects.

## 5. GT-02: Vehicle positions versus time

Figure:
03_Graphs/task24_02B_05_GT02_vehicle_position_time.png

Method:
Plot world X, Y and Z against recorded container timestamp.

Interpretation:
Vehicle entries begin at different times, and their
recorded positions evolve over the observation window.

Limitation:
Container timestamp labels are not independently verified
sensor acquisition times.

## 6. GT-03: Implied speed and motion anomalies

Figure:
03_Graphs/task24_02B_05_GT03_motion_speed_flags.png

Method:
For consecutive observations of the same object ID,
calculate 3D displacement divided by timestamp difference.

Diagnostic threshold: 50 metres per second.

Two flagged transitions belong to FollowVehicleCamera,
ID 77191:

- Frame 0 to 1: 575.675 m/s implied speed.
- Frame 1 to 2: 93.445 m/s implied speed.

Interpretation:
The camera-support actor has motion discontinuities
that should not be treated as ordinary vehicle dynamics.

Limitation:
The cause of the jumps has not been independently proven.
Frame-difference speeds can also be affected by simulation
sampling and repeated object positions.

The 50 m/s threshold is diagnostic, not a calibrated
physical acceptance criterion.

## 7. GT-04: Vehicle orientation

Figure:
03_Graphs/task24_02B_05_GT04_vehicle_orientation.png

Method:
Convert recorded yaw and pitch from radians to degrees
and plot them against time.

Interpretation:
Vehicle candidates show different headings.
Reported pitch remains near zero for the inspected
vehicle candidates.

Limitation:
No sensor-based heading reconstruction is validated here.

## 8. GT-05: Object presence timeline

Figure:
03_Graphs/task24_02B_05_GT05_object_presence.png

Method:
Mark each object's recorded presence by frame index.

First appearances:
- Small car: frame 0.
- Truck: frame 27.
- Bus: frame 57.
- Large car: frame 89.
- FollowVehicleCamera: frame 0.

Interpretation:
The test data contains targets entering the GroundTruth
record at different times. This is useful for later
track initiation and termination evaluation.

Limitation:
GroundTruth presence does not establish sensor visibility
or detection.

## 9. Verification status

All five MATLAB figure files exist and passed PNG
dimension and nonempty-file checks.

The underlying source is the recorded GEMSTAR GroundTruth
CSV, not a synthetic trajectory generator.

## 10. Conclusions

The first 100 frames provide usable GroundTruth vehicle
candidates and an independently identified simulation
support actor.

This analysis establishes a documented GroundTruth
reference for subsequent fusion research.

It does not establish valid Camera-LiDAR-Radar object
correspondence, measured tracking accuracy, or sensor
synchronization.

## 11. Next research actions

1. Validate sensor-to-vehicle coordinate conventions.
2. Establish the available vehicle/world pose reference.
3. Verify actual Camera projection geometry.
4. Reconstruct and compare real sensor observations.
5. Associate observations to GroundTruth objects.
6. Evaluate EKF tracking after association is validated.