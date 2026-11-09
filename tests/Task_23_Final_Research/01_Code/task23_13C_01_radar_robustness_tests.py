import csv
import math
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV_PATH = (
    TASK / "02_CSV_Data"
    / "task23_13C_01_radar_robustness_tests.csv"
)

C = 299792458.0

def preprocess_radar_return(tof, strength):
    """Decode a valid Radar reflection or reject invalid inputs."""

    if isinstance(tof, bool) or isinstance(strength, bool):
        raise ValueError("Boolean Radar input is invalid")

    if not isinstance(tof, (int, float)):
        raise TypeError("Time-of-flight must be numeric")

    if not isinstance(strength, (int, float)):
        raise TypeError("Signal strength must be numeric")

    if not math.isfinite(tof) or not math.isfinite(strength):
        raise ValueError("Nonfinite Radar measurement")

    if tof <= 0 or strength <= 0:
        raise ValueError("Non-positive Radar measurement")

    range_m = C * tof / 2.0

    if not math.isfinite(range_m) or range_m <= 0:
        raise ValueError("Invalid calculated range")

    return {
        "status": "VALID",
        "range_m": range_m,
        "signal_strength": float(strength),
    }


tests = [
    ("VALID_BASELINE", 5.6949722052e-8, 0.51504362, True),
    ("VALID_DISPLACED", 7.03496585692e-8, 0.47833541, True),
    ("ZERO_TOF", 0.0, 0.5, False),
    ("NEGATIVE_TOF", -1.0e-8, 0.5, False),
    ("ZERO_STRENGTH", 5.7e-8, 0.0, False),
    ("NEGATIVE_STRENGTH", 5.7e-8, -0.5, False),
    ("NAN_TOF", float("nan"), 0.5, False),
    ("INFINITE_TOF", float("inf"), 0.5, False),
    ("NAN_STRENGTH", 5.7e-8, float("nan"), False),
    ("MISSING_TOF", None, 0.5, False),
    ("STRING_TOF", "invalid", 0.5, False),
    ("BOOLEAN_TOF", True, 0.5, False),
]

if CSV_PATH.exists():
    raise RuntimeError("CSV already exists")

rows = []
failures = 0

for name, tof, strength, expected_accept in tests:

    accepted = False
    error_type = ""
    calculated_range = ""

    try:
        result = preprocess_radar_return(tof, strength)
        accepted = result["status"] == "VALID"
        calculated_range = result["range_m"]

    except (TypeError, ValueError) as exc:
        error_type = type(exc).__name__

    passed = accepted == expected_accept
    failures += int(not passed)

    rows.append({
        "Test": name,
        "ExpectedAccept": expected_accept,
        "ActualAccept": accepted,
        "ErrorType": error_type,
        "RangeM": calculated_range,
        "Result": "PASS" if passed else "FAIL",
    })

    print(
        f"TEST={name} "
        f"EXPECTED={expected_accept} "
        f"ACTUAL={accepted} "
        f"RESULT={'PASS' if passed else 'FAIL'}"
    )

with CSV_PATH.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV_SAVED={CSV_PATH}")
print(f"TESTS_TOTAL={len(rows)}")
print(f"TESTS_PASSED={len(rows) - failures}")
print(f"TESTS_FAILED={failures}")

if failures:
    raise RuntimeError("Radar robustness test failure")

print("TASK23_13C_01_RADAR_ROBUSTNESS_PASS")
