import csv
import math
import sys
from pathlib import Path

task = Path(sys.argv[1])
csv_dir = task / "02_CSV_Data"

frame_file = csv_dir / "task23_11F_04B_frame_reliability.csv"
summary_file = csv_dir / "task23_11F_04B_reliability_summary.csv"
baseline_file = csv_dir / "task23_11E_three_weather_comparison.csv"

with baseline_file.open(encoding="utf-8-sig", newline="") as f:
    baseline_rows = list(csv.DictReader(f))

with summary_file.open(encoding="utf-8-sig", newline="") as f:
    summary_rows = list(csv.DictReader(f))

baseline = {r["Weather"]: r for r in baseline_rows}
summary = {r["weather"]: r for r in summary_rows}

expected = {"Clear", "Fog100", "Fog20"}

assert len(baseline_rows) == 3
assert len(summary_rows) == 3
assert set(baseline) == expected
assert set(summary) == expected

counts = {name: 0 for name in expected}
previous_times = {name: None for name in expected}
sums = {name: 0.0 for name in expected}
minimums = {name: math.inf for name in expected}
maximums = {name: -math.inf for name in expected}

with frame_file.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        name = row["weather"]

        if name not in expected:
            raise AssertionError("Unknown weather: " + name)

        index = int(row["frame_index"])
        timestamp = float(row["timestamp_seconds"])
        positive = int(row["positive_returns"])
        total = int(row["total_reflections"])
        score = float(row["availability_score"])

        if index != counts[name]:
            raise AssertionError(f"{name}: invalid frame sequence")

        if not math.isfinite(timestamp) or timestamp < 0:
            raise AssertionError(f"{name}: invalid timestamp")

        previous = previous_times[name]

        if previous is not None and timestamp <= previous:
            raise AssertionError(f"{name}: timestamps not increasing")

        if not math.isfinite(score) or not (0 <= score <= 1):
            raise AssertionError(f"{name}: score outside [0,1]")

        expected_positive = int(
            baseline[name]["PositiveReturnsPerFrame"]
        )

        expected_total = int(
            baseline[name]["ReflectionSlotsPerFrame"]
        )

        if positive != expected_positive or total != expected_total:
            raise AssertionError(f"{name}: return count mismatch")

        calculated = positive / total

        if abs(score - calculated) > 1e-10:
            raise AssertionError(f"{name}: incorrect score")

        expected_status = "VALID" if positive > 0 else "NO_RETURNS"

        if row["status"] != expected_status:
            raise AssertionError(f"{name}: status mismatch")

        counts[name] += 1
        previous_times[name] = timestamp
        sums[name] += score
        minimums[name] = min(minimums[name], score)
        maximums[name] = max(maximums[name], score)

for name in ("Clear", "Fog100", "Fog20"):
    expected_frames = int(baseline[name]["TotalFrames"])

    if counts[name] != expected_frames:
        raise AssertionError(f"{name}: frame count mismatch")

    recorded = summary[name]

    if int(recorded["frames"]) != counts[name]:
        raise AssertionError(f"{name}: summary frame mismatch")

    mean_score = sums[name] / counts[name]

    for field, value in (
        ("mean_score", mean_score),
        ("min_score", minimums[name]),
        ("max_score", maximums[name])
    ):
        if abs(float(recorded[field]) - value) > 1e-10:
            raise AssertionError(f"{name}: {field} mismatch")

    print(
        f"{name}: PASS | "
        f"FRAMES={counts[name]} | "
        f"MEAN_SCORE={mean_score:.9f} | "
        f"TIMESTAMPS=VALID"
    )

print(f"TOTAL_VALIDATED_FRAMES={sum(counts.values())}")
print("TASK23_11F_05A_CSV_VALIDATION_PASS")
