import sys, csv, json
from pathlib import Path

root = Path(sys.argv[1])
task = root / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(task / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C11B_sensitivity_sweep as sweep
import task29_5E9L_quality_model_selector as selector

data = task / "02_CSV_Data"
cfg = task / "03_Configurations"

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

events = read_csv(data / "task29_4C12C1_time_varying_events.csv")
scenarios = {
    r["ScenarioID"]: r
    for r in read_csv(data / "task29_4C11A_architecture_scenarios.csv")
}
timing = json.loads(
    (cfg / "task29_4C3_assumptions.json").read_text(encoding="utf-8-sig")
)
power = json.loads(
    (cfg / "task29_4C6_energy_assumptions.json").read_text(encoding="utf-8-sig")
)
pipeline = stage.build_models(timing)
ai_models = selector.load_models(
    data / "Task29_5E8E_Controlled_Comparison_V4"
    / "task29_5E8E_v4_comparison.csv"
)

if len(events) != 76 or len(scenarios) != 16:
    raise RuntimeError("Source count mismatch")

def replay(speedup, cooldown_enabled):
    sim = None
    last_sid = None
    admitted = rejected = holds = misses = switches = 0
    total_energy = 0.0
    max_wait = 0.0
    by_phase = {str(p): [0, 0] for p in range(1, 5)}

    for event in events:
        sid = event["ScenarioID"]
        phase = event["Phase"]

        if sid != last_sid:
            scenario = dict(scenarios[sid])
            scenario["CameraAiAvailable"] = "False"
            prior = sim
            sim = sweep.Simulator(
                scenario, pipeline, timing, power,
                "ARRIVAL_AWARE_ENERGY"
            )
            if prior is not None:
                sim.previous = prior.previous
                sim.last_switch_tick = prior.last_switch_tick
                sim.server_free = prior.server_free
                sim.finishes = prior.finishes
            last_sid = sid

        if event["HealthMode"] == "HOLD_OR_ALERT":
            holds += 1
            continue

        arrival = float(event["ArrivalMs"])
        deadline = float(event["AbsoluteDeadlineMs"])
        interval = float(event["ConfiguredIntervalMs"])
        tick = int(event["GlobalTick"])
        start = max(arrival, sim.server_free)
        wait = start - arrival
        max_wait = max(max_wait, wait)

        candidates = []

        for action in sim.allowed():
            if action in (sweep.CAM, sweep.BOTH):
                continue

            if (
                cooldown_enabled
                and action != sim.previous
                and tick - sim.last_switch_tick
                    < timing["minimum_ticks_between_switches"]
                and sim.previous in sim.allowed()
            ):
                continue

            service0, energy0, _ = sim.evaluate(action)
            other_ms = service0 - sim.cam_cpu

            if other_ms < -1e-6:
                raise RuntimeError("Negative non-camera cost")

            scale = sim.camera_load * sim.arm_factor

            accelerated = [
                {
                    "name": m["name"],
                    "f1": m["f1"],
                    "p99_ms": m["p99_ms"] * scale / speedup
                }
                for m in ai_models
            ]

            budget = deadline - arrival - other_ms
            if budget <= 0:
                continue

            choice = selector.select_model(
                accelerated,
                queue_wait_ms=wait,
                budget_ms=budget,
                minimum_f1=0.50
            )

            if choice["model"] is None:
                continue

            m = next(
                x for x in accelerated
                if x["name"] == choice["model"]
            )

            service = other_ms + m["p99_ms"]
            energy = (
                energy0 - sim.arm_power * sim.cam_cpu
                + sim.arm_power * m["p99_ms"]
            )

            if start + service <= deadline + 1e-6:
                candidates.append((action, service, energy))

        if not candidates:
            rejected += 1
            by_phase[phase][1] += 1
            continue

        capacity = [c for c in candidates if c[1] <= interval]
        selected = (
            min(capacity, key=lambda x: (x[2], x[1]))
            if capacity
            else min(candidates, key=lambda x: (x[1], x[2]))
        )

        action, service, energy = selected
        finish = start + service

        admitted += 1
        by_phase[phase][0] += 1
        total_energy += energy
        misses += int(finish > deadline + 1e-6)

        if action != sim.previous:
            switches += 1
            sim.last_switch_tick = tick

        sim.previous = action
        sim.server_free = finish
        sim.finishes.append(finish)

    assert admitted + rejected == 72
    assert holds == 4
    assert misses == 0

    return {
        "admitted": admitted,
        "rejected": rejected,
        "switches": switches,
        "max_wait": max_wait,
        "energy": total_energy,
        "energy_per_job": total_energy / admitted if admitted else 0,
        "by_phase": by_phase
    }

print("=== COOLDOWN COMPARISON ===")

for speedup in (1.0, 4.0, 8.0):
    for enabled in (False, True):
        result = replay(speedup, enabled)

        print(
            f"\nSPEEDUP={speedup:g}x "
            f"COOLDOWN={'ON' if enabled else 'OFF'}"
        )
        print("ADMITTED:", result["admitted"])
        print("REJECTED:", result["rejected"])
        print("SWITCHES:", result["switches"])
        print("MAX_QUEUE_WAIT_MS:", round(result["max_wait"], 3))
        print("MODELED_ACTIVE_ENERGY_MJ:", round(result["energy"], 3))
        print("ENERGY_PER_ADMITTED_JOB_MJ:",
              round(result["energy_per_job"], 3))
        print("PHASE_ADMITTED_REJECTED:", result["by_phase"])

        if speedup == 1.0 and not enabled:
            assert (result["admitted"], result["rejected"]) == (19, 53)
        if speedup == 8.0 and not enabled:
            assert (result["admitted"], result["rejected"]) == (72, 0)

print("\nMODEL QUALITY AFTER SPEEDUP: ASSUMED UNCHANGED")
print("CAMERA SPEEDUP: HYPOTHETICAL")
print("LIDAR FPGA COSTS: HYPOTHETICAL")
print("ENERGY: ACTIVE-ONLY ESTIMATE")
print("EXISTING FILES MODIFIED: NO")
print("STATUS: TASK 29.5E.9R COMPLETE")