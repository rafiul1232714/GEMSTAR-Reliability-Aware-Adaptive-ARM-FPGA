import math
from types import SimpleNamespace

from task23_11F_lidar_reliability import score_lidar_frame


def make_reflection(tof, strength):
    return SimpleNamespace(
        time_of_flight=tof,
        signal_strength=strength
    )


def test_case(name, reflections, expected_positive, expected_status):
    view = SimpleNamespace(reflection=reflections)

    result = score_lidar_frame(
        view,
        timestamp=10.0,
        previous_timestamp=9.0
    )

    assert result.positive_returns == expected_positive, (
        f"{name}: positive count mismatch"
    )

    assert result.total_reflections == len(reflections), (
        f"{name}: total count mismatch"
    )

    assert result.status == expected_status, (
        f"{name}: status mismatch"
    )

    expected_score = expected_positive / len(reflections)

    assert result.availability_score is not None
    assert abs(result.availability_score - expected_score) < 1e-12

    print(
        f"{name}: PASS | "
        f"positive={result.positive_returns} | "
        f"score={result.availability_score:.6f}"
    )


cases = [
    (
        "NAN_TIME_OF_FLIGHT",
        [make_reflection(math.nan, 1.0)],
        0, "NO_RETURNS"
    ),
    (
        "NAN_SIGNAL_STRENGTH",
        [make_reflection(1e-8, math.nan)],
        0, "NO_RETURNS"
    ),
    (
        "INFINITE_TIME_OF_FLIGHT",
        [make_reflection(math.inf, 1.0)],
        0, "NO_RETURNS"
    ),
    (
        "INFINITE_SIGNAL_STRENGTH",
        [make_reflection(1e-8, math.inf)],
        0, "NO_RETURNS"
    ),
    (
        "NEGATIVE_TIME_OF_FLIGHT",
        [make_reflection(-1e-8, 1.0)],
        0, "NO_RETURNS"
    ),
    (
        "NEGATIVE_SIGNAL_STRENGTH",
        [make_reflection(1e-8, -1.0)],
        0, "NO_RETURNS"
    ),
    (
        "ZERO_TIME_OF_FLIGHT",
        [make_reflection(0.0, 1.0)],
        0, "NO_RETURNS"
    ),
    (
        "ZERO_SIGNAL_STRENGTH",
        [make_reflection(1e-8, 0.0)],
        0, "NO_RETURNS"
    ),
    (
        "MIXED_VALID_AND_INVALID",
        [
            make_reflection(1e-8, 1.0),
            make_reflection(math.nan, 1.0),
            make_reflection(2e-8, 0.5),
            make_reflection(3e-8, math.inf)
        ],
        2, "VALID"
    ),
]


for name, reflections, positive, status in cases:
    test_case(name, reflections, positive, status)


print(f"TOTAL_TESTS={len(cases)}")
print("TASK23_11F_06A_ABNORMAL_REFLECTION_TESTS_PASS")
