import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"

sys.path.insert(0, str(TASK / "04_Code"))

import task29_4C3_stage_aware_scheduler as stage
import task29_4C7_energy_optimizer as optimizer

TIMING = TASK / "03_Configurations" / "task29_4C3_assumptions.json"
POWER = TASK / "03_Configurations" / "task29_4C6_energy_assumptions.json"
PRIOR = TASK / "06_Research_Findings" / "task29_4C9_four_policy_report.json"

OUT = TASK / "02_CSV_Data" / "task29_4C10_power_sensitivity.csv"
REPORT = TASK / "06_Research_Findings" / "task29_4C10_power_sensitivity_report.json"

CPU = optimizer.CPU
CAM = optimizer.CAM
LIDAR = optimizer.LIDAR
BOTH = optimizer.BOTH

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main():
    if OUT.exists() or REPORT.exists():
        raise FileExistsError("Existing output preserved")

    timing = load(TIMING)
    base_power = load(POWER)
    prior = load(PRIOR)

    if prior["status"] != "PASS" or prior["policies_compared"] != 4:
        raise RuntimeError("Four-policy reference missing")

    if (
        timing["measured_fpga_execution"] is not False
        or base_power["actual_power_measured"] is not False
        or base_power["actual_fpga_executed"] is not False
    ):
        raise RuntimeError("Hardware evidence provenance violation")

    models = stage.build_models(timing)

    def power_profile(camera=None, lidar=None):
        p = dict(base_power)
        if camera is not None:
            p["fpga_camera_active_w"] = camera
        if lidar is not None:
            p["fpga_lidar_active_w"] = lidar
        return p

    profiles = {
        "BASE_ASSUMPTIONS": power_profile(),
        "HIGH_CAMERA_FPGA_POWER": power_profile(camera=100.0),
        "HIGH_LIDAR_FPGA_POWER": power_profile(lidar=100.0),
        "HIGH_BOTH_FPGA_POWER": power_profile(
            camera=100.0, lidar=100.0
        ),
    }

    cpu_time = (
        models["camera"]["cpu_ms"]
        + models["lidar"]["cpu_ms"]
    )
    relaxed_deadline = cpu_time * 2

    rows = []

    def test(name, engine, deadline, tick, mode, expected):
        before = engine.previous

        costs_before = {
            a: engine.evaluate(a)
            for a in optimizer.ACTIONS
        }

        decision = engine.decide(deadline, mode, tick)

        if decision["action"] != expected:
            raise AssertionError(
                name + ": expected " + expected
                + ", got " + decision["action"]
            )

        if mode != "HOLD_OR_ALERT":
            selected = decision["action"]
            if selected not in optimizer.ACTIONS:
                raise AssertionError("Invalid selected action")

            if decision["energy_mj"] < 0:
                raise AssertionError("Negative energy")

            if decision["permission"] != "PROVISIONAL_ONLY":
                raise AssertionError("Unverified quality authorized")
        else:
            if decision["permission"] != "WITHHOLD_VALID_RESULT":
                raise AssertionError("Safety authorization failure")

        rows.append({
            "test": name,
            "tick": tick,
            "previous_action": before,
            "selected_action": decision["action"],
            "deadline_ms": deadline,
            "health_mode": mode,
            "camera_fpga_power_assumed_w":
                engine.power["fpga_camera_active_w"],
            "lidar_fpga_power_assumed_w":
                engine.power["fpga_lidar_active_w"],
            "cpu_candidate_energy_mj":
                round(costs_before[CPU]["energy_mj"], 6),
            "camera_candidate_energy_mj":
                round(costs_before[CAM]["energy_mj"], 6),
            "lidar_candidate_energy_mj":
                round(costs_before[LIDAR]["energy_mj"], 6),
            "combined_candidate_energy_mj":
                round(costs_before[BOTH]["energy_mj"], 6),
            "selected_energy_mj": decision["energy_mj"],
            "selected_latency_ms": decision["latency_ms"],
            "deadline_met": decision["deadline_met"],
            "reason": decision["reason"],
            "cost_origin": "HYPOTHETICAL_POWER_AND_FPGA",
            "fpga_executed": False,
            "quality_verified": False,
        })

        print(
            name,
            "=>", decision["action"],
            "REASON:", decision["reason"],
            flush=True
        )
        return decision

    # Four independent power sensitivity cases.
    expected = {
        "BASE_ASSUMPTIONS": BOTH,
        "HIGH_CAMERA_FPGA_POWER": LIDAR,
        "HIGH_LIDAR_FPGA_POWER": CAM,
        "HIGH_BOTH_FPGA_POWER": CPU,
    }

    for name, p in profiles.items():
        test(
            name,
            optimizer.EnergyScheduler(models, timing, p),
            relaxed_deadline,
            0,
            "NORMAL_CANDIDATE",
            expected[name]
        )

    # A deadline may require faster hardware even when
    # its hypothetical active energy is very expensive.
    tight = optimizer.EnergyScheduler(
        models, timing,
        profiles["HIGH_BOTH_FPGA_POWER"]
    )

    costs = {
        a: tight.evaluate(a)["latency_ms"]
        for a in optimizer.ACTIONS
    }

    if not costs[BOTH] < costs[CAM]:
        raise AssertionError("Unexpected modeled latency ordering")

    deadline = (costs[BOTH] + costs[CAM]) / 2

    # Ensure combined is the only deadline-feasible action.
    if any(
        costs[a] <= deadline
        for a in (CPU, CAM, LIDAR)
    ):
        raise AssertionError(
            "Sensitivity deadline is not uniquely restrictive"
        )

    test(
        "EXPENSIVE_BUT_DEADLINE_REQUIRED",
        tight, deadline, 0,
        "NORMAL_CANDIDATE", BOTH
    )

    test(
        "SAFETY_HOLD",
        optimizer.EnergyScheduler(
            models, timing, profiles["BASE_ASSUMPTIONS"]
        ),
        relaxed_deadline, 0,
        "HOLD_OR_ALERT", "NO_EXECUTION"
    )

    # Sequential operating-condition change.
    # Cooldown should prevent immediate oscillation.
    changing = optimizer.EnergyScheduler(
        models, timing, profiles["BASE_ASSUMPTIONS"]
    )

    test(
        "SEQUENCE_ENTER_COMBINED",
        changing, relaxed_deadline, 0,
        "NORMAL_CANDIDATE", BOTH
    )

    changing.power = dict(
        profiles["HIGH_BOTH_FPGA_POWER"]
    )

    retained = test(
        "SEQUENCE_COOLDOWN",
        changing, relaxed_deadline, 1,
        "NORMAL_CANDIDATE", BOTH
    )

    if retained["reason"] != "SWITCH_COOLDOWN":
        raise AssertionError("Cooldown did not engage")

    if retained["switch_ms"] != 0:
        raise AssertionError(
            "Switching penalty charged while retaining placement"
        )

    test(
        "SEQUENCE_SWITCH_TO_CPU",
        changing, relaxed_deadline, 2,
        "NORMAL_CANDIDATE", CPU
    )

    if len(rows) != 9:
        raise AssertionError("Expected nine sensitivity tests")

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "task": "29.4C.10",
        "status": "PASS",
        "unit_tests": len(rows),
        "independent_power_profiles": len(profiles),
        "expected_placement_for_each_profile": expected,
        "dynamic_switching_tested": True,
        "cooldown_tested": True,
        "deadline_priority_tested": True,
        "safety_hold_tested": True,
        "hardware_costs": "HYPOTHETICAL",
        "sensor_data_pairing": "SYNTHETIC_REFERENCE",
        "actual_fpga_executed": False,
        "real_energy_savings_measured": False,
        "four_weather_scenarios_executed": False,
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("UNIT_TESTS:", len(rows))
    print("POWER_PROFILES:", len(profiles))
    print("DYNAMIC_SWITCHING: PASS")
    print("SWITCH_COOLDOWN: PASS")
    print("DEADLINE_PRIORITY: PASS")
    print("SAFETY_HOLD: PASS")
    print("REAL_HARDWARE_MEASUREMENTS: NONE")
    print("TASK 29.4C.10: PASS")

if __name__ == "__main__":
    main()
