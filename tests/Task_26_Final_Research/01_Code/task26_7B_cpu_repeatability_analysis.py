from pathlib import Path
from collections import defaultdict
from statistics import mean, median, stdev
import csv
import json
import math

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_26_Final_Research"
)

DATA = ROOT / "02_CSV_Data"
FINDINGS = ROOT / "06_Research_Findings"

GROUP_OUTPUT = DATA / "task26_7B_repeatability_by_group.csv"
WORKLOAD_OUTPUT = DATA / "task26_7B_repeatability_by_workload.csv"
REPORT_OUTPUT = FINDINGS / "task26_7B_repeatability_report.json"

SPECS = [
    {
        "name": "EKF",
        "file": "task26_3B_ekf_cpu_timing.csv",
        "column": "elapsed_ms",
        "keys": ["workload"],
        "expected": 200,
        "unit": "Complete EKF replay"
    },
    {
        "name": "Camera",
        "file": "task26_4B_camera_cpu_timing.csv",
        "column": "elapsed_ms",
        "keys": ["weather", "mode"],
        "expected": 600,
        "unit": "Camera preprocessing execution"
    },
    {
        "name": "LiDAR",
        "file": "task26_4D_lidar_cpu_timing.csv",
        "column": "elapsed_ms",
        "keys": ["frame", "stage"],
        "expected": 2650,
        "unit": "Frame-specific LiDAR stage"
    },
    {
        "name": "Radar",
        "file": "task26_4G_radar_cpu_timing.csv",
        "column": "batch_elapsed_ms",
        "keys": ["pair_id", "frame", "returns_processed"],
        "expected": 1200,
        "unit": "Radar batch, not one return"
    },
    {
        "name": "YOLO11s",
        "file": "task26_4J_yolo_cpu_timing.csv",
        "column": "elapsed_ms",
        "keys": ["frame"],
        "expected": 50,
        "unit": "One CPU inference"
    },
    {
        "name": "Partial_LiDAR_Radar",
        "file": "task26_5C_integrated_cpu_timing.csv",
        "column": "total_ms",
        "keys": ["frame"],
        "expected": 1325,
        "unit": "LiDAR filter + cluster + Radar validation"
    }
]

EXPECTED_GROUPS = {
    "EKF": 2,
    "Camera": 6,
    "LiDAR": 106,
    "Radar": 12,
    "YOLO11s": 5,
    "Partial_LiDAR_Radar": 53
}

def percentile(values, p):
    """Linear-interpolated descriptive sample percentile."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Empty sample")
    position = (len(ordered) - 1) * p / 100
    lo = math.floor(position)
    hi = math.ceil(position)
    weight = position - lo
    return (
        ordered[lo] * (1 - weight)
        + ordered[hi] * weight
    )

def read_data(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as stream:
        return list(csv.DictReader(stream))

def compute_stats(values):
    if len(values) < 2:
        raise RuntimeError("Need at least two repetitions")

    avg = mean(values)
    sd = stdev(values)

    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = sum(
        (v < lower or v > upper) for v in values
    )

    return {
        "n": len(values),
        "mean_ms": avg,
        "median_ms": median(values),
        "std_ms": sd,
        "cv_percent": 100 * sd / avg if avg else 0,
        "p95_ms": percentile(values, 95),
        "p99_ms": percentile(values, 99),
        "min_ms": min(values),
        "max_ms": max(values),
        "tukey_outliers": outliers,
        "tukey_outlier_percent":
            100 * outliers / len(values),
        "tail_ratio_p99_to_median":
            percentile(values, 99) / median(values),
        "p99_sample_warning": (
            "SMALL_SAMPLE" if len(values) < 100
            else "DESCRIPTIVE_ONLY"
        )
    }

def write_csv(path, rows):
    if not rows:
        raise RuntimeError("No results to write")

    with path.open(
        "x", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

def main():
    outputs = [
        GROUP_OUTPUT, WORKLOAD_OUTPUT, REPORT_OUTPUT
    ]

    for path in outputs:
        if path.exists():
            raise FileExistsError(
                f"Existing result preserved: {path}"
            )

    group_results = []
    workload_results = []
    total_rows = 0

    print("=== TASK 26.7B CPU TIMING REPEATABILITY ===")

    for spec in SPECS:
        rows = read_data(DATA / spec["file"])

        if len(rows) != spec["expected"]:
            raise RuntimeError(
                f"{spec['name']}: expected "
                f"{spec['expected']} rows, got {len(rows)}"
            )

        total_rows += len(rows)

        groups = defaultdict(list)

        for row in rows:
            key = tuple(row[k] for k in spec["keys"])
            value = float(row[spec["column"]])

            if not math.isfinite(value) or value <= 0:
                raise RuntimeError(
                    f"Invalid timing: {spec['name']}"
                )

            groups[key].append(value)

        if len(groups) != EXPECTED_GROUPS[spec["name"]]:
            raise RuntimeError(
                f"Unexpected group count: {spec['name']}"
            )

        spec_group_results = []

        for key in sorted(groups):
            values = groups[key]
            stats = compute_stats(values)

            result = {
                "workload": spec["name"],
                "group": "|".join(key),
                "timing_unit": spec["unit"],
                **stats
            }

            group_results.append(result)
            spec_group_results.append(result)

        group_medians = [
            r["median_ms"] for r in spec_group_results
        ]

        group_p99 = [
            r["p99_ms"] for r in spec_group_results
        ]

        group_cv = [
            r["cv_percent"] for r in spec_group_results
        ]

        group_max = [
            r["max_ms"] for r in spec_group_results
        ]

        total_outliers = sum(
            r["tukey_outliers"]
            for r in spec_group_results
        )

        workload_result = {
            "workload": spec["name"],
            "timing_unit": spec["unit"],
            "groups": len(spec_group_results),
            "timing_rows": len(rows),
            "median_of_group_medians_ms":
                median(group_medians),
            "max_group_p99_ms": max(group_p99),
            "median_group_cv_percent":
                median(group_cv),
            "max_group_cv_percent": max(group_cv),
            "maximum_observed_ms": max(group_max),
            "tukey_outliers_within_groups":
                total_outliers,
            "outlier_rate_percent":
                100 * total_outliers / len(rows),
            "minimum_repeats_per_group":
                min(r["n"] for r in spec_group_results),
            "maximum_repeats_per_group":
                max(r["n"] for r in spec_group_results)
        }

        workload_results.append(workload_result)

        print()
        print("WORKLOAD:", spec["name"])
        print("TIMING_UNIT:", spec["unit"])
        print("GROUPS:", len(groups))
        print("TIMING_ROWS:", len(rows))
        print(
            "MEDIAN_OF_GROUP_MEDIANS_MS:",
            f"{median(group_medians):.6f}"
        )
        print(
            "MAX_GROUP_P99_MS:",
            f"{max(group_p99):.6f}"
        )
        print(
            "MEDIAN_GROUP_CV_PERCENT:",
            f"{median(group_cv):.3f}"
        )
        print(
            "MAX_OBSERVED_MS:",
            f"{max(group_max):.6f}"
        )
        print(
            "WITHIN_GROUP_TUKEY_OUTLIERS:",
            total_outliers
        )

    if total_rows != 6025 or len(group_results) != 184:
        raise RuntimeError("Benchmark coverage check failed")

    DATA.mkdir(parents=True, exist_ok=True)
    FINDINGS.mkdir(parents=True, exist_ok=True)

    write_csv(GROUP_OUTPUT, group_results)
    write_csv(WORKLOAD_OUTPUT, workload_results)

    report = {
        "task": "26.7B",
        "timing_rows": total_rows,
        "measurement_groups": len(group_results),
        "workload_summaries": workload_results,
        "statistical_method": {
            "percentiles": (
                "Linear interpolation at (n-1)*p/100"
            ),
            "standard_deviation": "Sample standard deviation",
            "cv": "100 * sample standard deviation / mean",
            "outliers": (
                "Within-group Tukey 1.5*IQR fences"
            ),
            "aggregation": (
                "Median of group medians; maximum of "
                "within-group descriptive p99 values"
            )
        },
        "limitations": [
            "Results reflect repeated runs of selected stored inputs.",
            "Different workloads have different timing units.",
            "A group p99 is not an end-to-end system p99.",
            "Ten YOLO repetitions are too few for robust p99.",
            "Twenty-five LiDAR/integrated repetitions provide limited tail evidence.",
            "Tukey outliers are descriptive and are not removed.",
            "No confidence bounds or certified WCET are established.",
            "Partial integrated timing excludes Camera, YOLO, fusion and I/O.",
            "No actual ARM-FPGA board power or energy was measured."
        ],
        "historical_benchmarks_modified": False
    }

    with REPORT_OUTPUT.open(
        "x", encoding="utf-8"
    ) as stream:
        json.dump(report, stream, indent=2)

    print()
    print("TOTAL_TIMING_ROWS:", total_rows)
    print("TOTAL_MEASUREMENT_GROUPS:", len(group_results))
    print("BENCHMARKS_REEXECUTED: NO")
    print("HISTORICAL_FILES_MODIFIED: NO")
    print("HARD_REAL_TIME_GUARANTEE: NO")
    print("TASK26_7B_REPEATABILITY_ANALYSIS_PASS")
    print("GROUP_CSV:", GROUP_OUTPUT)
    print("WORKLOAD_CSV:", WORKLOAD_OUTPUT)
    print("REPORT:", REPORT_OUTPUT)

if __name__ == "__main__":
    main()
