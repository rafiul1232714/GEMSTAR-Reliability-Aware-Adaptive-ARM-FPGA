"""Task 23.15: container-timestamp and missing-sensor readiness.

This module checks supplied timestamp metadata only.
It does not prove independent sensor acquisition synchronization.
"""

from task23_15_unified_preprocessing import (
    SensorMeasurement,
    validate_timestamp_ns,
)

SENSORS = ("camera", "lidar", "radar")


def evaluate_bundle(
    measurements,
    container_timestamp_ns,
    max_delta_ns=0,
):
    """Evaluate one proposed three-sensor measurement bundle."""

    if not validate_timestamp_ns(container_timestamp_ns):
        raise ValueError("Invalid container timestamp")

    if (
        type(max_delta_ns) is not int
        or max_delta_ns < 0
    ):
        raise ValueError("Invalid maximum timestamp difference")

    if not isinstance(measurements, dict):
        raise TypeError("measurements must be a dictionary")

    if set(measurements) - set(SENSORS):
        raise ValueError("Unknown sensor key")

    results = {}

    for sensor in SENSORS:
        measurement = measurements.get(sensor)

        if measurement is None:
            results[sensor] = {
                "status": "MISSING_SENSOR",
                "delta_ns": None,
                "source_status": None,
            }
            continue

        if not isinstance(measurement, SensorMeasurement):
            raise TypeError("Invalid sensor measurement object")

        if measurement.sensor != sensor:
            raise ValueError("Sensor identity mismatch")

        timestamp = measurement.timestamp_ns

        if not validate_timestamp_ns(timestamp):
            timing_status = "INVALID_TIMESTAMP"
            delta = None
        else:
            delta = timestamp - container_timestamp_ns

            if delta < -max_delta_ns:
                timing_status = "STALE"
            elif delta > max_delta_ns:
                timing_status = "FUTURE"
            else:
                timing_status = "ALIGNED_CONTAINER_TIME"

        results[sensor] = {
            "status": timing_status,
            "delta_ns": delta,
            "source_status": measurement.status,
        }

    all_aligned = all(
        results[s]["status"] == "ALIGNED_CONTAINER_TIME"
        for s in SENSORS
    )

    all_valid = all(
        results[s]["source_status"] == "VALID"
        for s in SENSORS
    )

    return {
        "container_timestamp_ns": container_timestamp_ns,
        "max_delta_ns": max_delta_ns,
        "sensors": results,
        "all_container_times_aligned": all_aligned,
        "all_measurements_valid": all_valid,
        "ready_for_fusion": all_aligned and all_valid,
        "independent_acquisition_sync_verified": False,
        "same_run_provenance_verified": False,
    }


if __name__ == "__main__":
    print("TASK23_15B_07A_TIMESTAMP_MODULE_PASS")
