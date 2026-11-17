import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C5_queue_scheduler as queue
import task29_4C11B_sensitivity_sweep as previous

SOURCE = TASK / "02_CSV_Data" / "task29_4C11A_architecture_scenarios.csv"
SUMMARY = TASK / "02_CSV_Data" / "task29_4C11B_policy_summary.csv"
TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"

OUTPUT = TASK / "02_CSV_Data" / "task29_4C12A_arrival_aware_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12A_arrival_aware_report.json"

def read(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def simulate(scenario, models, timing, power):
    sim = previous.Simulator(
        scenario, models, timing, power, "ARRIVAL_AWARE"
    )

    rows = []

    for event in queue.make_events():
        tick = int(event["tick"])
        arrival = float(event["arrival_ms"])
        deadline = float(event["deadline_ms"])
        health = event["health"]

        if health == "HOLD_OR_ALERT":
            rows.append({
                "scenario": scenario["ScenarioID"],
                "event": event["name"],
                "action": "NO_EXECUTION",
                "queue_wait_ms": "",
                "completion_ms": "",
                "deadline_met": "",
                "active_energy_mj": 0,
                "reason": "SAFETY_HOLD",
            })
            continue

        start = max(arrival, sim.server_free)
        costs = {a: sim.evaluate(a) for a in sim.allowed()}

        # Known synthetic arrival-rate configuration.
        # This is not inferred from future outcomes.
        interval = 12.0 if event["name"].startswith("BURST_") else 100.0

        # If even the fastest placement cannot keep pace with
        # incoming jobs, protect throughput first.
        fastest = min(costs, key=lambda a: costs[a][0])

        if costs[fastest][0] > interval:
            wanted = fastest
            reason = "ARRIVAL_RATE_CAPACITY_GUARD"
        else:
            feasible = [
                a for a in costs
                if start + costs[a][0] <= deadline
                and costs[a][0] <= interval
            ]

            if feasible:
                wanted = min(
                    feasible, key=lambda a: (costs[a][1], costs[a][0])
                )
                reason = "MIN_ENERGY_WITH_CAPACITY"
            else:
                wanted = fastest
                reason = "NO_CAPACITY_AND_DEADLINE_FEASIBLE_ACTION"

        # Retaining a previous action under cooldown must
        # never override the capacity guard.
        cooldown = timing["minimum_ticks_between_switches"]
        if (
            reason == "MIN_ENERGY_WITH_CAPACITY"
            and wanted != sim.previous
            and tick - sim.last_switch_tick < cooldown
            and sim.previous in costs
            and costs[sim.previous][0] <= interval
            and start + costs[sim.previous][0] <= deadline
        ):
            wanted = sim.previous
            reason = "SAFE_SWITCH_COOLDOWN"

        service, energy, switch = costs[wanted]
        finish = start + service

        if wanted != sim.previous:
            sim.last_switch_tick = tick
        sim.previous = wanted
        sim.server_free = finish
        sim.finishes.append(finish)

        rows.append({
            "scenario": scenario["ScenarioID"],
            "event": event["name"],
            "action": wanted,
            "queue_wait_ms": round(start - arrival, 6),
            "completion_ms": round(finish, 6),
            "deadline_met": finish <= deadline,
            "active_energy_mj": round(energy, 9),
            "reason": reason,
        })

    return rows

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Previous outputs preserved")

    scenarios = {
        r["ScenarioID"]: r for r in read(SOURCE)
    }
    old = read(SUMMARY)
    timing = load(TIMING)
    power = load(POWER)

    if len(scenarios) != 16 or len(old) != 64:
        raise RuntimeError("Historical evidence count changed")

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
    ):
        raise RuntimeError("Hardware evidence claim invalid")

    models = stage.build_models(timing)

    all_rows = []
    comparison = []

    for sid in ("H2_W1", "H3_W1"):
        rows = simulate(scenarios[sid], models, timing, power)
        all_rows.extend(rows)

        jobs = [r for r in rows if r["action"] != "NO_EXECUTION"]
        holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

        if len(jobs) != 18 or len(holds) != 1:
            raise AssertionError("Safety accounting mismatch")

        fixed = next(
            r for r in old
            if r["scenario"] == sid
            and r["policy"] == "FIXED_AVAILABLE_ACCELERATORS"
        )
        original = next(
            r for r in old
            if r["scenario"] == sid
            and r["policy"] == "ADAPTIVE_ENERGY"
        )

        energy = sum(r["active_energy_mj"] for r in jobs)
        misses = sum(r["deadline_met"] is False for r in jobs)
        fixed_misses = int(fixed["deadline_misses"])

        result = {
            "scenario": sid,
            "original_adaptive_misses": int(
                original["deadline_misses"]
            ),
            "new_misses": misses,
            "fixed_misses": fixed_misses,
            "new_energy_mj": round(energy, 6),
            "fixed_energy_mj": float(
                fixed["modeled_active_energy_mj"]
            ),
            "energy_change_vs_fixed_percent": round(
                100 * (
                    energy / float(fixed["modeled_active_energy_mj"]) - 1
                ), 3
            ),
            "actions": {
                a: sum(r["action"] == a for r in jobs)
                for a in previous.ACTIONS
            }
        }
        comparison.append(result)

        print(
            sid,
            "NEW_MISSES:", misses,
            "FIXED_MISSES:", fixed_misses,
            "ENERGY_CHANGE_VS_FIXED_%:",
            result["energy_change_vs_fixed_percent"],
            flush=True
        )

        if misses > fixed_misses:
            raise AssertionError(
                "Capacity-aware policy worsened deadline misses: " + sid
            )

    if len(all_rows) != 38:
        raise AssertionError("Expected 38 decision records")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    report = {
        "task": "29.4C.12A",
        "status": "PASS",
        "tested_scenarios": 2,
        "logged_decisions": 38,
        "comparisons": comparison,
        "arrival_rate_source": "KNOWN_SYNTHETIC_TRAFFIC_PROFILE",
        "scheduler_test": "ARRIVAL_RATE_CAPACITY_GUARD",
        "hardware_costs": "HYPOTHETICAL",
        "real_hardware_measured": False,
        "validated_perception_quality": False,
        "all_16_scenarios_retested": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("TESTED_SCENARIOS: 2")
    print("DECISIONS: 38")
    print("DEADLINE_REGRESSION_CHECK: PASS")
    print("REAL_HARDWARE_MEASURED: NO")
    print("TASK 29.4C.12A: PASS")

if __name__ == "__main__":
    main()
