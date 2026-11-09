# Task 23.11.G - Preliminary LiDAR Workload Profiling

## Objective

Measure the execution time of the Python LiDAR
availability-scoring function on the development PC.

## Experimental methodology

- Source: first real GEMSTAR LiDAR SensorView frame per weather condition.
- Each frame contains 5271 reflection slots.
- Timing uses Python time.perf_counter_ns.
- Preliminary G.1: 200 samples per weather condition.
- G.2: 3 rounds with 200 samples per weather per round.
- G.2 total: 1800 measurements.
- 30 warm-up calls before each measurement batch.
- Dataset order was shuffled using a fixed random seed.
- Disk reading and protobuf decoding were excluded from timed calls.

## Measured G.2 results

| Weather | Samples | Mean us | P50 us | P95 us | P99 us | Std us |
|---|---:|---:|---:|---:|---:|---:|
| Clear | 600 | 925.187 | 920.500 | 967.010 | 1256.396 | 78.212 |
| Fog100 | 600 | 932.944 | 919.300 | 965.305 | 1365.312 | 75.301 |
| Fog20 | 600 | 890.777 | 881.600 | 926.440 | 1073.268 | 58.146 |

## Interpretation

The scoring function required approximately 0.9 ms per
call on the development PC for the measured inputs.

P99 was above the median in all weather conditions.
The timings are preliminary empirical latency measurements.

Observed differences between weather conditions must not
be interpreted as causal speedups from fog.

## Limitations

- Each weather condition repeatedly scores one fixed LiDAR frame.
- Repetitions are not independent driving scenarios.
- CPU scheduling, system load, cache effects and Python overhead may influence timings.
- The measurement does not include OSI decoding or disk access.
- The measurement does not include Camera/Radar or sensor fusion.
- The measurement does not include live transport or scheduling.
- The test is not an ARM or FPGA hardware benchmark.
- No power or energy consumption was measured.
- Empirical P99 is not a worst-case execution-time guarantee.
- No complete platform specification was captured during profiling.

## Future research requirements

- Record hardware, Python version and operating conditions.
- Test dynamic driving data and representative workloads.
- Measure end-to-end preprocessing latency.
- Perform matched ARM CPU and FPGA benchmarks in later tasks.
- Measure energy per valid perception result.
- Verify perception quality and deadline constraints.

## Conclusion

Task G established a preliminary, reproducible Python
execution-time reference for LiDAR availability scoring.

It is suitable for initial workload planning but not for
hardware energy-efficiency or real-time guarantees.
