# Task 29.3E.3 — Camera AI Research Checkpoint

## 1. Research objective

Compare Camera AI inference candidates under controlled software
conditions and establish the requirements for later KR260 deployment.

## 2. Existing benchmark

YOLO11n median CPU inference latency: 19.5245 ms.

YOLO11s median CPU inference latency: 43.5010 ms.

YOLO11s / YOLO11n latency ratio: 2.2280.

These values come from the previous Task 29.3C benchmark.
They are workstation CPU results, not KR260 measurements.

YOLO11n is the preliminary lower-latency candidate.
A final model selection requires verified detection quality.

## 3. Camera annotation audit

Images reviewed: 20.

Original YOLO11s proposals: 18.

Provisional KEEP: 4.
Provisional RECLASS: 2.
Provisional REMOVE: 8.
Unresolved proposals: 4.

The review found a white truck classified as airplane.
Other false-positive candidates were also identified.

All corrections remain provisional.

## 4. Detection quality limitations

The 20-image dataset does not yet have complete independently
verified annotations.

The proposals came from YOLO11s and therefore cannot be used
as independent reference labels for unbiased YOLO11s evaluation.

False negatives and object completeness still need checking.

Validated precision, recall, mAP and F1: NOT AVAILABLE.

## 5. INT8 and deployment readiness

Available: YOLO11n.pt and YOLO11s.pt.

ONNX models found: 0.
Compiled XMODEL files found: 0.
Hardware platforms/bitstreams found: 0.
Confirmed DPU architecture configurations found: 0.

The previous PowerShell inventory accidentally classified
task18_e9_archive_verification.json as an architecture file.
This was a filename-matching false positive.

Validated INT8 accuracy: NOT AVAILABLE.
KR260 DPU compatibility: NOT VERIFIED.
KR260 inference latency: NOT MEASURED.
KR260 energy: NOT MEASURED.

## 6. Research conclusion

The software CPU benchmarking and preliminary visual audit support
using YOLO11n as the lower-latency Camera AI candidate.

No conclusion can yet be made that YOLO11n has superior
detection quality or energy efficiency.

INT8 export and target-specific DPU compatibility remain
future experiments. Real FPGA performance and energy claims
require physical target hardware measurements.

## 7. Outstanding validation

- Resolve four uncertain proposals.
- Verify bounding boxes and missed objects across 20 images.
- Establish an independent ground-truth dataset if quantitative
  precision/recall comparison is required.
- Verify target-specific INT8 quantization and DPU compilation.
- Measure actual KR260 performance and energy during hardware work.

## 8. Checkpoint status

Task 29.3 software feasibility checkpoint: COMPLETE.

Independent detection-accuracy validation: OPEN.

Hardware acceleration and power validation: OPEN.
