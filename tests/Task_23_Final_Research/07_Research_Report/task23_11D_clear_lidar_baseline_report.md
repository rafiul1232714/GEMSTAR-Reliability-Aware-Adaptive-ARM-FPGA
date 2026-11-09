# Task 23.11.D — Clear LiDAR Baseline Validation

## Objective

Establish a reproducible LiDAR baseline using the preserved
573-frame GEMSTAR Clear recording.

## Source recording

20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi

## Frame integrity

- Frames decoded: 573
- Missing timestamps: 0
- Non-monotonic timestamps: 0
- Missing LiDAR views: 0
- Empty reflection arrays: 0
- Protobuf parsing errors: 0

## LiDAR measurements

- Reflection slots per frame: 5271
- Screened returns per frame: 5090
- Mean accepted coverage: 96.566116%
- Coverage standard deviation: 0
- Median range: 13.266293947 m
- Median-range standard deviation: 0

## Timestamp statistics

- Minimum interval: 8.271798 ms
- Median interval: 10.724651 ms
- Maximum interval: 40.230498 ms
- Interval standard deviation: 2.281087 ms

## Raw-reflection comparison

Frames compared: 1, 2, 25, 100, 300, 573

Each sampled frame contained 5271 reflections.

All six sampled frames had identical SHA-256 hashes
of their ordered time-of-flight and signal-strength values.

Status: IDENTICAL_SAMPLED_REFLECTIONS

## Interpretation

The analyzed recording provides a reproducible static
LiDAR measurement baseline.

Identical sampled reflection arrays do not establish whether
the cause is a stationary scene, simulator caching, or another
simulation behavior.

The recording must not be presented as evidence of dynamic
scene tracking or weather-induced degradation.

## Scientific limitations

- Only six frames were directly compared using reflection hashes.
- Constant summary statistics do not prove every raw frame is identical.
- Detection accuracy has not been measured.
- Three-dimensional beam geometry remains insufficiently validated.
- Clear-versus-Fog physical degradation has not been established.
- CPU-versus-FPGA energy efficiency has not been measured.

## Evidence

- 02_CSV_Data/task23_11D_clear_lidar_frame_metrics.csv
- 06_Research_Findings/task23_11D_baseline_stability.txt
- 06_Research_Findings/task23_11D_range_variability.txt
- 03_Graphs/task23_11D_clear_coverage.png
- 03_Graphs/task23_11D_clear_ranges.png
- 03_Graphs/task23_11D_timestamp_intervals.png
- 01_Code/task23_11D_compare_raw_frames.py

## Conclusion

Task 23.11.D static Clear baseline characterization: PASS.

The recording is suitable as a repeatable preprocessing and
static sensor-measurement reference, but dynamic and
weather-dependent performance remain unvalidated.

Next: Task 23.11.E — Controlled Fog comparison.
