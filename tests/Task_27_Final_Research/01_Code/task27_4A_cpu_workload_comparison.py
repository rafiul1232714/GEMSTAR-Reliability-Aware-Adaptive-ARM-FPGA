from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
T26 = ROOT / "Task_26_Final_Research" / "02_CSV_Data"
T27 = ROOT / "Task_27_Final_Research"

OUT_SUMMARY = T27 / "02_CSV_Data" / "task27_4A_cpu_workload_summary.csv"
OUT_GROUPS = T27 / "02_CSV_Data" / "task27_4A_cpu_workload_groups.csv"
OUT_REPORT = T27 / "06_Research_Findings" / "task27_4A_cpu_workload_findings.txt"
OUT_MANIFEST = T27 / "06_Research_Findings" / "task27_4A_cpu_input_manifest.json"

SOURCES = [
    (
        "EKF", "task26_3B_ekf_cpu_timing.csv",
        200, "elapsed_ms", ("workload",),
        "Full tracking replay per run; not a per-frame latency"
    ),
    (
        "Camera", "task26_4B_camera_cpu_timing.csv",
        600, "elapsed_ms", ("weather", "mode"),
        "One image preprocessing run"
    ),
    (
        "LiDAR", "task26_4D_lidar_cpu_timing.csv",
        2650, "elapsed_ms", ("frame", "stage"),
        "Isolated filter or cluster stage per frame"
    ),
    (
        "Radar", "task26_4G_radar_cpu_timing.csv",
        1200, "batch_elapsed_ms", ("pair_id", "frame"),
        "One radar return batch; not one return"
    ),
    (
        "YOLO11s", "task26_4J_yolo_cpu_timing.csv",
        50, "elapsed_ms", ("frame",),
        "One image inference call"
    ),
    (
        "Partial_LiDAR_Radar",
        "task26_5C_integrated_cpu_timing.csv",
        1325, "total_ms", ("frame",),
        "Sequential LiDAR filtering + clustering + Radar batch"
    ),
]

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

def percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def save_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def main():
    print("=== TASK 27.4A: CPU WORKLOAD COMPARISON ===")

    outputs = (
        OUT_SUMMARY, OUT_GROUPS, OUT_REPORT, OUT_MANIFEST
    )

    for path in outputs:
        if path.exists():
            raise FileExistsError(
                f"Existing research output preserved: {path}"
            )

    summary = []
    group_rows = []
    manifest = []
    all_rows = 0

    for name, filename, expected, column, keys, scope in SOURCES:
        path = T26 / filename

        if not path.is_file():
            raise FileNotFoundError(path)

        data = read_csv(path)

        if len(data) != expected:
            raise RuntimeError(
                f"{name}: expected {expected} rows, got {len(data)}"
            )

        grouped = defaultdict(list)

        for row in data:
            if column not in row:
                raise RuntimeError(
                    f"{filename}: missing column {column}"
                )

            value = float(row[column])

            if not math.isfinite(value) or value <= 0:
                raise RuntimeError(
                    f"Invalid elapsed time in {filename}"
                )

            label = "|".join(
                f"{key}={row[key]}" for key in keys
            )

            grouped[label].append(value)

        medians = []

        for label, values in sorted(grouped.items()):
            median_ms = statistics.median(values)
            medians.append(median_ms)

            group_rows.append({
                "workload": name,
                "group": label,
                "measurements": len(values),
                "median_ms": median_ms,
                "mean_ms": statistics.mean(values),
                "p95_ms": percentile(values, 0.95),
                "p99_ms": percentile(values, 0.99),
                "min_ms": min(values),
                "max_ms": max(values),
                "timing_scope": scope
            })

        summary.append({
            "workload": name,
            "timing_rows": len(data),
            "groups": len(grouped),
            "median_of_group_medians_ms":
                statistics.median(medians),
            "minimum_group_median_ms": min(medians),
            "maximum_group_median_ms": max(medians),
            "maximum_group_p99_ms":
                max(
                    r["p99_ms"] for r in group_rows
                    if r["workload"] == name
                ),
            "timing_scope": scope,
            "directly_comparable_across_workloads": "NO"
        })

        manifest.append({
            "workload": name,
            "source": str(path),
            "sha256": sha256(path),
            "rows": len(data),
            "elapsed_column": column,
            "group_columns": list(keys),
            "timing_scope": scope
        })

        all_rows += len(data)

        print(
            f"WORKLOAD={name} "
            f"ROWS={len(data)} "
            f"GROUPS={len(grouped)} "
            f"MEDIAN_GROUP_MS="
            f"{statistics.median(medians):.6f}"
        )

    if all_rows != 6025:
        raise RuntimeError(
            f"Total timing rows mismatch: {all_rows}"
        )

    if len(summary) != 6:
        raise RuntimeError("Missing workload")

    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    save_csv(OUT_SUMMARY, summary)
    save_csv(OUT_GROUPS, group_rows)

    with OUT_MANIFEST.open("x", encoding="utf-8") as handle:
        json.dump({
            "task": "27.4A",
            "inputs": manifest,
            "total_timing_rows": all_rows,
            "group_p95_p99_method": "linear interpolation",
            "source_data_modified": False,
            "hardware_energy_measured": False,
            "comparison_warning":
                "Different workloads and input sizes have "
                "different timing units and boundaries."
        }, handle, indent=2)

    findings = [
        "GEMSTAR TASK 27.4A - CPU WORKLOAD COMPARISON",
        "============================================",
        f"Source timing datasets: {len(SOURCES)}",
        f"Original timing rows: {all_rows}",
        f"Distinct timing groups: {len(group_rows)}",
        "",
        "WORKLOAD SUMMARY:",
    ]

    for record in summary:
        findings.append(
            f"{record['workload']}: "
            f"{record['timing_rows']} observations, "
            f"{record['groups']} groups, "
            f"median of group medians "
            f"{record['median_of_group_medians_ms']:.6f} ms"
        )

    findings.extend([
        "",
        "SCIENTIFIC LIMITATIONS:",
        "Different benchmarks have different processing scopes.",
        "EKF time represents a replay, not one frame.",
        "Radar times represent batches, not individual returns.",
        "LiDAR filtering and clustering were timed separately.",
        "YOLO is not part of the partial integrated benchmark.",
        "The partial integrated workload excludes Camera and EKF.",
        "Per-group p99 is descriptive, not a latency guarantee.",
        "Archived timings originate from a development CPU.",
        "No ARM-FPGA execution or hardware energy measured.",
        "No final kernel-selection decision established.",
    ])

    with OUT_REPORT.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(findings) + "\n")

    print()
    print("SOURCE_FILES_VERIFIED:", len(SOURCES))
    print("TOTAL_TIMING_ROWS:", all_rows)
    print("TOTAL_GROUPS:", len(group_rows))
    print("SUMMARY_CSV:", OUT_SUMMARY)
    print("GROUP_CSV:", OUT_GROUPS)
    print("FINDINGS:", OUT_REPORT)
    print("INPUT_MANIFEST:", OUT_MANIFEST)
    print("ORIGINAL_DATA_MODIFIED: NO")
    print("TASK27_4A_CPU_WORKLOAD_COMPARISON_DONE")

if __name__ == "__main__":
    main()