import csv
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C5_queue_scheduler as queue
import task29_4C11B_sensitivity_sweep as sweep
import task29_4C12A_arrival_aware_test as arrival

SCENARIO_FILE = TASK / "02_CSV_Data" / "task29_4C11A_architecture_scenarios.csv"
TIMING_FILE = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER_FILE = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"

OUT = TASK / "02_CSV_Data" / "task29_4C12D4_frequency_summary.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12D4_frequency_report.json"

SCENARIO_IDS = ("H1_W1", "H2_W1", "H4_W1")
FREQUENCIES = (0.50, 0.75, 1.00, 1.25)
POWER_EXPONENT = 1.5

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def p99(values):
    s = sorted(float(v) for v in values)
    if not s:
        raise ValueError("Empty latency sample")
    return s[math.ceil(0.99 * len(s)) - 1]

def run_fixed(scenario, models, timing, power, events):
    sim = sweep.Simulator(
        scenario, models, timing, power,
        "FIXED_AVAILABLE_ACCELERATORS"
    )
    return [sim.process(e) for e in events]

def summarize(rows, scenario_id, freq, policy, arm_w, arm_factor):
    jobs = [r for r in rows if r["action"] != "NO_EXECUTION"]
    holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

    if len(jobs) != 18 or len(holds) != 1:
        raise AssertionError("Job and safety-hold accounting failed")

    # Resolve arrival times from the original event schedule.
    # The arrival-aware policy does not log arrival_ms.
    arrivals = {
        str(e["name"]): float(e["arrival_ms"])
        for e in queue.make_events()
    }
    response_times = [
        float(r["completion_ms"]) - arrivals[r["event"]]
        for r in jobs
    ]
    waits = [float(r["queue_wait_ms"]) for r in jobs]
    energy = sum(float(r["active_energy_mj"]) for r in jobs)
    misses = sum(r["deadline_met"] is False for r in jobs)

    if any(v < 0 or not math.isfinite(v) for v in response_times):
        raise AssertionError("Invalid response-time estimate")

    if not math.isfinite(energy) or energy <= 0:
        raise AssertionError("Invalid modeled energy")

    counts = Counter(r["action"] for r in jobs)

    return {
        "scenario": scenario_id,
        "frequency_factor": freq,
        "policy": policy,
        "assumed_arm_power_w": round(arm_w, 6),
        "assumed_arm_latency_factor": round(arm_factor, 6),
        "processed": len(jobs),
        "safety_holds": len(holds),
        "deadline_misses": misses,
        "modeled_active_energy_mj": round(energy, 6),
        "max_queue_wait_ms": round(max(waits), 6),
        "modeled_response_p99_ms": round(p99(response_times), 6),
        "cpu_decisions": counts[sweep.CPU],
        "camera_decisions": counts[sweep.CAM],
        "lidar_decisions": counts[sweep.LIDAR],
        "combined_decisions": counts[sweep.BOTH],
        "hardware_measured": False,
        "quality_verified": False,
    }

def main():
    if OUT.exists() or REPORT.exists():
        raise FileExistsError("Existing research preserved")

    scenarios = {
        r["ScenarioID"]: r
        for r in read_csv(SCENARIO_FILE)
    }
    timing = load_json(TIMING_FILE)
    power = load_json(POWER_FILE)

    if len(scenarios) != 16:
        raise RuntimeError("Scenario reference mismatch")

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
        or power["actual_fpga_executed"] is not False
    ):
        raise RuntimeError("Hardware provenance gate failed")

    models = stage.build_models(timing)
    events = queue.make_events()

    if len(events) != 19:
        raise RuntimeError("Unexpected event count")

    rows = []

    for sid in SCENARIO_IDS:
        if sid not in scenarios:
            raise RuntimeError("Missing scenario " + sid)

        base = scenarios[sid]
        base_factor = float(base["ArmLatencyFactor"])
        base_power = float(base["ArmPowerW"])

        for freq in FREQUENCIES:
            variant = deepcopy(base)

            # Hypothetical DVFS model; not an ARM measurement.
            arm_factor = base_factor / freq
            arm_power = base_power * freq ** POWER_EXPONENT

            variant["ArmLatencyFactor"] = str(arm_factor)
            variant["ArmPowerW"] = str(arm_power)

            fixed = run_fixed(
                variant, models, timing, power, events
            )
            adaptive = arrival.simulate(
                variant, models, timing, power
            )

            rows.append(summarize(
                fixed, sid, freq, "FIXED_AVAILABLE",
                arm_power, arm_factor
            ))
            rows.append(summarize(
                adaptive, sid, freq, "ARRIVAL_AWARE",
                arm_power, arm_factor
            ))

        print("SCENARIO_COMPLETE:", sid, flush=True)

    if len(rows) != 24:
        raise AssertionError("Expected 24 policy summaries")

    # Baseline frequency must reproduce the prior
    # arrival-aware and fixed simulation results.
    previous = read_csv(
        TASK / "02_CSV_Data"
        / "task29_4C12B_comparisons.csv"
    )

    old = {r["scenario"]: r for r in previous}

    for sid in SCENARIO_IDS:
        if sid not in old:
            raise AssertionError("Historical comparison missing")

        now = next(
            r for r in rows
            if r["scenario"] == sid
            and r["frequency_factor"] == 1.0
            and r["policy"] == "ARRIVAL_AWARE"
        )

        if now["deadline_misses"] != int(
            old[sid]["new_adaptive_misses"]
        ):
            raise AssertionError("Reference deadline regression")

        if abs(
            now["modeled_active_energy_mj"]
            - float(old[sid]["new_energy_mj"])
        ) > 0.00001:
            raise AssertionError("Reference energy mismatch")

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "task": "29.4C.12D.4",
        "status": "PASS",
        "scenarios": list(SCENARIO_IDS),
        "frequency_factors": list(FREQUENCIES),
        "frequency_power_exponent": POWER_EXPONENT,
        "policy_summaries": len(rows),
        "processed_jobs_per_policy_run": 18,
        "reference_frequency_reproduced": True,
        "response_p99": "SYNTHETIC_NEAREST_RANK_18_JOBS",
        "queue_model": "SINGLE_SERIALIZED_SERVER",
        "power_model": "ILLUSTRATIVE_ACTIVE_ONLY",
        "frequency_scaling_measured": False,
        "whole_board_energy_measured": False,
        "perception_quality_verified": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== ARM FREQUENCY ANALYSIS ===")
    print("SCENARIOS:", len(SCENARIO_IDS))
    print("FREQUENCY_LEVELS:", len(FREQUENCIES))
    print("POLICY_SUMMARIES:", len(rows))
    print("REFERENCE_FREQUENCY_REPRODUCED: PASS")
    print("=== ARRIVAL-AWARE POLICY RESULTS ===")

    for r in rows:
        if r["policy"] == "ARRIVAL_AWARE":
            print(
                r["scenario"],
                "FREQUENCY:", r["frequency_factor"],
                "MISSES:", r["deadline_misses"],
                "ENERGY_MJ:", r["modeled_active_energy_mj"],
                "P99_MS:", r["modeled_response_p99_ms"],
                flush=True
            )

    print("ARM_FREQUENCY_MEASURED: NO")
    print("HARDWARE_ENERGY_MEASURED: NO")
    print("TASK 29.4C.12D.4: PASS")

if __name__ == "__main__":
    main()

