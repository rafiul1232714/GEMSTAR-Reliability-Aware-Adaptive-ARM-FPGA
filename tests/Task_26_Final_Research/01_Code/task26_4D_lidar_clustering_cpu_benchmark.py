from pathlib import Path
from collections import defaultdict, deque
from statistics import median
import ast
import csv
import hashlib
import json
import math
import re
import statistics
import time

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
TASK24 = ROOT / "Task_24_Final_Research" / "09_Controlled_Scenario" / "C02_MovingTarget"
DATA = TASK24 / "C02_V2_EKF_Input_53Frames_V1"
TASK26 = ROOT / "Task_26_Final_Research"

SOURCE = TASK24 / "C02_V2_Lidar_Clustering_53Frames_V1.py"
POINTS = DATA / "lidar_points.csv"
FRAMES = DATA / "selected_frames.csv"
REFERENCE = DATA / "lidar_clustering_summary_v1.csv"

TIMINGS = TASK26 / "02_CSV_Data" / "task26_4D_lidar_cpu_timing.csv"
SUMMARY = TASK26 / "02_CSV_Data" / "task26_4D_lidar_cpu_summary.csv"
REPORT = TASK26 / "06_Research_Findings" / "task26_4D_lidar_cpu_report.json"

WARMUP = 5
REPEATS = 25

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def percentile(values, fraction):
    values = sorted(values)
    position = (len(values)-1)*fraction
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (values[high]-values[low])*(position-low)

def load_original_clustering():
    source = SOURCE.read_text(encoding="utf-8-sig")

    expected = {
        "CELL_M": 0.50,
        "MIN_POINTS": 8,
        "Y_LIMIT": 15.0,
    }

    for key, value in expected.items():
        pattern = rf"(?m)^{key}\s*=\s*([0-9.]+)"
        match = re.search(pattern, source)
        if match is None or float(match.group(1)) != value:
            raise RuntimeError(f"Unexpected original constant: {key}")

    for line in (
        "X_MIN, X_MAX = 3.0, 60.0",
        "Z_MIN, Z_MAX = 0.45, 3.50",
    ):
        if line not in source:
            raise RuntimeError(f"Original filter setting changed: {line}")

    tree = ast.parse(source, filename=str(SOURCE))
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "cluster_frame"
    ]

    if len(nodes) != 1:
        raise RuntimeError("Expected one original clustering function")

    function_source = ast.get_source_segment(source, nodes[0])

    namespace = {
        "defaultdict": defaultdict,
        "deque": deque,
        "median": median,
        "math": math,
        "CELL_M": 0.50,
        "MIN_POINTS": 8,
    }

    exec(
        compile(function_source, str(SOURCE), "exec"),
        namespace
    )

    return namespace["cluster_frame"]

def filter_points(raw):
    filtered = []

    for x, y, z in raw:
        if not all(math.isfinite(v) for v in (x, y, z)):
            continue

        if not (
            3.0 <= x <= 60.0
            and abs(y) <= 15.0
            and 0.45 <= z <= 3.50
        ):
            continue

        filtered.append((x, y, z))

    return filtered

def benchmark(fn):
    for _ in range(WARMUP):
        fn()

    values = []
    for _ in range(REPEATS):
        start = time.perf_counter_ns()
        fn()
        values.append(
            (time.perf_counter_ns() - start) / 1e6
        )

    return values

def main():
    for output in (TIMINGS, SUMMARY, REPORT):
        if output.exists():
            raise FileExistsError(
                f"Existing output preserved: {output}"
            )

    for path in (SOURCE, POINTS, FRAMES, REFERENCE):
        if not path.is_file():
            raise FileNotFoundError(path)

    cluster_frame = load_original_clustering()

    selected = {}
    with FRAMES.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            frame = int(row["frame"])
            if frame in selected:
                raise RuntimeError("Duplicate selected frame")
            selected[frame] = float(row["time_s"])

    if len(selected) != 53:
        raise RuntimeError("Expected exactly 53 frames")

    archived = {}
    with REFERENCE.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            frame = int(row["frame"])
            if frame in archived:
                raise RuntimeError("Duplicate archived frame")
            archived[frame] = row

    if set(archived) != set(selected):
        raise RuntimeError("Reference frame IDs do not match")

    points_by_frame = defaultdict(list)
    total_rows = 0

    with POINTS.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            frame = int(row["frame"])

            if frame not in selected:
                raise RuntimeError("Unexpected LiDAR frame")

            t = float(row["time_s"])
            if not math.isclose(t, selected[frame], abs_tol=1e-6):
                raise RuntimeError("Frame timestamp mismatch")

            points_by_frame[frame].append((
                float(row["x_vehicle_m"]),
                float(row["y_vehicle_m"]),
                float(row["z_vehicle_m"]),
            ))
            total_rows += 1

    if total_rows != 172839:
        raise RuntimeError(
            f"Unexpected input row count: {total_rows}"
        )

    raw_timings = []
    summary = []

    for frame in sorted(selected):
        raw = points_by_frame[frame]
        filtered = filter_points(raw)
        clusters = cluster_frame(filtered)

        observed = {
            "filtered_points": len(filtered),
            "clusters_found": len(clusters),
            "largest_cluster_points": (
                len(clusters[0]) if clusters else 0
            ),
            "retained_cluster_points": sum(
                len(c) for c in clusters
            ),
        }

        for key, actual in observed.items():
            expected = int(archived[frame][key])
            if actual != expected:
                raise RuntimeError(
                    f"Frame {frame}, {key}: "
                    f"expected {expected}, got {actual}"
                )

        stages = {
            "filter": lambda raw=raw: filter_points(raw),
            "cluster": lambda filtered=filtered: cluster_frame(filtered),
        }

        for stage, fn in stages.items():
            times = benchmark(fn)

            for run, ms in enumerate(times, start=1):
                raw_timings.append({
                    "frame": frame,
                    "stage": stage,
                    "repeat": run,
                    "input_points": len(raw),
                    "filtered_points": len(filtered),
                    "clusters_found": len(clusters),
                    "elapsed_ms": ms,
                })

            summary.append({
                "frame": frame,
                "stage": stage,
                "input_points": len(raw),
                "filtered_points": len(filtered),
                "clusters_found": len(clusters),
                "median_ms": statistics.median(times),
                "p95_ms": percentile(times, 0.95),
                "p99_ms": percentile(times, 0.99),
                "mean_ms": statistics.mean(times),
            })

        print(
            f"FRAME={frame} "
            f"INPUT={len(raw)} "
            f"FILTERED={len(filtered)} "
            f"CLUSTERS={len(clusters)} "
            f"REFERENCE=PASS"
        )

    for path, rows in (
        (TIMINGS, raw_timings),
        (SUMMARY, summary),
    ):
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(rows[0].keys())
            )
            writer.writeheader()
            writer.writerows(rows)

    report = {
        "task": "26.4D",
        "description": "Isolated filtering and original grid clustering",
        "source_sha256": sha256(SOURCE),
        "input_sha256": sha256(POINTS),
        "frame_manifest_sha256": sha256(FRAMES),
        "reference_sha256": sha256(REFERENCE),
        "selected_frames": len(selected),
        "raw_point_rows": total_rows,
        "warmup_per_stage_per_frame": WARMUP,
        "timed_repeats_per_stage_per_frame": REPEATS,
        "timing_rows": len(raw_timings),
        "reference_frame_validation": "PASS",
        "csv_parsing_timed": False,
        "filter_and_cluster_timed_separately": True,
        "end_to_end_latency_measured": False,
        "energy_measured": False,
        "hardware": "Development workstation CPU",
        "limitations": [
            "Archived 53-frame controlled scenario only",
            "Clustering is not validated object classification",
            "Stage timings do not include OSI or CSV decoding",
            "No measurements from ARM or FPGA hardware",
        ],
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print("=== TASK 26.4D LIDAR CPU BENCHMARK ===")
    print("SOURCE_FUNCTION: Original Task 24 cluster_frame")
    print("INPUT_LIDAR_ROWS:", total_rows)
    print("FRAMES_VALIDATED:", len(selected))
    print("REFERENCE_MATCH: PASS")
    print("TIMING_ROWS:", len(raw_timings))
    print("FILTER_AND_CLUSTER_SEPARATE: YES")
    print("END_TO_END_MEASURED: NO")
    print("ENERGY_MEASURED: NO")
    print("TASK26_4D_LIDAR_CPU_BENCHMARK_PASS")
    print("TIMINGS:", TIMINGS)
    print("SUMMARY:", SUMMARY)
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
