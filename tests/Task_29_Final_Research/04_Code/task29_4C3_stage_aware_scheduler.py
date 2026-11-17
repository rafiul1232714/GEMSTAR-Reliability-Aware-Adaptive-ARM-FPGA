import csv
import json
import math
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TESTS = ROOT / "tests"
TASK = TESTS / "Task_29_Final_Research"

RAW = (
    TESTS / "Task_26_Final_Research"
    / "02_CSV_Data" / "task26_5C_integrated_cpu_timing.csv"
)
LEDGER = TASK / "02_CSV_Data" / "task29_4B6_cpu_workload_ledger.csv"
REFERENCE = TASK / "02_CSV_Data" / "task29_4B4_real_cpu_frame_reference.csv"
CONFIG = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
OUTPUT = TASK / "02_CSV_Data" / "task29_4C3_scheduler_decisions.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C3_scheduler_report.json"

CPU = "CPU_ONLY"
CAM = "CPU_CAMERA_ACCELERATOR"
LIDAR = "CPU_LIDAR_ACCELERATOR"

def read(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def number(value):
    x = float(value)
    if not math.isfinite(x) or x < 0:
        raise ValueError("Invalid numeric value")
    return x

def percentile(values, p):
    v = sorted(number(x) for x in values)
    if not v:
        raise ValueError("Empty percentile input")
    pos = (len(v) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)

def build_models(config):
    raw = read(RAW)
    ledger = read(LEDGER)
    references = read(REFERENCE)

    if len(raw) != 1325 or len(ledger) != 93:
        raise RuntimeError("Source evidence counts changed")

    frames = sorted(set(int(r["frame"]) for r in raw))
    if len(frames) != 53:
        raise RuntimeError("Unexpected LiDAR frame count")

    frame = frames[0]
    samples = [r for r in raw if int(r["frame"]) == frame]

    if len(samples) != 25:
        raise RuntimeError("Expected 25 repeated measurements")

    if set(int(r["repeat"]) for r in samples) != set(range(1, 26)):
        raise RuntimeError("Invalid repeat identifiers")

    cpu_samples = []
    lidar_offload_samples = []
    lidar_stage_samples = []
    radar_stage_samples = []

    for r in samples:
        filt = number(r["filter_ms"])
        cluster = number(r["cluster_ms"])
        radar = number(r["radar_ms"])
        total = number(r["total_ms"])

        if abs(filt + cluster + radar - total) > 0.01:
            raise RuntimeError("Stage timing mismatch")

        lidar_stage_samples.append(filt + cluster)
        radar_stage_samples.append(radar)
        cpu_samples.append(total)

        # Hypothetical FPGA compute time; real CPU Radar retained.
        lidar_offload_samples.append(
            (filt + cluster) * config["lidar_execution_factor"]
            + radar
            + config["lidar_dma_ms"]
        )

    lidar_cpu_p99 = percentile(cpu_samples, 0.99)

    matching = [
        r for r in references if int(r["Frame"]) == frame
    ]
    if len(matching) != 1:
        raise RuntimeError("Missing LiDAR/Radar reference")

    if abs(
        lidar_cpu_p99 - float(matching[0]["P99TotalMs"])
    ) > 0.00001:
        raise RuntimeError("Archived p99 reference mismatch")

    camera_rows = [
        r for r in ledger
        if r["WorkloadType"] == "CAMERA_AI"
        and r["Model"] == "yolo11s"
    ]
    if not camera_rows:
        raise RuntimeError("No Camera YOLO11s workload")

    camera = camera_rows[0]
    camera_cpu_p99 = number(camera["CPU_P99Ms"])

    return {
        "lidar": {
            "id": "LR_F" + str(frame),
            "cpu_ms": lidar_cpu_p99,
            "offload_ms": percentile(
                lidar_offload_samples, 0.99
            ),
            "switch_ms": config["lidar_switch_ms"],
            "action": LIDAR,
            "lidar_cpu_p99_ms": percentile(
                lidar_stage_samples, 0.99
            ),
            "radar_cpu_p99_ms": percentile(
                radar_stage_samples, 0.99
            ),
        },
        "camera": {
            "id": camera["WorkloadID"],
            "cpu_ms": camera_cpu_p99,
            "offload_ms": (
                camera_cpu_p99
                * config["camera_execution_factor"]
                + config["camera_dma_ms"]
            ),
            "switch_ms": config["camera_switch_ms"],
            "action": CAM,
        },
    }

class Scheduler:
    def __init__(self, cooldown):
        self.previous_action = CPU
        self.last_switch_tick = -1000000
        self.cooldown = cooldown

    def decide(self, model, health, deadline, tick):
        if health not in (
            "NORMAL_CANDIDATE",
            "DEGRADED_CANDIDATE",
            "HOLD_OR_ALERT"
        ):
            raise ValueError("Unknown health state")

        deadline = number(deadline)
        if deadline <= 0 or type(tick) is not int or tick < 0:
            raise ValueError("Invalid scheduler input")

        cpu_ms = model["cpu_ms"]
        accelerator = model["action"]

        # Safety override takes precedence over switching cooldown.
        if health == "HOLD_OR_ALERT":
            if self.previous_action != CPU:
                self.previous_action = CPU
                self.last_switch_tick = tick
            return {
                "action": CPU,
                "latency_ms": cpu_ms,
                "deadline_met": cpu_ms <= deadline,
                "permission": "WITHHOLD_VALID_RESULT",
                "reason": "REQUIRED_SENSOR_UNAVAILABLE",
            }

        # Include switching penalty when entering accelerator mode.
        offload_ms = model["offload_ms"]
        if self.previous_action != accelerator:
            offload_ms += model["switch_ms"]

        if cpu_ms <= deadline:
            wanted = CPU
            reason = "CPU_MEETS_DEADLINE"
        elif offload_ms <= deadline:
            wanted = accelerator
            reason = "ACCELERATOR_MODEL_MEETS_DEADLINE"
        else:
            wanted = CPU
            reason = "NO_FEASIBLE_DEADLINE_CANDIDATE"

        if (
            wanted != self.previous_action
            and tick - self.last_switch_tick < self.cooldown
        ):
            wanted = self.previous_action
            reason = "SWITCH_COOLDOWN"

        # The current model must support the retained action.
        if wanted not in (CPU, accelerator):
            wanted = CPU
            reason = "UNSUPPORTED_RETAINED_ACTION_CPU_FALLBACK"

        latency = cpu_ms if wanted == CPU else offload_ms

        if wanted != self.previous_action:
            self.previous_action = wanted
            self.last_switch_tick = tick

        return {
            "action": wanted,
            "latency_ms": latency,
            "deadline_met": latency <= deadline,
            "permission": "PROVISIONAL_ONLY",
            "reason": reason,
        }

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing Task 29 output preserved")

    config = json.loads(CONFIG.read_text(encoding="utf-8-sig"))

    if config["measured_fpga_execution"] is not False:
        raise RuntimeError("Invalid FPGA evidence claim")

    if config["calibrated_energy_model"] is not False:
        raise RuntimeError("Invalid energy evidence claim")

    for key in (
        "lidar_execution_factor", "lidar_dma_ms",
        "lidar_switch_ms", "camera_execution_factor",
        "camera_dma_ms", "camera_switch_ms"
    ):
        number(config[key])

    cooldown = config["minimum_ticks_between_switches"]
    if type(cooldown) is not int or cooldown < 0:
        raise ValueError("Invalid cooldown")

    models = build_models(config)

    for model in models.values():
        if (
            model["offload_ms"] + model["switch_ms"]
            >= model["cpu_ms"]
        ):
            raise RuntimeError(
                "Assumed accelerator does not offer test speedup"
            )

    cases = []

    def test(name, model, health, deadline, tick, expected, scheduler=None):
        engine = scheduler if scheduler else Scheduler(cooldown)
        decision = engine.decide(model, health, deadline, tick)
        if decision["action"] != expected:
            raise AssertionError(
                f"{name}: expected {expected}, got {decision['action']}"
            )

        cases.append({
            "test": name,
            "tick": tick,
            "workload_id": model["id"],
            "health": health,
            "cpu_p99_ms": model["cpu_ms"],
            "hypothetical_offload_p99_ms": model["offload_ms"],
            "deadline_ms": deadline,
            "action": decision["action"],
            "modeled_latency_ms": decision["latency_ms"],
            "deadline_met_in_model": decision["deadline_met"],
            "permission": decision["permission"],
            "reason": decision["reason"],
            "fpga_executed": False,
            "energy_measured": False,
        })
        print(name, "=>", decision["action"], decision["reason"], flush=True)
        return decision

    lr = models["lidar"]
    cam = models["camera"]

    def middle(model):
        return (
            model["cpu_ms"]
            + model["offload_ms"]
            + model["switch_ms"]
        ) / 2

    test("LIDAR_CPU", lr, "NORMAL_CANDIDATE",
         lr["cpu_ms"] * 1.2, 0, CPU)

    test("LIDAR_OFFLOAD", lr, "NORMAL_CANDIDATE",
         middle(lr), 0, LIDAR)

    test("CAMERA_OFFLOAD", cam, "DEGRADED_CANDIDATE",
         middle(cam), 0, CAM)

    test("CAMERA_CPU", cam, "NORMAL_CANDIDATE",
         cam["cpu_ms"] * 1.2, 0, CPU)

    infeasible = test(
        "NO_FEASIBLE", lr, "NORMAL_CANDIDATE",
        min(lr["cpu_ms"], lr["offload_ms"]) * 0.5,
        0, CPU
    )
    assert infeasible["deadline_met"] is False

    hold = test("SAFETY_HOLD", cam, "HOLD_OR_ALERT",
                middle(cam), 0, CPU)
    assert hold["permission"] == "WITHHOLD_VALID_RESULT"

    # Sequential tests verify switching cooldown.
    sequence = Scheduler(cooldown)

    test("SWITCH_ENTER", cam, "NORMAL_CANDIDATE",
         middle(cam), 0, CAM, sequence)

    retained = test(
        "SWITCH_COOLDOWN", cam, "NORMAL_CANDIDATE",
        cam["cpu_ms"] * 1.2, 1, CAM, sequence
    )
    assert retained["reason"] == "SWITCH_COOLDOWN"

    test("SWITCH_RETURN_CPU", cam, "NORMAL_CANDIDATE",
         cam["cpu_ms"] * 1.2, 2, CPU, sequence)

    if len(cases) != 9:
        raise RuntimeError("Unit-test count mismatch")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(cases[0]))
        writer.writeheader()
        writer.writerows(cases)

    report = {
        "task": "29.4C.3",
        "status": "PASS",
        "unit_tests": len(cases),
        "lidar_recorded_repeats": 25,
        "lidar_cpu_p99_ms": lr["cpu_ms"],
        "lidar_stage_cpu_p99_ms": lr["lidar_cpu_p99_ms"],
        "radar_stage_cpu_p99_ms": lr["radar_cpu_p99_ms"],
        "lidar_offload_hypothetical_p99_ms": lr["offload_ms"],
        "camera_cpu_p99_ms": cam["cpu_ms"],
        "camera_offload_hypothetical_ms": cam["offload_ms"],
        "lidar_accelerator_tested": True,
        "camera_accelerator_tested": True,
        "cooldown_tested": True,
        "combined_accelerators_tested": False,
        "queue_simulator_implemented": False,
        "energy_optimization_implemented": False,
        "hardware_measured": False,
        "weather_scenarios_executed": False,
        "evidence_pairing": "SEPARATE_SOURCE_WORKLOADS"
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("UNIT_TESTS: 9")
    print("LIDAR_STAGE_AWARE_MODEL: PASS")
    print("CAMERA_ACCELERATOR_MODEL: PASS")
    print("SWITCH_COOLDOWN: PASS")
    print("HARDWARE_EXECUTED: NO")
    print("TASK 29.4C.3: PASS")

if __name__ == "__main__":
    main()
