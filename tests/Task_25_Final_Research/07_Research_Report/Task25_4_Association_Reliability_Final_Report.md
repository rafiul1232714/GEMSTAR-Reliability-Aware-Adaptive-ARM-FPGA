# Task 25.4 - Sensor Association Reliability

## 1. Research scope

Dataset: GEMSTAR C02 V2 selected-frame experiment.
Analysis: 53 selected frames from the original 2122-frame recording.
Sensors: Camera, LiDAR and Radar.
This is an offline association analysis, not live hardware validation.

## 2. Association status distribution

| Dataset | Recorded status | Count |
|---|---|---:|
| Radar_Returns | PROVISIONAL_BOX_GATE | 670 |
| Radar_Tracks | PROVISIONAL_RADAR_SPATIAL_MATCH | 65 |
| Radar_Tracks | NO_RADAR_SPATIAL_MATCH | 16 |
| LiDAR_Tracks | INITIALIZED | 7 |
| LiDAR_Tracks | MATCHED | 74 |
| Camera_Bearing | BEARING_GEOMETRICALLY_COMPATIBLE_NOT_CALIBRATED | 1 |

## 3. Track and frame coverage

| Dataset | Rows | Unique frames | Unique track IDs |
|---|---:|---:|---:|
| Radar_Returns | 670 | 53 | 3 |
| Radar_Tracks | 81 | 53 | 7 |
| LiDAR_Tracks | 81 | 53 | 7 |
| Camera_Bearing | 1 | 1 | 1 |

## 4. Geometric association-distance statistics

| Metric | Radar spatial gap | LiDAR temporal distance |
|---|---:|---:|
| Valid distances | 65 | 74 |
| Minimum (m) | 0.000000 | 0.000000 |
| Mean (m) | 0.044080 | 0.094688 |
| Maximum (m) | 0.879610 | 1.045790 |

These are different geometrical measures and cannot be directly ranked as sensor accuracies.

## 5. MATLAB visualizations

- task25_34_association_distance_histograms.png
- task25_34_association_distance_histograms.pdf
- task25_35_association_support_timeline.png
- task25_35_association_support_timeline.pdf
- task25_36_association_distance_timeline.png
- task25_36_association_distance_timeline.pdf

## 6. Scientific interpretation

- Radar has 65 provisional track-level spatial matches and 16 records without spatial matches.
- LiDAR has 74 temporally matched records and 7 initialized track records.
- Radar's 670 return-level box-gate candidates are not confirmed object-identity matches.
- Camera has only one geometrically compatible, uncalibrated bearing association.
- Zero spatial gap to a Radar candidate box does not prove correct object identity.
- A small mean association distance does not establish calibrated reliability.

## 7. Limitations

- No sufficient identity-ground-truth evidence to calculate association accuracy.
- Camera extrinsic calibration and association evidence remain limited.
- Selected frames from one sequence are temporally dependent.
- Radar and LiDAR distance definitions differ.
- Sensor payload repetition and unknown acquisition age remain separate concerns.
- No validated energy savings or hardware power measurements exist.

## 8. Next research stage

Task 25.5: EKF statistical consistency and uncertainty calibration.
Then Task 25.6: offline multi-sensor BEV visualization.

TASK25_04E_REPORT_PASS
