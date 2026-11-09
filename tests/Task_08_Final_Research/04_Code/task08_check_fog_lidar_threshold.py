
from pathlib import Path
import csv
import math

from osi3.osi_sensorview_pb2 import SensorView

# TASK 8.15.2 - CHECK FOG LIDAR DISTANCE THRESHOLD

C = 299792458.0

project = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

datasets = {
    "fog": (
        project / "data" / "raw"
        / "baseline_fog_working_radar"
        / "20261027T152743Z_sv_380_X_794_GEMSTAR.osi"
    ),
    "clear": (
        project / "data" / "raw"
        / "baseline_clear"
        / "20261027T205013Z_sv_380_X_829_GEMSTAR.osi"
    ),
}

output_file = (
    project / "data" / "processed"
    / "task08_lidar_threshold_diagnostic.csv"
)

output_file.parent.mkdir(parents=True, exist_ok=True)

# Diagnostic distance thresholds (metres)
thresholds = [6.0, 7.0, 10.0, 15.0, 20.0]

results = []

for weather, input_file in datasets.items():

    print(f"\n========== {weather.upper()} ==========")

    if not input_file.exists():
        raise FileNotFoundError(input_file)

    total_frames = 0
    valid_reflections = 0

    counts = {threshold: 0 for threshold in thresholds}

    maximum_distance = 0.0

    with input_file.open("rb") as source:

        while True:
            header = source.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            length = int.from_bytes(header, "little")

            if length <= 0:
                raise ValueError("Invalid OSI message length")

            payload = source.read(length)

            if len(payload) != length:
                raise ValueError("Incomplete OSI message")

            view = SensorView()
            view.ParseFromString(payload)

            total_frames += 1

            for sensor in view.lidar_sensor_view:
                for reflection in sensor.reflection:

                    tof = reflection.time_of_flight
                    strength = reflection.signal_strength

                    if not (
                        math.isfinite(tof)
                        and math.isfinite(strength)
                        and tof > 0
                        and strength > 0
                    ):
                        continue

                    distance = C * tof / 2.0

                    valid_reflections += 1

                    maximum_distance = max(
                        maximum_distance, distance
                    )

                    for threshold in thresholds:
                        if distance > threshold:
                            counts[threshold] += 1

            if total_frames % 200 == 0:
                print(f"Processed {total_frames} frames")

    print("Total frames:", total_frames)
    print("Positive LiDAR reflections:", valid_reflections)
    print(
        "Maximum positive-return distance:",
        round(maximum_distance, 3),
        "m"
    )

    for threshold in thresholds:

        count = counts[threshold]

        percentage = (
            100 * count / valid_reflections
            if valid_reflections else 0
        )

        print(
            f"Positive returns beyond {threshold:.1f} m: "
            f"{count} ({percentage:.3f}%)"
        )

        results.append({
            "weather": weather,
            "threshold_m": threshold,
            "frames": total_frames,
            "positive_reflections": valid_reflections,
            "returns_beyond_threshold": count,
            "percentage_beyond_threshold": percentage,
            "maximum_distance_m": maximum_distance
        })

with output_file.open(
    "w", newline="", encoding="utf-8"
) as destination:

    writer = csv.DictWriter(
        destination,
        fieldnames=list(results[0].keys())
    )

    writer.writeheader()
    writer.writerows(results)

print("\n====================================")
print("TASK 8.15.2 COMPLETED")
print("CSV saved:", output_file)
print("====================================")
