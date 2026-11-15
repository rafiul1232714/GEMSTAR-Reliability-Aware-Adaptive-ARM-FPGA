from pathlib import Path
import csv
import json
import hashlib
import statistics
import math

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
TASK = ROOT / "Task_27_Final_Research"
CSV = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

SUMMARY = CSV / "task27_5A_kernel_summary.csv"
STRUCTURE = CSV / "task27_5A_kernel_structure.csv"
LIDAR = CSV / "task27_3C_lidar_memory_model.csv"
SENSORS = CSV / "task27_4C_sensor_compute_characterization.csv"

OUT = CSV / "task27_6A_fpga_candidate_matrix.csv"
REPORT = FINDINGS / "task27_6A_fpga_candidate_findings.txt"
MANIFEST = FINDINGS / "task27_6A_fpga_candidate_manifest.json"

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def main():
    print("=== TASK 27.6A: FPGA CANDIDATE COMPARISON ===")

    inputs = [SUMMARY, STRUCTURE, LIDAR, SENSORS]

    for p in inputs:
        if not p.is_file():
            raise FileNotFoundError(p)

    for p in (OUT, REPORT, MANIFEST):
        if p.exists():
            raise FileExistsError(
                f"Existing research output preserved: {p}"
            )

    summary = read_csv(SUMMARY)
    structure = read_csv(STRUCTURE)
    lidar = read_csv(LIDAR)
    sensors = read_csv(SENSORS)

    if (len(summary), len(structure), len(lidar), len(sensors)) != \
       (5, 129, 53, 23):
        raise RuntimeError("Unexpected input dataset dimensions")

    stages = {r["stage"]: r for r in summary}

    if len(stages) != 5:
        raise RuntimeError("Duplicate or missing stage")

    expected = {
        "LiDAR_filter": 0.747300,
        "LiDAR_cluster": 0.045400,
        "Camera_preprocessing": 1.815050,
        "Radar_valid_returns": 0.008825,
        "YOLO11s_predict": 43.746050,
    }

    for name, reference in expected.items():
        if name not in stages:
            raise RuntimeError(f"Stage missing: {name}")

        actual = float(
            stages[name]["median_of_record_medians_ms"]
        )

        if not math.isclose(actual, reference, abs_tol=1e-6):
            raise RuntimeError(
                f"Unexpected CPU median: {name}={actual}"
            )

    if sum(int(r["input_points"]) for r in lidar) != 172839:
        raise RuntimeError("LiDAR input count mismatch")

    if sum(int(r["filtered_points"]) for r in lidar) != 16295:
        raise RuntimeError("LiDAR filtered count mismatch")

    input_bytes = sum(
        int(r["nominal_input_xyz_bytes"]) for r in lidar
    )

    filtered_bytes = sum(
        int(r["nominal_output_xyz_bytes"]) for r in lidar
    )

    if (input_bytes, filtered_bytes) != (2074068, 195540):
        raise RuntimeError("LiDAR payload model mismatch")

    camera = [r for r in sensors if r["workload"] == "Camera"]
    radar = [r for r in sensors if r["workload"] == "Radar"]
    yolo = [r for r in sensors if r["workload"] == "YOLO11s"]

    if (len(camera), len(radar), len(yolo)) != (6, 12, 5):
        raise RuntimeError("Sensor workload count mismatch")

    camera_full = [
        r for r in camera if r["mode"] == "FULL"
    ]
    camera_roi = [
        r for r in camera if r["mode"] == "ROI"
    ]

    if len(camera_full) != 3 or len(camera_roi) != 3:
        raise RuntimeError("Camera FULL/ROI groups missing")

    if {r["scenario"] for r in camera_full} != \
       {"CLEAR", "FOG100", "FOG20"}:
        raise RuntimeError("Camera scenarios changed")

    # Explicit evidence-based qualitative assessment.
    # Not an empirical ranking or energy optimization.
    #
    # The shortlist is provisional, requiring later
    # accuracy, latency, hardware feasibility and energy
    # validation before final commitment.

    assessments = {
        "LiDAR_filter": {
            "regularity": "HIGH",
            "parallel_structure": "Independent point comparisons",
            "main_hardware_challenge": "DMA and transfer overhead",
            "decision": "PROVISIONAL_SHORTLIST",
            "reason": (
                "Streaming-friendly filter with recorded "
                "input reduction; transfer break-even "
                "and perception quality remain unproven."
            ),
        },
        "Camera_preprocessing": {
            "regularity": "HIGH",
            "parallel_structure": "Pixel and neighborhood processing",
            "main_hardware_challenge": (
                "Intermediate buffering and neighborhood windows"
            ),
            "decision": "PROVISIONAL_SHORTLIST",
            "reason": (
                "Regular image operations and measurable "
                "CPU cost; preserve full-frame quality and "
                "verify FPGA transfer benefits."
            ),
        },
        "YOLO11s_predict": {
            "regularity": "MIXED",
            "parallel_structure": "Neural-network tensor operations",
            "main_hardware_challenge": (
                "Layer mapping, weights, activations and memory"
            ),
            "decision": "DEFER_LAYER_PROFILING",
            "reason": (
                "Largest archived CPU time, but full-model "
                "resource feasibility, model quality and "
                "layer-level performance are unverified."
            ),
        },
        "LiDAR_cluster": {
            "regularity": "IRREGULAR",
            "parallel_structure": (
                "Grid indexing and connected-cell traversal"
            ),
            "main_hardware_challenge": (
                "Variable-size cells and neighborhood traversal"
            ),
            "decision": "DEFER_INITIAL_ACCELERATION",
            "reason": (
                "Small standalone CPU time on the recorded "
                "dataset and more complex memory organization."
            ),
        },
        "Radar_valid_returns": {
            "regularity": "HIGH",
            "parallel_structure": "Independent return validation",
            "main_hardware_challenge": (
                "Offload overhead relative to small batches"
            ),
            "decision": "DEFER_INITIAL_ACCELERATION",
            "reason": (
                "Very small archived batch latency; "
                "dedicated offload may not justify its overhead."
            ),
        },
    }

    rows = []

    order = [
        "LiDAR_filter",
        "Camera_preprocessing",
        "YOLO11s_predict",
        "LiDAR_cluster",
        "Radar_valid_returns",
    ]

    for name in order:
        details = assessments[name]
        s = stages[name]

        rows.append({
            "kernel": name,
            "archived_cpu_median_ms": float(
                s["median_of_record_medians_ms"]
            ),
            "timing_groups": int(s["records"]),
            "processing_regularity": details["regularity"],
            "parallel_structure": details["parallel_structure"],
            "main_hardware_challenge": (
                details["main_hardware_challenge"]
            ),
            "decision": details["decision"],
            "decision_reason": details["reason"],
            "perception_quality_validated": "NO",
            "fpga_latency_measured": "NO",
            "fpga_energy_measured": "NO",
            "final_hardware_selection": "NO",
        })

    shortlisted = [
        r["kernel"] for r in rows
        if r["decision"] == "PROVISIONAL_SHORTLIST"
    ]

    if len(shortlisted) != 2:
        raise RuntimeError("Expected exactly two provisional kernels")

    # Complete validation before writing anything.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    model = {
        "task": "27.6A",
        "analysis_type": "Qualitative evidence-gated shortlist",
        "kernel_count": len(rows),
        "provisional_shortlist": shortlisted,
        "source_files": [
            {
                "path": str(p),
                "sha256": digest(p)
            }
            for p in inputs
        ],
        "lidar_total_input_xyz_bytes": input_bytes,
        "lidar_total_filtered_xyz_bytes": filtered_bytes,
        "camera_full_bgr_bytes_per_frame": 921600,
        "camera_roi_bgr_bytes_per_frame": 331776,
        "candidate_ranking_measured": False,
        "fpga_power_measured": False,
        "energy_saving_claimed": False,
        "final_selection_made": False
    }

    with MANIFEST.open("x", encoding="utf-8") as f:
        json.dump(model, f, indent=2)

    findings = [
        "GEMSTAR TASK 27.6A",
        "FPGA Candidate Comparison",
        "===================================",
        f"Candidate kernel types: {len(rows)}",
        f"Provisional shortlist count: {len(shortlisted)}",
        "",
        "PROVISIONAL SHORTLIST:",
    ]

    for name in shortlisted:
        findings.append(f"- {name}")

    findings.extend([
        "",
        "CANDIDATE EVIDENCE:"
    ])

    for row in rows:
        findings.append(
            f"{row['kernel']}: "
            f"{row['archived_cpu_median_ms']:.6f} ms; "
            f"{row['decision']}"
        )
        findings.append(f"  Reason: {row['decision_reason']}")

    findings.extend([
        "",
        "NEXT VALIDATION GATES:",
        "1. Matched-input quality preservation.",
        "2. Hardware-compatible numerical fidelity.",
        "3. Actual transfer and execution latency.",
        "4. Processing deadline and p99 performance.",
        "5. Total system joules per valid result.",
        "",
        "LIMITATIONS:",
        "This is a provisional engineering shortlist.",
        "Different CPU timing scopes are not directly comparable.",
        "No measured FPGA speedup or energy reduction.",
        "No final hardware mapping has been approved.",
        "YOLO remains a candidate for later layer-level profiling.",
    ])

    with REPORT.open("x", encoding="utf-8") as f:
        f.write("\n".join(findings) + "\n")

    print("CANDIDATE_KERNELS:", len(rows))
    print("PROVISIONAL_SHORTLIST_COUNT:", len(shortlisted))

    for row in rows:
        print(
            f"KERNEL={row['kernel']} "
            f"CPU_MEDIAN_MS={row['archived_cpu_median_ms']:.6f} "
            f"DECISION={row['decision']}"
        )

    print("FPGA_ENERGY_MEASURED: NO")
    print("FINAL_HARDWARE_SELECTION: NO")
    print("OUTPUT_MATRIX:", OUT)
    print("OUTPUT_FINDINGS:", REPORT)
    print("OUTPUT_MANIFEST:", MANIFEST)
    print("TASK27_6A_FPGA_CANDIDATE_COMPARISON_DONE")

if __name__ == "__main__":
    main()