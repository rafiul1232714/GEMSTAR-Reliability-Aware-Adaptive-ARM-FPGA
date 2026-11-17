import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as previous

CONFIG = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
HEALTH = TASK / "02_CSV_Data" / "task29_4B10_scheduler_health_states.csv"
OUTPUT = TASK / "02_CSV_Data" / "task29_4C5_queue_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C5_queue_report.json"

CPU = "CPU_ONLY"
CAM = "CPU_CAMERA_ACCELERATOR"
LIDAR = "CPU_LIDAR_ACCELERATOR"
BOTH = "CPU_COMBINED_ACCELERATORS"
ACTIONS = (CPU, CAM, LIDAR, BOTH)

RESOURCES = {
    CPU: frozenset(),
    CAM: frozenset(("camera",)),
    LIDAR: frozenset(("lidar",)),
    BOTH: frozenset(("camera", "lidar")),
}

def finite_positive(x):
    return type(x) in (int, float) and math.isfinite(x) and x > 0

class QueueSimulator:
    def __init__(self, models, config, policy):
        self.models = models
        self.config = config
        self.policy = policy
        self.previous = CPU
        self.last_switch_tick = -100000
        self.server_free_ms = 0.0
        self.completions = []

    def service_cost(self, action):
        c = self.models["camera"]
        l = self.models["lidar"]

        camera = (
            c["offload_ms"] if "camera" in RESOURCES[action]
            else c["cpu_ms"]
        )
        lidar = (
            l["offload_ms"] if "lidar" in RESOURCES[action]
            else l["cpu_ms"]
        )

        changed = RESOURCES[action] ^ RESOURCES[self.previous]
        transition = sum(
            self.config[name + "_switch_ms"]
            for name in changed
        )

        # One serialized processing server.
        # This is NOT a measured parallel CPU/FPGA schedule.
        return camera + lidar + transition, transition

    def process(self, event):
        tick = event["tick"]
        arrival = event["arrival_ms"]
        deadline = event["deadline_ms"]
        health = event["health"]

        if not (
            type(tick) is int and tick >= 0
            and type(arrival) in (int, float)
            and math.isfinite(arrival) and arrival >= 0
            and finite_positive(deadline)
        ):
            raise ValueError("Invalid event timing")

        if health not in (
            "NORMAL_CANDIDATE",
            "DEGRADED_CANDIDATE",
            "HOLD_OR_ALERT"
        ):
            raise ValueError("Invalid health mode")

        # Number of unfinished previously admitted jobs at arrival.
        backlog = sum(t > arrival for t in self.completions)

        if health == "HOLD_OR_ALERT":
            # No perception job admitted under a safety hold.
            # State remains unchanged; no switch is charged.
            return {
                "policy": self.policy,
                "event": event["name"],
                "tick": tick,
                "arrival_ms": arrival,
                "absolute_deadline_ms": deadline,
                "health_mode": health,
                "queue_depth_at_arrival": backlog,
                "queue_wait_ms": None,
                "service_ms": None,
                "switch_ms": 0.0,
                "completion_ms": None,
                "deadline_met": None,
                "action": "NO_EXECUTION",
                "result_permission": "WITHHOLD_VALID_RESULT",
                "reason": "SAFETY_HOLD",
                "fpga_executed": False,
                "energy_measured": False,
            }

        start = max(arrival, self.server_free_ms)
        wait = start - arrival

        costs = {a: self.service_cost(a) for a in ACTIONS}

        if self.policy == "CPU_ONLY":
            chosen = CPU
            reason = "STATIC_CPU_BASELINE"
        else:
            cpu_finish = start + costs[CPU][0]

            if cpu_finish <= deadline:
                chosen = CPU
                reason = "CPU_FINISHES_BEFORE_DEADLINE"
            else:
                feasible = [
                    a for a in ACTIONS
                    if start + costs[a][0] <= deadline
                ]

                if feasible:
                    chosen = min(
                        feasible, key=lambda a: costs[a][0]
                    )
                    reason = "ACCELERATOR_AVOIDS_DEADLINE_MISS"
                else:
                    chosen = min(
                        ACTIONS, key=lambda a: costs[a][0]
                    )
                    reason = "NO_FEASIBLE_ACTION_MINIMIZE_LATENESS"

            cooldown = self.config["minimum_ticks_between_switches"]
            if (
                chosen != self.previous
                and tick - self.last_switch_tick < cooldown
            ):
                chosen = self.previous
                reason = "SWITCH_COOLDOWN"

        duration, switch = costs[chosen]
        finish = start + duration

        if chosen != self.previous:
            self.last_switch_tick = tick
            self.previous = chosen

        self.server_free_ms = finish
        self.completions.append(finish)

        return {
            "policy": self.policy,
            "event": event["name"],
            "tick": tick,
            "arrival_ms": arrival,
            "absolute_deadline_ms": deadline,
            "health_mode": health,
            "queue_depth_at_arrival": backlog,
            "queue_wait_ms": round(wait, 6),
            "service_ms": round(duration, 6),
            "switch_ms": round(switch, 6),
            "completion_ms": round(finish, 6),
            "deadline_met": finish <= deadline,
            "action": chosen,
            "result_permission": "PROVISIONAL_ONLY",
            "reason": reason,
            "fpga_executed": False,
            "energy_measured": False,
        }

def make_events():
    events = []
    tick = 0

    # Synthetic high-rate arrivals.
    for i in range(12):
        arrival = i * 12.0
        events.append({
            "name": f"BURST_{i:02d}",
            "tick": tick,
            "arrival_ms": arrival,
            "deadline_ms": arrival + 75.0,
            "health": "NORMAL_CANDIDATE",
        })
        tick += 1

    # Controlled gap to allow the queue to drain.
    for i in range(6):
        arrival = 1000.0 + i * 100.0
        events.append({
            "name": f"SPACED_{i:02d}",
            "tick": tick,
            "arrival_ms": arrival,
            "deadline_ms": arrival + 75.0,
            "health": "DEGRADED_CANDIDATE",
        })
        tick += 1

    events.append({
        "name": "SAFETY_HOLD",
        "tick": tick,
        "arrival_ms": 1600.0,
        "deadline_ms": 1675.0,
        "health": "HOLD_OR_ALERT",
    })

    return events

def summarize(rows):
    processed = [r for r in rows if r["action"] != "NO_EXECUTION"]
    return {
        "processed": len(processed),
        "safety_holds": len(rows) - len(processed),
        "deadline_met": sum(r["deadline_met"] is True for r in processed),
        "deadline_missed": sum(r["deadline_met"] is False for r in processed),
        "max_wait_ms": max(r["queue_wait_ms"] for r in processed),
        "max_backlog": max(r["queue_depth_at_arrival"] for r in rows),
        "accelerator_decisions": sum(
            r["action"] not in (CPU, "NO_EXECUTION")
            for r in rows
        ),
        "total_modeled_service_ms": round(
            sum(r["service_ms"] for r in processed), 6
        ),
    }

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing Task 29 output preserved")

    config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    models = previous.build_models(config)

    if (
        config["measured_fpga_execution"] is not False
        or config["calibrated_energy_model"] is not False
    ):
        raise RuntimeError("Evidence provenance gate failed")

    with HEALTH.open(newline="", encoding="utf-8-sig") as f:
        health = list(csv.DictReader(f))

    if len(health) != 168:
        raise RuntimeError("Unexpected health reference count")

    events = make_events()
    all_rows = []
    summaries = {}

    for policy in ("CPU_ONLY", "ADAPTIVE_DEADLINE"):
        simulator = QueueSimulator(models, config, policy)
        rows = [simulator.process(e) for e in events]
        all_rows.extend(rows)
        summaries[policy] = summarize(rows)

        print(
            policy,
            "PROCESSED:", summaries[policy]["processed"],
            "MISSES:", summaries[policy]["deadline_missed"],
            "MAX_WAIT_MS:", summaries[policy]["max_wait_ms"],
            "ACCELERATOR_DECISIONS:",
            summaries[policy]["accelerator_decisions"],
            flush=True
        )

    baseline = summaries["CPU_ONLY"]
    adaptive = summaries["ADAPTIVE_DEADLINE"]

    if len(all_rows) != 38:
        raise AssertionError("Expected 38 logged decisions")

    if baseline["processed"] != 18 or adaptive["processed"] != 18:
        raise AssertionError("Unexpected processing event count")

    if baseline["safety_holds"] != 1 or adaptive["safety_holds"] != 1:
        raise AssertionError("Safety hold not enforced")

    if baseline["max_wait_ms"] <= 0:
        raise AssertionError("Burst failed to create CPU backlog")

    if adaptive["accelerator_decisions"] < 1:
        raise AssertionError("Adaptive accelerator was never selected")

    if adaptive["deadline_missed"] > baseline["deadline_missed"]:
        raise AssertionError("Adaptive policy increased deadline misses")

    # Every processed event must finish after its arrival.
    for r in all_rows:
        if r["action"] != "NO_EXECUTION":
            if r["completion_ms"] < r["arrival_ms"]:
                raise AssertionError("Impossible completion time")
            if r["service_ms"] <= 0:
                raise AssertionError("Invalid service time")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    report = {
        "task": "29.4C.5",
        "status": "PASS",
        "events_per_policy": len(events),
        "logged_decisions": len(all_rows),
        "summary": summaries,
        "workload_provenance": "SEPARATE_MEASURED_CPU_REFERENCES",
        "arrival_times": "SYNTHETIC",
        "deadlines": "SYNTHETIC",
        "accelerator_costs": "HYPOTHETICAL",
        "resource_model": "ONE_SERIALIZED_SERVER",
        "parallel_fpga_execution_modeled": False,
        "energy_optimization": False,
        "fpga_executed": False,
        "weather_scenarios_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("EVENTS_PER_POLICY:", len(events))
    print("LOGGED_DECISIONS:", len(all_rows))
    print("SAFETY_HOLD: PASS")
    print("QUEUE_WAIT_ACCOUNTING: PASS")
    print("DEADLINE_CHECKS: PASS")
    print("HARDWARE_EXECUTED: NO")
    print("TASK 29.4C.5: PASS")

if __name__ == "__main__":
    main()
