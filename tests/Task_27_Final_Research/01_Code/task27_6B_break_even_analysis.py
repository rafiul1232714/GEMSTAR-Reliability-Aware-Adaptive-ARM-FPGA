from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
T27 = ROOT / "Task_27_Final_Research"
DATA = T27 / "02_CSV_Data"
FIND = T27 / "06_Research_Findings"

LIDAR = DATA / "task27_3C_lidar_memory_model.csv"
SENSORS = DATA / "task27_4C_sensor_compute_characterization.csv"
CANDIDATES = DATA / "task27_6A_fpga_candidate_matrix.csv"

OUT = DATA / "task27_6B_break_even_scenarios.csv"
SUMMARY = DATA / "task27_6B_break_even_summary.csv"
REPORT = FIND / "task27_6B_break_even_findings.txt"
MANIFEST = FIND / "task27_6B_break_even_manifest.json"

# Hypothetical, NOT measured ARM-FPGA values.
BANDWIDTH_MBPS = [100, 500, 1000]
COMPUTE_MS = [0.05, 0.25]
FIXED_OVERHEAD_MS = 0.05

def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def save_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    print("=== TASK 27.6B: FPGA BREAK-EVEN ANALYSIS ===")

    sources = [LIDAR, SENSORS, CANDIDATES]

    for path in sources:
        if not path.is_file():
            raise FileNotFoundError(path)

    for path in (OUT, SUMMARY, REPORT, MANIFEST):
        if path.exists():
            raise FileExistsError(
                f"Existing output preserved: {path}"
            )

    lidar = read_rows(LIDAR)
    sensors = read_rows(SENSORS)
    candidate_rows = read_rows(CANDIDATES)

    if len(lidar) != 53 or len(sensors) != 23:
        raise RuntimeError("Unexpected archived research rows")

    selected = {
        r["kernel"] for r in candidate_rows
        if r["decision"] == "PROVISIONAL_SHORTLIST"
    }

    if selected != {"LiDAR_filter", "Camera_preprocessing"}:
        raise RuntimeError("Candidate shortlist mismatch")

    inputs = []

    # LiDAR interface: send raw XYZ, receive filtered XYZ.
    for r in lidar:
        frame = int(r["frame"])
        cpu = float(r["archived_cpu_filter_median_ms"])
        incoming = int(r["nominal_input_xyz_bytes"])
        outgoing = int(r["nominal_output_xyz_bytes"])
        recorded_total = int(r["model_roundtrip_payload_bytes"])

        if incoming + outgoing != recorded_total:
            raise RuntimeError(f"LiDAR payload mismatch: {frame}")

        inputs.append({
            "kernel": "LiDAR_filter",
            "case_id": f"frame_{frame}",
            "cpu_median_ms": cpu,
            "input_bytes": incoming,
            "output_bytes": outgoing,
            "interface_note": "Raw XYZ in; filtered XYZ out"
        })

    # Camera interface assumption:
    # Input uint8 BGR = 3 bytes/pixel.
    # Output grayscale + Canny edges = 2 bytes/pixel.
    # Small quality-feature metadata is excluded.
    # The FULL/ROI input is the processing region only.
    # Real FPGA boundary and transfer method are undecided.
    camera = [
        r for r in sensors if r["workload"] == "Camera"
    ]

    if len(camera) != 6:
        raise RuntimeError("Expected six Camera cases")

    seen_camera = set()

    for r in camera:
        case = (r["scenario"], r["mode"])
        if case in seen_camera:
            raise RuntimeError("Duplicate Camera case")
        seen_camera.add(case)

        pixels = int(r["processing_items"])
        incoming = int(r["nominal_processing_input_bytes"])

        if incoming != pixels * 3:
            raise RuntimeError("Camera input size mismatch")

        inputs.append({
            "kernel": "Camera_preprocessing",
            "case_id": f"{r['scenario']}_{r['mode']}",
            "cpu_median_ms": float(r["archived_cpu_median_ms"]),
            "input_bytes": incoming,
            "output_bytes": pixels * 2,
            "interface_note": (
                "BGR in; grayscale and edges out; "
                "small feature metadata omitted"
            )
        })

    assert len(inputs) == 59

    rows = []
    groups = defaultdict(list)

    for item in inputs:
        cpu = item["cpu_median_ms"]
        payload = item["input_bytes"] + item["output_bytes"]

        if cpu <= 0 or payload <= 0:
            raise RuntimeError("Invalid input model")

        for bw in BANDWIDTH_MBPS:
            transfer_ms = payload / (bw * 1e6) * 1000

            for compute_ms in COMPUTE_MS:
                offload_ms = (
                    transfer_ms + compute_ms + FIXED_OVERHEAD_MS
                )

                # Latency improvement is only modeled.
                latency_faster = offload_ms < cpu

                # Under a simplified matched-work energy
                # comparison, E = average power * elapsed time.
                #
                # To use LESS energy:
                # P_offload / P_CPU < T_CPU / T_offload
                #
                # Average powers have NOT been measured.
                max_power_ratio = cpu / offload_ms

                result = {
                    "kernel": item["kernel"],
                    "case_id": item["case_id"],
                    "archived_cpu_median_ms": cpu,
                    "input_bytes": item["input_bytes"],
                    "output_bytes": item["output_bytes"],
                    "roundtrip_bytes": payload,
                    "hypothetical_bandwidth_MBps": bw,
                    "hypothetical_compute_ms": compute_ms,
                    "hypothetical_fixed_overhead_ms":
                        FIXED_OVERHEAD_MS,
                    "hypothetical_transfer_ms": transfer_ms,
                    "hypothetical_total_offload_ms":
                        offload_ms,
                    "modeled_latency_faster":
                        "YES" if latency_faster else "NO",
                    "modeled_latency_ratio_cpu_over_offload":
                        cpu / offload_ms,
                    "energy_break_even_max_average_power_ratio":
                        max_power_ratio,
                    "power_measured": "NO",
                    "fpga_latency_measured": "NO",
                    "energy_saving_demonstrated": "NO",
                    "interface_assumption": item["interface_note"]
                }

                rows.append(result)
                groups[(item["kernel"], bw, compute_ms)].append(
                    result
                )

    if len(rows) != 354 or len(groups) != 12:
        raise RuntimeError("Break-even model dimension mismatch")

    summary_rows = []

    for (kernel, bw, comp), sample in sorted(groups.items()):
        ratios = [
            r["energy_break_even_max_average_power_ratio"]
            for r in sample
        ]

        summary_rows.append({
            "kernel": kernel,
            "hypothetical_bandwidth_MBps": bw,
            "hypothetical_compute_ms": comp,
            "hypothetical_fixed_overhead_ms":
                FIXED_OVERHEAD_MS,
            "cases": len(sample),
            "modeled_latency_faster_cases": sum(
                r["modeled_latency_faster"] == "YES"
                for r in sample
            ),
            "median_modeled_offload_ms": statistics.median(
                r["hypothetical_total_offload_ms"]
                for r in sample
            ),
            "median_max_average_power_ratio_for_energy_saving":
                statistics.median(ratios),
            "measured_energy": "NO"
        })

    # All calculations and validations are complete.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    FIND.mkdir(parents=True, exist_ok=True)

    save_csv(OUT, rows)
    save_csv(SUMMARY, summary_rows)

    metadata = {
        "task": "27.6B",
        "analysis": "Hypothetical latency and energy break-even",
        "source_files": [
            {"path": str(p), "sha256": sha256(p)}
            for p in sources
        ],
        "input_cases": 59,
        "model_scenarios": len(rows),
        "bandwidth_MBps": BANDWIDTH_MBPS,
        "compute_ms": COMPUTE_MS,
        "fixed_overhead_ms": FIXED_OVERHEAD_MS,
        "camera_output_assumption": (
            "Two uint8 output arrays: grayscale and edges. "
            "Feature metadata and other transfers excluded."
        ),
        "energy_equation": (
            "E_offload < E_cpu iff "
            "P_offload_avg/P_cpu_avg < T_cpu/T_offload "
            "for equivalent accounting windows."
        ),
        "real_dma_measured": False,
        "real_fpga_compute_measured": False,
        "real_power_measured": False,
        "real_energy_measured": False,
        "perception_quality_validated": False
    }

    with MANIFEST.open("x", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    report = [
        "GEMSTAR TASK 27.6B - BREAK-EVEN REQUIREMENTS",
        "============================================",
        f"Candidate kernels: {len(selected)}",
        f"Recorded workload cases: {len(inputs)}",
        f"Hypothetical model scenarios: {len(rows)}",
        "",
        "MODEL:",
        "Offload time = transfer + compute + fixed overhead",
        "Latency faster when offload time < archived CPU time.",
        "",
        "ENERGY CONDITION:",
        "E = average power x execution time.",
        "For matched accounting boundaries:",
        "P_offload_avg / P_cpu_avg < T_cpu / T_offload",
        "Power ratios are limits, not measurements.",
        "",
        "PARAMETER SWEEP:",
        f"Bandwidth MB/s: {BANDWIDTH_MBPS}",
        f"Compute time ms: {COMPUTE_MS}",
        f"Fixed overhead ms: {FIXED_OVERHEAD_MS}",
        "",
        "GROUP RESULTS:"
    ]

    for r in summary_rows:
        report.append(
            f"{r['kernel']}, {r['hypothetical_bandwidth_MBps']} MB/s,"
            f" compute={r['hypothetical_compute_ms']} ms:"
            f" {r['modeled_latency_faster_cases']}/{r['cases']}"
            f" modeled faster; median allowable average power ratio"
            f" {r['median_max_average_power_ratio_for_energy_saving']:.4f}"
        )

    report.extend([
        "",
        "LIMITATIONS:",
        "Bandwidth, FPGA compute and overhead are hypothetical.",
        "No actual DMA throughput or FPGA execution measured.",
        "Camera interface is hypothetical and excludes metadata.",
        "ROI excludes pixels; quality equivalence not established.",
        "Timing uses separate development-workstation CPU runs.",
        "The simple energy model excludes other system activity.",
        "Power must be measured with matched accounting boundaries.",
        "No p99 real-time guarantee or quality validation.",
        "No measured FPGA speedup or energy saving."
    ])

    with REPORT.open("x", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")

    print("CANDIDATE_KERNELS:", len(selected))
    print("RECORDED_WORKLOAD_CASES:", len(inputs))
    print("MODEL_SCENARIOS:", len(rows))
    print("SUMMARY_GROUPS:", len(summary_rows))
    print("HYPOTHETICAL_BANDWIDTHS_MBPS:", BANDWIDTH_MBPS)
    print("HYPOTHETICAL_FPGA_COMPUTE_MS:", COMPUTE_MS)
    print("HYPOTHETICAL_FIXED_OVERHEAD_MS:", FIXED_OVERHEAD_MS)
    print("REAL_POWER_MEASURED: NO")
    print("ENERGY_SAVINGS_DEMONSTRATED: NO")
    print("OUTPUT_CSV:", OUT)
    print("OUTPUT_SUMMARY:", SUMMARY)
    print("OUTPUT_REPORT:", REPORT)
    print("OUTPUT_MANIFEST:", MANIFEST)
    print("TASK27_6B_BREAK_EVEN_ANALYSIS_DONE")

if __name__ == "__main__":
    main()