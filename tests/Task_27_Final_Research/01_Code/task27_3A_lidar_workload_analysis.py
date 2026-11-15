from pathlib import Path
from collections import defaultdict
import csv
import math
import statistics
import hashlib
import json

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
DATA = ROOT / "Task_24_Final_Research" / "09_Controlled_Scenario" / "C02_MovingTarget" / "C02_V2_EKF_Input_53Frames_V1"
TASK26 = ROOT / "Task_26_Final_Research"
TASK27 = ROOT / "Task_27_Final_Research"

SOURCE = DATA.parent / "C02_V2_Lidar_Clustering_53Frames_V1.py"
POINTS = DATA / "lidar_points.csv"
REFERENCE = DATA / "lidar_clustering_summary_v1.csv"
TIMING = TASK26 / "02_CSV_Data" / "task26_4D_lidar_cpu_summary.csv"
BENCH_REPORT = TASK26 / "06_Research_Findings" / "task26_4D_lidar_cpu_report.json"

OUT_CSV = TASK27 / "02_CSV_Data" / "task27_3A_lidar_workload_metrics.csv"
OUT_TXT = TASK27 / "06_Research_Findings" / "task27_3A_lidar_workload_findings.txt"

CELL = 0.50

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def main():
    print("=== TASK 27.3A: LIDAR WORKLOAD ANALYSIS ===")

    for path in (SOURCE, POINTS, REFERENCE, TIMING, BENCH_REPORT):
        if not path.is_file():
            raise FileNotFoundError(path)

    for path in (OUT_CSV, OUT_TXT):
        if path.exists():
            raise FileExistsError(f"Existing output preserved: {path}")

    report = json.loads(BENCH_REPORT.read_text(encoding="utf-8-sig"))

    hashes = {
        "source_sha256": SOURCE,
        "input_sha256": POINTS,
        "reference_sha256": REFERENCE,
    }
    for key, path in hashes.items():
        if sha256(path) != report[key].upper():
            raise RuntimeError(f"Archived hash mismatch: {path.name}")

    print("ARCHIVED_SOURCE_HASHES: PASS")

    points = defaultdict(list)

    for row in read_csv(POINTS):
        frame = int(row["frame"])
        points[frame].append((
            float(row["x_vehicle_m"]),
            float(row["y_vehicle_m"]),
            float(row["z_vehicle_m"])
        ))

    references = {
        int(r["frame"]): r for r in read_csv(REFERENCE)
    }

    timing = defaultdict(dict)
    for row in read_csv(TIMING):
        frame = int(row["frame"])
        stage = row["stage"]
        if stage in timing[frame]:
            raise RuntimeError("Duplicate frame/stage timing")
        timing[frame][stage] = float(row["median_ms"])

    if len(points) != 53 or sum(map(len, points.values())) != 172839:
        raise RuntimeError("Unexpected archived LiDAR dataset")

    if set(points) != set(references) or set(points) != set(timing):
        raise RuntimeError("Frame mismatch between datasets")

    results = []

    for frame in sorted(points):
        raw = points[frame]

        filtered = [
            (x, y, z) for x, y, z in raw
            if math.isfinite(x) and math.isfinite(y) and math.isfinite(z)
            and 3.0 <= x <= 60.0
            and abs(y) <= 15.0
            and 0.45 <= z <= 3.50
        ]

        expected = int(references[frame]["filtered_points"])
        if len(filtered) != expected:
            raise RuntimeError(f"Frame {frame}: filtered count mismatch")

        cells = {
            (math.floor(x / CELL), math.floor(y / CELL))
            for x, y, z in filtered
        }

        n = len(raw)
        k = len(filtered)
        occupied = len(cells)

        if "filter" not in timing[frame] or "cluster" not in timing[frame]:
            raise RuntimeError(f"Frame {frame}: missing CPU stage")

        filter_ms = timing[frame]["filter"]
        cluster_ms = timing[frame]["cluster"]

        results.append({
            "frame": frame,
            "input_points": n,
            "filtered_points": k,
            "rejected_points": n - k,
            "retention_pct": round(100 * k / n, 6),
            "occupied_grid_cells": occupied,
            "cell_neighbor_candidates_upper_bound": 8 * occupied,
            "nominal_input_xyz_bytes": n * 12,
            "nominal_filtered_xyz_bytes": k * 12,
            "nominal_xyz_reduction_bytes": (n - k) * 12,
            "median_filter_ms": filter_ms,
            "median_cluster_ms": cluster_ms,
            "sum_stage_medians_ms": round(filter_ms + cluster_ms, 8),
            "archived_clusters_found": int(
                references[frame]["clusters_found"]
            )
        })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    total_input = sum(r["input_points"] for r in results)
    total_kept = sum(r["filtered_points"] for r in results)
    reduction = 100 * (1 - total_kept / total_input)

    findings = [
        "GEMSTAR TASK 27.3A - LIDAR WORKLOAD FINDINGS",
        f"Frames: {len(results)}",
        f"Total input points: {total_input}",
        f"Total filtered points: {total_kept}",
        f"Weighted point reduction: {reduction:.4f}%",
        f"Mean occupied cells/frame: {statistics.mean(r['occupied_grid_cells'] for r in results):.2f}",
        f"Median filter stage time (across frame medians): {statistics.median(r['median_filter_ms'] for r in results):.6f} ms",
        f"Median cluster stage time (across frame medians): {statistics.median(r['median_cluster_ms'] for r in results):.6f} ms",
        "",
        "LIMITATIONS:",
        "CPU times are archived workstation timings, not ARM timings.",
        "The sum of stage medians is not end-to-end measured latency.",
        "8*occupied_cells is a structural upper bound on neighbor-cell candidates, not measured operations.",
        "Nominal XYZ sizes assume float32 triples, not Python object allocation or DRAM traffic.",
        "Occupied cells do not include Python dictionary/list overhead.",
        "This step does not rerun clustering or validate cluster identities.",
        "No FPGA energy or acceleration results are claimed.",
    ]

    with OUT_TXT.open("x", encoding="utf-8") as f:
        f.write("\n".join(findings) + "\n")

    print("FRAMES_ANALYZED:", len(results))
    print("INPUT_POINTS:", total_input)
    print("FILTERED_POINTS:", total_kept)
    print("POINT_REDUCTION_PCT:", round(reduction, 4))
    print("MEAN_OCCUPIED_CELLS:", round(statistics.mean(
        r["occupied_grid_cells"] for r in results), 2))
    print("OUTPUT_CSV:", OUT_CSV)
    print("OUTPUT_FINDINGS:", OUT_TXT)
    print("TASK27_3A_LIDAR_WORKLOAD_ANALYSIS_DONE")

if __name__ == "__main__":
    main()