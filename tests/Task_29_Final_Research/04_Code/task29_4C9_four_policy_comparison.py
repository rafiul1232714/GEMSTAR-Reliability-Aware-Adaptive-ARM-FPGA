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
import task29_4C7_energy_optimizer as energy

TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"
PRIOR = TASK / "06_Research_Findings" / "task29_4C8_policy_comparison.json"

OUT = TASK / "02_CSV_Data" / "task29_4C9_fixed_acceleration_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C9_four_policy_report.json"

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main():
    if OUT.exists() or REPORT.exists():
        raise FileExistsError("Previous Task 29.4C.9 files preserved")

    timing = load(TIMING)
    power = load(POWER)
    prior = load(PRIOR)

    if prior["status"] != "PASS" or prior["policies_compared"] != 3:
        raise RuntimeError("Previous comparison unavailable")

    if timing["measured_fpga_execution"] is not False:
        raise RuntimeError("Unexpected FPGA measurement claim")

    if power["actual_power_measured"] is not False:
        raise RuntimeError("Unexpected power measurement claim")

    models = stage.build_models(timing)
    model = energy.EnergyScheduler(models, timing, power)
    events = queue.make_events()

    if len(events) != 19:
        raise RuntimeError("Arrival sequence count changed")

    rows = []
    finishes = []
    server_free = 0.0

    for event in events:
        arrival = float(event["arrival_ms"])
        deadline = float(event["deadline_ms"])
        health = event["health"]
        backlog = sum(t > arrival for t in finishes)

        if health == "HOLD_OR_ALERT":
            rows.append({
                "event": event["name"],
                "tick": event["tick"],
                "arrival_ms": arrival,
                "absolute_deadline_ms": deadline,
                "queue_depth_at_arrival": backlog,
                "action": "NO_EXECUTION",
                "wait_ms": "",
                "service_ms": "",
                "switch_ms": 0.0,
                "completion_ms": "",
                "deadline_met": "",
                "modeled_energy_mj": 0.0,
                "permission": "WITHHOLD_VALID_RESULT",
                "reason": "SAFETY_HOLD",
            })
            continue

        # Fixed policy: use both modeled accelerators on
        # every admitted job, even if CPU would suffice.
        start = max(arrival, server_free)
        cost = model.evaluate(energy.BOTH)

        service = float(cost["latency_ms"])
        active_energy = float(cost["energy_mj"])
        finish = start + service

        if not all(
            math.isfinite(x) for x in
            (service, active_energy, finish)
        ):
            raise RuntimeError("Non-finite modeled result")

        if service <= 0 or active_energy <= 0:
            raise RuntimeError("Invalid modeled cost")

        rows.append({
            "event": event["name"],
            "tick": event["tick"],
            "arrival_ms": arrival,
            "absolute_deadline_ms": deadline,
            "queue_depth_at_arrival": backlog,
            "action": energy.BOTH,
            "wait_ms": round(start - arrival, 6),
            "service_ms": round(service, 6),
            "switch_ms": round(cost["switch_ms"], 6),
            "completion_ms": round(finish, 6),
            "deadline_met": finish <= deadline,
            "modeled_energy_mj": round(active_energy, 6),
            "permission": "PROVISIONAL_ONLY",
            "reason": "FIXED_COMBINED_ACCELERATION",
        })

        model.previous = energy.BOTH
        server_free = finish
        finishes.append(finish)

    processed = [r for r in rows if r["action"] != "NO_EXECUTION"]
    holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

    if len(processed) != 18 or len(holds) != 1:
        raise AssertionError("Unexpected event accounting")

    if processed[0]["switch_ms"] <= 0:
        raise AssertionError("Missing initial accelerator switch")

    if any(r["switch_ms"] != 0 for r in processed[1:]):
        raise AssertionError("Repeated switch cost charged")

    fixed = {
        "processed": len(processed),
        "safety_holds": len(holds),
        "deadline_missed": sum(
            r["deadline_met"] is False for r in processed
        ),
        "max_wait_ms": max(r["wait_ms"] for r in processed),
        "accelerator_decisions": 18,
        "estimated_active_energy_mj": round(
            sum(r["modeled_energy_mj"] for r in processed), 6
        ),
    }

    comparisons = dict(prior["comparisons"])
    comparisons["FIXED_COMBINED"] = fixed

    if len(comparisons) != 4:
        raise AssertionError("Expected four policies")

    baseline = comparisons["CPU_ONLY"]["estimated_active_energy_mj"]
    adaptive = comparisons["ADAPTIVE_ENERGY"]["estimated_active_energy_mj"]

    report = {
        "task": "29.4C.9",
        "status": "PASS",
        "policies_compared": 4,
        "events_per_policy": 19,
        "fixed_policy_processed": 18,
        "fixed_policy_holds": 1,
        "comparisons": comparisons,
        "fixed_energy_change_vs_cpu_percent": round(
            100 * (fixed["estimated_active_energy_mj"] / baseline - 1), 3
        ),
        "energy_adaptive_minus_fixed_mj": round(
            adaptive - fixed["estimated_active_energy_mj"], 6
        ),
        "same_arrival_sequence": True,
        "cpu_sources": "RECORDED_WORKSTATION_REFERENCES",
        "hardware_and_power": "HYPOTHETICAL",
        "serialized_processing": True,
        "energy_scope": "ACTIVE_PROCESSING_ONLY",
        "sensor_data_synchronized": False,
        "quality_validated": False,
        "hardware_energy_measured": False,
        "real_fpga_executed": False,
        "weather_scenarios_executed": False,
    }

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("POLICIES_COMPARED: 4")

    for name in (
        "CPU_ONLY",
        "ADAPTIVE_DEADLINE",
        "ADAPTIVE_ENERGY",
        "FIXED_COMBINED",
    ):
        r = comparisons[name]
        print(
            name,
            "MISSES:", r["deadline_missed"],
            "MAX_WAIT_MS:", round(r["max_wait_ms"], 3),
            "ENERGY_MJ:", round(
                r["estimated_active_energy_mj"], 3
            ),
            "OFFLOAD_DECISIONS:", r["accelerator_decisions"],
            flush=True
        )

    print(
        "ADAPTIVE_MINUS_FIXED_ENERGY_MJ:",
        report["energy_adaptive_minus_fixed_mj"]
    )
    print("FOUR_POLICY_COMPARISON: PASS")
    print("REAL_FPGA_EXECUTION: NO")
    print("TASK 29.4C.9: PASS")

if __name__ == "__main__":
    main()
