import sys
import json
import time
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TESTS = ROOT / "tests"

TASK25_CODE = TESTS / "Task_25_Final_Research" / "01_Code"
sys.path.insert(0, str(TASK25_CODE))

import task25_replay as fusion

INPUT = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
    / "C02_V2_EKF_Input_53Frames_V1"
)

OUTPUT = (
    TESTS / "Task_29_Final_Research"
    / "06_Research_Findings"
    / "task29_4B9_ekf_reliability_integration.json"
)

def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)

    print("LOADING_ARCHIVED_EKF_INPUTS", flush=True)

    (
        tracks,
        radar,
        camera,
        reference,
        camera_reference,
        ground_truth,
        source_hashes,
    ) = fusion.load_inputs(INPUT)

    if len(tracks) != 24:
        raise RuntimeError("Expected 24 recorded track samples")

    if len(fusion.SCENARIOS) != 7:
        raise RuntimeError("Unexpected fault scenario count")

    results = []
    summaries = []

    start = time.perf_counter_ns()

    for scenario in fusion.SCENARIOS:

        processed = fusion.replay(
            tracks, radar, camera, scenario
        )

        if len(processed) != 24:
            raise RuntimeError(
                f"{scenario}: unexpected sample count"
            )

        if len({
            row["frame"] for row in processed
        }) != 24:
            raise RuntimeError(
                f"{scenario}: duplicate frames"
            )

        results.extend(processed)

        summaries.append({
            "scenario": scenario,
            "samples": len(processed),
            "lidar_measurements_used": sum(
                int(r["lidar_used"])
                for r in processed
            ),
            "radar_updates_accepted": sum(
                r["radar_status"] == "ACCEPTED"
                for r in processed
            ),
            "radar_updates_rejected": sum(
                r["radar_status"] == "REJECTED_BY_NIS"
                for r in processed
            ),
            "camera_updates_experimental": sum(
                r["camera_status"]
                == "EXPERIMENTAL_ACCEPTED"
                for r in processed
            ),
        })

        print(
            "SCENARIO:",
            scenario,
            "SAMPLES:",
            len(processed),
            flush=True
        )

    end = time.perf_counter_ns()

    baseline = [
        row for row in results
        if row["scenario"] == "baseline"
    ]

    max_difference = fusion.validate_baseline(
        baseline,
        reference,
        camera_reference
    )

    if max_difference > 1e-5:
        raise AssertionError("Archived EKF reference mismatch")

    if len(results) != 168:
        raise RuntimeError("Expected 168 replay results")

    report = {
        "task": "29.4B.9",
        "status": "PASS",
        "source": "EXISTING_TASK25_EKF_REPLAY",
        "original_input_directory": str(INPUT),
        "recorded_track_samples": len(tracks),
        "fault_scenarios": len(fusion.SCENARIOS),
        "processed_scenario_samples": len(results),
        "archived_reference_match": True,
        "maximum_baseline_difference_m": max_difference,
        "scenario_summary": summaries,
        "input_file_hashes": source_hashes,
        "total_replay_wall_ms": (
            end - start
        ) / 1e6,
        "timing_is_representative_ekf_benchmark": False,
        "camera_association_calibrated": False,
        "three_sensor_ekf_accuracy_validated": False,
        "new_yolo_detections_integrated": False,
        "full_perception_pipeline_timed": False,
        "adaptive_scheduler_implemented": False,
        "hardware_energy_measured": False,
        "original_research_modified": False
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("EKF_TRACK_SAMPLES: 24", flush=True)
    print("FAULT_SCENARIOS: 7", flush=True)
    print("TOTAL_REPLAY_RESULTS: 168", flush=True)
    print(
        "MAX_BASELINE_DIFFERENCE_M:",
        max_difference,
        flush=True
    )
    print("ARCHIVED_REFERENCE_MATCH: PASS", flush=True)
    print("TASK 29.4B.9: PASS", flush=True)

if __name__ == "__main__":
    main()
