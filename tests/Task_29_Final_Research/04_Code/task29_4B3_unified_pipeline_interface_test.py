import sys
import json
from pathlib import Path

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
)

SOURCE = (
    ROOT / "tests" / "Task_23_Final_Research"
    / "01_Code"
)

OUTPUT = (
    ROOT / "tests" / "Task_29_Final_Research"
    / "06_Research_Findings"
    / "task29_4B3_unified_pipeline_interface_test.json"
)

sys.path.insert(0, str(SOURCE))

from task23_15_unified_preprocessing import (
    make_measurement,
)
from task23_15_timestamp_bundle import (
    evaluate_bundle,
)

def sensor(name, timestamp, status="VALID"):
    frame = {
        "camera": "CAMERA_LOCAL",
        "lidar": "LIDAR_LOCAL",
        "radar": "RADAR_LOCAL",
    }[name]

    return make_measurement(
        sensor=name,
        timestamp_ns=timestamp,
        coordinate_frame=frame,
        status=status,
        quality={},
        data=None,
    )

def main():
    print("=== TASK 29.4B.3 ===", flush=True)

    t = 1_000_000_000

    # Case 1: All three sensors aligned and valid.
    aligned = {
        "camera": sensor("camera", t),
        "lidar": sensor("lidar", t),
        "radar": sensor("radar", t),
    }

    result1 = evaluate_bundle(
        aligned, t, max_delta_ns=0
    )

    assert result1["ready_for_fusion"] is True
    print("ALIGNED_BUNDLE: PASS", flush=True)

    # Case 2: Radar is missing.
    missing = {
        "camera": sensor("camera", t),
        "lidar": sensor("lidar", t),
    }

    result2 = evaluate_bundle(
        missing, t, max_delta_ns=0
    )

    assert result2["ready_for_fusion"] is False
    assert (
        result2["sensors"]["radar"]["status"]
        == "MISSING_SENSOR"
    )

    print("MISSING_RADAR: PASS", flush=True)

    # Case 3: Camera measurement is stale.
    stale = {
        "camera": sensor("camera", t - 100_000_000),
        "lidar": sensor("lidar", t),
        "radar": sensor("radar", t),
    }

    result3 = evaluate_bundle(
        stale, t, max_delta_ns=10_000_000
    )

    assert result3["ready_for_fusion"] is False
    assert (
        result3["sensors"]["camera"]["status"]
        == "STALE"
    )

    print("STALE_CAMERA: PASS", flush=True)

    # Case 4: Aligned timestamp but invalid data.
    invalid = {
        "camera": sensor(
            "camera", t, "INVALID_MEASUREMENT"
        ),
        "lidar": sensor("lidar", t),
        "radar": sensor("radar", t),
    }

    result4 = evaluate_bundle(
        invalid, t, max_delta_ns=0
    )

    assert result4["ready_for_fusion"] is False
    print("INVALID_CAMERA: PASS", flush=True)

    cases = {
        "aligned": result1,
        "missing_radar": result2,
        "stale_camera": result3,
        "invalid_camera": result4,
    }

    report = {
        "task": "29.4B.3",
        "status": "PASS",
        "test_type": "SYNTHETIC_METADATA_INTERFACE",
        "test_cases": 4,
        "source": "Task 23.15",
        "real_sensor_frames_processed": False,
        "independent_sensor_sync_verified": False,
        "cpu_pipeline_integrated": False,
        "adaptive_scheduler_implemented": False,
        "cases": cases,
    }

    OUTPUT.parent.mkdir(
        parents=True, exist_ok=True
    )

    with OUTPUT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("TEST_CASES: 4/4", flush=True)
    print("REAL_SENSOR_PROCESSING: NO", flush=True)
    print("ADAPTIVE_SCHEDULER: NOT YET", flush=True)

    print(
        "TASK 29.4B.3: PASS",
        flush=True
    )

if __name__ == "__main__":
    main()
