# Task 23.11.E - Controlled LiDAR Weather Validation

## Research objective

Validate whether GEMSTAR's simulated weather conditions produce
measurable differences in recorded LiDAR positive-return coverage
while keeping the underlying validation scene and sensor
configuration controlled.

## Experimental conditions

- Clear weather
- Fog with meteorological optical range (MOR) = 100 m
- Fog with MOR = 20 m
- Validation map: SensorFusionValidationMap
- LiDAR reflection slots per frame: 5,271
- OSI SensorView and Ground Truth recordings preserved separately

## Full-dataset results

| Weather | Frames | Missing LiDAR frames | Positive returns/frame | Coverage |
|---|---:|---:|---:|---:|
| Clear | 13,819 | 0 | 5,090 | 96.566116% |
| Fog MOR 100 | 12,386 | 0 | 5,090 | 96.566116% |
| Fog MOR 20 | 14,597 | 0 | 0 | 0% |

All three datasets had strictly increasing timestamps.
Each dataset contained only one unique LiDAR reflection hash.

## Distance-threshold consistency

Clear positive-return distances:

- Minimum: 8.502465 m
- Median: 13.266294 m
- Maximum: 15.767747 m

Fog MOR 20 estimated reflectivity-dependent cutoffs:

- Low-reflectivity cutoff: 6.057307 m
- High-reflectivity cutoff: 6.926873 m

All 5,090 positive Clear returns were beyond both MOR 20
distance cutoffs.

The corresponding MOR 100 cutoffs are approximately
30.286536 m and 34.634364 m.

## Reflection-field comparison

The first Clear and Fog MOR 20 frames contained 5,271
corresponding reflection slots.

- Matching time-of-flight slots: 5,271
- Matching signal-strength slots: 181
- Previously positive Clear returns set to zero strength: 5,090
- Fog MOR 20 slots with zero signal strength: 5,271
- Fog MOR 20 slots retaining positive time-of-flight: 5,090

These observations are consistent with weather processing
invalidating signal strength without changing time of flight.

## Main findings

1. Clear weather preserved 5,090 positive LiDAR returns per frame.
2. Fog MOR 100 preserved the same positive-return coverage
   and identical sampled reflection values as Clear.
3. Fog MOR 20 resulted in zero positive returns across
   all 14,597 recorded frames.
4. The measured results agree with the inspected distance-cutoff
   behaviour of GEMSTAR's LiDAR weather-effect implementation.

## Scientific limitations

- This is simulated sensor-return coverage, not object-detection accuracy.
- The experiments do not establish physical realism of fog attenuation.
- Identical reflection hashes across all frames indicate a constant
  LiDAR measurement pattern in this controlled validation scene.
- Dynamic sensor response, changing traffic, and ego-motion effects
  have not been validated by these experiments.
- The measurements do not establish Camera-LiDAR-Radar fusion quality.
- Hardware energy, FPGA utilization and execution latency are
  outside the scope of this experiment.
- The different run lengths must not be interpreted as sensor
  performance differences.

## Evidence

Comparison CSV:
02_CSV_Data/task23_11E_three_weather_comparison.csv

Graphs:
03_Graphs/task23_11E_lidar_coverage_by_weather.png
03_Graphs/task23_11E_positive_vs_invalid_returns.png

Runtime logs:
05_Raw_Data_References/task23_11E_clear_runtime.log
05_Raw_Data_References/task23_11E_fog20_runtime.log
05_Raw_Data_References/task23_11E_fog100_runtime.log

The original OSI recordings remain in the GEMSTAR Output folder.

## Conclusion

Task 23.11.E demonstrates a controlled,
model-consistent change in recorded LiDAR return availability
between Clear, Fog MOR 100 and Fog MOR 20.

Further dynamic-scene and multisensor validation is required
before using these results to support claims about perception
accuracy or adaptive sensor-fusion reliability.
