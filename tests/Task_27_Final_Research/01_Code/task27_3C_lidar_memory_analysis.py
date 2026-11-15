from pathlib import Path
import csv
import hashlib
import json
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
TASK = ROOT / "Task_27_Final_Research"

SOURCE = TASK / "02_CSV_Data" / "task27_3A_lidar_workload_metrics.csv"
OUTPUT = TASK / "02_CSV_Data" / "task27_3C_lidar_memory_model.csv"
REPORT = TASK / "06_Research_Findings" / "task27_3C_memory_findings.txt"
MANIFEST = TASK / "06_Research_Findings" / "task27_3C_model_metadata.json"

# Nominal compact data representations, not Python-object sizes.
XYZ_BYTES_PER_POINT = 12  # 3 x float32
GRID_KEY_BYTES = 8        # 2 x int32, illustrative only

# Hypothetical effective transfer bandwidths, NOT measured.
BANDWIDTH_MBPS = (100, 500, 1000)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print("=== TASK 27.3C: LIDAR MEMORY ANALYSIS ===")

    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    for p in (OUTPUT, REPORT, MANIFEST):
        if p.exists():
            raise FileExistsError(
                f"Existing research output preserved: {p}"
            )

    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        inputs = list(csv.DictReader(f))

    if len(inputs) != 53:
        raise RuntimeError("Expected 53 workload frames")

    results = []
    for row in inputs:
        frame = int(row["frame"])
        n = int(row["input_points"])
        k = int(row["filtered_points"])
        occupied = int(row["occupied_grid_cells"])
        cpu_ms = float(row["median_filter_ms"])

        if not (0 <= k <= n and occupied >= 0 and cpu_ms > 0):
            raise RuntimeError(f"Invalid workload values: {frame}")

        input_bytes = n * XYZ_BYTES_PER_POINT
        output_bytes = k * XYZ_BYTES_PER_POINT

        # Model: input payload goes to FPGA, filtered payload
        # returns to host. This is NOT a measured DMA trace.
        roundtrip_bytes = input_bytes + output_bytes

        # Original grid traversal includes 3x3 cells,
        # including the current cell.
        neighbor_probes = 9 * occupied

        # Compact key sizes are illustrative, not actual
        # Python hash-table or FPGA on-chip memory usage.
        nominal_key_bytes = occupied * GRID_KEY_BYTES

        # At zero FPGA execution and scheduling overhead,
        # this is a necessary bandwidth threshold only.
        required_mb_s = roundtrip_bytes / (cpu_ms / 1000) / 1e6

        result = {
            "frame": frame,
            "input_points": n,
            "filtered_points": k,
            "occupied_grid_cells": occupied,
            "nominal_input_xyz_bytes": input_bytes,
            "nominal_output_xyz_bytes": output_bytes,
            "model_roundtrip_payload_bytes": roundtrip_bytes,
            "model_compact_grid_key_bytes": nominal_key_bytes,
            "model_neighbor_cell_probes": neighbor_probes,
            "output_payload_reduction_pct": (
                100.0 * (1.0 - k/n) if n else 0.0
            ),
            "archived_cpu_filter_median_ms": cpu_ms,
            "required_transfer_bw_MBps_zero_compute": required_mb_s,
        }

        for bw in BANDWIDTH_MBPS:
            # Decimal MB/s, not MiB/s.
            transfer_ms = (
                roundtrip_bytes / (bw * 1_000_000) * 1000
            )
            result[f"hypothetical_transfer_ms_{bw}MBps"] = transfer_ms

        results.append(result)

    if sum(r["input_points"] for r in results) != 172839:
        raise RuntimeError("Input point count mismatch")

    if sum(r["filtered_points"] for r in results) != 16295:
        raise RuntimeError("Filtered point count mismatch")

    fields = list(results[0].keys())

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    # Calculate before saving.
    total_in = sum(r["nominal_input_xyz_bytes"] for r in results)
    total_out = sum(r["nominal_output_xyz_bytes"] for r in results)
    total_roundtrip = total_in + total_out
    weighted_reduction = 100 * (1 - total_out / total_in)

    required = [
        r["required_transfer_bw_MBps_zero_compute"]
        for r in results
    ]

    metadata = {
        "task": "27.3C",
        "source_csv_sha256": sha256(SOURCE),
        "frames": len(results),
        "xyz_bytes_per_point": XYZ_BYTES_PER_POINT,
        "illustrative_grid_key_bytes": GRID_KEY_BYTES,
        "hypothetical_bandwidth_MBps": list(BANDWIDTH_MBPS),
        "model": "Host-to-FPGA raw XYZ plus FPGA-to-host filtered XYZ",
        "measured_transfer": False,
        "measured_memory_traffic": False,
        "measured_energy": False,
        "measured_fpga_execution": False,
        "limitations": [
            "Compact float32 representation assumed.",
            "Actual transport framing and transfer overhead excluded.",
            "Python heap usage, cache traffic and DRAM traffic unknown.",
            "The original grid clustering executes additional operations.",
            "Bandwidth thresholds assume zero FPGA compute/overhead.",
            "CPU measurements originate from a development workstation.",
            "No FPGA acceleration or energy benefit established."
        ]
    }

    findings = [
        "GEMSTAR TASK 27.3C - LIDAR MEMORY MODEL",
        "========================================",
        f"Frames analyzed: {len(results)}",
        f"Nominal input XYZ bytes: {total_in}",
        f"Nominal filtered XYZ bytes: {total_out}",
        f"Modeled input + output bytes: {total_roundtrip}",
        f"Output payload reduction: {weighted_reduction:.4f}%",
        f"Median zero-compute bandwidth threshold: "
        f"{statistics.median(required):.4f} MB/s",
        f"Maximum zero-compute bandwidth threshold: "
        f"{max(required):.4f} MB/s",
        "",
        "CONDITION FOR ACTUAL LATENCY IMPROVEMENT:",
        "Transfer + FPGA execution + scheduling/other overhead",
        "must be less than the matched CPU processing time.",
        "",
        "NOT MEASURED:",
        "Real DMA throughput, bus transactions, cache traffic,",
        "FPGA execution latency, board power and energy.",
        "",
        "NO FPGA SPEEDUP OR ENERGY CLAIM IS ESTABLISHED."
    ]

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    with REPORT.open("x", encoding="utf-8") as f:
        f.write("\n".join(findings) + "\n")

    with MANIFEST.open("x", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("FRAMES_ANALYZED:", len(results))
    print("NOMINAL_INPUT_BYTES:", total_in)
    print("NOMINAL_FILTERED_OUTPUT_BYTES:", total_out)
    print("MODELED_ROUNDTRIP_BYTES:", total_roundtrip)
    print("OUTPUT_REDUCTION_PCT:", round(weighted_reduction, 4))
    print("MEDIAN_REQUIRED_BW_MBPS:",
          round(statistics.median(required), 4))
    print("MAX_REQUIRED_BW_MBPS:", round(max(required), 4))
    print("MEASURED_DMA_BANDWIDTH: NO")
    print("MEASURED_FPGA_ENERGY: NO")
    print("CSV_SAVED:", OUTPUT)
    print("FINDINGS_SAVED:", REPORT)
    print("METADATA_SAVED:", MANIFEST)
    print("TASK27_3C_LIDAR_MEMORY_ANALYSIS_DONE")

if __name__ == "__main__":
    main()