import csv
import json
import math
import sys
import time
from collections import defaultdict, deque
from pathlib import Path
from statistics import median

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TESTS = ROOT / "tests"

TASK26_CODE = TESTS / "Task_26_Final_Research" / "01_Code"
sys.path.insert(0, str(TASK26_CODE))

import task26_5C_lidar_radar_cpu_replay as old

DATA = old.DATA

OUTPUT = (
    TESTS / "Task_29_Final_Research"
    / "06_Research_Findings"
    / "task29_4B7_real_lidar_radar_cpu_test.json"
)

def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)

    required = [
        old.LIDAR_CODE,
        old.RADAR_CODE,
        DATA / "selected_frames.csv",
        DATA / "lidar_points.csv",
        DATA / "radar_returns.csv",
        DATA / "lidar_clustering_summary_v1.csv",
    ]

    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)

    selected = rows(DATA / "selected_frames.csv")
    frame = min(int(r["frame"]) for r in selected)

    timestamps = {
        int(r["frame"]): float(r["time_s"])
        for r in selected
    }

    if len(timestamps) != 53:
        raise RuntimeError("Expected 53 unique selected frames")

    lidar_rows = [
        r for r in rows(DATA / "lidar_points.csv")
        if int(r["frame"]) == frame
    ]

    radar_rows = [
        r for r in rows(DATA / "radar_returns.csv")
        if int(r["frame"]) == frame
    ]

    references = [
        r for r in rows(DATA / "lidar_clustering_summary_v1.csv")
        if int(r["frame"]) == frame
    ]

    if len(references) != 1:
        raise RuntimeError("Expected one archived frame reference")

    expected = references[0]

    if not lidar_rows or not radar_rows:
        raise RuntimeError("Selected frame has no sensor data")

    for r in lidar_rows + radar_rows:
        if abs(float(r["time_s"]) - timestamps[frame]) > 1e-6:
            raise RuntimeError("Recorded timestamp mismatch")

    points = [
        (
            float(r["x_vehicle_m"]),
            float(r["y_vehicle_m"]),
            float(r["z_vehicle_m"]),
        )
        for r in lidar_rows
    ]

    cluster = old.extract_function(
        old.LIDAR_CODE,
        "cluster_frame",
        {
            "defaultdict": defaultdict,
            "deque": deque,
            "median": median,
            "math": math,
            "CELL_M": 0.5,
            "MIN_POINTS": 8,
        }
    )

    radar_process = old.extract_function(
        old.RADAR_CODE,
        "preprocess_radar_return",
        {"math": math, "C": old.C}
    )

    start = time.perf_counter_ns()

    filtered = old.filter_points(points)
    t_filter = time.perf_counter_ns()

    clusters = cluster(filtered)
    t_cluster = time.perf_counter_ns()

    valid_radar = 0
    invalid_radar = 0

    for row in radar_rows:
        range_m = float(row["range_m"])
        strength = float(row["signal_strength"])

        tof = 2.0 * range_m / old.C

        try:
            result = radar_process(tof, strength)
        except (ValueError, TypeError):
            invalid_radar += 1
            continue

        if not math.isclose(
            result["range_m"], range_m,
            rel_tol=1e-10, abs_tol=1e-7
        ):
            raise RuntimeError("Radar range mismatch")

        valid_radar += 1

    finish = time.perf_counter_ns()

    checks = {
        "filtered_points": (
            len(filtered),
            int(expected["filtered_points"])
        ),
        "clusters_found": (
            len(clusters),
            int(expected["clusters_found"])
        ),
        "largest_cluster_points": (
            max((len(c) for c in clusters), default=0),
            int(expected["largest_cluster_points"])
        ),
        "retained_cluster_points": (
            sum(len(c) for c in clusters),
            int(expected["retained_cluster_points"])
        ),
    }

    for name, (actual, archived) in checks.items():
        if actual != archived:
            raise AssertionError(
                f"{name}: actual={actual}, archived={archived}"
            )

    result = {
        "task": "29.4B.7",
        "status": "PASS",
        "input_type": "REAL_RECORDED_GEMSTAR",
        "execution": "WORKSTATION_CPU",
        "frame": frame,
        "time_s": timestamps[frame],
        "lidar_input_points": len(points),
        "lidar_filtered_points": len(filtered),
        "clusters": len(clusters),
        "radar_input_returns": len(radar_rows),
        "radar_valid_returns": valid_radar,
        "radar_invalid_returns": invalid_radar,
        "filter_ms": (t_filter - start) / 1e6,
        "cluster_ms": (t_cluster - t_filter) / 1e6,
        "radar_ms": (finish - t_cluster) / 1e6,
        "total_ms": (finish - start) / 1e6,
        "archived_reference_match": True,
        "camera_included": False,
        "ekf_included": False,
        "energy_measured": False,
        "timing_scope": "PROCESSING_ONLY_SINGLE_UNWARMED_RUN",
        "timing_is_statistical_benchmark": False,
        "radar_tof_source": "DERIVED_FROM_RECORDED_RANGE",
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("FRAME:", frame, flush=True)
    print("LIDAR_POINTS:", len(points), flush=True)
    print("FILTERED_POINTS:", len(filtered), flush=True)
    print("CLUSTERS:", len(clusters), flush=True)
    print("RADAR_RETURNS:", len(radar_rows), flush=True)
    print("CPU_PROCESSING_MS:", round(result["total_ms"], 6), flush=True)
    print("ARCHIVED_REFERENCE_MATCH: PASS", flush=True)
    print("TASK 29.4B.7: PASS", flush=True)

if __name__ == "__main__":
    main()
