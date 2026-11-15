# GEMSTAR Task 27 — Final Research Report

**Study:** Workload characterization, nominal memory
modeling and preliminary ARM–FPGA candidate selection.

**Status:** Software profiling and analytical modeling
completed; final hardware and perception validation pending.

## 1. Research objective

Identify promising ARM–FPGA processing kernels while
preserving perception quality and eventually minimizing
measured system energy per valid perception result.

## 2. Reproducible evidence

- Original CPU timing observations: 6,025
- Registered research datasets: 20
- Source hash checks repeated: 15
- MATLAB figures checked: 24 PNG/FIG pairs

## 3. CPU workload observations

| Workload | Median of group medians (ms) |
|---|---:|
| EKF | 5.485225 |
| Camera | 1.815050 |
| LiDAR | 0.460500 |
| Radar | 0.008825 |
| YOLO11s | 43.746050 |
| Partial_LiDAR_Radar | 0.794900 |

Different benchmarks cover different data sizes and
processing boundaries. EKF is a replay; Radar times
cover batches; LiDAR stages were timed individually.
These values are not equivalent end-to-end frame times.

## 4. LiDAR structural and memory analysis

- Input points: 172,839
- Retained after spatial filtering: 16,295
- Point reduction: 90.5722%
- Nominal XYZ input bytes: 2,074,068
- Nominal filtered XYZ output bytes: 195,540
- Modeled two-way payload bytes: 2,269,608

Point reduction is not an energy saving and does not
establish preservation of all relevant objects.
Payload sizes assume compact float32 XYZ triples.

## 5. Camera, Radar and YOLO analysis

Camera uses BGR-to-grayscale/HSV conversion, Canny
edges, and float64 Laplacian processing. Named buffer
sizes are calculated, not observed DRAM traffic.

Radar timing measures valid-return batches, excluding
association and invalid returns.

YOLO11s prediction is the largest measured standalone
workload, but detection accuracy, layer-level resource
costs and accelerator feasibility remain unvalidated.

## 6. Provisional FPGA kernel shortlist

- **LiDAR_filter**
- **Camera_preprocessing**

This is a provisional engineering shortlist, not
a measured energy-optimal selection. YOLO remains
a candidate for further layer-level study.

## 7. Transfer and energy break-even

- Workload/model cases: 354
- Parameter-sweep summary groups: 12
- Transfer bandwidths are hypothetical.
- FPGA compute and fixed overhead are hypothetical.
- No real DMA, FPGA execution or power was measured.

An energy comparison requires matched execution
boundaries and measured total-system energy.
A lower latency alone does not prove lower energy.

## 8. Scientific limitations

- No empirical hardware roofline established.
- Exact operation counts and DRAM traffic unknown.
- No measured ARM–FPGA latency or energy savings.
- Full three-sensor perception quality unverified.
- No end-to-end p99 deadline guarantee.
- Rain and dense-traffic generalization unverified.
- Camera ROI equivalence to FULL not established.
- Development CPU timings cannot stand in for ARM.

## 9. Requirements for the next tasks

Task 28: validate numerical fidelity and hardware-
compatible representations against matched inputs.

Task 29: use quality and deadline constraints when
designing the adaptive scheduling architecture.

Hardware stages: measure transfers, actual execution
time and complete board/system energy; compare with
matched CPU baselines and valid perception outputs.

## 10. Provenance

Primary data: Task 26 CPU measurements and Task 27
derived research CSVs. The evidence register and
SHA-256 archive manifest accompany this report.

The archive manifest covers files present at the
time of finalization, including this report, but
excludes the manifest itself and the final JSON.
