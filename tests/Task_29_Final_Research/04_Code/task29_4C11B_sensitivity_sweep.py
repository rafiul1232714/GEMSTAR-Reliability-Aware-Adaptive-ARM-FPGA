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
import task29_4C5_queue_scheduler as queue

SOURCE = TASK / "02_CSV_Data" / "task29_4C11A_architecture_scenarios.csv"
TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"
OUTPUT = TASK / "02_CSV_Data" / "task29_4C11B_all_decisions.csv"
SUMMARY = TASK / "02_CSV_Data" / "task29_4C11B_policy_summary.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C11B_sensitivity_report.json"

CPU = "CPU_ONLY"
CAM = "CPU_CAMERA_ACCELERATOR"
LIDAR = "CPU_LIDAR_ACCELERATOR"
BOTH = "CPU_COMBINED_ACCELERATORS"
ACTIONS = (CPU, CAM, LIDAR, BOTH)
POLICIES = (
    "CPU_ONLY",
    "ADAPTIVE_DEADLINE",
    "ADAPTIVE_ENERGY",
    "FIXED_AVAILABLE_ACCELERATORS",
)
RESOURCES = {
    CPU: frozenset(),
    CAM: frozenset(("camera",)),
    LIDAR: frozenset(("lidar",)),
    BOTH: frozenset(("camera", "lidar")),
}

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def positive(x):
    x = float(x)
    if not math.isfinite(x) or x <= 0:
        raise ValueError("Invalid positive parameter")
    return x

def write_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

class Simulator:
    def __init__(self, scenario, models, timing, power, policy):
        self.s = scenario
        self.models = models
        self.timing = timing
        self.power = power
        self.policy = policy
        self.previous = CPU
        self.last_switch_tick = -1000000
        self.server_free = 0.0
        self.finishes = []

        self.arm_factor = positive(scenario["ArmLatencyFactor"])
        self.arm_power = positive(scenario["ArmPowerW"])
        self.camera_load = positive(scenario["CameraWorkloadFactor"])
        self.lidar_load = positive(scenario["LidarWorkloadFactor"])
        self.dma_factor = positive(scenario["DmaMultiplier"])

        self.camera_available = (
            scenario["CameraAiAvailable"].strip().lower() == "true"
        )
        self.lidar_available = (
            scenario["LidarFpgaAvailable"].strip().lower() == "true"
        )

        radar_reference = models["lidar"]["radar_cpu_p99_ms"]
        lidar_reference = models["lidar"]["cpu_ms"]
        lidar_fpga_reference = (
            models["lidar"]["offload_ms"]
            - timing["lidar_dma_ms"]
            - radar_reference
        )

        if lidar_fpga_reference < -1e-9:
            raise RuntimeError("Invalid LiDAR stage cost model")

        # Illustrative ARM and FPGA timing extrapolations.
        self.cam_cpu = (
            models["camera"]["cpu_ms"]
            * self.camera_load * self.arm_factor
        )
        self.lidar_cpu = (
            lidar_reference * self.lidar_load * self.arm_factor
        )
        self.radar_arm = (
            radar_reference * self.lidar_load * self.arm_factor
        )
        self.cam_fpga = (
            (models["camera"]["offload_ms"]
             - timing["camera_dma_ms"])
            * self.camera_load
        )
        self.lidar_fpga = (
            max(0.0, lidar_fpga_reference) * self.lidar_load
        )

    def allowed(self):
        result = [CPU]
        if self.camera_available:
            result.append(CAM)
        if self.lidar_available:
            result.append(LIDAR)
        if self.camera_available and self.lidar_available:
            result.append(BOTH)
        return result

    def evaluate(self, action):
        active = RESOURCES[action]
        changed = active ^ RESOURCES[self.previous]

        cpu_ms = 0.0
        camera_fpga_ms = 0.0
        lidar_fpga_ms = 0.0
        dma_ms = 0.0

        if "camera" in active:
            camera_fpga_ms = self.cam_fpga
            dma_ms += (
                self.timing["camera_dma_ms"] * self.dma_factor
            )
        else:
            cpu_ms += self.cam_cpu

        if "lidar" in active:
            lidar_fpga_ms = self.lidar_fpga
            cpu_ms += self.radar_arm
            dma_ms += (
                self.timing["lidar_dma_ms"] * self.dma_factor
            )
        else:
            cpu_ms += self.lidar_cpu

        transition_ms = sum(
            self.timing[name + "_switch_ms"]
            for name in changed
        )

        latency = (
            cpu_ms + camera_fpga_ms + lidar_fpga_ms
            + dma_ms + transition_ms
        )

        energy = (
            self.arm_power * cpu_ms
            + float(self.s["CameraFpgaPowerW"]) * camera_fpga_ms
            + float(self.s["LidarFpgaPowerW"]) * lidar_fpga_ms
            + self.power["dma_host_active_w"] * dma_ms
            + self.power["switch_energy_mj_per_resource"] * len(changed)
        )

        if not (math.isfinite(latency) and latency > 0):
            raise RuntimeError("Invalid service latency")

        if not (math.isfinite(energy) and energy > 0):
            raise RuntimeError("Invalid modeled energy")

        return latency, energy, transition_ms

    def process(self, event):
        arrival = float(event["arrival_ms"])
        deadline = float(event["deadline_ms"])
        tick = int(event["tick"])

        backlog = sum(x > arrival for x in self.finishes)

        if event["health"] == "HOLD_OR_ALERT":
            # No processing admitted. Idle energy is not modeled.
            return {
                "scenario": self.s["ScenarioID"],
                "profile": self.s["HardwareProfile"],
                "workload": self.s["WorkloadLevel"],
                "policy": self.policy,
                "event": event["name"],
                "arrival_ms": arrival,
                "deadline_ms": deadline,
                "queue_depth": backlog,
                "action": "NO_EXECUTION",
                "queue_wait_ms": "",
                "service_ms": "",
                "completion_ms": "",
                "deadline_met": "",
                "active_energy_mj": 0.0,
                "reason": "SAFETY_HOLD",
                "quality_verified": False,
                "hardware_measured": False,
            }

        start = max(arrival, self.server_free)
        costs = {
            action: self.evaluate(action)
            for action in self.allowed()
        }

        if self.policy == "CPU_ONLY":
            chosen = CPU
            reason = "FIXED_CPU"

        elif self.policy == "FIXED_AVAILABLE_ACCELERATORS":
            if BOTH in costs:
                chosen = BOTH
            elif LIDAR in costs:
                chosen = LIDAR
            elif CAM in costs:
                chosen = CAM
            else:
                chosen = CPU
            reason = "FIXED_AVAILABLE_OFFLOAD"

        else:
            feasible = [
                action for action in costs
                if start + costs[action][0] <= deadline
            ]

            if self.policy == "ADAPTIVE_DEADLINE":
                if CPU in feasible:
                    chosen = CPU
                    reason = "CPU_FEASIBLE"
                elif feasible:
                    chosen = min(feasible, key=lambda a: costs[a][0])
                    reason = "MIN_LATENCY_FEASIBLE"
                else:
                    chosen = min(costs, key=lambda a: costs[a][0])
                    reason = "NO_FEASIBLE_DEADLINE"

            elif self.policy == "ADAPTIVE_ENERGY":
                if feasible:
                    chosen = min(
                        feasible,
                        key=lambda a: (costs[a][1], costs[a][0])
                    )
                    reason = "MIN_ENERGY_FEASIBLE"
                else:
                    chosen = min(costs, key=lambda a: costs[a][0])
                    reason = "NO_FEASIBLE_DEADLINE"
            else:
                raise RuntimeError("Unknown scheduling policy")

            cooldown = self.timing["minimum_ticks_between_switches"]
            if (
                chosen != self.previous
                and tick - self.last_switch_tick < cooldown
                and self.previous in costs
            ):
                chosen = self.previous
                reason = "SWITCH_COOLDOWN"

        service, energy, transition = costs[chosen]
        finish = start + service

        if chosen != self.previous:
            self.last_switch_tick = tick
        self.previous = chosen
        self.server_free = finish
        self.finishes.append(finish)

        return {
            "scenario": self.s["ScenarioID"],
            "profile": self.s["HardwareProfile"],
            "workload": self.s["WorkloadLevel"],
            "policy": self.policy,
            "event": event["name"],
            "arrival_ms": arrival,
            "deadline_ms": deadline,
            "queue_depth": backlog,
            "action": chosen,
            "queue_wait_ms": round(start - arrival, 6),
            "service_ms": round(service, 6),
            "completion_ms": round(finish, 6),
            "deadline_met": finish <= deadline,
            "active_energy_mj": round(energy, 9),
            "reason": reason,
            "quality_verified": False,
            "hardware_measured": False,
        }

def summarize(rows, scenario, policy):
    jobs = [r for r in rows if r["action"] != "NO_EXECUTION"]
    holds = [r for r in rows if r["action"] == "NO_EXECUTION"]

    if len(jobs) != 18 or len(holds) != 1:
        raise RuntimeError("Safety or job accounting mismatch")

    return {
        "scenario": scenario["ScenarioID"],
        "profile": scenario["HardwareProfile"],
        "workload": scenario["WorkloadLevel"],
        "policy": policy,
        "processed": 18,
        "safety_holds": 1,
        "deadline_misses": sum(
            r["deadline_met"] is False for r in jobs
        ),
        "maximum_wait_ms": round(
            max(r["queue_wait_ms"] for r in jobs), 6
        ),
        "modeled_active_energy_mj": round(
            sum(r["active_energy_mj"] for r in jobs), 6
        ),
        "cpu_decisions": sum(r["action"] == CPU for r in jobs),
        "camera_decisions": sum(r["action"] == CAM for r in jobs),
        "lidar_decisions": sum(r["action"] == LIDAR for r in jobs),
        "combined_decisions": sum(r["action"] == BOTH for r in jobs),
    }

def main():
    for path in (OUTPUT, SUMMARY, REPORT):
        if path.exists():
            raise FileExistsError("Existing research preserved: " + str(path))

    scenarios = read_csv(SOURCE)
    timing = load(TIMING)
    power = load(POWER)
    models = stage.build_models(timing)
    events = queue.make_events()

    if len(scenarios) != 16 or len(events) != 19:
        raise RuntimeError("Unexpected scenario or event count")

    if (
        timing["measured_fpga_execution"] is not False
        or power["actual_power_measured"] is not False
        or power["actual_fpga_executed"] is not False
    ):
        raise RuntimeError("Hardware provenance check failed")

    all_rows = []
    summaries = []

    for scenario in scenarios:
        if scenario["HardwareMeasured"].lower() != "false":
            raise RuntimeError("Unexpected measured hardware claim")

        for policy in POLICIES:
            simulator = Simulator(
                scenario, models, timing, power, policy
            )
            rows = [simulator.process(event) for event in events]

            all_rows.extend(rows)
            summaries.append(summarize(rows, scenario, policy))

        selected = [
            r for r in summaries
            if r["scenario"] == scenario["ScenarioID"]
        ]

        print(
            scenario["ScenarioID"],
            scenario["HardwareProfile"],
            scenario["WorkloadLevel"],
            "ENERGY_ACTIONS:",
            next(
                (
                    f"CPU={r['cpu_decisions']},"
                    f"CAM={r['camera_decisions']},"
                    f"LIDAR={r['lidar_decisions']},"
                    f"BOTH={r['combined_decisions']}"
                )
                for r in selected
                if r["policy"] == "ADAPTIVE_ENERGY"
            ),
            flush=True
        )

    if len(all_rows) != 1216 or len(summaries) != 64:
        raise AssertionError("Sensitivity sweep count mismatch")

    # Safety and physical-consistency checks.
    for row in all_rows:
        if row["action"] == "NO_EXECUTION":
            if row["reason"] != "SAFETY_HOLD":
                raise AssertionError("Unexpected skipped execution")
            continue

        if float(row["completion_ms"]) < float(row["arrival_ms"]):
            raise AssertionError("Completion precedes arrival")

        if float(row["active_energy_mj"]) <= 0:
            raise AssertionError("Invalid active energy")

        if (
            row["profile"] == "NO_CAMERA_AI_IP"
            and row["action"] in (CAM, BOTH)
        ):
            raise AssertionError("Unavailable Camera AI accelerator used")

    write_csv(OUTPUT, all_rows)
    write_csv(SUMMARY, summaries)

    differences = []
    for scenario in scenarios:
        subset = {
            r["policy"]: r for r in summaries
            if r["scenario"] == scenario["ScenarioID"]
        }

        adaptive = subset["ADAPTIVE_ENERGY"]
        fixed = subset["FIXED_AVAILABLE_ACCELERATORS"]

        differences.append({
            "scenario": scenario["ScenarioID"],
            "adaptive_minus_fixed_energy_mj": round(
                adaptive["modeled_active_energy_mj"]
                - fixed["modeled_active_energy_mj"], 6
            ),
            "adaptive_minus_fixed_deadline_misses": (
                adaptive["deadline_misses"]
                - fixed["deadline_misses"]
            ),
        })

    report = {
        "task": "29.4C.11B",
        "status": "PASS",
        "hardware_workload_scenarios": 16,
        "policies": 4,
        "events_per_policy": 19,
        "logged_decisions": len(all_rows),
        "policy_summaries": len(summaries),
        "adaptive_vs_fixed_by_scenario": differences,
        "data_source": "RECORDED_WORKSTATION_CPU_REFERENCES",
        "arm_cpu_model": "HYPOTHETICAL_SCALING",
        "fpga_latency_model": "HYPOTHETICAL_SCALING",
        "energy_model": "ILLUSTRATIVE_ACTIVE_ONLY",
        "processing_model": "SINGLE_SERIALIZED_SERVER",
        "workloads_synchronized": False,
        "hardware_measurements": False,
        "validated_perception_quality": False,
        "weather_simulation_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("SENSITIVITY_SCENARIOS:", len(scenarios))
    print("POLICIES_PER_SCENARIO:", len(POLICIES))
    print("TOTAL_DECISIONS:", len(all_rows))
    print("POLICY_SUMMARIES:", len(summaries))
    print("HARDWARE_MEASUREMENTS: NONE")
    print("WEATHER_SIMULATION: NOT YET")
    print("TASK 29.4C.11B: PASS")

if __name__ == "__main__":
    main()
