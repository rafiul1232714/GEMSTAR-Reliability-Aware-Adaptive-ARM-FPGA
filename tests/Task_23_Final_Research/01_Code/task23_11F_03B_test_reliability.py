from types import SimpleNamespace
from task23_11F_lidar_reliability import score_lidar_frame


def reflection(tof, strength):
    return SimpleNamespace(
        time_of_flight=tof,
        signal_strength=strength
    )


def view(reflections):
    return SimpleNamespace(reflection=reflections)


cases = [
    (
        "ALL_VALID",
        view([reflection(1e-8, 1), reflection(2e-8, 1)]),
        1.0, None, "VALID", 1.0
    ),
    (
        "HALF_VALID",
        view([reflection(1e-8, 1), reflection(2e-8, 0)]),
        2.0, 1.0, "VALID", 0.5
    ),
    (
        "NO_RETURNS",
        view([reflection(1e-8, 0), reflection(2e-8, 0)]),
        3.0, 2.0, "NO_RETURNS", 0.0
    ),
    (
        "MISSING_FRAME",
        None,
        4.0, 3.0, "MISSING_FRAME", None
    ),
    (
        "EMPTY_FRAME",
        view([]),
        5.0, 4.0, "EMPTY_FRAME", None
    ),
    (
        "INVALID_TIMESTAMP",
        view([reflection(1e-8, 1)]),
        float("nan"), 5.0, "INVALID_TIMESTAMP", None
    ),
    (
        "NON_INCREASING_TIMESTAMP",
        view([reflection(1e-8, 1)]),
        5.0, 5.0, "INVALID_TIMESTAMP", None
    ),
]

for name, lidar, timestamp, previous, expected_status, expected_score in cases:
    result = score_lidar_frame(
        lidar,
        timestamp,
        previous_timestamp=previous
    )

    assert result.status == expected_status, (
        f"{name}: unexpected status {result.status}"
    )

    if expected_score is None:
        assert result.availability_score is None, (
            f"{name}: expected undefined score"
        )
    else:
        assert abs(result.availability_score - expected_score) < 1e-12, (
            f"{name}: unexpected score {result.availability_score}"
        )

    print(
        f"{name}: PASS | "
        f"status={result.status} | "
        f"score={result.availability_score}"
    )

print(f"TOTAL_TESTS={len(cases)}")
print("TASK23_11F_03B_UNIT_TESTS_PASS")
