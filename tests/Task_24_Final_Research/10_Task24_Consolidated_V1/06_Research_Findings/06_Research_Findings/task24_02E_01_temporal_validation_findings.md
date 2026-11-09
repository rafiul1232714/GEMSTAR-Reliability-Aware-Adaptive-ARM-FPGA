# Task 24.2 ? Temporal Validation Research Findings

## Evidence scope

Source recording: `20261105T231919Z`, paired GEMSTAR
SensorView and GroundTruth OSI streams.

This report distinguishes recorder-level timestamp consistency
from independently established sensor acquisition synchronization.

## 1. Recorded message completeness

- SensorView frames: **372**
- GroundTruth frames: **372**
- Exactly matching SV/GT timestamps: **372/372**
- Camera/LiDAR/Radar views present together: **372/372**
- Nonpositive recording intervals: **0**

These checks establish recorder-level consistency, not
independent Camera/LiDAR/Radar acquisition synchronization.

## 2. Timing regimes

| Property | Initial regime | Later regime |
|---|---:|---:|
| Ending frame indices of intervals | 1?310 | 311?371 |
| Intervals | 310 | 61 |
| Mean interval (ms) | 33.260154 | 333.334059 |
| Median interval (ms) | 32.709200 | 333.333492 |

- Transition begins at frame **311**.
- Later/initial mean-interval ratio: **10.0220**.
- Full-recording interval minimum: **28.567199 ms**.
- Full-recording interval maximum: **333.368808 ms**.
- Full-recording interval mean: **82.598451 ms**.
- Cause of regime transition: **not established**.

## 3. Host-pose comparisons

- Comparable host-pose frames: **355**.
- Initial regime comparisons: **310**.
- Later regime comparisons: **45**.
- Initial mean same-frame horizontal discrepancy:
  **0.336992410 m**.
- Later mean same-frame horizontal discrepancy:
  **2.322639708 m**.
- Overall preceding-frame horizontal discrepancy:
  **0.173693141 m**.
- Mean preceding-frame ego-local residual:
  - X: **-0.111434336 m**
  - Y: **0.133235491 m**
  - Z: **-0.826199945 m**

The nearly fixed residual is compatible with a systematic
actor-origin/bounding-centre difference and apparent frame-index
offset. It does **not** prove a one-frame acquisition delay.

## 4. Host availability

- Embedded host pose missing at frame **0**.
- Embedded host pose missing at frames **356?371**.
- GroundTruth host ID `76895` is present at frame 0.
- Separate GroundTruth host ID `76895` is absent
  at frames **356?371**, based on the separate full-GT audit.
- Camera, LiDAR and Radar views remain present at all
  these frame indices.
- Reason for final host disappearance: **not established**.

## 5. Implications for subsequent fusion work

1. Use the measured variable logger timestep for
   frame-indexed baseline experiments; do not assume 30 FPS.
2. Do not treat shared message timestamps as proof of
   independently synchronized sensor acquisitions.
3. Do not apply a one-frame temporal correction without
   separate runtime/acquisition validation.
4. Mark host-pose-dependent operations unavailable when
   required host data is missing.
5. Maintain separate validity masks for sensor presence,
   ego-pose availability, and object ground truth.
6. Do not claim calibrated physical alignment from the
   nominal camera/LiDAR/Radar projection alone.

## 6. Evidence files and SHA-256 checksums

- `task24_02D_02_full_recording_timestamps.csv`: `8392332862426a9383e87dee6a5b465fc10e39223c44ee9fcd9745e8c6b0f91d`
- `task24_02D_04_timing_regime_segments.csv`: `37ea4d3fa91a44d85287eb86b7ec0114d03ec55b9e9cb96c4cd9baa57ed17e27`
- `task24_02D_05_host_pose_offset_full_recording.csv`: `33878bf978a5c66e1fbaa419b3c8e4259fcd1c26d86252f47fe6ccd1a2a2e469`
- `task24_02D_06_embedded_host_presence_372frames.csv`: `5636863a149d2d5958dde403d0c2126ca5131e28e36430973d504d837a4ecb52`

## Conclusion

**Task 24.2.D: Completed as a diagnostic temporal-validation
stage with documented limitations.**

Independent acquisition synchronization, physical cross-sensor
registration, the cause of the frame-311 interval transition,
and the cause of host disappearance remain unresolved.
