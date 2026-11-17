import csv
import json
import math
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

LEDGER = TASK / "02_CSV_Data" / "task29_4B6_cpu_workload_ledger.csv"
HEALTH = TASK / "02_CSV_Data" / "task29_4B10_scheduler_health_states.csv"
CONFIG = TASK / "03_Configurations" / "task29_4C2_hypothetical_hardware.json"
OUT = TASK / "02_CSV_Data" / "task29_4C2_scheduler_test_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C2_scheduler_test_report.json"

CPU = "CPU_ONLY"
CAMERA = "CPU_CAMERA_ACCELERATOR"
LIDAR = "CPU_LIDAR_ACCELERATOR"

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def finite_nonnegative(x):
    return (
        type(x) in (int, float)
        and math.isfinite(x)
        and x >= 0
    )

class Scheduler:
    def __init__(self, config):
        self.config = config
        self.previous_action = CPU
        self.last_switch_tick = -1000000

    def decide(self, workload, health, deadline_ms, tick):
        if not finite_nonnegative(deadline_ms) or deadline_ms == 0:
            raise ValueError("Deadline must be positive and finite")
        if type(tick) is not int or tick < 0:
            raise ValueError("Invalid tick")

        kind = workload["WorkloadType"]
        cpu_ms = float(workload["CPU_P99Ms"])

        if not finite_nonnegative(cpu_ms):
            raise ValueError("Invalid measured CPU reference")

        mode = health["controller_mode"]
        permission = health["result_permission"]

        if mode not in (
            "NORMAL_CANDIDATE",
            "DEGRADED_CANDIDATE",
            "HOLD_OR_ALERT"
        ):
            raise ValueError("Invalid health mode")

        if health["quality_authorization"] != "UNVERIFIED":
            raise ValueError("Unexpected quality authorization")

        if mode == "HOLD_OR_ALERT":
            return {
                "action": CPU,
                "latency_ms": cpu_ms,
                "deadline_met": cpu_ms <= deadline_ms,
                "result_permission": "WITHHOLD_VALID_RESULT",
                "reason": "REQUIRED_SENSOR_UNAVAILABLE",
                "fpga_executed": False,
                "energy_measured": False,
            }

        if permission != "PROVISIONAL_ONLY":
            raise ValueError("Unexpected result permission")

        candidates = {CPU: cpu_ms}

        # Hardware estimates below are hypothetical.
        # They are not measurements from an FPGA.
        if kind == "CAMERA_AI":
            candidates[CAMERA] = (
                cpu_ms * self.config["camera_acceleration_factor"]
                + self.config["camera_dma_ms"]
                + (
                    self.config["camera_switch_ms"]
                    if self.previous_action != CAMERA else 0.0
                )
            )

        elif kind == "LIDAR_RADAR":
            # Only the LiDAR portion is hypothetically accelerated.
            # Radar remains on CPU.
            lidar_cpu = (
                float(workload["CPU_MedianMs"])
                - 0.0
            )

            # A stage-resolved LiDAR fraction is not present
            # in this workload ledger. Do not invent one.
            # Therefore no quantitative LiDAR FPGA candidate
            # can be evaluated from this ledger alone.
            lidar_cpu = None

        else:
            raise ValueError("Unknown workload type")

        # CPU is preferred whenever it meets the deadline.
        if cpu_ms <= deadline_ms:
            chosen = CPU
            reason = "CPU_MEETS_DEADLINE"

        else:
            feasible = [
                (action, latency)
                for action, latency in candidates.items()
                if latency <= deadline_ms
            ]

            if feasible:
                chosen = min(
                    feasible, key=lambda pair: pair[1]
                )[0]
                reason = "CPU_MISSES_ACCELERATOR_CANDIDATE_MEETS"
            else:
                chosen = CPU
                reason = "NO_FEASIBLE_PLACEMENT_DEADLINE_WARNING"

        cooldown = self.config["minimum_ticks_between_switches"]

        if (
            chosen != self.previous_action
            and tick - self.last_switch_tick < cooldown
        ):
            chosen = self.previous_action
            if chosen not in candidates:
                chosen = CPU
            reason = "SWITCH_COOLDOWN"

        if chosen != self.previous_action:
            self.last_switch_tick = tick
            self.previous_action = chosen

        latency = candidates[chosen]

        return {
            "action": chosen,
            "latency_ms": latency,
            "deadline_met": latency <= deadline_ms,
            "result_permission": permission,
            "reason": reason,
            "fpga_executed": False,
            "energy_measured": False,
        }

def main():
    if OUT.exists() or REPORT.exists():
        raise FileExistsError("Existing Task 29 outputs preserved")

    workloads = read_csv(LEDGER)
    health = read_csv(HEALTH)
    config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))

    if len(workloads) != 93 or len(health) != 168:
        raise RuntimeError("Input evidence count mismatch")

    if config["fpga_execution_measured"] is not False:
        raise RuntimeError("Unexpected hardware evidence claim")

    for key in (
        "camera_acceleration_factor",
        "lidar_acceleration_factor",
        "camera_dma_ms",
        "lidar_dma_ms",
        "camera_switch_ms",
        "lidar_switch_ms",
    ):
        if not finite_nonnegative(config[key]):
            raise RuntimeError("Invalid hypothetical parameter")

    if type(config["minimum_ticks_between_switches"]) is not int:
        raise RuntimeError("Invalid cooldown configuration")

    cameras = [
        x for x in workloads
        if x["WorkloadType"] == "CAMERA_AI"
    ]
    lidars = [
        x for x in workloads
        if x["WorkloadType"] == "LIDAR_RADAR"
    ]

    normal = next(
        h for h in health
        if h["controller_mode"] == "NORMAL_CANDIDATE"
    )
    degraded = next(
        h for h in health
        if h["controller_mode"] == "DEGRADED_CANDIDATE"
    )
    hold = next(
        h for h in health
        if h["controller_mode"] == "HOLD_OR_ALERT"
    )

    camera = next(
        x for x in cameras if x["Model"] == "yolo11s"
    )
    lidar = lidars[0]

    cpu_camera = float(camera["CPU_P99Ms"])
    cpu_lidar = float(lidar["CPU_P99Ms"])

    # Synthetic deadlines are used ONLY for policy unit tests.
    cases = [
        ("CPU_NORMAL", camera, normal, cpu_camera * 1.20, 0),
        ("CAMERA_OFFLOAD", camera, degraded, cpu_camera * 0.80, 2),
        ("CAMERA_HOLD", camera, hold, cpu_camera * 0.80, 3),
        ("CPU_RECOVERY", camera, normal, cpu_camera * 1.20, 5),
        ("LIDAR_CPU_WARNING", lidar, normal, cpu_lidar * 0.80, 7),
        ("LIDAR_CPU_OK", lidar, normal, cpu_lidar * 1.20, 9),
    ]

    scheduler = Scheduler(config)
    decisions = []

    for name, workload, state, deadline, tick in cases:
        result = scheduler.decide(
            workload, state, deadline, tick
        )

        decisions.append({
            "test_case": name,
            "tick": tick,
            "workload_id": workload["WorkloadID"],
            "workload_type": workload["WorkloadType"],
            "health_mode": state["controller_mode"],
            "cpu_p99_reference_ms": workload["CPU_P99Ms"],
            "synthetic_deadline_ms": deadline,
            "selected_action": result["action"],
            "estimated_latency_ms": result["latency_ms"],
            "deadline_met_in_model": result["deadline_met"],
            "result_permission": result["result_permission"],
            "reason_code": result["reason"],
            "fpga_executed": False,
            "energy_measured": False,
            "workload_health_pairing": "SYNTHETIC_TEST",
        })

        print(
            name,
            "ACTION:", result["action"],
            "REASON:", result["reason"],
            flush=True
        )

    by_name = {r["test_case"]: r for r in decisions}

    expected = {
        "CPU_NORMAL": CPU,
        "CAMERA_OFFLOAD": CAMERA,
        "CAMERA_HOLD": CPU,
        "CPU_RECOVERY": CPU,
        "LIDAR_CPU_WARNING": CPU,
        "LIDAR_CPU_OK": CPU,
    }

    for name, action in expected.items():
        if by_name[name]["selected_action"] != action:
            raise AssertionError(f"Unexpected decision: {name}")

    assert (
        by_name["CAMERA_HOLD"]["result_permission"]
        == "WITHHOLD_VALID_RESULT"
    )
    assert (
        by_name["LIDAR_CPU_WARNING"]["deadline_met_in_model"]
        is False
    )

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)

    report = {
        "task": "29.4C.2",
        "status": "PASS",
        "unit_tests": len(decisions),
        "measured_cpu_references": len(workloads),
        "sensor_health_references": len(health),
        "hardware_costs": "HYPOTHETICAL",
        "cpu_fpga_decision_logic_implemented": True,
        "camera_acceleration_candidate_tested": True,
        "lidar_acceleration_quantitatively_tested": False,
        "combined_acceleration_tested": False,
        "real_hardware_executed": False,
        "energy_optimization_implemented": False,
        "deadline_thresholds": "SYNTHETIC_TEST_ONLY",
        "weather_scenarios_executed": False,
        "independent_sensor_sync_verified": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("UNIT_TESTS:", len(decisions), flush=True)
    print("CPU_REFERENCES:", len(workloads), flush=True)
    print("HEALTH_REFERENCES:", len(health), flush=True)
    print("FPGA_EXECUTED: NO", flush=True)
    print("ENERGY_OPTIMIZATION: NOT YET", flush=True)
    print("TASK 29.4C.2: PASS", flush=True)

if __name__ == "__main__":
    main()
