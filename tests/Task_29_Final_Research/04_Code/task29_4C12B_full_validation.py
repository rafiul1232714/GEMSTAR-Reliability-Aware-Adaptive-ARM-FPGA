import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C11B_sensitivity_sweep as sweep
import task29_4C12A_arrival_aware_test as improved

SOURCE = TASK / "02_CSV_Data" / "task29_4C11A_architecture_scenarios.csv"
OLD = TASK / "02_CSV_Data" / "task29_4C11B_policy_summary.csv"

TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"

DECISIONS = TASK / "02_CSV_Data" / "task29_4C12B_decisions.csv"
SUMMARY = TASK / "02_CSV_Data" / "task29_4C12B_comparisons.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12B_validation_report.json"

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_csv(path, records):
    with path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

def main():
    for path in (DECISIONS, SUMMARY, REPORT):
        if path.exists():
            raise FileExistsError("Existing output preserved: " + str(path))

    scenarios = read_csv(SOURCE)
    historical = read_csv(OLD)

    timing = load_json(TIMING)
    power = load_json(POWER)

    if len(scenarios) != 16 or len(historical) != 64:
        raise RuntimeError("Historical evidence counts changed")

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
    ):
        raise RuntimeError("Hardware provenance gate failed")

    models = stage.build_models(timing)

    lookup = {
        (r["scenario"], r["policy"]): r
        for r in historical
    }

    if len(lookup) != 64:
        raise RuntimeError("Duplicate historical summaries")

    all_decisions = []
    comparisons = []

    for scenario in scenarios:
        sid = scenario["ScenarioID"]

        rows = improved.simulate(
            scenario, models, timing, power
        )

        if len(rows) != 19:
            raise RuntimeError("Expected 19 events in " + sid)

        jobs = [r for r in rows if r["action"] != "NO_EXECUTION"]
        holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

        if len(jobs) != 18 or len(holds) != 1:
            raise RuntimeError("Safety accounting mismatch: " + sid)

        misses = sum(r["deadline_met"] is False for r in jobs)
        modeled_energy = sum(
            float(r["active_energy_mj"])
            for r in jobs
        )

        fixed = lookup[(sid, "FIXED_AVAILABLE_ACCELERATORS")]
        original = lookup[(sid, "ADAPTIVE_ENERGY")]

        fixed_misses = int(fixed["deadline_misses"])
        fixed_energy = float(fixed["modeled_active_energy_mj"])

        if not math.isfinite(modeled_energy) or modeled_energy <= 0:
            raise RuntimeError("Invalid modeled energy: " + sid)

        if fixed_energy <= 0:
            raise RuntimeError("Invalid historical baseline")

        savings = 100.0 * (
            fixed_energy - modeled_energy
        ) / fixed_energy

        # Classify the result; do not hide failed comparisons.
        if misses > fixed_misses:
            finding = "DEADLINE_REGRESSION"
        elif savings > 0.0001:
            finding = "ADAPTIVE_ENERGY_BENEFIT"
        elif savings < -0.0001:
            finding = "FIXED_ENERGY_BENEFIT"
        else:
            finding = "ENERGY_EQUIVALENT"

        counts = Counter(r["action"] for r in jobs)

        comparisons.append({
            "scenario": sid,
            "profile": scenario["HardwareProfile"],
            "workload": scenario["WorkloadLevel"],
            "original_adaptive_misses":
                int(original["deadline_misses"]),
            "new_adaptive_misses": misses,
            "fixed_misses": fixed_misses,
            "new_energy_mj": round(modeled_energy, 6),
            "fixed_energy_mj": round(fixed_energy, 6),
            "saving_vs_fixed_percent": round(savings, 3),
            "cpu_decisions": counts[sweep.CPU],
            "camera_decisions": counts[sweep.CAM],
            "lidar_decisions": counts[sweep.LIDAR],
            "combined_decisions": counts[sweep.BOTH],
            "finding": finding,
        })

        for row in rows:
            all_decisions.append({
                "scenario": sid,
                "profile": scenario["HardwareProfile"],
                "workload": scenario["WorkloadLevel"],
                **row
            })

        print(
            sid,
            "MISSES:", misses,
            "FIXED:", fixed_misses,
            "ENERGY_SAVING_%:", round(savings, 3),
            "FINDING:", finding,
            flush=True
        )

    if len(all_decisions) != 304 or len(comparisons) != 16:
        raise RuntimeError("Validation record count mismatch")

    # Confirm results reproduce the two earlier tests.
    earlier = load_json(
        TASK / "06_Research_Findings"
        / "task29_4C12A_arrival_aware_report.json"
    )

    for prior in earlier["comparisons"]:
        current = next(
            x for x in comparisons
            if x["scenario"] == prior["scenario"]
        )

        if current["new_adaptive_misses"] != prior["new_misses"]:
            raise AssertionError("Previous deadline result changed")

        if abs(
            current["new_energy_mj"] - prior["new_energy_mj"]
        ) > 0.00001:
            raise AssertionError("Previous energy result changed")

    write_csv(DECISIONS, all_decisions)
    write_csv(SUMMARY, comparisons)

    findings = Counter(r["finding"] for r in comparisons)

    report = {
        "task": "29.4C.12B",
        "status": "PASS",
        "scenarios": 16,
        "events_per_scenario": 19,
        "decision_records": len(all_decisions),
        "comparisons": len(comparisons),
        "finding_counts": dict(findings),
        "deadline_regressions": findings["DEADLINE_REGRESSION"],
        "adaptive_energy_benefits":
            findings["ADAPTIVE_ENERGY_BENEFIT"],
        "previous_two_scenarios_reproduced": True,
        "scheduler": "ARRIVAL_RATE_AWARE",
        "arrival_information": "KNOWN_SYNTHETIC_INTERVALS",
        "latency": "WORKSTATION_REFERENCES_WITH_ARM_SCALING",
        "fpga_power_and_dma": "HYPOTHETICAL",
        "quality_validated": False,
        "hardware_energy_measured": False,
        "weather_simulation_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("SCENARIOS:", len(comparisons))
    print("DECISION_RECORDS:", len(all_decisions))
    print("ADAPTIVE_ENERGY_BENEFITS:",
          findings["ADAPTIVE_ENERGY_BENEFIT"])
    print("DEADLINE_REGRESSIONS:",
          findings["DEADLINE_REGRESSION"])
    print("PREVIOUS_TWO_SCENARIOS: REPRODUCED")
    print("HARDWARE_MEASURED: NO")
    print("TASK 29.4C.12B: PASS")

if __name__ == "__main__":
    main()
