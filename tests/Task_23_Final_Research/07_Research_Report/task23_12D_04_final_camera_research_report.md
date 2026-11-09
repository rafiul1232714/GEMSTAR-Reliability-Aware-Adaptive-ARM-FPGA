# Task 23.12 — Camera Preprocessing and Controlled Weather Validation

Generated: 2026-11-06 00:57:04

## 1. Research objective

Establish reproducible Camera data acquisition and CPU preprocessing readiness for the GEMSTAR reliability-aware, energy-efficient ARM–FPGA sensor-processing thesis.

This experiment evaluates controlled Camera signal characteristics under Clear, Fog MOR 100 m, and Fog MOR 20 m.

It is a sensor-readiness experiment, not a vehicle-detection or sensor-fusion accuracy benchmark.

## 2. Experimental environment

- Unreal Engine / GEMSTAR
- Map: /Game/ResearchValidation/SensorFusionValidationMap
- Scene: static geometric validation arena
- Camera image format: 640 x 480, three-channel uint8
- Image payload: 921600 bytes per inspected frame
- Simulation conditions: Clear, Fog100, Fog20
- Original map backed up, then restored with SHA-256 verification

The validation scene has no demonstrated road, vehicle, or pedestrian targets.

## 3. Recording provenance

### Clear
- Runtime configuration: Task23_12_Camera_Clear.ini
- ActiveWeatherType=Clear
- No fog-application message found in audited runtime log
- SensorView size: 6327756797 bytes
- Frames indicated by filename: 6865

### Fog MOR 100
- Runtime configuration: Task23_12_Camera_FogMOR100.ini
- Runtime confirmed: Fog applied, MOR=100.00 m, FogDensity=0.0200
- SensorView size: 5696364729 bytes
- Frames indicated by filename: 6180

### Fog MOR 20
- Runtime configuration: Task23_12_Camera_FogMOR20.ini
- Runtime confirmed: Fog applied, MOR=20.00 m, FogDensity=0.1000
- SensorView size: 6926890904 bytes
- Frames indicated by filename: 7515

All three experiments produced nonempty SensorView and GroundTruth files.

Actual full-dataset frame counts have not yet been independently verified. Counts above are inferred from filenames.

## 4. Raw OSI recording manifest

| Scenario | File | Bytes | SHA-256 |
|---|---|---:|---|
| T23_12_CAMERA_CLEAR | 20261105T232522Z_sv_380_X_6865_T23_12_CAMERA_CLEAR.osi | 6327756797 | 9BC98A8BD390DB4172DE046A6E51530275B0479A1D721A5DBB363EE9CDC9AF4B |
| T23_12_CAMERA_CLEAR | 20261105T232525Z_gt_380_X_6865_T23_12_CAMERA_CLEAR.osi | 6295859 | 924660CAB4F81C48500F2DE6CEBA511C0EC348664E4E563791610B6F73ED7F29 |
| T23_12_CAMERA_FOG100 | 20261105T233335Z_sv_380_X_6180_T23_12_CAMERA_FOG100.osi | 5696364729 | BE7D03CD66FC599FC6782EAE185E4281DA32A87BBD7B39A5B5A07B894DE9B05F |
| T23_12_CAMERA_FOG100 | 20261105T233337Z_gt_380_X_6180_T23_12_CAMERA_FOG100.osi | 5760015 | A228C8E15D04D1544111B2E636F44236D0690145F17FCFCB6533373648E837E3 |
| T23_12_CAMERA_FOG20 | 20261105T234100Z_sv_380_X_7515_T23_12_CAMERA_FOG20.osi | 6926890904 | 5CA5225D663AB381A224A9BD55387D5BFE5EC366E558475C98F387C3B13D85E6 |
| T23_12_CAMERA_FOG20 | 20261105T234103Z_gt_380_X_7515_T23_12_CAMERA_FOG20.osi | 6997582 | 860B25A5D7DD84A353F185FA53F98524715EE22AAC53E8B7BB0C3D5A48F1742C |

The original OSI files remain in GEMSTAR/Output. Their immutable source paths and SHA-256 hashes are recorded in the accompanying CSV evidence manifest.

## 5. Camera payload verification

- Three initial Camera frames checked per scenario: 9/9 passed.
- The timing audit subsequently checked the first ten frames per scenario: 30/30 contained one Camera view and a 921600-byte image payload.
- These checks establish sampled payload availability, not complete-dataset validity.
- Simulation timestamps were collected independently for all three scenarios.

## 6. Matched-time image comparison

Images were extracted near simulation time 0.20 seconds:

- Clear: frame 2, timestamp 0.189942 s
- Fog100: frame 2, timestamp 0.203152 s
- Fog20: frame 2, timestamp 0.192330 s

All images were extracted from the original OSI data and saved as PNG.

The camera viewpoint and static scene geometry appeared visually comparable.

Time matching and visual similarity do not prove pixel-perfect scene correspondence.

## 7. Quantitative Camera quality metrics

| Scenario | Region | Luminance | Contrast | Edge density | Laplacian variance | Saturation |
|---|---|---:|---:|---:|---:|---:|
| CLEAR | FULL | 125.5095 | 73.9714 | 0.009147 | 317.6918 | 80.0809 |
| CLEAR | CENTER | 169.4138 | 45.9824 | 0.011366 | 257.5174 | 38.7888 |
| FOG100 | FULL | 139.5759 | 70.5069 | 0.008418 | 275.8732 | 35.4572 |
| FOG100 | CENTER | 178.8827 | 43.6135 | 0.010986 | 228.0982 | 26.7923 |
| FOG20 | FULL | 165.4152 | 56.8249 | 0.008314 | 142.0111 | 16.0378 |
| FOG20 | CENTER | 194.8957 | 31.049 | 0.00897 | 107.0663 | 12.694 |

The metrics were measured from selected images, using the full image and fixed central ROI.

The central ROI is x=128, y=96, width=384, height=288 pixels.

Fog20 exhibited lower intensity contrast and edge density than Clear in the examined static scene.

These values are image-quality proxies, not calibrated object-detection accuracy or sensor reliability probabilities.

## 8. Reusable CPU Camera preprocessing

Implemented in:

01_Code/task23_12C_06_camera_cpu_preprocessing.py

Functions:
- Validate uint8 BGR Camera image input
- Validate configurable ROI
- Extract grayscale image
- Compute Canny edges
- Calculate luminance, contrast, edge density, Laplacian variance, and saturation

This module is a candidate CPU preprocessing baseline for later processor/FPGA design-space and energy comparisons.

No hardware energy savings or real-time guarantees are claimed at this stage.

## 9. Independent MATLAB validation

MATLAB reproduced Python luminance and contrast measurements for the three central ROIs.

The recorded largest luminance difference was approximately 0.0045 grayscale levels.

MATLAB verification tolerance: 0.5.

Validation result: PASS.

Outputs:
- 02_CSV_Data/task23_12C_07_matlab_camera_validation.csv
- 03_Graphs/task23_12C_07_matlab_camera_weather_comparison.png

## 10. Invalid-input robustness

Eight test cases executed; eight passed.

Accepted:
- Valid full Camera image
- Valid central ROI

Rejected:
- Missing input
- Empty image
- Wrong datatype
- Grayscale input where BGR was required
- ROI outside image boundaries
- Zero-width ROI

Current invalid-input handling raises Python exceptions. Integration with scheduler health-status messages remains future work.

## 11. Research limitations

1. Static validation arena does not contain verified vehicles or pedestrians.
2. No Camera object-detection accuracy, false-positive rate, or tracking quality was measured.
3. Only sampled OSI frames were audited; complete dataset integrity and frame totals remain unverified.
4. Quality metrics were primarily demonstrated on one matched-time triplet rather than a statistically representative frame set.
5. Weather-dependent image features are not equivalent to calibrated perception confidence.
6. No CPU-versus-FPGA energy comparison has been conducted.
7. Dynamic driving-scene validation remains necessary for meaningful later three-sensor association, EKF tracking, and fusion reliability experiments.

## 12. Final Task 23.12 conclusions

PASS — Controlled Camera recordings obtained for all three weather configurations.

PASS — Sampled RGB payload decoding and image-size checks.

PASS — Reusable Camera CPU preprocessing demonstrated.

PASS — Quantitative quality metrics calculated.

PASS — MATLAB cross-tool validation.

PASS — Eight invalid-input robustness tests.

PASS — Original Unreal map restored to its verified pre-experiment bytes.

PASS — Research evidence manifest created with source paths and SHA-256 hashes.

Task 23.12 establishes Camera preprocessing readiness within the stated limits. It does not complete the overall Task 23 three-sensor readiness gate.

## 13. Next research work

Continue the remaining Task 23 requirements:
- Radar OSI range serialization readiness
- Sensor coordinate-frame and timestamp conventions
- Unified Camera/LiDAR/Radar preprocessing interfaces
- Task 23 final acceptance and evidence consolidation

Later Task 24 requires representative dynamic-object scenes and independent ground truth for meaningful three-sensor association and EKF tracking.

## 14. Evidence organization

01_Code — Python and MATLAB implementations
02_CSV_Data — Timing, quality, MATLAB, robustness results
03_Graphs — MATLAB comparison PNG
04_Configurations — Weather INIs, original map backup and experimental map archive
05_Raw_Data_References — Runtime logs and SHA-256 dataset manifest
06_Research_Findings — Map-setting and independent verification evidence
07_Research_Report — This report
08_Processed_Data — Extracted Camera PNG images and visual comparison

Evidence manifest:
05_Raw_Data_References/task23_12D_03_camera_evidence_manifest.csv

Manifest entries before this report: 63
