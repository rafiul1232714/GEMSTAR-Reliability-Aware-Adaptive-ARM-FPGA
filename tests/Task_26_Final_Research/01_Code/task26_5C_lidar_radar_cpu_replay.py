from pathlib import Path
from collections import defaultdict, deque
from statistics import median
import ast
import csv
import hashlib
import json
import math
import statistics
import time

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
BASE = TESTS / "Task_24_Final_Research" / "09_Controlled_Scenario" / "C02_MovingTarget"
DATA = BASE / "C02_V2_EKF_Input_53Frames_V1"
T23 = TESTS / "Task_23_Final_Research"
T26 = TESTS / "Task_26_Final_Research"

LIDAR_CODE = BASE / "C02_V2_Lidar_Clustering_53Frames_V1.py"
RADAR_CODE = T23 / "01_Code" / "task23_13C_01_radar_robustness_tests.py"

FILES = {
    "frames": DATA / "selected_frames.csv",
    "lidar": DATA / "lidar_points.csv",
    "radar": DATA / "radar_returns.csv",
    "reference": DATA / "lidar_clustering_summary_v1.csv",
}

CSV_OUT = T26 / "02_CSV_Data" / "task26_5C_integrated_cpu_timing.csv"
SUMMARY_OUT = T26 / "02_CSV_Data" / "task26_5C_integrated_cpu_summary.csv"
REPORT_OUT = T26 / "06_Research_Findings" / "task26_5C_integrated_cpu_report.json"

WARMUP = 5
REPEATS = 25
C = 299792458.0

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        yield from csv.DictReader(f)

def extract_function(path, name, namespace):
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    matches = [
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Function not uniquely found: {name}")
    code = ast.get_source_segment(source, matches[0])
    if not code:
        raise RuntimeError(f"Cannot extract: {name}")
    exec(compile(code, str(path), "exec"), namespace)
    return namespace[name]

def filter_points(points):
    kept = []
    for x, y, z in points:
        if not all(math.isfinite(v) for v in (x, y, z)):
            continue
        if (
            3.0 <= x <= 60.0
            and abs(y) <= 15.0
            and 0.45 <= z <= 3.50
        ):
            kept.append((x, y, z))
    return kept

def pct(values, p):
    v = sorted(values)
    pos = (len(v)-1)*p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return v[lo] + (v[hi]-v[lo])*(pos-lo)

def main():
    outputs = [CSV_OUT, SUMMARY_OUT, REPORT_OUT]
    if any(p.exists() for p in outputs):
        raise FileExistsError("Task 26.5C outputs already exist. Preserving them.")

    sources = [LIDAR_CODE, RADAR_CODE, *FILES.values()]
    for p in sources:
        if not p.is_file():
            raise FileNotFoundError(p)

    lidar_source = LIDAR_CODE.read_text(encoding="utf-8-sig")
    lidar_tree = ast.parse(lidar_source)

    required_constants = {
        "CELL_M": 0.5,
        "MIN_POINTS": 8,
        "Y_LIMIT": 15.0,
    }
    constants = {}
    for node in lidar_tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            key = node.targets[0].id
            if key in required_constants:
                constants[key] = ast.literal_eval(node.value)

    if constants != required_constants:
        raise RuntimeError("LiDAR constants differ from archived reference")

    if (
        "X_MIN, X_MAX = 3.0, 60.0" not in lidar_source
        or "Z_MIN, Z_MAX = 0.45, 3.50" not in lidar_source
    ):
        raise RuntimeError("LiDAR filtering bounds changed")

    cluster = extract_function(
        LIDAR_CODE, "cluster_frame",
        {
            "defaultdict": defaultdict,
            "deque": deque,
            "median": median,
            "math": math,
            "CELL_M": 0.5,
            "MIN_POINTS": 8,
        }
    )

    radar_source = RADAR_CODE.read_text(encoding="utf-8-sig")
    radar_tree = ast.parse(radar_source)
    c_values = [
        ast.literal_eval(n.value)
        for n in radar_tree.body
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "C"
    ]
    if len(c_values) != 1 or c_values[0] != C:
        raise RuntimeError("Radar propagation constant mismatch")

    radar_process = extract_function(
        RADAR_CODE, "preprocess_radar_return",
        {"math": math, "C": C}
    )

    selected = {}
    for row in read_rows(FILES["frames"]):
        frame = int(row["frame"])
        if frame in selected:
            raise RuntimeError("Duplicate selected frame")
        selected[frame] = float(row["time_s"])

    if len(selected) != 53:
        raise RuntimeError("Expected 53 selected frames")

    reference = {}
    for row in read_rows(FILES["reference"]):
        frame = int(row["frame"])
        if frame in reference:
            raise RuntimeError("Duplicate reference frame")
        reference[frame] = row

    if set(reference) != set(selected):
        raise RuntimeError("Reference frames do not match")

    lidar = defaultdict(list)
    radar = defaultdict(list)
    lidar_rows = 0
    radar_rows = 0

    for row in read_rows(FILES["lidar"]):
        frame = int(row["frame"])
        if frame not in selected:
            raise RuntimeError("Unexpected LiDAR frame")
        if abs(float(row["time_s"]) - selected[frame]) > 1e-6:
            raise RuntimeError("LiDAR timestamp mismatch")
        lidar[frame].append((
            float(row["x_vehicle_m"]),
            float(row["y_vehicle_m"]),
            float(row["z_vehicle_m"]),
        ))
        lidar_rows += 1

    for row in read_rows(FILES["radar"]):
        frame = int(row["frame"])
        if frame not in selected:
            raise RuntimeError("Unexpected Radar frame")
        if abs(float(row["time_s"]) - selected[frame]) > 1e-6:
            raise RuntimeError("Radar timestamp mismatch")
        radar[frame].append((
            float(row["range_m"]),
            float(row["signal_strength"]),
        ))
        radar_rows += 1

    if lidar_rows != 172839 or radar_rows != 3348:
        raise RuntimeError("Unexpected recorded sensor row counts")

    if set(lidar) != set(selected) or set(radar) != set(selected):
        raise RuntimeError("Some synchronized frames have no sensor records")

    def run_frame(frame):
        t0 = time.perf_counter_ns()
        filtered = filter_points(lidar[frame])
        t1 = time.perf_counter_ns()
        clusters = cluster(filtered)
        t2 = time.perf_counter_ns()

        radar_valid = 0
        radar_invalid = 0

        for range_m, strength in radar[frame]:
            # Derived TOF; Task 24 CSV contains range, not raw TOF.
            tof = 2.0 * range_m / C

            try:
                result = radar_process(tof, strength)
            except (ValueError, TypeError):
                radar_invalid += 1
                continue

            if not math.isclose(
                result["range_m"], range_m,
                rel_tol=1e-10, abs_tol=1e-7
            ):
                raise RuntimeError("Radar reconstructed range differs")

            radar_valid += 1

        t3 = time.perf_counter_ns()

        return {
            "filter_ms": (t1-t0)/1e6,
            "cluster_ms": (t2-t1)/1e6,
            "radar_ms": (t3-t2)/1e6,
            "total_ms": (t3-t0)/1e6,
            "filtered_points": len(filtered),
            "cluster_count": len(clusters),
            "largest_cluster_points": len(clusters[0]) if clusters else 0,
            "retained_cluster_points": sum(len(c) for c in clusters),
            "radar_valid": radar_valid,
            "radar_invalid": radar_invalid,
        }

    timing_rows = []
    summary_rows = []

    for frame in sorted(selected):
        # Check numerical agreement before recording timings.
        check = run_frame(frame)
        expected = reference[frame]

        for key, observed, ref_key in [
            ("filtered", check["filtered_points"], "filtered_points"),
            ("clusters", check["cluster_count"], "clusters_found"),
            ("largest", check["largest_cluster_points"], "largest_cluster_points"),
            ("retained", check["retained_cluster_points"], "retained_cluster_points"),
        ]:
            if observed != int(expected[ref_key]):
                raise RuntimeError(f"Frame {frame}: {key} mismatch")

        for _ in range(WARMUP):
            run_frame(frame)

        results = [run_frame(frame) for _ in range(REPEATS)]

        for repeat, value in enumerate(results, 1):
            timing_rows.append({
                "frame": frame,
                "repeat": repeat,
                "lidar_input_points": len(lidar[frame]),
                "lidar_filtered_points": value["filtered_points"],
                "radar_input_returns": len(radar[frame]),
                "radar_valid_returns": value["radar_valid"],
                "radar_invalid_returns": value["radar_invalid"],
                "clusters": value["cluster_count"],
                "filter_ms": value["filter_ms"],
                "cluster_ms": value["cluster_ms"],
                "radar_ms": value["radar_ms"],
                "total_ms": value["total_ms"],
            })

        total = [r["total_ms"] for r in results]
        summary_rows.append({
            "frame": frame,
            "lidar_input_points": len(lidar[frame]),
            "lidar_filtered_points": check["filtered_points"],
            "radar_input_returns": len(radar[frame]),
            "clusters": check["cluster_count"],
            "median_filter_ms": median(r["filter_ms"] for r in results),
            "median_cluster_ms": median(r["cluster_ms"] for r in results),
            "median_radar_ms": median(r["radar_ms"] for r in results),
            "median_total_ms": median(total),
            "p95_total_ms": pct(total, 0.95),
            "p99_total_ms": pct(total, 0.99),
        })

        print(
            f"FRAME={frame} "
            f"LIDAR={len(lidar[frame])} "
            f"RADAR={len(radar[frame])} "
            f"MEDIAN_TOTAL_MS={median(total):.4f} "
            f"REFERENCE=PASS"
        )

    for path, rows in [
        (CSV_OUT, timing_rows),
        (SUMMARY_OUT, summary_rows),
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    report = {
        "task": "26.5C",
        "pipeline_type": "Partial sequential LiDAR–Radar CPU replay",
        "frames": len(selected),
        "lidar_points": lidar_rows,
        "radar_returns": radar_rows,
        "warmups_per_frame": WARMUP,
        "timed_repeats_per_frame": REPEATS,
        "timing_rows": len(timing_rows),
        "archived_lidar_reference_match": "PASS",
        "radar_tof": "Derived from stored range; not original raw TOF",
        "source_sha256": {
            str(p): digest(p) for p in sources
        },
        "csv_and_osi_read_timed": False,
        "camera_included": False,
        "association_included": False,
        "ekf_included": False,
        "energy_measured": False,
        "timing_type": "Sequential execution of three processing stages",
        "p99_limitation": "25 repeats per frame; exploratory",
    }

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_OUT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print("=== TASK 26.5C INTEGRATED CPU REPLAY ===")
    print("FRAMES_VALIDATED:", len(selected))
    print("LIDAR_ROWS:", lidar_rows)
    print("RADAR_ROWS:", radar_rows)
    print("TIMING_ROWS:", len(timing_rows))
    print("LIDAR_REFERENCE_MATCH: PASS")
    print("PIPELINE_TYPE: PARTIAL_LIDAR_RADAR")
    print("CAMERA_EKF_ASSOCIATION_INCLUDED: NO")
    print("ENERGY_MEASURED: NO")
    print("TASK26_5C_INTEGRATED_CPU_REPLAY_PASS")
    print("TIMING:", CSV_OUT)
    print("SUMMARY:", SUMMARY_OUT)
    print("REPORT:", REPORT_OUT)

if __name__ == "__main__":
    main()
