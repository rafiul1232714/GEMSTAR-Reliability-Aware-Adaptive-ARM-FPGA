import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage

TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"
PREVIOUS = TASK / "06_Research_Findings" / "task29_4C6_energy_report.json"

OUTPUT = TASK / "02_CSV_Data" / "task29_4C7_energy_scheduler_tests.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C7_energy_scheduler_report.json"

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

class EnergyScheduler:
    def __init__(self, models, timing, power):
        self.models = models
        self.timing = timing
        self.power = dict(power)
        self.previous = CPU
        self.last_switch = -1000000

        lidar = models["lidar"]
        self.radar_ms = min(
            lidar["radar_cpu_p99_ms"],
            lidar["offload_ms"] - timing["lidar_dma_ms"]
        )

        self.lidar_fpga_ms = (
            lidar["offload_ms"]
            - timing["lidar_dma_ms"]
            - self.radar_ms
        )

        self.camera_fpga_ms = (
            models["camera"]["offload_ms"]
            - timing["camera_dma_ms"]
        )

        if min(
            self.radar_ms,
            self.lidar_fpga_ms,
            self.camera_fpga_ms
        ) < 0:
            raise ValueError("Invalid approximate stage decomposition")

    def evaluate(self, action):
        if action not in ACTIONS:
            raise ValueError("Unknown placement")

        current = RESOURCES[action]
        changed = current ^ RESOURCES[self.previous]

        cpu_ms = 0.0
        camera_fpga_ms = 0.0
        lidar_fpga_ms = 0.0
        dma_ms = 0.0

        if "camera" in current:
            camera_fpga_ms = self.camera_fpga_ms
            dma_ms += self.timing["camera_dma_ms"]
        else:
            cpu_ms += self.models["camera"]["cpu_ms"]

        if "lidar" in current:
            lidar_fpga_ms = self.lidar_fpga_ms
            cpu_ms += self.radar_ms
            dma_ms += self.timing["lidar_dma_ms"]
        else:
            cpu_ms += self.models["lidar"]["cpu_ms"]

        switch_ms = sum(
            self.timing[name + "_switch_ms"]
            for name in changed
        )

        latency = (
            cpu_ms + camera_fpga_ms + lidar_fpga_ms
            + dma_ms + switch_ms
        )

        energy = (
            cpu_ms * self.power["cpu_active_w"]
            + camera_fpga_ms * self.power["fpga_camera_active_w"]
            + lidar_fpga_ms * self.power["fpga_lidar_active_w"]
            + dma_ms * self.power["dma_host_active_w"]
            + len(changed)
              * self.power["switch_energy_mj_per_resource"]
        )

        if not (
            math.isfinite(latency) and latency > 0
            and math.isfinite(energy) and energy > 0
        ):
            raise ValueError("Invalid modeled cost")

        return {
            "latency_ms": latency,
            "energy_mj": energy,
            "switch_ms": switch_ms,
        }

    def decide(self, deadline, mode, tick, allowed=ACTIONS):
        if (
            type(deadline) not in (int, float)
            or not math.isfinite(deadline)
            or deadline <= 0
        ):
            raise ValueError("Invalid deadline")

        if type(tick) is not int or tick < 0:
            raise ValueError("Invalid tick")

        allowed = set(allowed)
        if not allowed or not allowed.issubset(ACTIONS):
            raise ValueError("Invalid allowed actions")

        if mode not in (
            "NORMAL_CANDIDATE",
            "DEGRADED_CANDIDATE",
            "HOLD_OR_ALERT"
        ):
            raise ValueError("Unknown health mode")

        if mode == "HOLD_OR_ALERT":
            self.previous = CPU
            self.last_switch = tick
            return {
                "action": "NO_EXECUTION",
                "latency_ms": None,
                "energy_mj": 0.0,
                "switch_ms": 0.0,
                "deadline_met": None,
                "permission": "WITHHOLD_VALID_RESULT",
                "reason": "SAFETY_HOLD",
            }

        costs = {
            action: self.evaluate(action)
            for action in ACTIONS if action in allowed
        }

        feasible = [
            action for action in costs
            if costs[action]["latency_ms"] <= deadline
        ]

        if feasible:
            chosen = min(
                feasible,
                key=lambda action: (
                    costs[action]["energy_mj"],
                    costs[action]["latency_ms"]
                )
            )
            reason = "MINIMUM_MODELED_ENERGY_FEASIBLE"
        else:
            chosen = min(
                costs,
                key=lambda action: costs[action]["latency_ms"]
            )
            reason = "NO_DEADLINE_FEASIBLE_ACTION"

        cooldown = self.timing["minimum_ticks_between_switches"]

        if (
            chosen != self.previous
            and tick - self.last_switch < cooldown
            and self.previous in allowed
        ):
            chosen = self.previous
            reason = "SWITCH_COOLDOWN"

        selected = costs[chosen]

        if chosen != self.previous:
            self.last_switch = tick

        self.previous = chosen

        return {
            "action": chosen,
            "latency_ms": selected["latency_ms"],
            "energy_mj": selected["energy_mj"],
            "switch_ms": selected["switch_ms"],
            "deadline_met": selected["latency_ms"] <= deadline,
            "permission": "PROVISIONAL_ONLY",
            "reason": reason,
        }

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing Task 29.4C.7 output")

    timing = json.loads(TIMING.read_text(encoding="utf-8-sig"))
    power = json.loads(POWER.read_text(encoding="utf-8-sig"))
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8-sig"))

    if previous["status"] != "PASS" or previous["decisions_replayed"] != 38:
        raise RuntimeError("Task 29.4C.6 evidence incomplete")

    if (
        power["actual_power_measured"] is not False
        or power["actual_fpga_executed"] is not False
        or power["valid_perception_results_verified"] is not False
        or timing["measured_fpga_execution"] is not False
    ):
        raise RuntimeError("Unverified hardware evidence")

    for key in (
        "cpu_active_w",
        "fpga_camera_active_w",
        "fpga_lidar_active_w",
        "dma_host_active_w",
    ):
        x = power[key]
        if type(x) not in (int, float) or not math.isfinite(x) or x <= 0:
            raise ValueError("Invalid power assumption")

    models = stage.build_models(timing)

    def make(power_override=None):
        return EnergyScheduler(
            models, timing,
            power_override if power_override is not None else power
        )

    relaxed = (
        models["camera"]["cpu_ms"]
        + models["lidar"]["cpu_ms"]
    ) * 2.0

    probe = make()
    startup = {a: probe.evaluate(a) for a in ACTIONS}
    combined_deadline = (
        startup[BOTH]["latency_ms"]
        + startup[CAM]["latency_ms"]
    ) / 2

    tests = []

    def check(name, engine, deadline, mode, tick, allowed, expected):
        before = engine.previous
        decision = engine.decide(deadline, mode, tick, allowed)

        if decision["action"] != expected:
            raise AssertionError(
                f"{name}: expected {expected}, got {decision['action']}"
            )

        tests.append({
            "test": name,
            "tick": tick,
            "previous_action": before,
            "selected_action": decision["action"],
            "health_mode": mode,
            "deadline_ms": deadline,
            "modeled_latency_ms": decision["latency_ms"],
            "modeled_active_energy_mj": decision["energy_mj"],
            "switch_ms": decision["switch_ms"],
            "deadline_met": decision["deadline_met"],
            "permission": decision["permission"],
            "reason": decision["reason"],
            "hardware_costs": "HYPOTHETICAL",
            "quality_verified": False,
            "fpga_executed": False,
        })

        print(
            name,
            "=>",
            decision["action"],
            decision["reason"],
            flush=True
        )

        return decision

    # Test against declared illustrative power assumptions.
    check("ENERGY_MINIMUM", make(), relaxed,
          "NORMAL_CANDIDATE", 0, ACTIONS, BOTH)

    check("CAMERA_AVAILABLE", make(), relaxed,
          "NORMAL_CANDIDATE", 0, (CPU, CAM), CAM)

    check("LIDAR_AVAILABLE", make(), relaxed,
          "NORMAL_CANDIDATE", 0, (CPU, LIDAR), LIDAR)

    check("CPU_RESOURCE_ONLY", make(), relaxed,
          "NORMAL_CANDIDATE", 0, (CPU,), CPU)

    check("COMBINED_DEADLINE", make(), combined_deadline,
          "DEGRADED_CANDIDATE", 0, ACTIONS, BOTH)

    hold = check("HEALTH_HOLD", make(), relaxed,
                 "HOLD_OR_ALERT", 0, ACTIONS,
                 "NO_EXECUTION")

    assert hold["permission"] == "WITHHOLD_VALID_RESULT"

    # Sensitivity test: extremely expensive assumed FPGA power.
    # This proves the optimizer can choose CPU to save energy.
    expensive = dict(power)
    expensive["fpga_camera_active_w"] = 100.0
    expensive["fpga_lidar_active_w"] = 100.0

    check("HIGH_FPGA_POWER_CPU", make(expensive), relaxed,
          "NORMAL_CANDIDATE", 0, ACTIONS, CPU)

    # Sequential transition / cooldown behavior.
    sequence = make()

    check("ENTER_ACCELERATORS", sequence, relaxed,
          "NORMAL_CANDIDATE", 0, ACTIONS, BOTH)

    sequence.power = dict(expensive)

    retained = check("COOLDOWN_RETAIN", sequence, relaxed,
                     "NORMAL_CANDIDATE", 1, ACTIONS, BOTH)

    if retained["switch_ms"] != 0:
        raise AssertionError("Switch cost charged without transition")

    check("COOLDOWN_RELEASE", sequence, relaxed,
          "NORMAL_CANDIDATE", 2, ACTIONS, CPU)

    if len(tests) != 10:
        raise AssertionError("Incorrect test count")

    if any(
        row["permission"] == "VALIDATED"
        for row in tests
    ):
        raise AssertionError("Unverified quality authorization")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(tests[0]))
        writer.writeheader()
        writer.writerows(tests)

    report = {
        "task": "29.4C.7",
        "status": "PASS",
        "unit_tests": len(tests),
        "optimization_objective": "MINIMUM_MODELED_ACTIVE_ENERGY",
        "deadline_feasibility_checked": True,
        "all_four_placements_tested": True,
        "power_sensitivity_tested": True,
        "switch_cooldown_tested": True,
        "quality_authorization": "UNVERIFIED",
        "stage_decomposition": "UNCALIBRATED_SURROGATE",
        "power_and_fpga_costs": "HYPOTHETICAL",
        "idle_system_energy_included": False,
        "real_fpga_execution": False,
        "measured_energy_savings": False,
        "full_queue_comparison_with_energy_policy": False,
        "weather_scenarios_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("UNIT_TESTS:", len(tests))
    print("ENERGY_OPTIMIZING_DECISION_LOGIC: PASS")
    print("DEADLINE_FEASIBILITY: PASS")
    print("POWER_SENSITIVITY: PASS")
    print("SWITCH_COOLDOWN: PASS")
    print("MEASURED_HARDWARE_ENERGY: NO")
    print("TASK 29.4C.7: PASS")

if __name__ == "__main__":
    main()
