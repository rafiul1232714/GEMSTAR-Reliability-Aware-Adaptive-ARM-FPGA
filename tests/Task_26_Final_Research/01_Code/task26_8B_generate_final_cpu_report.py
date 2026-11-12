from pathlib import Path
import csv
import json
import math
from datetime import datetime, timezone

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_26_Final_Research"
)

DATA = ROOT / "02_CSV_Data"
FINDINGS = ROOT / "06_Research_Findings"

OUTPUT = FINDINGS / "task26_8B_final_cpu_research_report.md"

def load_csv(name):
    path = DATA / name
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def value(row, key):
    result = float(row[key])
    if not math.isfinite(result):
        raise ValueError(f"Nonfinite value: {key}")
    return result

def main():
    if OUTPUT.exists():
        raise FileExistsError(
            f"Existing final report preserved: {OUTPUT}"
        )

    workloads = load_csv(
        "task26_7B_repeatability_by_workload.csv"
    )
    groups = load_csv(
        "task26_7B_repeatability_by_group.csv"
    )
    quality = load_csv(
        "task26_6C_ekf_position_error_summary.csv"
    )
    manifest = load_csv(
        "task26_8A_research_file_manifest.csv"
    )

    if len(workloads) != 6:
        raise RuntimeError("Unexpected workload coverage")
    if len(groups) != 184:
        raise RuntimeError("Unexpected measurement-group count")
    if len(quality) != 3:
        raise RuntimeError("Unexpected quality-method count")
    if len(manifest) != 114:
        raise RuntimeError("Unexpected archive manifest count")

    timing_rows = sum(
        int(r["timing_rows"]) for r in workloads
    )
    if timing_rows != 6025:
        raise RuntimeError("Timing-row coverage mismatch")

    by_workload = {r["workload"]: r for r in workloads}
    by_quality = {r["method"]: r for r in quality}

    expected = {
        "EKF", "Camera", "LiDAR", "Radar",
        "YOLO11s", "Partial_LiDAR_Radar"
    }
    if set(by_workload) != expected:
        raise RuntimeError("Unexpected workload names")

    known_quality = {
        "lidar_only",
        "radar_assisted",
        "camera_experimental"
    }
    if set(by_quality) != known_quality:
        raise RuntimeError("Unexpected quality methods")

    radar_center_rmse = value(
        by_quality["radar_assisted"],
        "position_rmse_m_diagnostic"
    )
    lidar_center_rmse = value(
        by_quality["lidar_only"],
        "position_rmse_m_diagnostic"
    )
    camera_center_rmse = value(
        by_quality["camera_experimental"],
        "position_rmse_m_diagnostic"
    )

    reduction_percent = 100 * (
        lidar_center_rmse - radar_center_rmse
    ) / lidar_center_rmse

    lines = []

    def add(*items):
        lines.extend(items)

    add(
        "# Task 26 — Final CPU Benchmark and Quality Evidence Report",
        "",
        "**Project:** GEMSTAR reliability-aware, "
        "energy-adaptive Camera/LiDAR/Radar processing "
        "for future ARM–FPGA implementation",
        "",
        "**Report status:** CPU baseline and diagnostic "
        "quality evidence; not final system validation.",
        "",
        "## 1. Executive summary",
        "",
        f"- Original recorded CPU timing observations: "
        f"**{timing_rows:,}**.",
        f"- Comparable timing groups: **{len(groups)}**.",
        f"- Hashed research files in Task 26.8A manifest: "
        f"**{len(manifest)}**.",
        "- Original benchmark datasets were not rerun "
        "or modified during report generation.",
        "- No ARM–FPGA hardware energy savings have "
        "been measured.",
        "- Full-pipeline accuracy and p99 latency "
        "constraints remain unverified.",
        "",
        "## 2. Objective and scope",
        "",
        "The long-term objective is to minimize measured "
        "total system energy per valid perception result "
        "while satisfying independently evaluated "
        "perception quality and a predeclared p99 "
        "latency constraint.",
        "",
        "Task 26 establishes CPU-based reference timings "
        "for selected software components and a partial "
        "processing pipeline. It does not measure a "
        "complete end-to-end real-time perception system.",
        "",
        "## 3. CPU measurement methodology",
        "",
        "Timing results originate from repeated execution "
        "of stored test inputs on the development CPU. "
        "Workload groups use different timing units, "
        "sample counts and input sizes.",
        "",
        "The development machine is reported as using "
        "an AMD Ryzen AI 7 450 CPU with 8 cores and "
        "16 threads. These timings should not be "
        "transferred directly to a future ARM processor.",
        "",
        "Statistics include sample mean, median, sample "
        "standard deviation, coefficient of variation, "
        "interpolated p95/p99 and Tukey 1.5-IQR "
        "outlier counts.",
        "",
        "## 4. CPU runtime repeatability",
        "",
        "| Workload | Groups | Timings | Median of group "
        "medians (ms) | Max group p99 (ms) | "
        "Median within-group CV | Outlier rate |",
        "|---|---:|---:|---:|---:|---:|---:|"
    )

    order = [
        "EKF", "Camera", "LiDAR", "Radar",
        "YOLO11s", "Partial_LiDAR_Radar"
    ]

    for name in order:
        r = by_workload[name]
        add(
            f"| {name} "
            f"| {int(r['groups'])} "
            f"| {int(r['timing_rows'])} "
            f"| {value(r,'median_of_group_medians_ms'):.6f} "
            f"| {value(r,'max_group_p99_ms'):.6f} "
            f"| {value(r,'median_group_cv_percent'):.3f}% "
            f"| {value(r,'outlier_rate_percent'):.3f}% |"
        )

    add(
        "",
        "**Interpretation:** These medians and p99 values "
        "describe different workload sizes. They must "
        "not be summed or interpreted as a shared "
        "end-to-end frame deadline.",
        "",
        "### Important timing findings",
        "",
        "- YOLO11s CPU inference is the largest "
        "measured standalone workload in this study.",
        "- Radar batches have high relative timing "
        "variation and an observed 0.617 ms outlier.",
        "- The Radar pooled median of 0.0108 ms "
        "differs from the median of its group medians "
        "(0.008825 ms), because the aggregation "
        "methods are different.",
        "- The partial pipeline contains LiDAR filtering, "
        "LiDAR clustering and Radar validation only.",
        "- All observed outliers were retained.",
        "",
        "## 5. Ground-truth position diagnostics",
        "",
        "Matching C02 moving-target GT/EKF frames: **23**. "
        "The evaluation target is OSI object ID **76897**.",
        "",
        "| EKF configuration | Diagnostic object-center "
        "position RMSE (m) |",
        "|---|---:|"
    )

    for name in [
        "lidar_only",
        "radar_assisted",
        "camera_experimental"
    ]:
        add(
            f"| {name} "
            f"| {value(by_quality[name], 'position_rmse_m_diagnostic'):.6f} |"
        )

    add(
        "",
        f"Radar assistance reduced the diagnostic "
        f"GT-center RMSE by **{reduction_percent:.4f}%** "
        f"over this small matched evaluation set.",
        "",
        "This does not demonstrate a general "
        "sensor-fusion accuracy improvement.",
        "",
        "The experimental Camera update at frame 530 "
        "was not authorized for validated operation.",
        "",
        "## 6. Surface-versus-center geometry",
        "",
        "- Radar mean GT-center distance: **1.628205 m**.",
        "- Radar mean approximate GT-rear-face "
        "distance: **0.639567 m**.",
        "- Reported OSI target length: "
        "**1.173327–2.168729 m**.",
        "- Original surface diagnostic reads "
        "`GroundTruth.moving_object.base.dimension`.",
        "- The reported dimensions vary with target "
        "orientation in the observed sequence.",
        "- The rear-face point is a constructed "
        "approximation, not a verified LiDAR-hit position.",
        "",
        "A difference in distance to two reference "
        "points must not be reported as a reduction "
        "in algorithmic localization error.",
        "",
        "## 7. Perception-quality limitations",
        "",
        "1. GT world-to-ego transformation is "
        "mathematically consistent but was explicitly "
        "labelled preliminary in the original diagnostic.",
        "2. Target association uses the known GT ID "
        "for evaluation only.",
        "3. Ground-truth velocity integrity flagged "
        "six samples with zero reported actor velocity "
        "during inferred motion.",
        "4. Camera acceptance at frame 530 is "
        "experimental and unauthorized.",
        "5. YOLO inference timing does not establish "
        "detection accuracy or reliable perception quality.",
        "6. No full-pipeline validated detection, tracking, "
        "precision/recall or three-sensor quality "
        "guarantee has been established.",
        "",
        "## 8. Repeatability limitations",
        "",
        "- Workloads process different input sizes "
        "and have different timing units.",
        "- Repeated measurements of the same stored "
        "input are not independent driving scenarios.",
        "- Per-group p99 is descriptive, not a certified "
        "worst-case execution time.",
        "- Ten-sample YOLO groups and 25-sample "
        "LiDAR/integrated groups give limited "
        "tail-latency evidence.",
        "- No confidence interval establishes "
        "a hard real-time guarantee.",
        "- CPU timings were measured on the "
        "development host, not an ARM–FPGA board.",
        "",
        "## 9. Requirements for Tasks 27–36",
        "",
        "Before claiming an optimization:",
        "",
        "1. Use matched inputs and unchanged "
        "ground-truth evaluation references.",
        "2. Define the exact processing scope and "
        "timing boundaries for each candidate.",
        "3. Validate object identity, association, "
        "detection quality and tracking quality.",
        "4. Select quality thresholds before "
        "optimizing, based on defensible "
        "requirements and validation data.",
        "5. Specify latency deadlines and an "
        "appropriate p99 evaluation protocol.",
        "6. Benchmark software and FPGA candidates "
        "under matched workloads and accounting rules.",
        "7. Measure total ARM–FPGA board/system "
        "power during actual operation, including "
        "data movement and idle overhead.",
        "8. Calculate measured joules per valid "
        "perception result, with confidence bounds.",
        "9. Reject candidates violating quality "
        "or deadline constraints.",
        "",
        "## 10. Task 26 completion interpretation",
        "",
        "**Completed:** CPU component profiling, "
        "partial LiDAR–Radar sequential timing, "
        "diagnostic GT comparison, statistical "
        "repeatability and research archive checks.",
        "",
        "**Not established:** validated full "
        "three-sensor accuracy, hard real-time "
        "feasibility, complete end-to-end latency, "
        "ARM–FPGA energy savings.",
        "",
        "## 11. Provenance",
        "",
        "Primary timing sources: "
        "`task26_3B_ekf_cpu_timing.csv`, "
        "`task26_4B_camera_cpu_timing.csv`, "
        "`task26_4D_lidar_cpu_timing.csv`, "
        "`task26_4G_radar_cpu_timing.csv`, "
        "`task26_4J_yolo_cpu_timing.csv`, "
        "`task26_5C_integrated_cpu_timing.csv`.",
        "",
        "Quality source: "
        "`task26_6C_ekf_position_error_summary.csv`.",
        "",
        "Repeatability sources: "
        "`task26_7B_repeatability_by_group.csv` "
        "and `task26_7B_repeatability_by_workload.csv`.",
        "",
        "Archive record: "
        "`task26_8A_research_file_manifest.csv`.",
        "",
        "The Task 26.8A manifest predates this "
        "report and this generator script. They "
        "must be accounted for in Task 26.8C.",
        "",
        "---",
        "",
        "*Research report generated from archived "
        "diagnostic and benchmark data. No claims "
        "of measured energy efficiency are made.*"
    )

    FINDINGS.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("=== TASK 26.8B FINAL CPU RESEARCH REPORT ===")
    print("TIMING_OBSERVATIONS:", timing_rows)
    print("MEASUREMENT_GROUPS:", len(groups))
    print("QUALITY_METHODS:", len(quality))
    print("PREVIOUS_MANIFEST_ENTRIES:", len(manifest))
    print(
        "RADAR_RMSE_REDUCTION_PERCENT:",
        f"{reduction_percent:.4f}"
    )
    print("REPORT_CREATED:", OUTPUT.is_file())
    print("FULL_PIPELINE_ACCURACY_VALIDATED: NO")
    print("END_TO_END_LATENCY_MEASURED: NO")
    print("ARM_FPGA_ENERGY_MEASURED: NO")
    print("HISTORICAL_FILES_MODIFIED: NO")
    print("TASK26_8B_FINAL_REPORT_PASS")
    print("REPORT:", OUTPUT)

if __name__ == "__main__":
    main()
