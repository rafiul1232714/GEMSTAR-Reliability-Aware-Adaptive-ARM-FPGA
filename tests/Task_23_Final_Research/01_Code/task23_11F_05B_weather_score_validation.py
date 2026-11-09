import csv
import math
import sys
from pathlib import Path

task = Path(sys.argv[1])

source = (
    task / "02_CSV_Data" /
    "task23_11F_04B_reliability_summary.csv"
)

with source.open(encoding="utf-8-sig", newline="") as f:
    records = list(csv.DictReader(f))

if len(records) != 3:
    raise RuntimeError("Expected exactly three weather records")

scores = {}

for row in records:
    weather = row["weather"]

    if weather in scores:
        raise RuntimeError("Duplicate weather: " + weather)

    score = float(row["mean_score"])

    if not math.isfinite(score) or not 0 <= score <= 1:
        raise RuntimeError("Invalid score: " + weather)

    scores[weather] = score

if set(scores) != {"Clear", "Fog100", "Fog20"}:
    raise RuntimeError("Missing or unexpected weather condition")

clear = scores["Clear"]
fog100 = scores["Fog100"]
fog20 = scores["Fog20"]

tolerance = 1e-10

if abs(clear - fog100) > tolerance:
    raise RuntimeError("Clear and Fog100 scores differ")

if not clear > fog20:
    raise RuntimeError("Expected lower availability under Fog20")

if abs(fog20) > tolerance:
    raise RuntimeError("Fog20 score should be zero")

if abs(clear - 5090 / 5271) > tolerance:
    raise RuntimeError("Clear score differs from measured reference")

print(f"CLEAR_SCORE={clear:.9f}")
print(f"FOG100_SCORE={fog100:.9f}")
print(f"FOG20_SCORE={fog20:.9f}")

print(f"CLEAR_MINUS_FOG100={clear - fog100:.9f}")
print(f"CLEAR_MINUS_FOG20={clear - fog20:.9f}")

print("WEATHER_SCORE_ORDERING=PASS")
print("TASK23_11F_05B_WEATHER_VALIDATION_PASS")
