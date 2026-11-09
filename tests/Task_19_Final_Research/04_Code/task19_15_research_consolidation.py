import csv
import json
import hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_19_Final_Research"
)

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"
REPORTS = BASE / "07_Research_Report"

FINDINGS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

def read_csv(name):
    path = DATA / name
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")

def median(values):
    import statistics
    values = [numeric(x) for x in values]
    values = [v for v in values if v == v]
    return statistics.median(values) if values else None

def fmt(value, digits=3):
    return "N/A" if value is None else f"{value:.{digits}f}"

def md_table(headers, rows):
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(
            str(v).replace("|", "/") for v in row
        ) + " |")
    return "\n".join(output)

print("\n=== TASK 19.15 RESEARCH CONSOLIDATION ===")

inventory = read_csv(
    "task19_10l_cross_recording_inventory.csv"
)
quality = read_csv(
    "task19_11_preprocessing_quality_audit.csv"
)
monitor = read_csv(
    "task19_10p_observability_monitor_results.csv"
)
pipeline = read_csv(
    "task19_10t_full_monitor_pipeline_results.csv"
)
timing = read_csv(
    "task19_10t_full_monitor_timing_samples.csv"
)
quant = read_csv(
    "task19_13_quantization_summary.csv"
)

required = [
    "task19_12_deadline_scenario_summary.csv",
    "task19_14_hardware_software_partition.csv",
    "task19_14_hardware_validation_matrix.csv",
]

for name in required:
    read_csv(name)

assert len(inventory) == 48
assert len(quality) == 48
assert len(monitor) == 48
assert len(pipeline) == 48

scenario_counts = Counter(r["Scenario"] for r in inventory)
state_counts = Counter(
    r["ObservabilityState"] for r in monitor
)
mode_counts = Counter(r["PolicyMode"] for r in pipeline)

evaluated = [
    r for r in quality
    if r["Evaluated"].lower() in ("true", "1")
]

failures = [
    r for r in evaluated
    if r["RequiresQualityInvestigation"].lower()
       in ("true", "1")
]

processed = [
    r for r in pipeline
    if r["PolicyMode"] != "SKIP"
]

speed_ratio = median(r["SpeedRatio"] for r in processed)
monitor_ms = median(r["MonitorMedianMs"] for r in pipeline)

deadline_ms = 3.0
baseline_misses = sum(
    numeric(r["BaselineMs"]) > deadline_ms
    for r in timing
)
policy_misses = sum(
    numeric(r["PolicyMs"]) > deadline_ms
    for r in timing
)

def p95(values):
    v = sorted(numeric(x) for x in values)
    if not v:
        return None
    import math
    return v[math.ceil(0.95 * len(v)) - 1]

baseline_p95 = p95(r["BaselineMs"] for r in timing)
policy_p95 = p95(r["PolicyMs"] for r in timing)

# Create verified file inventory with SHA-256 hashes.
file_rows = []

for path in sorted(BASE.rglob("*")):
    if not path.is_file():
        continue

    # Exclude generated consolidation files.
    if path.name.startswith("task19_15_"):
        continue

    sha = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(block)

    file_rows.append({
        "RelativePath": str(path.relative_to(BASE)),
        "SizeBytes": path.stat().st_size,
        "SHA256": sha.hexdigest(),
    })

inventory_out = FINDINGS / "task19_15_artifact_manifest.csv"

with inventory_out.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=[
            "RelativePath", "SizeBytes", "SHA256"
        ]
    )
    writer.writeheader()
    writer.writerows(file_rows)

scenario_rows = [
    [name, scenario_counts[name]]
    for name in sorted(scenario_counts)
]

quant_rows = []

for r in quant:
    quant_rows.append([
        r["BitWidth"],
        fmt(numeric(r["PositionRMSEM"]) * 1000, 3),
        r["ChangedGroundLabels"],
        fmt(numeric(
            r["ClassificationAgreementPercent"]
        ), 3),
        fmt(numeric(
            r["StorageReductionVsDoublePercent"]
        ), 1),
    ])

failure_rows = [
    [
        r["Scenario"],
        r["FrameIndex"],
        r["ObservabilityState"],
        r["ExecutedMode"],
        fmt(numeric(r["AgreementPercent"]), 2),
        fmt(numeric(r["FalseGroundCount"]), 0),
    ]
    for r in failures
]

markdown = f"""# GEMSTAR Task 19 — Consolidated Research Findings

Generated: {datetime.now(timezone.utc).isoformat()}

## 1. Scope

This research evaluates GEMSTAR LiDAR reconstruction,
geometric preprocessing, ground segmentation, voxel
reduction, sensor observability, software scheduling,
timing robustness, quantization and prospective ARM-FPGA
hardware/software partitioning.

The experiments are software investigations. No real
FPGA implementation, board power measurement or
hardware acceleration result is claimed.

## 2. Recordings

{md_table(["Recording", "Selected frames"], scenario_rows)}

Total cross-recording frames: **{len(inventory)}**.

Frames with completed numerical quality evaluation:
**{len(evaluated)}**.

One low-data frame was excluded from segmentation
quality evaluation.

## 3. Observability monitor

{md_table(
    ["Provisional state", "Frames"],
    [[name, state_counts[name]] for name in
     ["OBSERVABLE", "REVIEW", "INSUFFICIENT"]]
)}

These diagnostic states are not validated sensor
health or failure labels.

## 4. Executed processing policy

{md_table(
    ["Mode", "Frames"],
    [[name, mode_counts[name]] for name in
     ["FULL", "VOXEL", "SKIP"]]
)}

Overall processed-frame median baseline/policy
speed ratio: **{fmt(speed_ratio)}x**.

Median complete-monitor time:
**{fmt(monitor_ms, 5)} ms**.

These are PC MATLAB measurements and exclude OSI
decoding, file I/O, hardware transfer and downstream
sensor fusion.

## 5. Processing-quality audit

Evaluated frames: **{len(evaluated)}**.

Selected-policy diagnostic failures:
**{len(failures)}**.

{md_table(
    ["Recording", "Frame", "Observability", "Mode",
     "Reference agreement (%)", "False-ground count"],
    failure_rows
)}

Agreement is against full-resolution RANSAC, not
independent road/obstacle ground truth.

## 6. Timing and illustrative deadline

Experimental processing deadline: **3 ms**.

Timing samples: **{len(timing)}**.

Full-reference overall P95:
**{fmt(baseline_p95, 5)} ms**.

Adaptive-policy overall P95:
**{fmt(policy_p95, 5)} ms**.

Full-reference sampled deadline misses:
**{baseline_misses}**.

Adaptive-policy sampled deadline misses:
**{policy_misses}**.

These are observed violations of an illustrative
budget, not automotive real-time safety guarantees.

## 7. Quantization

Frame 150; 1,922 ROI points; fixed reference plane.

{md_table(
    ["Bits", "XYZ RMSE (mm)", "Changed labels",
     "Reference agreement (%)", "Raw storage saving (%)"],
    quant_rows
)}

Scales were calibrated on the evaluated frame.
Plane arithmetic was floating-point; these results
do not validate integer-only RANSAC or FPGA behavior.

## 8. Proposed ARM-FPGA architecture

Initial CPU responsibilities:
buffer management, observability monitoring,
scheduling, RANSAC hypotheses and SVD refinement.

Initial candidate FPGA kernel:
fixed-point point-to-plane distance evaluation,
threshold comparison and inlier counting.

The architecture and interface are specifications,
not implemented hardware.

## 9. Limitations

- No independent semantic ground-truth validation.
- No actual ARM-FPGA latency comparison.
- No hardware power or energy measurements.
- No completed RTL functional verification.
- No OSI decoding or transfer time in benchmark.
- Limited repeated timing samples on Windows MATLAB.
- Different simulation recordings may have different
  scenes, configurations or weather conditions.
- Quantization evaluated on one frame.
- Monitoring thresholds are experimental.
- Some scheduler failures occurred in observations
  classified as OBSERVABLE.

## 10. Required next hardware research

1. Verify fixed-point precision across recordings.
2. Implement and verify the first RTL kernel.
3. Establish CPU and FPGA functional equivalence.
4. Integrate data transfer and processing control.
5. Measure end-to-end latency and deadline misses.
6. Measure actual board power and energy per frame.
7. Compare accuracy, resource cost and energy fairly.

## 11. Reproducibility

Artifact files inventoried: **{len(file_rows)}**.

See `06_Research_Findings/task19_15_artifact_manifest.csv`
for relative paths, file sizes and SHA-256 hashes.

The final illustrated PDF is produced in Task 19.16.
"""

report_path = FINDINGS / "task19_15_consolidated_findings.md"
report_path.write_text(markdown, encoding="utf-8")

metrics = {
    "recordings": scenario_counts,
    "frames": len(inventory),
    "evaluated_frames": len(evaluated),
    "observability_states": state_counts,
    "processing_modes": mode_counts,
    "selected_policy_failures": len(failures),
    "median_processed_speed_ratio": speed_ratio,
    "median_monitor_ms": monitor_ms,
    "deadline_ms": deadline_ms,
    "baseline_p95_ms": baseline_p95,
    "policy_p95_ms": policy_p95,
    "baseline_deadline_misses": baseline_misses,
    "policy_deadline_misses": policy_misses,
    "artifact_count": len(file_rows),
}

metrics_path = FINDINGS / "task19_15_verified_metrics.json"

metrics_path.write_text(
    json.dumps(metrics, indent=2, default=dict),
    encoding="utf-8"
)

print("\n=== VERIFIED RESEARCH METRICS ===")
print("Frames:", len(inventory))
print("Evaluated:", len(evaluated))
print("Quality failures:", len(failures))
print("Monitor states:", dict(state_counts))
print("Processing modes:", dict(mode_counts))
print("Median speed ratio:", fmt(speed_ratio), "x")
print("Median monitor latency:", fmt(monitor_ms, 5), "ms")
print("Baseline P95:", fmt(baseline_p95, 5), "ms")
print("Policy P95:", fmt(policy_p95, 5), "ms")
print("Deadline misses:", baseline_misses, "vs", policy_misses)

print("\n=== TASK 19.15 COMPLETE ===")
print("Manifest saved:", inventory_out.is_file())
print("Research findings saved:", report_path.is_file())
print("Verified metrics saved:", metrics_path.is_file())
print("Files inventoried:", len(file_rows))
