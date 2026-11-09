import csv
import math
from collections import Counter
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

SOURCE = (
    TASK / "08_Processed_Data"
    / "task23_04c_raw_lidar_measurements.csv"
)

REPORT = (
    TASK / "06_Research_Findings"
    / "task23_11C_mask_validation_report.txt"
)

C = 299792458.0
MIN_RANGE = 0.05
MAX_RANGE = 200.0
ABS_TOL_M = 1e-6

counts = Counter()
examples = []

with SOURCE.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        counts["Rows"] += 1

        tof = float(row["TimeOfFlightS"])
        strength = float(row["SignalStrength"])

        finite = math.isfinite(tof) and math.isfinite(strength)

        positive = finite and tof > 0 and strength > 0

        distance = C * tof / 2.0 if finite else math.nan

        screened = (
            positive
            and MIN_RANGE <= distance <= MAX_RANGE
        )

        stored_positive = int(row["PythonPositive"])
        stored_screened = int(row["PythonScreened"])
        stored_range = row["PythonRangeM"].strip()

        if positive:
            counts["PositiveReturns"] += 1

        if screened:
            counts["ScreenedReturns"] += 1

        problems = []

        if stored_positive != int(positive):
            counts["PositiveMaskMismatch"] += 1
            problems.append("positive mask mismatch")

        if stored_screened != int(screened):
            counts["ScreenedMaskMismatch"] += 1
            problems.append("screened mask mismatch")

        if screened:
            if not stored_range:
                counts["MissingAcceptedRange"] += 1
                problems.append("missing accepted range")
            else:
                saved_distance = float(stored_range)

                if (
                    not math.isfinite(saved_distance)
                    or not math.isclose(
                        saved_distance,
                        distance,
                        rel_tol=1e-9,
                        abs_tol=ABS_TOL_M
                    )
                ):
                    counts["RangeMismatch"] += 1
                    problems.append("range mismatch")
        elif stored_range:
            counts["RejectedRangeNotBlank"] += 1
            problems.append("rejected range not blank")

        if problems and len(examples) < 10:
            examples.append(
                f"Pair={row['PairID']} "
                f"Frame={row['Frame']} "
                f"Ray={row['RayIndex']}: "
                + ", ".join(problems)
            )

failure_keys = [
    "PositiveMaskMismatch",
    "ScreenedMaskMismatch",
    "MissingAcceptedRange",
    "RangeMismatch",
    "RejectedRangeNotBlank"
]

failures = sum(counts[key] for key in failure_keys)

status = (
    "MASK_VALIDATION_PASS"
    if counts["Rows"] > 0 and failures == 0
    else "MASK_VALIDATION_REQUIRES_INVESTIGATION"
)

lines = [
    "TASK 23.11.C - INDEPENDENT LIDAR MASK VALIDATION",
    f"Source: {SOURCE}",
    f"Total rows: {counts['Rows']}",
    f"Positive returns: {counts['PositiveReturns']}",
    f"Screened returns: {counts['ScreenedReturns']}",
    *[f"{key}: {counts[key]}" for key in failure_keys],
    f"Total mismatches: {failures}",
    f"Status: {status}",
    "",
    "Mismatch examples:",
    *(examples or ["None"])
]

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n".join(lines))
