# GEMSTAR — Task 24.3 Final Research Report

## 1. Research objective

Prepare and assess Camera, LiDAR and Radar measurements for
subsequent three-sensor object association and EKF tracking.

This task concerns measurement extraction, data quality,
geometric feasibility and fusion readiness.

It does not claim completed object-level fusion or tracking.

## 2. Dataset

Source: GEMSTAR OSI recording, 20261105T231919Z, 380_X_372.

Validated paired frames: 372.

Camera images: 372.
LiDAR ray records: 1,960,812.
Radar ray records: 37,200.

LiDAR candidate returns: 823254.
Radar candidate returns: 24161.

Original OSI recordings were treated as immutable inputs.
GroundTruth object identities were excluded from fusion
measurement files.

## 3. Measurement extraction and verification

- Completed the first 10-frame extraction pilot.
- Verified 52,710 pilot LiDAR records.
- Verified 1,000 pilot Radar records.
- Extracted the complete 372-frame recording.
- Verified 37,200 Radar Doppler measurements against
  the earlier independent recorded-value audit.
- Confirmed zero numerical disagreement in the tested
  frame-0 geometry comparisons.
- Saved full measurements as compressed CSV files.
- Stored per-frame quality and freshness indicators.

Important: numerical consistency does not establish
physical sensor calibration.

## 4. Measurement freshness and reliability

LiDAR exact repeated consecutive pairs: 148.
Radar exact repeated consecutive pairs: 57.

Radar all-zero candidate-Doppler frames: 149.
Radar returns exceeding the provisional absolute
70 m/s review threshold: 58.

The 58 extreme returns occurred in frame 1.

Recorded timestamps advance even when some sensor
reflection payloads are unchanged.

Sensor acquisition synchronization remains unverified.

The frame interval changes near frame 311 from
approximately 33.26 ms to 333.33 ms.

These findings require independent sensor-quality flags
and measured variable-delta-time processing.

## 5. LiDAR geometry and clustering

A 0.75 m voxel clustering pilot was evaluated on
frames 2, 172, 311 and 355.

The largest clusters occupied most candidate points,
indicating poor suitability as independent detections.

Near-horizontal RANSAC planes explained:

- Frame 2: 87.48% of ROI points.
- Frame 172: 84.49%.
- Frame 311: 100%.
- Frame 355: 95.99%.

These are geometric plane classifications, not
confirmed road labels.

Above-plane clustering retained:

- Frame 2: three clusters.
- Frame 172: one cluster.
- Frame 311: zero clusters.
- Frame 355: zero clusters.

The retained structures were often thin or elongated.
They cannot be considered verified vehicle detections.

Simulator-side LiDAR source IDs were inspected for
diagnostics only and must not enter the fusion pipeline.

## 6. LiDAR-Radar association feasibility

Four exploratory above-plane LiDAR clusters were
compared against corresponding Radar candidate returns.

Point-to-point proximity was evaluated against a
dominant-plane control.

Only five nearby Radar observations across the
per-cluster comparisons were closer to the candidate
cluster than to the plane within 1 m.

This is not a count of five unique associated objects,
and Radar returns can contribute to multiple comparisons.

Physical object correspondence has not been established.

## 7. Cross-sensor visibility

Four frames were selected: 2, 172, 311 and 355.

Radar candidates inspected: 269.

Elevated Radar candidates above 2 m: 60.

Of these elevated returns:

- 31 mapped outside the nominal LiDAR field of view.
- 29 mapped inside the nominal LiDAR field of view
  but had a nearest LiDAR no-hit ray.
- None of those 29 had a candidate in the inspected
  3x3 LiDAR angular neighborhood.

All 269 Radar candidate returns projected inside
the nominal Camera image boundaries.

Camera image inclusion is not object detection.

## 8. Camera visual inspection

Original Camera images and Radar overlay images were
reviewed for frames 2, 172, 311 and 355.

The scenes contain roads, roadside vegetation,
structures and other visible scene elements.

A light-colored vehicle is visible in frame 311,
but the tested LiDAR above-plane extractor produced
no retained object cluster in that frame.

Orange/yellow curved graphics were visible in
the original Camera images. Their simulator-side
origin remains unverified.

These images do not establish validated Camera-Radar
or Camera-LiDAR object association.

## 9. MATLAB outputs

The research includes:

- Candidate-return time-series plots.
- Sensor payload-freshness visualization.
- Radar Doppler anomaly visualization.
- Combined reliability and timing timeline.
- LiDAR-Radar geometry figures for four frames.
- Camera-Radar overlay images for four frames.

The exact produced artifacts are tracked in the
separate SHA-256 evidence manifest.

## 10. Dataset decision

RETAIN the original 372-frame dataset for:

- Sensor freshness and reliability research.
- Variable frame-interval analysis.
- Doppler diagnostics.
- Sensor preprocessing and scheduling experiments.
- Reproducible baseline studies.

Do not claim validated object-level fusion accuracy
from this recording.

## 11. Controlled-recording plan

Five experimental scenarios have been planned:

- Clear weather, stationary target around 10 m.
- Clear weather, stationary target around 20 m.
- Clear weather, stationary target around 30 m.
- Clear weather, moving target vehicle.
- Fog, repeating a suitable validated clear scenario.

There are 12 planned validation checks.

The controlled recording has NOT been executed.

Its acceptance criteria require observable sensor-only
measurements, separately held GroundTruth evaluation,
explicit unmatched outcomes and reproducible evidence.

## 12. Scientific limitations

- Nominal extrinsic geometry is uncalibrated.
- Recorder timestamp equality does not prove
  independent sensor acquisition synchronization.
- Radar signal strength is not a calibrated probability.
- Exact repeated measurements do not independently
  prove a sensor buffer fault.
- RANSAC plane outliers are not object labels.
- Spatial proximity is not confirmed object association.
- Camera projection is not Camera object detection.
- No validated EKF trajectory estimates are reported.
- No perception-accuracy improvement is claimed.
- No hardware energy savings have been measured.

## 13. Task 24.3 closure

Status: COMPLETE WITH DOCUMENTED LIMITATIONS.

Completed scope:

- Full measurement extraction and integrity validation.
- Reliability/freshness analysis.
- MATLAB visualization.
- LiDAR geometric feasibility diagnostics.
- Cross-sensor spatial and visibility diagnostics.
- Camera overlay inspection.
- Controlled-recording decision and acceptance plan.

Pending beyond this completed diagnostic scope:

- Actual controlled GEMSTAR recording.
- Sensor-only object detection and association.
- Independent object-level GroundTruth evaluation.
- EKF implementation and tracking validation.
- Hardware energy and latency benchmarking.

The broader Task 24 three-sensor fusion objective
remains IN PROGRESS.

## 14. Reproducibility

The companion evidence manifest records file paths,
sizes and SHA-256 hashes for the research package.

The manifest excludes itself.

Raw OSI recordings reside outside this research folder
and are not copied or modified by consolidation.