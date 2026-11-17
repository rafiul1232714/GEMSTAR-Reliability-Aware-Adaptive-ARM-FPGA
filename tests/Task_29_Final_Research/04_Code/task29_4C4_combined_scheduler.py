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
OUTPUT = TASK / "02_CSV_Data" / "task29_4C4_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C4_report.json"

CPU = "CPU_ONLY"
CAM = "CPU_CAMERA_ACCELERATOR"
LIDAR = "CPU_LIDAR_ACCELERATOR"
BOTH = "CPU_COMBINED_ACCELERATORS"

ACTIONS = (CPU, CAM, LIDAR, BOTH)

def resources(action):
    return {
        CPU: frozenset(),
        CAM: frozenset(("camera",)),
        LIDAR: frozenset(("lidar",)),
        BOTH: frozenset(("camera", "lidar")),
    }[action]

class Scheduler:
    def __init__(self, config, models):
        self.config = config
        self.models = models
        self.previous = CPU
        self.last_switch = -100000

    def latency(self, action):
        cam = self.models["camera"]
        lidar = self.models["lidar"]

        # A synthetic paired workload. Sequential service:
        # no claim of synchronized recordings or parallel speedup.
        camera_ms = (
            cam["offload_ms"] if "camera" in resources(action)
            else cam["cpu_ms"]
        )
        lidar_ms = (
            lidar["offload_ms"] if "lidar" in resources(action)
            else lidar["cpu_ms"]
        )

        base = camera_ms + lidar_ms

        # Charge only when accelerator resource state changes.
        changed = resources(action) ^ resources(self.previous)
        switching = sum(
            self.config[name + "_switch_ms"]
            for name in changed
        )

        return base + switching, switching

    def decide(self, deadline, mode, tick, allowed):
        if not math.isfinite(deadline) or deadline <= 0:
            raise ValueError("Invalid deadline")
        if type(tick) is not int or tick < 0:
            raise ValueError("Invalid tick")
        if mode not in (
            "NORMAL_CANDIDATE",
            "DEGRADED_CANDIDATE",
            "HOLD_OR_ALERT",
        ):
            raise ValueError("Invalid health mode")

        allowed = set(allowed)
        if not allowed.issubset(ACTIONS) or CPU not in allowed:
            raise ValueError("Invalid action availability")

        if mode == "HOLD_OR_ALERT":
            # Invalid perception output must never be authorized.
            # This is a control decision, not an executed workload.
            self.previous = CPU
            self.last_switch = tick
            return {
                "action": CPU,
                "latency_ms": None,
                "switch_ms": None,
                "deadline_met": None,
                "permission": "WITHHOLD_VALID_RESULT",
                "reason": "SAFETY_HOLD_NO_EXECUTION",
            }

        cpu_ms = self.latency(CPU)[0]

        if cpu_ms <= deadline:
            wanted = CPU
            reason = "CPU_MEETS_DEADLINE"
        else:
            feasible = [
                (action, self.latency(action)[0])
                for action in ACTIONS
                if action in allowed
                and self.latency(action)[0] <= deadline
            ]
            if feasible:
                wanted = min(
                    feasible, key=lambda item: item[1]
                )[0]
                reason = "MODELED_ACCELERATOR_MEETS_DEADLINE"
            else:
                wanted = CPU
                reason = "NO_FEASIBLE_DEADLINE_CANDIDATE"

        cooldown = self.config["minimum_ticks_between_switches"]

        if (
            wanted != self.previous
            and tick - self.last_switch < cooldown
            and self.previous in allowed
        ):
            wanted = self.previous
            reason = "SWITCH_COOLDOWN"

        if wanted != self.previous:
            self.last_switch = tick

        latency, switch_ms = self.latency(wanted)
        self.previous = wanted

        return {
            "action": wanted,
            "latency_ms": latency,
            "switch_ms": switch_ms,
            "deadline_met": latency <= deadline,
            "permission": "PROVISIONAL_ONLY",
            "reason": reason,
        }

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing outputs preserved")

    config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    models = previous.build_models(config)

    if config["measured_fpga_execution"] is not False:
        raise RuntimeError("Hardware assumption gate failed")

    cam = models["camera"]
    lidar = models["lidar"]

    # Baseline candidate costs, including entry overhead.
    probe = Scheduler(config, models)
    costs = {a: probe.latency(a)[0] for a in ACTIONS}

    if not (
        costs[BOTH] < costs[CAM] < costs[CPU]
        and costs[LIDAR] < costs[CPU]
    ):
        raise RuntimeError(
            "Assumptions do not support required unit-test ordering"
        )

    tests = []

    def check(name, engine, deadline, mode,
              tick, allowed, expected):
        before = engine.previous
        result = engine.decide(deadline, mode, tick, allowed)
        if result["action"] != expected:
            raise AssertionError(
                f"{name}: expected {expected}, got {result['action']}"
            )

        row = {
            "test": name,
            "tick": tick,
            "health_mode": mode,
            "previous_action": before,
            "action": result["action"],
            "deadline_ms": deadline,
            "modeled_latency_ms": result["latency_ms"],
            "switch_ms": result["switch_ms"],
            "deadline_met": result["deadline_met"],
            "permission": result["permission"],
            "reason": result["reason"],
            "pairing": "SYNTHETIC_SEQUENTIAL_WORKLOAD",
            "fpga_executed": False,
            "energy_measured": False,
        }
        tests.append(row)
        print(name, "=>", result["action"],
              result["reason"], flush=True)
        return result

    relaxed = costs[CPU] * 1.2

    check(
        "CPU_NORMAL",
        Scheduler(config, models),
        relaxed, "NORMAL_CANDIDATE", 0,
        ACTIONS, CPU
    )

    check(
        "CAMERA_ONLY_AVAILABLE",
        Scheduler(config, models),
        (costs[CPU] + costs[CAM]) / 2,
        "NORMAL_CANDIDATE", 0,
        (CPU, CAM), CAM
    )

    check(
        "LIDAR_ONLY_AVAILABLE",
        Scheduler(config, models),
        (costs[CPU] + costs[LIDAR]) / 2,
        "NORMAL_CANDIDATE", 0,
        (CPU, LIDAR), LIDAR
    )

    check(
        "COMBINED_NEEDED",
        Scheduler(config, models),
        (costs[BOTH] + costs[CAM]) / 2,
        "NORMAL_CANDIDATE", 0,
        ACTIONS, BOTH
    )

    check(
        "NO_FEASIBLE",
        Scheduler(config, models),
        costs[BOTH] * 0.5,
        "NORMAL_CANDIDATE", 0,
        ACTIONS, CPU
    )

    check(
        "SAFETY_HOLD",
        Scheduler(config, models),
        relaxed, "HOLD_OR_ALERT", 0,
        ACTIONS, CPU
    )

    sequence = Scheduler(config, models)
    deadline_combined = (costs[BOTH] + costs[CAM]) / 2

    check(
        "ENTER_COMBINED",
        sequence, deadline_combined,
        "NORMAL_CANDIDATE", 0, ACTIONS, BOTH
    )

    retained = check(
        "RETAIN_COOLDOWN",
        sequence, relaxed,
        "NORMAL_CANDIDATE", 1, ACTIONS, BOTH
    )

    if retained["switch_ms"] != 0:
        raise AssertionError(
            "Switching cost charged without state change"
        )

    check(
        "RETURN_CPU",
        sequence, relaxed,
        "NORMAL_CANDIDATE", 2, ACTIONS, CPU
    )

    if len(tests) != 9:
        raise RuntimeError("Expected 9 tests")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(tests[0]))
        writer.writeheader()
        writer.writerows(tests)

    report = {
        "task": "29.4C.4",
        "status": "PASS",
        "tests": len(tests),
        "cpu_measured_sources_reused": True,
        "candidate_costs_ms": costs,
        "combined_acceleration_tested": True,
        "switch_cost_only_on_transition": True,
        "safety_hold_tested": True,
        "pairing": "SYNTHETIC_SEQUENTIAL_WORKLOAD",
        "scheduler_objective": "DEADLINE_FEASIBILITY",
        "queue_simulation_implemented": False,
        "energy_optimization_implemented": False,
        "hardware_measurements": False,
        "weather_simulation_completed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("UNIT_TESTS:", len(tests))
    print("COMBINED_ACCELERATION: PASS")
    print("TRANSITION_COST_ACCOUNTING: PASS")
    print("SAFETY_HOLD: PASS")
    print("REAL_FPGA_EXECUTION: NO")
    print("TASK 29.4C.4: PASS")

if __name__ == "__main__":
    main()
