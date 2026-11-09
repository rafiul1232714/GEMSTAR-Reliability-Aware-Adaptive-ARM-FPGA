# Task 15 — Final Research Findings

## 1. Research Objective

Establish a reproducible archive of GEMSTAR Camera,
LiDAR, Radar and GroundTruth recordings from Tasks 1–14.

## 2. Dataset Integrity

- Total OSI file references: 49
- Unique OSI file hashes: 38
- Unique SensorView recordings: 19
- Candidate GT/SV recording pairs: 19
- Ground-truth pairing verification: Pending Task 17

## 3. Three-Sensor Payload Coverage

- Full Camera/LiDAR/Radar payload coverage: 10 recordings
- Missing at least one sensor payload: 9 recordings

Full coverage means nonempty image/reflection payloads
in every parsed frame. It does not establish detection
accuracy, valid reflections, calibration or synchronization.

## 4. Scenario Evidence

Available scenario-folder labels include:
- baseline_clear
- baseline_fog
- baseline_fog_working_radar
- fog_mor100
- fog_postfix_validation
- task05_fog_test

The fog_mor20 and fog_mor50 folders are empty.

Scenario labels remain provisional until historical
simulation configurations are verified.

## 5. Configuration Findings

- Camera and LiDAR mount parameters were identified.
- Radar mounting requires further verification.
- Logger inputs differ between configuration snapshots.
- Fog MOR=20 appears in inspected configurations.
- Historical configuration-to-recording links remain unresolved.

## 6. Open Research Issues

Total unresolved issues: 7

- T15-001: 9 of 19 unique recordings lack at least one populated sensor stream
- T15-002: fog_mor20 and fog_mor50 research folders contain no recordings
- T15-003: Recording 415 GT counterpart exists in GEMSTAR Output but not in baseline_fog folder
- T15-004: Radar Mount setting commented out in inspected configuration snapshots
- T15-005: Historical configuration for each recording has not been conclusively identified
- T15-006: Full payload coverage does not establish valid returns, calibration, synchronization or object association
- T15-007: Earlier Task 14 Camera-Radar association provisional and target LiDAR association unconfirmed

## 7. Research Conclusions

Ten recordings contain nonempty payloads from all
three sensors in every parsed SensorView message.

Nineteen unique SensorView recordings were parsed
successfully without reported parser errors.

The archive provides a foundation for the following tasks:

- Task 17: Sensor timestamp and geometry validation
- Task 18: Camera feature and detection validation
- Task 19: LiDAR filtering and geometry
- Task 20: Radar measurement validation
- Task 21: Multi-sensor association

## 8. Scientific Limitations

Payload availability is not equivalent to sensor accuracy.
GT/SV filename pairing is not proof of synchronization.
Weather-folder labels do not prove historical weather settings.
No three-sensor object-level fusion has been validated here.
