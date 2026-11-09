# Task 24.3.10 — Controlled Recording Validation Plan

## Objective

Create a reproducible GEMSTAR dataset that supports independently
validated Camera-LiDAR-Radar object measurements.

The existing 372-frame recording remains the baseline for timing,
freshness, geometry and reliability analysis.

## Proposed scenarios

| ID | Condition | Target | Planned placement |
|---|---|---|---|
| C01 | Clear | One stationary vehicle | Approximately 10 m |
| C02 | Clear | One stationary vehicle | Approximately 20 m |
| C03 | Clear | One stationary vehicle | Approximately 30 m |
| C04 | Clear | One moving vehicle | Measured trajectory |
| C05 | Fog | Repeat validated clear scenario | Matched conditions |

All distances are proposed test parameters, not verified results.

## Pre-recording requirements

1. Record the exact GEMSTAR, Unreal, SUMO and sensor configurations.
2. Verify that the target vehicle is positioned in the sensor coverage area.
3. Investigate Camera-visible orange/yellow debug graphics.
4. Verify sensor coordinate conventions without assuming physical calibration.
5. Retain immutable SensorView and separate GroundTruth recording files.
6. Save SHA-256 hashes and source configuration snapshots.

## Measurement acceptance criteria

### Camera

- Original RGB frames must be readable and independently hashed.
- Target visibility must be assessed from actual image content.
- Image localization must not use GT identity as a detector input.
- Save bounding boxes or image regions with an explicit detection method.

### LiDAR

- Preserve all reflection categories and original measurements.
- Test whether target-related geometric returns can be separated.
- Do not equate RANSAC plane outliers with vehicles automatically.
- Document missed, fragmented and merged detections.

### Radar

- Preserve range, angle, Doppler and measurement quality.
- Audit freshness and velocity anomalies.
- Compare object proximity using independently assessed geometry.
- Do not treat proximity alone as a confirmed target match.

### Cross-sensor fusion readiness

- Define association using sensor observations only.
- Record unmatched, ambiguous and missing observations.
- Keep GroundTruth identities completely separate from fusion inputs.
- Evaluate position error and matching quality only after validation.
- Document timestamp alignment uncertainty.

## Acceptance decision

PASS: Evidence supports at least one independently evaluated,
sensor-only target measurement and a reproducible association test.

PARTIAL: Some sensors observe the target, but association remains
unverified. Retain the data with explicit limitations.

FAIL: No defensible object measurements are available.
Investigate simulation configuration and repeat a controlled test.

The actual result must be established experimentally.
No acceptance result is assigned in advance.

## Scope boundary

This document defines the exit criteria for the data-preparation
stage. It does not claim completed object detection, fusion,
EKF validation or measured energy savings.

## Next action

Complete Task 24.3 research consolidation, then implement and
execute the controlled recording as part of the continued Task 24
object-association and tracking workflow.