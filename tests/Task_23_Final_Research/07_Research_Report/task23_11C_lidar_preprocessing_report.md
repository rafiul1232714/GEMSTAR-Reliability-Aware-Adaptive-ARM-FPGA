# Task 23.11.C — LiDAR Preprocessing Validation

## Objective

Verify the reproducibility and numerical consistency of the existing GEMSTAR LiDAR preprocessing pipeline.

## Methodology

1. Decode LiDAR time-of-flight and signal-strength measurements.
2. Reconstruct distances using d = c × TOF / 2.
3. Check finite and positive time-of-flight and signal strength.
4. Apply preliminary range screening between 0.05 m and 200 m.
5. Preserve rejected measurements and acceptance flags.
6. Independently recalculate the filtering rules.
7. Verify saved NPZ arrays and reconstructed point counts.
8. Cross-validate the exported measurements using MATLAB.

## Verification results

- Exported measurements: 63,252
- Positive returns: 33,304
- Accepted screened returns: 25,774
- Positive-mask mismatches: 0
- Screening-mask mismatches: 0
- Saved-range mismatches: 0
- NPZ datasets checked: 18
- NPZ datasets passed: 18
- MATLAB positive classification mismatches: 0
- MATLAB screening classification mismatches: 0
- MATLAB maximum reported range error: 0 m
- MATLAB tolerance: 1e-7 m

## Geometry representations

The existing datasets use two reconstruction methods:

- UNIFORM_FOV_HYPOTHESIS
- SIMPLELIDAR_SOURCE_MATCHED

The uniform-FOV representation is a geometry hypothesis.

The source-matched representation requires further physical and coordinate-system validation before being used as verified 3D geometry.

## Startup-frame observation

The sampled Frame 0 contained 4,424 positive returns but only 1,914 screened returns.

This may indicate startup behavior. Its cause is not established.

Frame 0 must remain in the original datasets. Subsequent evaluations should separately report startup-inclusive and startup-excluded results.

## Scientific limitations

- Cross-language numerical consistency does not establish detection accuracy.
- Existing MATLAB frame-level analysis covered selected frames, not complete recordings.
- Range-image ordering assumes row-major ray indexing.
- Three-dimensional beam geometry has not been independently GroundTruth-validated.
- These historical datasets do not establish a controlled Clear-versus-Fog degradation result.
- No CPU-versus-FPGA energy savings have been measured.

## Evidence

- 02_CSV_Data/task23_11C_npz_integrity.csv
- 06_Research_Findings/task23_11C_mask_validation_report.txt
- 06_Research_Findings/task23_04c2_matlab_findings.txt
- 08_Processed_Data/task23_04c_raw_lidar_measurements.csv
- 01_Code/task23_04c2_matlab_lidar_validation.m

## Conclusion

Task 23.11.C preprocessing consistency: PASS.

The numerical range-processing and saved dataset structures are suitable for subsequent baseline analysis, subject to the stated geometry and physical-validity limitations.

Next: Task 23.11.D — Clear LiDAR baseline metrics.
