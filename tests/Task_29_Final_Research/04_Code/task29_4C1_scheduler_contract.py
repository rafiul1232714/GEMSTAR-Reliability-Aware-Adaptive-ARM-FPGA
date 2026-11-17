import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

LEDGER = TASK / "02_CSV_Data" / "task29_4B6_cpu_workload_ledger.csv"
HEALTH = TASK / "02_CSV_Data" / "task29_4B10_scheduler_health_states.csv"

SCHEMA = TASK / "03_Configurations" / "task29_4C1_scheduler_schema.json"
REPORT = TASK / "06_Research_Findings" / "task29_4C1_scheduler_contract_report.json"

ACTIONS = (
    "CPU_ONLY",
    "CPU_CAMERA_ACCELERATOR",
    "CPU_LIDAR_ACCELERATOR",
    "CPU_COMBINED_ACCELERATORS",
)

MODES = (
    "NORMAL_CANDIDATE",
    "DEGRADED_CANDIDATE",
    "HOLD_OR_ALERT",
)

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def nonnegative(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value >= 0

def validate_state(state):
    required = (
        "health_mode",
        "quality_authorization",
        "cpu_latency_ms",
        "deadline_ms",
        "queue_depth",
        "workload_id",
        "workload_source",
        "health_source",
    )
    for field in required:
        if field not in state:
            raise ValueError("Missing state field: " + field)

    if state["health_mode"] not in MODES:
        raise ValueError("Unknown health mode")

    if state["quality_authorization"] != "UNVERIFIED":
        raise ValueError("Unverified evidence cannot authorize quality")

    if not nonnegative(state["cpu_latency_ms"]):
        raise ValueError("Invalid CPU latency")

    deadline = state["deadline_ms"]
    if deadline is not None and (
        not nonnegative(deadline) or deadline == 0
    ):
        raise ValueError("Invalid deadline")

    depth = state["queue_depth"]
    if type(depth) is not int or depth < 0:
        raise ValueError("Invalid queue depth")

    if not state["workload_id"]:
        raise ValueError("Missing workload identifier")

    if not state["workload_source"] or not state["health_source"]:
        raise ValueError("Missing evidence provenance")

    return True

def safe_baseline(state):
    validate_state(state)

    if state["health_mode"] == "HOLD_OR_ALERT":
        return {
            "processing_placement": "CPU_ONLY",
            "result_permission": "WITHHOLD_VALID_RESULT",
            "reason": "REQUIRED_SENSOR_UNAVAILABLE",
            "deadline_verified": False,
            "quality_verified": False,
            "fpga_executed": False,
        }

    return {
        "processing_placement": "CPU_ONLY",
        "result_permission": "PROVISIONAL_ONLY",
        "reason": "BASELINE_NO_HARDWARE_MODEL",
        "deadline_verified": (
            state["deadline_ms"] is not None
            and state["cpu_latency_ms"] <= state["deadline_ms"]
        ),
        "quality_verified": False,
        "fpga_executed": False,
    }

def main():
    if SCHEMA.exists() or REPORT.exists():
        raise FileExistsError("Existing scheduler artifacts preserved")

    ledger = read_csv(LEDGER)
    health = read_csv(HEALTH)

    if len(ledger) != 93 or len(health) != 168:
        raise RuntimeError("Input evidence counts changed")

    ids = [r["WorkloadID"] for r in ledger]
    if len(set(ids)) != 93:
        raise RuntimeError("Duplicate workload identifiers")

    for row in ledger:
        for field in ("CPU_MedianMs", "CPU_P95Ms", "CPU_P99Ms"):
            value = float(row[field])
            if not nonnegative(value):
                raise RuntimeError("Invalid measured CPU timing")

        if row["MeasurementOrigin"] != "WORKSTATION_CPU":
            raise RuntimeError("Unexpected timing provenance")

    modes = {r["controller_mode"] for r in health}
    if modes != set(MODES):
        raise RuntimeError("Unexpected sensor-health modes")

    for row in health:
        if row["quality_authorization"] != "UNVERIFIED":
            raise RuntimeError("Unexpected quality authorization")

    lr = next(r for r in ledger if r["WorkloadType"] == "LIDAR_RADAR")

    def example(mode):
        return {
            "health_mode": mode,
            "quality_authorization": "UNVERIFIED",
            "cpu_latency_ms": float(lr["CPU_P99Ms"]),
            "deadline_ms": None,
            "queue_depth": 0,
            "workload_id": lr["WorkloadID"],
            "workload_source": "TASK29_4B6_CPU_REFERENCE",
            "health_source": "TASK29_4B10_FAULT_REPLAY",
        }

    decisions = {
        mode: safe_baseline(example(mode))
        for mode in MODES
    }

    assert decisions["HOLD_OR_ALERT"]["result_permission"] == (
        "WITHHOLD_VALID_RESULT"
    )
    assert decisions["NORMAL_CANDIDATE"]["result_permission"] == (
        "PROVISIONAL_ONLY"
    )
    assert decisions["DEGRADED_CANDIDATE"]["result_permission"] == (
        "PROVISIONAL_ONLY"
    )

    invalid_tests = 0
    for field, value in (
        ("cpu_latency_ms", -1.0),
        ("deadline_ms", -5.0),
        ("queue_depth", -1),
        ("quality_authorization", "VALIDATED"),
    ):
        bad = example("NORMAL_CANDIDATE")
        bad[field] = value
        try:
            validate_state(bad)
        except ValueError:
            invalid_tests += 1
        else:
            raise AssertionError("Invalid input accepted: " + field)

    schema = {
        "task": "29.4C.1",
        "actions": list(ACTIONS),
        "required_state_fields": [
            "health_mode",
            "quality_authorization",
            "cpu_latency_ms",
            "deadline_ms",
            "queue_depth",
            "workload_id",
            "workload_source",
            "health_source",
        ],
        "latency_units": "milliseconds",
        "cpu_reference": "measured_workstation_cpu",
        "fpga_execution_ms": None,
        "dma_transfer_ms": None,
        "mode_switch_ms": None,
        "cpu_power_w": None,
        "fpga_power_w": None,
        "energy_model_calibrated": False,
        "quality_constraint_calibrated": False,
        "input_pairing": "SEPARATE_REFERENCES_NOT_SYNCHRONIZED",
        "deadline_policy": "NOT_YET_SPECIFIED",
        "currently_executable_action": "CPU_ONLY",
        "offload_actions": "DECLARED_NOT_IMPLEMENTED",
    }

    report = {
        "task": "29.4C.1",
        "status": "PASS",
        "cpu_workload_references": len(ledger),
        "sensor_health_states": len(health),
        "health_modes_tested": len(decisions),
        "invalid_inputs_rejected": invalid_tests,
        "ledger_sha256": digest(LEDGER),
        "health_sha256": digest(HEALTH),
        "baseline_decisions": decisions,
        "adaptive_placement_implemented": False,
        "hardware_energy_measured": False,
        "full_pipeline_synchronized": False,
    }

    with SCHEMA.open("x", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("CPU_WORKLOAD_REFERENCES:", len(ledger))
    print("SENSOR_HEALTH_STATES:", len(health))
    print("HEALTH_MODES_TESTED:", len(decisions))
    print("INVALID_INPUTS_REJECTED:", invalid_tests)
    print("BASELINE_ACTION: CPU_ONLY")
    print("FPGA_OFFLOAD: NOT_IMPLEMENTED")
    print("SYNCHRONIZED_INPUTS: NOT_CLAIMED")
    print("TASK 29.4C.1: PASS")

if __name__ == "__main__":
    main()
