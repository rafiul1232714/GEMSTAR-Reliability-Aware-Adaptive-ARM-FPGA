import csv
import json
import math
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C11B_sensitivity_sweep as sweep

EVENTS = TASK / "02_CSV_Data" / "task29_4C12C1_time_varying_events.csv"
SCENARIOS = TASK / "02_CSV_Data" / "task29_4C11A_architecture_scenarios.csv"
TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"

OUT = TASK / "02_CSV_Data" / "task29_4C12C2_continuous_decisions.csv"
SUMMARY = TASK / "02_CSV_Data" / "task29_4C12C2_policy_summary.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C12C2_continuous_report.json"

POLICIES = (
    "CPU_ONLY",
    "FIXED_AVAILABLE_ACCELERATORS",
    "ADAPTIVE_DEADLINE",
    "ARRIVAL_AWARE_ENERGY",
)

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def make_simulator(scenario, models, timing, power, policy, prior=None):
    # Rebuild only the hardware cost model at a phase boundary.
    # Preserve FIFO queue, accelerator state and switching history.
    sim = sweep.Simulator(scenario, models, timing, power, policy)
    if prior is not None:
        sim.previous = prior.previous
        sim.last_switch_tick = prior.last_switch_tick
        sim.server_free = prior.server_free
        sim.finishes = prior.finishes

    # If a resource becomes unavailable, its action is excluded.
    # Its old state is retained until a valid transition is chosen.
    return sim

def choose(sim, event, start):
    costs = {a: sim.evaluate(a) for a in sim.allowed()}
    if not costs:
        raise RuntimeError("No available processing placement")

    policy = sim.policy
    deadline = float(event["AbsoluteDeadlineMs"])
    interval = float(event["ConfiguredIntervalMs"])
    tick = int(event["GlobalTick"])

    if policy == "CPU_ONLY":
        wanted = sweep.CPU
        reason = "STATIC_CPU"

    elif policy == "FIXED_AVAILABLE_ACCELERATORS":
        for action in (
            sweep.BOTH, sweep.LIDAR, sweep.CAM, sweep.CPU
        ):
            if action in costs:
                wanted = action
                break
        reason = "FIXED_AVAILABLE"

    elif policy == "ADAPTIVE_DEADLINE":
        feasible = [
            a for a in costs if start + costs[a][0] <= deadline
        ]
        if sweep.CPU in feasible:
            wanted = sweep.CPU
            reason = "CPU_DEADLINE_FEASIBLE"
        elif feasible:
            wanted = min(feasible, key=lambda a: costs[a][0])
            reason = "FASTEST_DEADLINE_FEASIBLE"
        else:
            wanted = min(costs, key=lambda a: costs[a][0])
            reason = "NO_FEASIBLE_DEADLINE"

    elif policy == "ARRIVAL_AWARE_ENERGY":
        fastest = min(costs, key=lambda a: costs[a][0])

        if costs[fastest][0] > interval:
            wanted = fastest
            reason = "ARRIVAL_RATE_CAPACITY_GUARD"
        else:
            feasible = [
                a for a in costs
                if costs[a][0] <= interval
                and start + costs[a][0] <= deadline
            ]
            if feasible:
                wanted = min(
                    feasible, key=lambda a: (costs[a][1], costs[a][0])
                )
                reason = "MIN_ENERGY_WITH_CAPACITY"
            else:
                wanted = fastest
                reason = "NO_CAPACITY_DEADLINE_FEASIBLE"

    else:
        raise ValueError("Unknown policy")

    cooldown = sim.timing["minimum_ticks_between_switches"]

    if (
        policy in ("ADAPTIVE_DEADLINE", "ARRIVAL_AWARE_ENERGY")
        and wanted != sim.previous
        and tick - sim.last_switch_tick < cooldown
        and sim.previous in costs
    ):
        previous_cost = costs[sim.previous][0]
        previous_meets_deadline = start + previous_cost <= deadline
        previous_meets_capacity = previous_cost <= interval

        if (
            previous_meets_deadline
            and (
                policy == "ADAPTIVE_DEADLINE"
                or previous_meets_capacity
            )
        ):
            wanted = sim.previous
            reason = "SAFE_SWITCH_COOLDOWN"

    return wanted, reason, costs

def run_policy(policy, events, scenarios, models, timing, power):
    sim = None
    current_scenario = None
    rows = []

    for event in events:
        sid = event["ScenarioID"]
        if sid != current_scenario:
            sim = make_simulator(
                scenarios[sid], models, timing, power, policy, sim
            )
            current_scenario = sid

        arrival = float(event["ArrivalMs"])
        deadline = float(event["AbsoluteDeadlineMs"])
        tick = int(event["GlobalTick"])
        backlog = sum(x > arrival for x in sim.finishes)

        if event["HealthMode"] == "HOLD_OR_ALERT":
            rows.append({
                "policy": policy,
                "event": event["EventID"],
                "phase": event["Phase"],
                "scenario": sid,
                "arrival_ms": arrival,
                "deadline_ms": deadline,
                "queue_depth": backlog,
                "previous_action": sim.previous,
                "action": "NO_EXECUTION",
                "queue_wait_ms": "",
                "service_ms": "",
                "switch_ms": 0,
                "completion_ms": "",
                "deadline_met": "",
                "active_energy_mj": 0,
                "reason": "SAFETY_HOLD",
                "result_permission": "WITHHOLD_VALID_RESULT",
                "hardware_measured": False,
            })
            continue

        start = max(arrival, sim.server_free)
        before = sim.previous

        chosen, reason, costs = choose(sim, event, start)
        service, energy, transition = costs[chosen]
        finish = start + service

        if chosen not in sim.allowed():
            raise AssertionError("Unavailable hardware selected")
        if service <= 0 or energy <= 0:
            raise AssertionError("Invalid modeled cost")
        if finish < arrival or not math.isfinite(finish):
            raise AssertionError("Invalid completion")

        if chosen != before:
            sim.last_switch_tick = tick

        sim.previous = chosen
        sim.server_free = finish
        sim.finishes.append(finish)

        rows.append({
            "policy": policy,
            "event": event["EventID"],
            "phase": event["Phase"],
            "scenario": sid,
            "arrival_ms": arrival,
            "deadline_ms": deadline,
            "queue_depth": backlog,
            "previous_action": before,
            "action": chosen,
            "queue_wait_ms": round(start - arrival, 6),
            "service_ms": round(service, 6),
            "switch_ms": round(transition, 6),
            "completion_ms": round(finish, 6),
            "deadline_met": finish <= deadline,
            "active_energy_mj": round(energy, 9),
            "reason": reason,
            "result_permission": "PROVISIONAL_ONLY",
            "hardware_measured": False,
        })

    return rows

def main():
    if any(p.exists() for p in (OUT, SUMMARY, REPORT)):
        raise FileExistsError("Existing results preserved")

    events = read_csv(EVENTS)
    scenario_list = read_csv(SCENARIOS)
    scenarios = {r["ScenarioID"]: r for r in scenario_list}
    timing = load_json(TIMING)
    power = load_json(POWER)

    if len(events) != 76 or len(scenarios) != 16:
        raise RuntimeError("Unexpected reference counts")

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
    ):
        raise RuntimeError("Hardware provenance failure")

    models = stage.build_models(timing)
    all_rows = []
    summary = []

    for policy in POLICIES:
        rows = run_policy(
            policy, events, scenarios, models, timing, power
        )
        all_rows.extend(rows)

        jobs = [r for r in rows if r["action"] != "NO_EXECUTION"]
        holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

        if len(jobs) != 72 or len(holds) != 4:
            raise AssertionError("Job/hold counts differ")

        if any(
            r["scenario"] == "H4_W1"
            and r["action"] in (sweep.CAM, sweep.BOTH)
            for r in jobs
        ):
            raise AssertionError("Unavailable Camera AI IP selected")

        for phase in ("1", "2", "3", "4"):
            group = [r for r in jobs if r["phase"] == phase]
            if len(group) != 18:
                raise AssertionError("Missing phase jobs")

            summary.append({
                "policy": policy,
                "phase": phase,
                "scenario": group[0]["scenario"],
                "processed": len(group),
                "deadline_misses": sum(
                    r["deadline_met"] is False for r in group
                ),
                "max_wait_ms": round(
                    max(r["queue_wait_ms"] for r in group), 6
                ),
                "modeled_active_energy_mj": round(
                    sum(r["active_energy_mj"] for r in group), 6
                ),
                "action_switches": sum(
                    r["action"] != r["previous_action"]
                    for r in group
                ),
                "action_counts": "|".join(
                    f"{k}:{v}" for k,v in
                    sorted(Counter(r["action"] for r in group).items())
                ),
            })

        print(policy, "PROCESSED:", len(jobs),
              "MISSES:", sum(r["deadline_met"] is False for r in jobs),
              "ENERGY_MJ:",
              round(sum(r["active_energy_mj"] for r in jobs), 3),
              flush=True)

    if len(all_rows) != 304 or len(summary) != 16:
        raise AssertionError("Output count mismatch")

    # Safety-hold and evidence checks.
    for r in all_rows:
        if r["action"] == "NO_EXECUTION":
            assert r["result_permission"] == "WITHHOLD_VALID_RESULT"
        else:
            assert r["result_permission"] == "PROVISIONAL_ONLY"

    write_csv(OUT, all_rows)
    write_csv(SUMMARY, summary)

    policy_totals = {}
    for policy in POLICIES:
        subset = [
            r for r in all_rows
            if r["policy"] == policy and r["action"] != "NO_EXECUTION"
        ]
        policy_totals[policy] = {
            "processed": len(subset),
            "deadline_misses": sum(
                r["deadline_met"] is False for r in subset
            ),
            "active_energy_mj": round(
                sum(r["active_energy_mj"] for r in subset), 6
            ),
            "max_queue_wait_ms": round(
                max(r["queue_wait_ms"] for r in subset), 6
            ),
            "switches": sum(
                r["action"] != r["previous_action"] for r in subset
            ),
        }

    report = {
        "task": "29.4C.12C.2",
        "status": "PASS",
        "policies": len(POLICIES),
        "phases": 4,
        "events_per_policy": 76,
        "total_decisions": len(all_rows),
        "phase_policy_summaries": len(summary),
        "policy_totals": policy_totals,
        "state_persisted_across_phases": True,
        "queue_model": "ONE_SERIALIZED_FIFO_SERVER",
        "phase_spacing": "1800_MS_START_TO_START",
        "hardware_conditions": "SYNTHETIC",
        "accelerator_performance": "HYPOTHETICAL",
        "power_model": "ILLUSTRATIVE_ACTIVE_ONLY",
        "complete_board_energy_measured": False,
        "quality_verified": False,
        "weather_simulation_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("POLICIES:", len(POLICIES))
    print("PHASES: 4")
    print("EVENTS_PER_POLICY: 76")
    print("TOTAL_DECISIONS:", len(all_rows))
    print("PHASE_POLICY_SUMMARIES:", len(summary))
    print("RESOURCE_AVAILABILITY: PASS")
    print("SAFETY_HOLDS: PASS")
    print("HARDWARE_MEASUREMENTS: NONE")
    print("TASK 29.4C.12C.2: PASS")

if __name__ == "__main__":
    main()
