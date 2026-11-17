import csv
import json
import math
from pathlib import Path
from itertools import product
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

D1 = TASK / "02_CSV_Data" / "task29_4C12D1_camera_break_even.csv"
D2 = TASK / "06_Research_Findings" / "task29_4C12D2_dma_report.json"

OUT = TASK / "02_CSV_Data" / "task29_4C12D3_workload_break_even.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12D3_workload_report.json"

WORKLOADS = (0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)
ARM_POWERS = (2.0, 4.0, 6.0)
FPGA_POWERS = (3.0, 6.0, 12.0)
DMA_MODELS = ("FIXED_TRANSFER", "PROPORTIONAL_TRANSFER")

DEADLINE_MS = 75.0
DMA_POWER_W = 6.0

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def choose(arm_e, fpga_e, arm_t, fpga_t):
    arm_ok = arm_t <= DEADLINE_MS
    fpga_ok = fpga_t <= DEADLINE_MS

    if arm_ok and fpga_ok:
        return "ARM" if arm_e <= fpga_e else "FPGA"
    if arm_ok:
        return "ARM"
    if fpga_ok:
        return "FPGA"
    return "NO_FEASIBLE_PLACEMENT"

def main():
    for path in (OUT, REPORT):
        if path.exists():
            raise FileExistsError("Previous research preserved: " + str(path))

    reference = read_csv(D1)
    previous = read_json(D2)

    if len(reference) != 256:
        raise RuntimeError("Task D1 reference count mismatch")

    if previous["status"] != "PASS" or previous["cases"] != 256:
        raise RuntimeError("Task D2 not verified")

    if previous["arm_hardware_measured"] is not False:
        raise RuntimeError("Unexpected ARM measurement claim")

    if previous["fpga_hardware_measured"] is not False:
        raise RuntimeError("Unexpected FPGA measurement claim")

    if abs(float(previous["dma_host_power_w_assumed"])
           - DMA_POWER_W) > 1e-9:
        raise RuntimeError("DMA power assumption changed")

    # Read reference timing from the recorded D1 modeling ledger.
    cpu_ref = float(reference[0]["arm_processing_ms"])
    arm_factor = float(reference[0]["arm_latency_factor"])
    cpu_ref /= arm_factor

    fpga_compute_ref = float(reference[0]["fpga_compute_ms"])

    dma_ref = (
        float(reference[0]["fpga_transfer_ms"])
        / float(reference[0]["dma_multiplier"])
    )

    if not all(
        math.isfinite(x) and x > 0
        for x in (cpu_ref, fpga_compute_ref, dma_ref)
    ):
        raise RuntimeError("Invalid reference timing")

    # Check consistent reference values across all D1 rows.
    for r in reference:
        expected_cpu = (
            float(r["arm_processing_ms"])
            / float(r["arm_latency_factor"])
        )
        expected_dma = (
            float(r["fpga_transfer_ms"])
            / float(r["dma_multiplier"])
        )

        if abs(expected_cpu - cpu_ref) > 1e-5:
            raise RuntimeError("Camera CPU reference inconsistent")

        if abs(float(r["fpga_compute_ms"])
               - fpga_compute_ref) > 1e-5:
            raise RuntimeError("FPGA compute reference inconsistent")

        if abs(expected_dma - dma_ref) > 1e-5:
            raise RuntimeError("DMA reference inconsistent")

    rows = []

    for factor, arm_w, fpga_w, dma_model in product(
        WORKLOADS,
        ARM_POWERS,
        FPGA_POWERS,
        DMA_MODELS
    ):
        # Illustrative workload scaling, NOT verified neural
        # network inference scaling on actual hardware.
        arm_ms = cpu_ref * factor
        fpga_compute_ms = fpga_compute_ref * factor

        if dma_model == "FIXED_TRANSFER":
            dma_ms = dma_ref
        else:
            dma_ms = dma_ref * factor

        fpga_total_ms = fpga_compute_ms + dma_ms

        arm_energy = arm_w * arm_ms
        fpga_energy = (
            fpga_w * fpga_compute_ms
            + DMA_POWER_W * dma_ms
        )

        if not all(
            math.isfinite(x) and x >= 0
            for x in (
                arm_ms, fpga_total_ms,
                arm_energy, fpga_energy
            )
        ):
            raise RuntimeError("Invalid modeled value")

        if fpga_energy < arm_energy:
            energy_winner = "FPGA"
        elif arm_energy < fpga_energy:
            energy_winner = "ARM"
        else:
            energy_winner = "TIE"

        selected = choose(
            arm_energy, fpga_energy,
            arm_ms, fpga_total_ms
        )

        # Under fixed DMA cost, the energy difference is:
        # x*(ARM_W*CPU_REF - FPGA_W*FPGA_REF)
        # minus DMA_POWER_W*DMA_REF.
        advantage_per_factor = (
            arm_w * cpu_ref
            - fpga_w * fpga_compute_ref
        )

        if dma_model == "FIXED_TRANSFER":
            if advantage_per_factor > 0:
                break_even_factor = (
                    DMA_POWER_W * dma_ref
                    / advantage_per_factor
                )
            else:
                break_even_factor = None
        else:
            # Both computation and DMA scale with workload.
            # There is no workload-dependent crossover
            # under this simplified linear model.
            break_even_factor = None

        rows.append({
            "workload_factor": factor,
            "arm_power_w": arm_w,
            "fpga_power_w": fpga_w,
            "dma_model": dma_model,
            "arm_latency_ms": round(arm_ms, 6),
            "fpga_latency_ms": round(fpga_total_ms, 6),
            "dma_latency_ms": round(dma_ms, 6),
            "arm_energy_mj": round(arm_energy, 6),
            "fpga_energy_mj": round(fpga_energy, 6),
            "fpga_energy_saving_percent": round(
                100 * (arm_energy - fpga_energy)
                / arm_energy, 6
            ),
            "energy_winner": energy_winner,
            "deadline_feasible_choice": selected,
            "fixed_dma_break_even_factor": (
                round(break_even_factor, 6)
                if break_even_factor is not None else ""
            ),
            "hardware_measured": False,
            "quality_verified": False,
        })

    if len(rows) != 126:
        raise AssertionError("Expected 126 sensitivity rows")

    energy_counts = Counter(
        r["energy_winner"] for r in rows
    )
    choice_counts = Counter(
        r["deadline_feasible_choice"] for r in rows
    )

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "task": "29.4C.12D.3",
        "status": "PASS",
        "cases": len(rows),
        "workload_levels": len(WORKLOADS),
        "power_combinations": (
            len(ARM_POWERS) * len(FPGA_POWERS)
        ),
        "dma_models": len(DMA_MODELS),
        "camera_cpu_reference_ms": cpu_ref,
        "camera_fpga_compute_model_ms": fpga_compute_ref,
        "dma_reference_ms": dma_ref,
        "deadline_ms": DEADLINE_MS,
        "energy_winner_counts": dict(energy_counts),
        "deadline_feasible_choice_counts": dict(choice_counts),
        "workload_scaling": "SYNTHETIC_LINEAR_PROXY",
        "ai_model_switching_tested": False,
        "sensor_quality_verified": False,
        "arm_hardware_measured": False,
        "fpga_hardware_measured": False,
        "whole_board_energy_measured": False,
        "queue_simulation_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== CAMERA WORKLOAD BREAK-EVEN ===")
    print("CPU_REFERENCE_MS:", round(cpu_ref, 6))
    print("FPGA_COMPUTE_MODEL_MS:",
          round(fpga_compute_ref, 6))
    print("DMA_REFERENCE_MS:", round(dma_ref, 6))
    print("SENSITIVITY_CASES:", len(rows))

    print("=== ENERGY WINNERS ===")
    for name in ("ARM", "FPGA", "TIE"):
        print(name + ":", energy_counts[name])

    print("=== DEADLINE-FEASIBLE CHOICES ===")
    for name in (
        "ARM", "FPGA", "NO_FEASIBLE_PLACEMENT"
    ):
        print(name + ":", choice_counts[name])

    print("AI_MODEL_SWITCHING: NOT TESTED")
    print("PERCEPTION_QUALITY: NOT VERIFIED")
    print("HARDWARE_MEASUREMENTS: NONE")
    print("TASK 29.4C.12D.3: PASS")

if __name__ == "__main__":
    main()
