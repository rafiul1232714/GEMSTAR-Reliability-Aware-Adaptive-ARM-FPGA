from types import SimpleNamespace
from task23_11F_lidar_reliability import score_lidar_frame


def make_view(reflections):
    return SimpleNamespace(reflection=reflections)


cases = [
    ("MISSING_REFLECTION_ATTRIBUTE",
     SimpleNamespace(), 0),

    ("NULL_REFLECTION_COLLECTION",
     make_view(None), 0),

    ("MISSING_TIME_OF_FLIGHT",
     make_view([SimpleNamespace(signal_strength=1.0)]), 1),

    ("MISSING_SIGNAL_STRENGTH",
     make_view([SimpleNamespace(time_of_flight=1e-8)]), 1),
]

for name, lidar, expected_total in cases:
    result = score_lidar_frame(
        lidar,
        timestamp=10.0,
        previous_timestamp=9.0
    )

    assert result.status == "MALFORMED_FRAME", (
        f"{name}: incorrect status"
    )

    assert result.availability_score is None, (
        f"{name}: score should be undefined"
    )

    assert result.positive_returns == 0, (
        f"{name}: unexpected positive count"
    )

    assert result.total_reflections == expected_total, (
        f"{name}: unexpected reflection count"
    )

    print(f"{name}: PASS | status={result.status}")


# Confirm the existing valid-zero-return distinction.
valid_zero = make_view([
    SimpleNamespace(
        time_of_flight=1e-8,
        signal_strength=0.0
    )
])

result = score_lidar_frame(valid_zero, 10.0, 9.0)

assert result.status == "NO_RETURNS"
assert result.availability_score == 0.0
assert result.total_reflections == 1

print("VALID_ZERO_RETURN_DISTINCTION: PASS")

print("TOTAL_ASSERTIONS=5")
print("TASK23_11F_06B2_MALFORMED_ASSERTIONS_PASS")
