from types import SimpleNamespace
from task23_11F_lidar_reliability import score_lidar_frame


def view(reflections):
    return SimpleNamespace(reflection=reflections)


def reflection(tof=1e-8, strength=1.0):
    return SimpleNamespace(
        time_of_flight=tof,
        signal_strength=strength
    )


cases = [
    ("MISSING_FRAME", None, 10.0, 9.0, "MISSING_FRAME", None),
    ("EMPTY_FRAME", view([]), 10.0, 9.0, "EMPTY_FRAME", None),
    ("MISSING_TIMESTAMP", view([reflection()]), None, 9.0,
     "INVALID_TIMESTAMP", None),
    ("NAN_TIMESTAMP", view([reflection()]), float("nan"), 9.0,
     "INVALID_TIMESTAMP", None),
    ("INFINITE_TIMESTAMP", view([reflection()]), float("inf"), 9.0,
     "INVALID_TIMESTAMP", None),
    ("NEGATIVE_TIMESTAMP", view([reflection()]), -1.0, None,
     "INVALID_TIMESTAMP", None),
    ("DUPLICATE_TIMESTAMP", view([reflection()]), 10.0, 10.0,
     "INVALID_TIMESTAMP", None),
    ("BACKWARD_TIMESTAMP", view([reflection()]), 9.0, 10.0,
     "INVALID_TIMESTAMP", None),
    ("INVALID_PREVIOUS_TIMESTAMP", view([reflection()]), 10.0,
     float("nan"), "INVALID_TIMESTAMP", None),
    ("VALID_FIRST_TIMESTAMP_ZERO", view([reflection()]), 0.0,
     None, "VALID", 1.0),
]

passed = 0

for name, lidar, timestamp, previous, status, score in cases:
    result = score_lidar_frame(lidar, timestamp, previous)

    assert result.status == status, (
        f"{name}: expected {status}, got {result.status}"
    )

    assert result.availability_score == score, (
        f"{name}: incorrect score"
    )

    passed += 1
    print(f"{name}: PASS")


# Structural robustness checks.
# These are diagnostic tests: a crash is reported, not hidden.
structural = [
    ("MISSING_REFLECTION_ATTRIBUTE", SimpleNamespace(), 10.0),
    ("NULL_REFLECTION_COLLECTION",
     SimpleNamespace(reflection=None), 10.0),
    ("MISSING_TIME_OF_FLIGHT",
     view([SimpleNamespace(signal_strength=1.0)]), 10.0),
    ("MISSING_SIGNAL_STRENGTH",
     view([SimpleNamespace(time_of_flight=1e-8)]), 10.0),
]

structural_failures = []

for name, lidar, timestamp in structural:
    try:
        result = score_lidar_frame(lidar, timestamp, 9.0)
        print(f"{name}: RETURNED status={result.status}")
    except Exception as exc:
        structural_failures.append(name)
        print(
            f"{name}: EXCEPTION "
            f"{type(exc).__name__}: {exc}"
        )

print(f"\nSTANDARD_TESTS_PASSED={passed}/{len(cases)}")
print(
    f"STRUCTURAL_EXCEPTIONS="
    f"{len(structural_failures)}/{len(structural)}"
)

if passed != len(cases):
    raise RuntimeError("Standard robustness tests failed")

print("TASK23_11F_06B_DIAGNOSTIC_TESTS_COMPLETE")
