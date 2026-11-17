import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage

CONFIG = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"
SOURCE = TASK / "02_CSV_Data" / "task29_4C5_queue_decisions.csv"
OUTPUT = TASK / "02_CSV_Data" / "task29_4C6_energy_estimates.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C6_energy_report.json"

CPU = "CPU_ONLY"
CAM = "CPU_CAMERA_ACCELERATOR"
LIDAR = "CPU_LIDAR_ACCELERATOR"
BOTH = "CPU_COMBINED_ACCELERATORS"

RESOURCES = {
    CPU: frozenset(),
    CAM: frozenset(("camera",)),
    LIDAR: frozenset(("lidar",)),
    BOTH: frozenset(("camera", "lidar")),
}

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def positive(x):
    return (
        type(x) in (int, float)
        and math.isfinite(x)
        and x > 0
    )

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing energy outputs preserved")

    timing_config = json.loads(
        CONFIG.read_text(encoding="utf-8-sig")
    )
    power = json.loads(
        POWER.read_text(encoding="utf-8-sig")
    )

    for key in (
        "cpu_active_w",
        "fpga_camera_active_w",
        "fpga_lidar_active_w",
        "dma_host_active_w",
    ):
        if not positive(power[key]):
            raise ValueError("Invalid illustrative power: " + key)

    if not math.isfinite(power["switch_energy_mj_per_resource"]):
        raise ValueError("Invalid switching energy")

    if power["switch_energy_mj_per_resource"] < 0:
        raise ValueError("Negative switching energy")

    if (
        power["actual_power_measured"] is not False
        or power["actual_fpga_executed"] is not False
        or power["valid_perception_results_verified"] is not False
    ):
        raise RuntimeError("Energy evidence gate failed")

    models = stage.build_models(timing_config)
    camera = models["camera"]
    lidar = models["lidar"]

    # These are model components, not independently measured
    # FPGA/DMA timings.
    cam_dma = timing_config["camera_dma_ms"]
    lidar_dma = timing_config["lidar_dma_ms"]

    cam_fpga = camera["offload_ms"] - cam_dma
    lidar_non_dma = lidar["offload_ms"] - lidar_dma

    # The p99 of a sum is not generally the sum of p99s.
    # Split the modeled LiDAR offload budget using a bounded
    # CPU Radar-stage reference; label this as a surrogate.
    radar_cpu = min(
        lidar["radar_cpu_p99_ms"],
        lidar_non_dma
    )
    lidar_fpga = lidar_non_dma - radar_cpu

    if min(cam_fpga, lidar_fpga, radar_cpu) < 0:
        raise RuntimeError("Invalid stage decomposition")

    original = read_csv(SOURCE)
    if len(original) != 38:
        raise RuntimeError("Expected 38 queue decisions")

    result_rows = []
    by_policy = defaultdict(list)
    last_action = {}

    for row in original:
        policy = row["policy"]
        action = row["action"]

        if policy not in ("CPU_ONLY", "ADAPTIVE_DEADLINE"):
            raise RuntimeError("Unknown comparison policy")

        previous = last_action.get(policy, CPU)

        if action == "NO_EXECUTION":
            if row["result_permission"] != "WITHHOLD_VALID_RESULT":
                raise RuntimeError("Unsafe hold permission")

            result_rows.append({
                "policy": policy,
                "event": row["event"],
                "action": action,
                "health_mode": row["health_mode"],
                "deadline_met": "",
                "cpu_active_ms": 0,
                "fpga_camera_ms": 0,
                "fpga_lidar_ms": 0,
                "dma_ms": 0,
                "switching_ms": 0,
                "modeled_active_energy_mj": 0,
                "energy_scope": "NO_EXECUTION_ONLY",
                "quality_verified": False,
                "power_measured": False,
            })
            continue

        if action not in RESOURCES:
            raise RuntimeError("Unknown scheduling action")

        active = RESOURCES[action]
        changed = active ^ RESOURCES[previous]

        expected_switch = sum(
            timing_config[name + "_switch_ms"]
            for name in changed
        )

        logged_switch = float(row["switch_ms"])

        if abs(expected_switch - logged_switch) > 0.00001:
            raise AssertionError(
                "Switching latency mismatch for " + row["event"]
            )

        cpu_ms = 0.0
        fpga_cam_ms = 0.0
        fpga_lidar_ms = 0.0
        dma_ms = 0.0

        if "camera" in active:
            fpga_cam_ms = cam_fpga
            dma_ms += cam_dma
        else:
            cpu_ms += camera["cpu_ms"]

        if "lidar" in active:
            fpga_lidar_ms = lidar_fpga
            cpu_ms += radar_cpu
            dma_ms += lidar_dma
        else:
            cpu_ms += lidar["cpu_ms"]

        expected_service = (
            cpu_ms + fpga_cam_ms + fpga_lidar_ms
            + dma_ms + expected_switch
        )

        logged_service = float(row["service_ms"])

        if abs(expected_service - logged_service) > 0.00002:
            raise AssertionError(
                "Service-time decomposition mismatch: "
                + row["event"]
            )

        energy = (
            power["cpu_active_w"] * cpu_ms
            + power["fpga_camera_active_w"] * fpga_cam_ms
            + power["fpga_lidar_active_w"] * fpga_lidar_ms
            + power["dma_host_active_w"] * dma_ms
            + power["switch_energy_mj_per_resource"] * len(changed)
        )

        if not math.isfinite(energy) or energy <= 0:
            raise RuntimeError("Invalid modeled energy")

        result = {
            "policy": policy,
            "event": row["event"],
            "action": action,
            "health_mode": row["health_mode"],
            "deadline_met": row["deadline_met"],
            "cpu_active_ms": round(cpu_ms, 6),
            "fpga_camera_ms": round(fpga_cam_ms, 6),
            "fpga_lidar_ms": round(fpga_lidar_ms, 6),
            "dma_ms": round(dma_ms, 6),
            "switching_ms": round(expected_switch, 6),
            "modeled_active_energy_mj": round(energy, 6),
            "energy_scope": "ILLUSTRATIVE_ACTIVE_PROCESSING_ONLY",
            "quality_verified": False,
            "power_measured": False,
        }

        result_rows.append(result)
        by_policy[policy].append(result)
        last_action[policy] = action

    if len(result_rows) != 38:
        raise RuntimeError("Missing energy estimates")

    summary = {}

    for policy, rows in by_policy.items():
        if len(rows) != 18:
            raise RuntimeError("Expected 18 executed jobs")

        energy = sum(
            r["modeled_active_energy_mj"] for r in rows
        )

        summary[policy] = {
            "processed_jobs": len(rows),
            "estimated_active_energy_mj": round(energy, 6),
            "estimated_active_energy_per_processed_job_mj": round(
                energy / len(rows), 6
            ),
            "verified_valid_results": None,
            "energy_per_valid_result_mj": None,
        }

    baseline = summary["CPU_ONLY"]["estimated_active_energy_mj"]
    adaptive = summary["ADAPTIVE_DEADLINE"]["estimated_active_energy_mj"]

    report = {
        "task": "29.4C.6",
        "status": "PASS",
        "decisions_replayed": len(result_rows),
        "summary": summary,
        "modeled_active_energy_change_percent": round(
            (adaptive / baseline - 1.0) * 100, 3
        ),
        "cpu_timing_origin": "RECORDED_WORKSTATION",
        "fpga_dma_power_origin": "ILLUSTRATIVE_ASSUMPTIONS",
        "stage_energy_decomposition": "UNCALIBRATED_SURROGATE",
        "idle_and_system_power_included": False,
        "validated_perception_quality": False,
        "energy_per_valid_result_available": False,
        "scheduler_optimizes_energy": False,
        "hardware_energy_measured": False,
    }

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(result_rows[0])
        )
        writer.writeheader()
        writer.writerows(result_rows)

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("DECISIONS_ANALYZED:", len(result_rows))
    print("CPU_ONLY_MODELED_ACTIVE_MJ:", round(baseline, 3))
    print("ADAPTIVE_MODELED_ACTIVE_MJ:", round(adaptive, 3))
    print(
        "MODELED_ACTIVE_ENERGY_CHANGE_PERCENT:",
        report["modeled_active_energy_change_percent"]
    )
    print("POWER_VALUES: HYPOTHETICAL")
    print("ENERGY_PER_VALID_RESULT: NOT AVAILABLE")
    print("ENERGY_OPTIMIZATION: NOT YET")
    print("TASK 29.4C.6: PASS")

if __name__ == "__main__":
    main()
