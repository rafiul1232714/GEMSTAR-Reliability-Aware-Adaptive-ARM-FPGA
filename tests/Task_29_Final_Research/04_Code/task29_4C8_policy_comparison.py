import csv
import json
import math
import sys
import hashlib
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C5_queue_scheduler as queue
import task29_4C7_energy_optimizer as optimizer

TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"

OLD_QUEUE = TASK / "06_Research_Findings" / "task29_4C5_queue_report.json"
OLD_ENERGY = TASK / "06_Research_Findings" / "task29_4C6_energy_report.json"

OUTPUT = TASK / "02_CSV_Data" / "task29_4C8_energy_policy_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C8_policy_comparison.json"

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Previous Task 29.4C.8 output preserved")

    timing = load_json(TIMING)
    power = load_json(POWER)
    old_queue = load_json(OLD_QUEUE)
    old_energy = load_json(OLD_ENERGY)

    if old_queue["status"] != "PASS" or old_energy["status"] != "PASS":
        raise RuntimeError("Previous comparisons are not verified")

    if old_queue["logged_decisions"] != 38:
        raise RuntimeError("Queue evidence count changed")

    if old_energy["decisions_replayed"] != 38:
        raise RuntimeError("Energy evidence count changed")

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
        or power["actual_fpga_executed"] is not False
        or power["valid_perception_results_verified"] is not False
    ):
        raise RuntimeError("Hardware or quality provenance mismatch")

    models = stage.build_models(timing)
    engine = optimizer.EnergyScheduler(models, timing, power)

    events = queue.make_events()

    if len(events) != 19:
        raise RuntimeError("Synthetic arrival sequence changed")

    server_free = 0.0
    completions = []
    rows = []

    for event in events:
        tick = event["tick"]
        arrival = float(event["arrival_ms"])
        deadline = float(event["deadline_ms"])
        health = event["health"]

        backlog = sum(t > arrival for t in completions)

        if health == "HOLD_OR_ALERT":
            result = engine.decide(
                1.0, health, tick
            )

            if result["action"] != "NO_EXECUTION":
                raise AssertionError("Safety hold admitted work")

            if result["permission"] != "WITHHOLD_VALID_RESULT":
                raise AssertionError("Unsafe result authorization")

            rows.append({
                "event": event["name"],
                "tick": tick,
                "arrival_ms": arrival,
                "absolute_deadline_ms": deadline,
                "health_mode": health,
                "queue_depth_at_arrival": backlog,
                "queue_wait_ms": "",
                "service_ms": "",
                "switch_ms": 0.0,
                "completion_ms": "",
                "deadline_met": "",
                "action": "NO_EXECUTION",
                "modeled_active_energy_mj": 0.0,
                "result_permission": result["permission"],
                "reason": result["reason"],
                "hardware_executed": False,
                "quality_verified": False,
            })
            continue

        start = max(arrival, server_free)
        waiting = start - arrival

        # Scheduler uses remaining time until the absolute
        # completion deadline, including queue waiting.
        remaining = max(0.000001, deadline - start)

        result = engine.decide(
            remaining, health, tick
        )

        if result["action"] == "NO_EXECUTION":
            raise AssertionError("Eligible work unexpectedly rejected")

        service = float(result["latency_ms"])
        energy = float(result["energy_mj"])
        finish = start + service

        if not (
            math.isfinite(service) and service > 0
            and math.isfinite(energy) and energy > 0
            and finish >= arrival
        ):
            raise AssertionError("Invalid modeled execution")

        server_free = finish
        completions.append(finish)

        rows.append({
            "event": event["name"],
            "tick": tick,
            "arrival_ms": arrival,
            "absolute_deadline_ms": deadline,
            "health_mode": health,
            "queue_depth_at_arrival": backlog,
            "queue_wait_ms": round(waiting, 6),
            "service_ms": round(service, 6),
            "switch_ms": round(result["switch_ms"], 6),
            "completion_ms": round(finish, 6),
            "deadline_met": finish <= deadline,
            "action": result["action"],
            "modeled_active_energy_mj": round(energy, 6),
            "result_permission": result["permission"],
            "reason": result["reason"],
            "hardware_executed": False,
            "quality_verified": False,
        })

    executed = [r for r in rows if r["action"] != "NO_EXECUTION"]
    holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

    if len(rows) != 19 or len(executed) != 18 or len(holds) != 1:
        raise AssertionError("Event processing count mismatch")

    new_summary = {
        "processed": len(executed),
        "safety_holds": len(holds),
        "deadline_met": sum(r["deadline_met"] is True for r in executed),
        "deadline_missed": sum(r["deadline_met"] is False for r in executed),
        "max_wait_ms": max(r["queue_wait_ms"] for r in executed),
        "max_backlog": max(r["queue_depth_at_arrival"] for r in rows),
        "accelerator_decisions": sum(
            r["action"] != "CPU_ONLY" for r in executed
        ),
        "estimated_active_energy_mj": round(
            sum(r["modeled_active_energy_mj"] for r in executed), 6
        ),
    }

    comparisons = {}

    for name, key in (
        ("CPU_ONLY", "CPU_ONLY"),
        ("ADAPTIVE_DEADLINE", "ADAPTIVE_DEADLINE")
    ):
        q = old_queue["summary"][key]
        e = old_energy["summary"][key]

        if q["processed"] != e["processed_jobs"]:
            raise AssertionError("Previous policy job counts differ")

        comparisons[name] = {
            "processed": q["processed"],
            "safety_holds": q["safety_holds"],
            "deadline_missed": q["deadline_missed"],
            "max_wait_ms": q["max_wait_ms"],
            "accelerator_decisions": q["accelerator_decisions"],
            "estimated_active_energy_mj": e["estimated_active_energy_mj"],
        }

    comparisons["ADAPTIVE_ENERGY"] = new_summary

    baseline = comparisons["CPU_ONLY"]["estimated_active_energy_mj"]
    energy = new_summary["estimated_active_energy_mj"]

    report = {
        "task": "29.4C.8",
        "status": "PASS",
        "events_per_policy": 19,
        "new_policy_processed": 18,
        "new_policy_safety_holds": 1,
        "policies_compared": 3,
        "comparisons": comparisons,
        "energy_policy_change_vs_cpu_percent": round(
            (energy / baseline - 1.0) * 100, 3
        ),
        "new_policy_decisions_logged": len(rows),
        "input_hashes": {
            "timing": sha256(TIMING),
            "power": sha256(POWER),
            "queue_reference": sha256(OLD_QUEUE),
            "energy_reference": sha256(OLD_ENERGY),
        },
        "arrival_times": "SYNTHETIC_TASK29_4C5",
        "cpu_timing": "RECORDED_WORKSTATION_REFERENCES",
        "fpga_and_power_models": "HYPOTHETICAL",
        "processing_model": "SINGLE_SERIALIZED_SERVER",
        "queue_model": "FIFO",
        "quality_verified": False,
        "energy_per_valid_result_available": False,
        "actual_hardware_energy_measured": False,
        "weather_scenarios_executed": False,
    }

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("POLICIES_COMPARED: 3")

    for name in (
        "CPU_ONLY",
        "ADAPTIVE_DEADLINE",
        "ADAPTIVE_ENERGY"
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

    print("ENERGY_POLICY_TEST: PASS")
    print("HARDWARE_ENERGY_MEASURED: NO")
    print("TASK 29.4C.8: PASS")

if __name__ == "__main__":
    main()
