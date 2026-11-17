import csv
import json
import math
from pathlib import Path
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

SOURCE = TASK / "02_CSV_Data" / "task29_4C12D1_camera_break_even.csv"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"
OUTPUT = TASK / "02_CSV_Data" / "task29_4C12D2_dma_limits.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12D2_dma_report.json"

def number(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("Nonfinite numeric input")
    return x

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing research preserved")

    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        source = list(csv.DictReader(f))

    if len(source) != 256:
        raise RuntimeError("Expected 256 verified cases")

    power = json.loads(
        POWER.read_text(encoding="utf-8-sig")
    )

    if power["actual_power_measured"] is not False:
        raise RuntimeError("Unexpected hardware claim")

    dma_power = number(power["dma_host_active_w"])
    if dma_power <= 0:
        raise RuntimeError("Invalid DMA power")

    rows = []

    for index, r in enumerate(source, start=1):
        arm_ms = number(r["arm_processing_ms"])
        arm_energy = number(r["arm_energy_mj"])

        fpga_compute_ms = number(r["fpga_compute_ms"])
        fpga_power = number(r["fpga_compute_power_w"])

        transfer_ms = number(r["fpga_transfer_ms"])
        deadline_ms = 75.0

        fpga_compute_energy = fpga_power * fpga_compute_ms

        # Transfer duration at which ARM and FPGA energy
        # would become equal, without clipping negative values.
        energy_limit_ms = (
            arm_energy - fpga_compute_energy
        ) / dma_power

        # Independent transfer-time deadline limit.
        timing_limit_ms = deadline_ms - fpga_compute_ms

        if energy_limit_ms <= 0:
            status = "FPGA_COMPUTE_ALREADY_TOO_EXPENSIVE"
            feasible_limit = 0.0
        elif timing_limit_ms <= 0:
            status = "FPGA_COMPUTE_ALREADY_TOO_SLOW"
            feasible_limit = 0.0
        else:
            feasible_limit = min(
                energy_limit_ms, timing_limit_ms
            )

            if energy_limit_ms < timing_limit_ms:
                status = "ENERGY_LIMIT_DOMINATES"
            elif timing_limit_ms < energy_limit_ms:
                status = "DEADLINE_LIMIT_DOMINATES"
            else:
                status = "BOTH_LIMITS_EQUAL"

        fpga_energy = (
            fpga_compute_energy
            + dma_power * transfer_ms
        )
        fpga_latency = fpga_compute_ms + transfer_ms

        energy_ok = fpga_energy < arm_energy
        deadline_ok = fpga_latency <= deadline_ms

        if energy_ok and deadline_ok:
            current_result = "FPGA_ENERGY_AND_DEADLINE_PASS"
        elif not energy_ok and deadline_ok:
            current_result = "FPGA_ENERGY_FAIL"
        elif energy_ok and not deadline_ok:
            current_result = "FPGA_DEADLINE_FAIL"
        else:
            current_result = "FPGA_BOTH_FAIL"

        # Verify original energy classification.
        expected_fpga = r["energy_winner"] == "FPGA_LOWER_ENERGY"
        if expected_fpga != energy_ok:
            # D1 saved rounded measurements; permit rounding
            # only when the energy difference is negligible.
            if abs(fpga_energy - arm_energy) > 0.0001:
                raise AssertionError(
                    "D1 energy classification mismatch"
                )

        rows.append({
            "case": index,
            "arm_latency_factor": r["arm_latency_factor"],
            "arm_power_w": r["arm_active_power_w"],
            "fpga_power_w": r["fpga_compute_power_w"],
            "dma_multiplier": r["dma_multiplier"],
            "arm_energy_mj": round(arm_energy, 6),
            "fpga_compute_energy_mj": round(
                fpga_compute_energy, 6
            ),
            "energy_break_even_dma_ms": round(
                energy_limit_ms, 6
            ),
            "deadline_max_dma_ms": round(
                timing_limit_ms, 6
            ),
            "strict_energy_and_deadline_dma_limit_ms":
                round(feasible_limit, 6),
            "tested_dma_ms": transfer_ms,
            "tested_fpga_energy_mj": round(
                fpga_energy, 6
            ),
            "energy_condition_pass": energy_ok,
            "deadline_condition_pass": deadline_ok,
            "limiting_condition": status,
            "tested_result": current_result,
            "hardware_measured": False,
        })

    counts = Counter(
        r["limiting_condition"] for r in rows
    )

    tested = Counter(
        r["tested_result"] for r in rows
    )

    if len(rows) != 256:
        raise AssertionError("DMA analysis count mismatch")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "task": "29.4C.12D.2",
        "status": "PASS",
        "cases": len(rows),
        "limiting_condition_counts": dict(counts),
        "tested_result_counts": dict(tested),
        "dma_host_power_w_assumed": dma_power,
        "deadline_ms": 75.0,
        "arm_hardware_measured": False,
        "fpga_hardware_measured": False,
        "power_model": "ACTIVE_ONLY_HYPOTHETICAL",
        "includes_queue_delay": False,
        "quality_verified": False,
        "note": (
            "Positive DMA limits are mathematical thresholds. "
            "Exact energy equality is not an energy saving. "
            "Zero feasible limit means no positive transfer "
            "duration satisfies both modeled constraints."
        ),
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== DMA BREAK-EVEN RESULTS ===")
    print("CASES:", len(rows))
    print("DMA_HOST_POWER_ASSUMED_W:", dma_power)

    for name in (
        "ENERGY_LIMIT_DOMINATES",
        "DEADLINE_LIMIT_DOMINATES",
        "BOTH_LIMITS_EQUAL",
        "FPGA_COMPUTE_ALREADY_TOO_EXPENSIVE",
        "FPGA_COMPUTE_ALREADY_TOO_SLOW",
    ):
        print(name + ":", counts[name])

    print("=== TESTED DMA CONFIGURATIONS ===")
    for name in (
        "FPGA_ENERGY_AND_DEADLINE_PASS",
        "FPGA_ENERGY_FAIL",
        "FPGA_DEADLINE_FAIL",
        "FPGA_BOTH_FAIL",
    ):
        print(name + ":", tested[name])

    print("HARDWARE_MEASUREMENTS: NONE")
    print("QUEUE_DELAY_INCLUDED: NO")
    print("TASK 29.4C.12D.2: PASS")

if __name__ == "__main__":
    main()
