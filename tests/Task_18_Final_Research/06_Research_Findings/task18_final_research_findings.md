# TASK 18 - FINAL RESEARCH FINDINGS

## Research Title
GEMSTAR Camera Perception: Image Decoding, Preprocessing,
Object Detection, Accuracy Evaluation and CPU Benchmarking

## 1. Research Objective

Develop a reproducible Camera perception reference pipeline
using recorded GEMSTAR SensorView measurements.

Investigate image processing, object detection correctness,
and CPU inference latency before ARM-FPGA implementation.

## 2. Dataset

Simulation platform: GEMSTAR / Unreal Engine
Scenario folder: fog_mor100

Source recording:
20261027T224313Z_sv_380_X_466_GEMSTAR.osi

Total source recording frames: 466
Selected experimental frames: 12

Selected frame indices:
0, 50, 100, 150, 200, 250, 300, 350,
400, 423, 424, 450

The selected sample includes both timing regimes
identified in Task 17.

## 3. Camera Image Decoding

Image resolution: 640 x 480
Image payload: 921600 bytes
Bytes per pixel: 3

Images were decoded as three-channel RGB arrays.
Visual inspection supported the RGB interpretation.

The exact OSI enumeration meaning and channel convention
were not independently established from source definitions.

## 4. Image Preprocessing

Python/OpenCV implementations:
- Grayscale conversion
- Gaussian smoothing
- Sobel gradient processing

Corresponding MATLAB implementations were developed
without requiring the Image Processing Toolbox.

Python-MATLAB mean absolute error:

Grayscale: 0.000146
Gaussian: 0.017559
Sobel: 0.122012

All values refer to the 0-255 pixel intensity scale.

These results indicate close numerical agreement
for the selected test frame.

## 5. Object Detection

Pretrained models:
- YOLO11 Nano
- YOLO11 Small

Model execution:
Desktop CPU, PyTorch CPU runtime

Detection settings in controlled experiments:
Image size: 640
Confidence threshold: 0.25
NMS IoU threshold: 0.70
Class-agnostic NMS: enabled

Both model weights were archived.

## 6. Annotation Dataset

Total reviewed frames: 12
Manual reference objects: 5

Reference objects:
Frame 100: car
Frame 150: car
Frame 300: car
Frame 350: car
Frame 450: truck

The remaining seven frames were recorded without
target-object reference annotations.

The annotation dataset is provisional and does
not establish exhaustive scene-level ground truth.

Frame 250 requires review of ambiguous distant objects.

## 7. Controlled Detection Accuracy

Evaluation matching:
IoU >= 0.50 and matching object class.

YOLO11 Nano:
True positives: 1
False positives: 5
False negatives: 4
Precision: 16.67 percent
Recall: 20.00 percent
F1 score: 18.18 percent
Class-independent localization matches: 3

YOLO11 Small:
True positives: 3
False positives: 7
False negatives: 2
Precision: 30.00 percent
Recall: 60.00 percent
F1 score: 40.00 percent
Class-independent localization matches: 3

Interpretation:
The Small model performed better on this limited,
provisionally annotated sample.

Both models exhibited classification failures,
particularly for partially visible vehicles.

Neither detector has been validated as sufficiently
reliable for safety-critical use.

## 8. Repeated CPU Benchmark

Experimental design:
12 frames x 5 repetitions per model.

Measurements per model: 60
Total inference measurements: 120

YOLO11 Nano:
Median inference: 19.137 ms
Mean inference: 19.392 ms
P95 inference: 21.911 ms
Standard deviation: 1.497 ms

YOLO11 Small:
Median inference: 44.512 ms
Mean inference: 44.664 ms
P95 inference: 47.356 ms
Standard deviation: 1.887 ms

Small/Nano median latency ratio:
Approximately 2.33.

These are desktop CPU inference measurements,
not ARM-FPGA measurements.

Inference times exclude some external
pipeline and transfer costs.

## 9. MATLAB Cross-Validation

MATLAB independently recalculated:
- Detection precision
- Detection recall
- Detection F1 scores
- Mean inference latency
- Median inference latency
- P95 inference latency
- Standard deviation

Python-MATLAB numerical consistency checks passed.

MATLAB research figures and CSV summaries were saved.

## 10. Main Research Findings

F01:
GEMSTAR Camera payloads can be decoded and processed
using a reproducible Python software pipeline.

F02:
MATLAB and Python preprocessing results agree closely
on the selected Camera image.

F03:
General-purpose pretrained detectors can misclassify
GEMSTAR vehicles as unrelated classes.

F04:
Class-independent localization success does not
guarantee correct classification.

F05:
YOLO11 Small improves the preliminary detection F1
relative to Nano, but incurs substantially greater
desktop CPU inference latency.

F06:
The experiment provides a software reference for
future hardware mapping and performance comparison.

## 11. Limitations

L01:
Only 12 selected images were evaluated.

L02:
Only five provisional manual reference objects
were available.

L03:
Annotation completeness and class correctness
were not independently verified.

L04:
Confidence scores were not calibrated as
reliability probabilities.

L05:
No test across independently labeled
weather and traffic scenario groups was performed.

L06:
The current CPU benchmark does not measure
ARM execution or board-level energy.

L07:
Model inference latency does not by itself
represent total perception pipeline latency.

L08:
No quantitative FPGA acceleration result
has been demonstrated in Task 18.

## 12. Implications for ARM-FPGA Thesis

The Camera operator pipeline is a potential
candidate for hardware-software partitioning.

Future experiments should investigate:
- RGB and grayscale preprocessing costs
- Image resizing and filtering acceleration
- Quantized neural-network inference
- Memory and CPU-FPGA transfer overhead
- Quality versus processing latency
- Sensor reliability and uncertainty
- Real-time deadline satisfaction

Performance and energy improvements must
be established using measurements on the
actual ARM-FPGA target hardware.

## 13. Next Research Tasks

Task 19:
LiDAR preprocessing and geometric analysis.

Task 20:
Radar preprocessing and measurement analysis.

Tasks 21-23:
Cross-sensor association, fusion,
tracking and uncertainty estimation.

Later hardware phase:
Implement and benchmark selected operators
on actual FPGA hardware.

## 14. Research Status

Task 18 software experiments completed.
Final illustrated PDF preparation pending.

Detection accuracy results remain provisional
and are not yet generalizable.
