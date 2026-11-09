# Task 23.11.H.2 - Scientific Readiness Review

## 1. Purpose

Evaluate the scientific readiness of the completed
LiDAR preprocessing, reliability and preliminary
workload profiling experiments.

## 2. Verified experimental foundation

Controlled weather datasets:

- Clear: 13,819 LiDAR frames
- Fog MOR 100: 12,386 LiDAR frames
- Fog MOR 20: 14,597 LiDAR frames

Total: 40,802 frames.

The recorded frames passed the Task F reliability
scoring and CSV consistency checks.

## 3. LiDAR availability results

| Weather | Mean availability |
|---|---:|
| Clear | 0.965661165 |
| Fog MOR 100 | 0.965661165 |
| Fog MOR 20 | 0.000000000 |

These values represent positive-return availability,
not object-detection accuracy.

## 4. Reliability algorithm

The Python scoring implementation distinguishes:

- VALID
- NO_RETURNS
- MISSING_FRAME
- EMPTY_FRAME
- INVALID_TIMESTAMP
- MALFORMED_FRAME

Functional tests and selected malformed-input
robustness tests passed.

This does not establish correctness for all possible
real-world or corrupted protobuf messages.

## 5. Preliminary execution-time profiling

G.2 collected 1800 execution-time measurements.

Each weather condition used:

- One fixed real LiDAR frame
- Three rounds
- 200 timed calls per round

Measured mean times:

- Clear: 925.187 microseconds
- Fog MOR 100: 932.944 microseconds
- Fog MOR 20: 890.777 microseconds

These are Python scoring times on the development PC.

They exclude:

- OSI file reading
- Protobuf decoding
- Live sensor transport
- Camera and Radar processing
- Sensor fusion
- ARM-FPGA communication

No processing energy was measured.

## 6. Scientific limitations

The controlled scene is static.

LiDAR reflection patterns were identical across
frames within each weather condition.

Therefore these experiments do not establish:

- Dynamic object detection quality
- Dynamic sensor reliability
- Object association or tracking performance
- Real-world fog-model accuracy
- Multisensor fusion accuracy
- ARM processor latency
- FPGA acceleration
- Hardware energy efficiency
- End-to-end real-time deadline compliance

The absence of positive returns must not be interpreted
automatically as hardware failure.

## 7. Readiness assessment

Controlled LiDAR data decoding:
    READY for further development.

LiDAR positive-return availability scoring:
    READY for controlled integration testing.

Preliminary workload characterization:
    COMPLETE as a development-PC reference.

Dynamic-scene LiDAR validation:
    NOT YET ESTABLISHED.

Three-sensor association and EKF tracking:
    NOT YET ESTABLISHED.

ARM-FPGA energy measurements:
    NOT YET ESTABLISHED.

## 8. Research transition

The next work must preserve the distinction between
measurement availability and perception correctness.

Task 24 will address three-sensor association
and EKF tracking fusion according to the selected
thesis roadmap.

Formal CPU benchmarking and hardware energy measurements
belong to their later roadmap tasks.

## 9. Conclusion

Task 23.11 provides validated controlled-scene LiDAR
availability measurements, reusable scoring code,
preliminary execution-time data, and documented evidence.

The work is ready for final archival review.

This assessment does not declare complete three-sensor
fusion or hardware implementation readiness.
