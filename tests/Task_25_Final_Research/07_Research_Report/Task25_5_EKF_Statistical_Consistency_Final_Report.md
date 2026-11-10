# Task 25.5 - EKF Uncertainty and Consistency Diagnostics

## 1. Research scope

- GEMSTAR C02 V2 offline Track 2 evaluation.
- 24 selected EKF observations.
- 23 aligned GT-center X-residual observations.
- Four accepted Radar updates with finite NIS.
- No hardware energy measurements.

## 2. Radar normalized innovation squared

| Frame | Radar status | NIS | Recorded gate result |
|---:|---|---:|---|
| 245 | ACCEPTED | 0.591499 | True |
| 286 | ACCEPTED | 1.060251 | True |
| 326 | ACCEPTED | 0.611538 | True |
| 816 | ACCEPTED | 0.019422 | True |

The four finite NIS observations are accepted updates.
The other 20 observations have no finite NIS in this dataset.
These four observations cannot establish statistical calibration.

## 3. GT-center X residuals and reported uncertainty

| Sensor estimator | Samples | Mean signed X residual (m) | Mean reported sigma X (m) | Abs residual > sigma |
|---|---:|---:|---:|---:|
| LiDAR | 23 | -1.623522 | 0.555641 | 23/23 |
| Radar | 23 | -1.601283 | 0.552601 | 23/23 |

Both signed X-residual means are negative and near -1.6 m.
The observed GT-center residuals exceed the reported one-sigma values in all 23 paired samples.

## 4. Scientific interpretation

- A persistent geometric-reference or estimator offset is present.
- Comparing a sensed vehicle surface with a GT object center may contribute to the offset.
- The exact cause has not been independently established.
- The original measurements were not bias-corrected.
- These results do not establish a valid full-state NEES.

## 5. MATLAB figures

- task25_44_matlab_radar_nis.png
- task25_44_matlab_radar_nis.pdf
- task25_45_matlab_residual_sigma.png
- task25_45_matlab_residual_sigma.pdf
- task25_46_matlab_normalized_residual.png
- task25_46_matlab_normalized_residual.pdf

## 6. Research limitations

- Only four accepted Radar NIS measurements.
- No independently verified full covariance matrix.
- GT-center and sensed-surface geometric definitions may differ.
- The 23 samples originate from one recording and are temporally dependent.
- No general uncertainty calibration claim is justified.
- No ARM-FPGA energy improvement is demonstrated.

## 7. Next investigations

- Task 25.6: offline BEV geometry and target-position visualization.
- Investigate coordinate frames, sensor origins, box surfaces, and GT center.
- Revisit covariance calibration only after geometric alignment is established.
- Preserve original measurements and evaluation reproducibility.

TASK25_05I_REPORT_PASS
