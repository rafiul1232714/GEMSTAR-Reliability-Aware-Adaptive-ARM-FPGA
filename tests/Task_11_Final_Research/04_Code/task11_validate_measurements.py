
from pathlib import Path
import csv
import math
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

ARCHIVE = (
    ROOT / "tests"
    / "Task_11_Final_Research"
)

DATA = ARCHIVE / "02_CSV_Data"
FINDINGS = ARCHIVE / "06_Research_Findings"

FINDINGS.mkdir(parents=True, exist_ok=True)


def analyze_sensor(filename, sensor_name):

    path = DATA / filename

    total = 0
    near_zero = 0
    beyond_01 = 0
    beyond_05 = 0
    beyond_1 = 0

    maximum = 0.0
    object_ids = Counter()

    with path.open("r", encoding="utf-8", newline="") as f:

        reader = csv.DictReader(f)

        for row in reader:

            distance = float(row["range_m"])
            total += 1

            if not math.isfinite(distance):
                continue

            if distance < 0.1:
                near_zero += 1

            if distance >= 0.1:
                beyond_01 += 1

            if distance >= 0.5:
                beyond_05 += 1

            if distance >= 1.0:
                beyond_1 += 1

            maximum = max(maximum, distance)

            if "object_id_diagnostic" in row:
                obj = row["object_id_diagnostic"]
                if obj:
                    object_ids[obj] += 1

    print(f"\n===== {sensor_name} =====")
    print("Total positive reflections:", total)
    print("Near-zero (<0.1 m):", near_zero)
    print("Range >= 0.1 m:", beyond_01)
    print("Range >= 0.5 m:", beyond_05)
    print("Range >= 1.0 m:", beyond_1)
    print("Maximum range (m):", maximum)

    if object_ids:
        print("Most frequent object IDs:")
        for obj, count in object_ids.most_common(5):
            print(" ", obj, count)

    return [
        [sensor_name, "total_positive", total],
        [sensor_name, "near_zero_lt_0_1m", near_zero],
        [sensor_name, "range_ge_0_1m", beyond_01],
        [sensor_name, "range_ge_0_5m", beyond_05],
        [sensor_name, "range_ge_1m", beyond_1],
        [sensor_name, "maximum_range_m", maximum]
    ]


summary = []

summary.extend(
    analyze_sensor(
        "task11_lidar_measurements.csv",
        "LiDAR"
    )
)

summary.extend(
    analyze_sensor(
        "task11_radar_measurements.csv",
        "Radar"
    )
)

output = DATA / "task11_measurement_validation.csv"

with output.open("w", encoding="utf-8", newline="") as f:

    writer = csv.writer(f)
    writer.writerow(["sensor", "metric", "value"])
    writer.writerows(summary)

print("\nSaved:", output)
print("TASK 11.3A COMPLETED")
