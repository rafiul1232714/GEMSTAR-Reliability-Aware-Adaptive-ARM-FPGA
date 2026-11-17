import csv
import json
import math
import sys
from pathlib import Path
from itertools import product
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage

TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"

OUTPUT = TASK / "02_CSV_Data" / "task29_4C12D1_camera_break_even.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12D1_camera_break_even_report.json"

ARM_LATENCY_FACTORS = (1.0, 1.5, 2.0, 3.0)
ARM_POWER_W = (2.0, 4.0, 6.0, 8.0)
FPGA_POWER_W = (2.0, 3.0, 6.0, 12.0)
DMA_MULTIPLIERS = (0.5, 1.0, 2.0, 5.0)

DEADLINE_MS = 75.0

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def checked(value, name, allow_zero=False):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(name + " is nonfinite")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(name + " is invalid")
    return value

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing results preserved")

    timing = load(TIMING)
    power = load(POWER)

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
        or power["actual_fpga_executed"] is not False
    ):
        raise RuntimeError("Hardware provenance gate failed")

    models = stage.build_models(timing)

    camera = models["camera"]

    cpu_ref_ms = checked(camera["cpu_ms"], "Camera CPU reference")
    dma_ref_ms = checked(timing["camera_dma_ms"], "DMA reference")
    fpga_total_ref_ms = checked(
        camera["offload_ms"], "FPGA modeled latency"
    )

    fpga_compute_ms = checked(
        fpga_total_ref_ms - dma_ref_ms,
        "FPGA compute reference"
    )

    dma_power_w = checked(
        power["dma_host_active_w"],
        "DMA host active power"
    )

    results = []

    for arm_factor, arm_w, fpga_w, dma_factor in product(
        ARM_LATENCY_FACTORS,
        ARM_POWER_W,
        FPGA_POWER_W,
        DMA_MULTIPLIERS
    ):
        arm_ms = cpu_ref_ms * arm_factor
        arm_energy = arm_w * arm_ms

        transfer_ms = dma_ref_ms * dma_factor
        fpga_ms = fpga_compute_ms + transfer_ms

        fpga_energy = (
            fpga_w * fpga_compute_ms
            + dma_power_w * transfer_ms
        )

        arm_deadline_met = arm_ms <= DEADLINE_MS
        fpga_deadline_met = fpga_ms <= DEADLINE_MS

        # Compare energy without conflating it with timing.
        difference = arm_energy - fpga_energy

        if abs(difference) <= 1e-9:
            energy_winner = "ENERGY_EQUAL"
        elif difference > 0:
            energy_winner = "FPGA_LOWER_ENERGY"
        else:
            energy_winner = "ARM_LOWER_ENERGY"

        if arm_deadline_met and fpga_deadline_met:
            feasible = (
                "ARM" if arm_energy <= fpga_energy
                else "FPGA"
            )
        elif arm_deadline_met:
            feasible = "ARM"
        elif fpga_deadline_met:
            feasible = "FPGA"
        else:
            feasible = "NO_DEADLINE_FEASIBLE_OPTION"

        # ARM active-power threshold at energy equality.
        break_even_arm_power_w = fpga_energy / arm_ms

        # Maximum DMA duration for FPGA to beat ARM energy.
        dma_limit_ms = (
            arm_energy - fpga_w * fpga_compute_ms
        ) / dma_power_w

        results.append({
            "arm_latency_factor": arm_factor,
            "arm_active_power_w": arm_w,
            "fpga_compute_power_w": fpga_w,
            "dma_multiplier": dma_factor,
            "arm_processing_ms": round(arm_ms, 6),
            "fpga_compute_ms": round(fpga_compute_ms, 6),
            "fpga_transfer_ms": round(transfer_ms, 6),
            "fpga_total_ms": round(fpga_ms, 6),
            "arm_energy_mj": round(arm_energy, 6),
            "fpga_energy_mj": round(fpga_energy, 6),
            "fpga_saving_vs_arm_percent": round(
                100.0 * difference / arm_energy, 6
            ),
            "break_even_arm_power_w": round(
                break_even_arm_power_w, 6
            ),
            "break_even_dma_duration_ms": round(
                dma_limit_ms, 6
            ),
            "arm_deadline_met": arm_deadline_met,
            "fpga_deadline_met": fpga_deadline_met,
            "energy_winner": energy_winner,
            "deadline_feasible_choice": feasible,
            "hardware_measured": False,
            "quality_verified": False,
        })

    if len(results) != 256:
        raise AssertionError("Expected 256 sensitivity cases")

    energy_counts = Counter(
        r["energy_winner"] for r in results
    )
    feasible_counts = Counter(
        r["deadline_feasible_choice"] for r in results
    )

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(results[0])
        )
        writer.writeheader()
        writer.writerows(results)

    report = {
        "task": "29.4C.12D.1",
        "status": "PASS",
        "analysis": "CAMERA_ARM_FPGA_ENERGY_BREAK_EVEN",
        "sensitivity_cases": len(results),
        "camera_cpu_reference_ms": cpu_ref_ms,
        "camera_fpga_compute_reference_ms": fpga_compute_ms,
        "camera_dma_reference_ms": dma_ref_ms,
        "assumed_dma_host_power_w": dma_power_w,
        "deadline_ms": DEADLINE_MS,
        "energy_winner_counts": dict(energy_counts),
        "deadline_feasible_counts": dict(feasible_counts),
        "model": "ILLUSTRATIVE_ACTIVE_PROCESSING_ONLY",
        "arm_performance": "HYPOTHETICAL_SCALING",
        "fpga_ai_implementation": "NOT_VERIFIED",
        "dma_costs": "HYPOTHETICAL",
        "queue_model_executed": False,
        "whole_board_energy_measured": False,
        "perception_quality_verified": False,
        "previous_results_modified": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== CAMERA BREAK-EVEN RESULTS ===")
    print("CAMERA_CPU_REFERENCE_MS:", round(cpu_ref_ms, 6))
    print("CAMERA_FPGA_COMPUTE_MODEL_MS:",
          round(fpga_compute_ms, 6))
    print("CAMERA_DMA_REFERENCE_MS:",
          round(dma_ref_ms, 6))
    print("SENSITIVITY_CASES:", len(results))

    for name in (
        "FPGA_LOWER_ENERGY",
        "ARM_LOWER_ENERGY",
        "ENERGY_EQUAL"
    ):
        print(name + ":", energy_counts[name])

    print("=== DEADLINE-FEASIBLE CHOICES ===")
    for name in (
        "ARM",
        "FPGA",
        "NO_DEADLINE_FEASIBLE_OPTION"
    ):
        print(name + ":", feasible_counts[name])

    print("REAL_HARDWARE_MEASUREMENTS: NONE")
    print("PERCEPTION_QUALITY_VERIFIED: NO")
    print("PREVIOUS_RESEARCH_MODIFIED: NO")
    print("TASK 29.4C.12D.1: PASS")

if __name__ == "__main__":
    main()
