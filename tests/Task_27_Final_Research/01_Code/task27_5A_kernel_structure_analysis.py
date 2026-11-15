from pathlib import Path
from collections import defaultdict
import csv
import json
import hashlib
import math
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
T27 = ROOT / "Task_27_Final_Research"
T23 = ROOT / "Task_23_Final_Research"
T24 = ROOT / "Task_24_Final_Research"

LIDAR = T27 / "02_CSV_Data" / "task27_3A_lidar_workload_metrics.csv"
SENSORS = T27 / "02_CSV_Data" / "task27_4C_sensor_compute_characterization.csv"

CAMERA_SOURCE = T23 / "01_Code" / "task23_12C_06_camera_cpu_preprocessing.py"
RADAR_SOURCE = T23 / "01_Code" / "task23_13C_01_radar_robustness_tests.py"
LIDAR_SOURCE = (
    T24 / "09_Controlled_Scenario" / "C02_MovingTarget"
    / "C02_V2_Lidar_Clustering_53Frames_V1.py"
)

OUT = T27 / "02_CSV_Data" / "task27_5A_kernel_structure.csv"
SUMMARY = T27 / "02_CSV_Data" / "task27_5A_kernel_summary.csv"
REPORT = T27 / "06_Research_Findings" / "task27_5A_kernel_findings.txt"
MANIFEST = T27 / "06_Research_Findings" / "task27_5A_source_manifest.json"

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def save_csv(path, data):
    with path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)

def make_row(stage, scenario, frame, items, input_bytes,
             output_bytes, buffers, cells, probes, ms, description):
    return {
        "stage": stage,
        "scenario": scenario,
        "frame": frame,
        "input_items": items,
        "nominal_input_bytes": input_bytes,
        "nominal_output_bytes": output_bytes,
        "nominal_named_buffer_sum_bytes": buffers,
        "occupied_grid_cells": cells,
        "modeled_neighbor_cell_probes": probes,
        "archived_cpu_median_ms": ms,
        "algorithm_structure": description,
        "exact_operation_count_known": "NO",
        "actual_memory_traffic_measured": "NO",
        "hardware_energy_measured": "NO"
    }

def main():
    print("=== TASK 27.5A: KERNEL STRUCTURE ANALYSIS ===")

    inputs = [
        LIDAR, SENSORS,
        CAMERA_SOURCE, RADAR_SOURCE, LIDAR_SOURCE
    ]

    for p in inputs:
        if not p.is_file():
            raise FileNotFoundError(p)

    for p in (OUT, SUMMARY, REPORT, MANIFEST):
        if p.exists():
            raise FileExistsError(
                f"Existing research output preserved: {p}"
            )

    lidar = read_csv(LIDAR)
    sensors = read_csv(SENSORS)

    if len(lidar) != 53 or len(sensors) != 23:
        raise RuntimeError("Unexpected archived dataset size")

    rows = []
    total_input = 0
    total_filtered = 0

    # LiDAR filtering and clustering: 53 frames each.
    for r in lidar:
        frame = int(r["frame"])
        n = int(r["input_points"])
        k = int(r["filtered_points"])
        occupied = int(r["occupied_grid_cells"])

        if not (0 <= k <= n and 0 <= occupied <= k):
            raise RuntimeError(f"Invalid LiDAR counts: {frame}")

        total_input += n
        total_filtered += k

        rows.append(make_row(
            "LiDAR_filter",
            "C02_CONTROLLED",
            frame,
            n,
            n * 12,
            k * 12,
            "",
            "",
            "",
            float(r["median_filter_ms"]),
            "Finite XYZ tests and spatial comparisons"
        ))

        rows.append(make_row(
            "LiDAR_cluster",
            "C02_CONTROLLED",
            frame,
            k,
            k * 12,
            "",
            "",
            occupied,
            occupied * 9,
            float(r["median_cluster_ms"]),
            "XY grid assignment and 3x3 cell traversal"
        ))

    if total_input != 172839 or total_filtered != 16295:
        raise RuntimeError("LiDAR totals do not match Task 27.3A")

    # Camera, Radar, YOLO: 23 characterization records.
    for r in sensors:
        workload = r["workload"]
        items = int(r["processing_items"])
        input_bytes = int(r["nominal_processing_input_bytes"])
        ms = float(r["archived_cpu_median_ms"])

        if workload == "Camera":
            rows.append(make_row(
                "Camera_preprocessing",
                f"{r['scenario']}_{r['mode']}",
                "",
                items,
                input_bytes,
                "",
                int(r["nominal_intermediate_buffer_sum_bytes"]),
                "",
                "",
                ms,
                "BGR to grayscale/HSV; Canny; float64 Laplacian"
            ))

        elif workload == "Radar":
            rows.append(make_row(
                "Radar_valid_returns",
                f"PAIR_{r['scenario']}",
                r["frame"],
                items,
                input_bytes,
                "",
                "",
                "",
                "",
                ms,
                "Return validation and time-of-flight range"
            ))

        elif workload == "YOLO11s":
            rows.append(make_row(
                "YOLO11s_predict",
                r["scenario"],
                r["frame"],
                items,
                input_bytes,
                "",
                "",
                "",
                "",
                ms,
                "CPU predict: preprocessing, inference, postprocessing"
            ))

        else:
            raise RuntimeError(f"Unexpected workload: {workload}")

    expected = {
        "LiDAR_filter": 53,
        "LiDAR_cluster": 53,
        "Camera_preprocessing": 6,
        "Radar_valid_returns": 12,
        "YOLO11s_predict": 5
    }

    groups = defaultdict(list)

    for row in rows:
        ms = float(row["archived_cpu_median_ms"])
        if not math.isfinite(ms) or ms <= 0:
            raise RuntimeError("Invalid archived CPU median")

        groups[row["stage"]].append(ms)

    if len(rows) != 129 or set(groups) != set(expected):
        raise RuntimeError("Unexpected stage structure")

    for stage, n in expected.items():
        if len(groups[stage]) != n:
            raise RuntimeError(f"Unexpected stage count: {stage}")

    summaries = []

    for stage, n in expected.items():
        times = groups[stage]

        summaries.append({
            "stage": stage,
            "records": n,
            "median_of_record_medians_ms": statistics.median(times),
            "minimum_record_median_ms": min(times),
            "maximum_record_median_ms": max(times),
            "exact_operation_count_known": "NO",
            "actual_dram_traffic_known": "NO",
            "fpga_energy_known": "NO"
        })

    # Source and numerical validation finished.
    # Write outputs only after all checks pass.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    save_csv(OUT, rows)
    save_csv(SUMMARY, summaries)

    metadata = {
        "task": "27.5A",
        "source_files": [
            {
                "path": str(p),
                "sha256": sha256(p),
                "size_bytes": p.stat().st_size
            }
            for p in inputs
        ],
        "total_stage_records": len(rows),
        "stage_counts": expected,
        "assumptions": {
            "lidar_xyz": "3 float32 values per point; 12 bytes",
            "lidar_grid_cell_m": 0.50,
            "neighbor_probes": "9 per occupied cell; structural count",
            "camera": "Named buffer sizes, not actual DRAM traffic",
            "radar": "Nominal valid-return representation",
            "yolo": "No exact FLOP count or runtime memory estimate"
        },
        "exact_operations_measured": False,
        "actual_memory_traffic_measured": False,
        "hardware_energy_measured": False,
        "original_data_modified": False
    }

    with MANIFEST.open("x", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    findings = [
        "GEMSTAR TASK 27.5A - KERNEL STRUCTURE",
        "===================================",
        f"Stage records: {len(rows)}",
        f"Stage types: {len(groups)}",
        f"LiDAR input points: {total_input}",
        f"LiDAR retained points: {total_filtered}",
        "",
        "STAGE CPU TIMINGS:"
    ]

    for r in summaries:
        findings.append(
            f"{r['stage']}: "
            f"{r['records']} records, "
            f"{r['median_of_record_medians_ms']:.6f} ms "
            "median of record medians"
        )

    findings.extend([
        "",
        "HARDWARE INTERPRETATION:",
        "LiDAR filtering is structurally streaming-friendly.",
        "LiDAR clustering requires cell storage and traversal.",
        "Camera contains pixel-local and neighborhood operations.",
        "Radar has relatively small valid-return batches.",
        "YOLO requires separate model-layer analysis.",
        "",
        "LIMITATIONS:",
        "These timings cover different workloads and inputs.",
        "No actual CPU instructions or FLOPs measured.",
        "No actual cache, DRAM or DMA traffic measured.",
        "No real hardware roofline established.",
        "No ARM-FPGA power, energy or speedup measured.",
        "No final FPGA kernel selected."
    ])

    with REPORT.open("x", encoding="utf-8") as f:
        f.write("\n".join(findings) + "\n")

    print("LIDAR_INPUT_POINTS:", total_input)
    print("LIDAR_FILTERED_POINTS:", total_filtered)
    print("KERNEL_TYPES:", len(groups))
    print("STAGE_RECORDS:", len(rows))

    for r in summaries:
        print(
            f"STAGE={r['stage']} "
            f"RECORDS={r['records']} "
            f"MEDIAN_MS={r['median_of_record_medians_ms']:.6f}"
        )

    print("EXACT_OPERATION_COUNTS_MEASURED: NO")
    print("ACTUAL_MEMORY_TRAFFIC_MEASURED: NO")
    print("HARDWARE_ENERGY_MEASURED: NO")
    print("OUTPUT_CSV:", OUT)
    print("OUTPUT_SUMMARY:", SUMMARY)
    print("OUTPUT_FINDINGS:", REPORT)
    print("OUTPUT_MANIFEST:", MANIFEST)
    print("TASK27_5A_KERNEL_STRUCTURE_ANALYSIS_DONE")

if __name__ == "__main__":
    main()