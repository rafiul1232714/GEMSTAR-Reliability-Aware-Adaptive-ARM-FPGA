
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView
import math
import csv

PROJECT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
C = 299792458.0

FILES = {
    "fog_before_fix": (
        PROJECT / "data/raw/baseline_fog_working_radar"
        / "20261027T152743Z_sv_380_X_794_GEMSTAR.osi"
    ),
    "fog_after_fix": (
        PROJECT / "data/raw/fog_postfix_validation"
        / "20261027T222053Z_sv_380_X_705_GEMSTAR.osi"
    ),
}

THRESHOLDS = [6.0, 7.0, 10.0, 15.0]

results = []

for name, path in FILES.items():

    if not path.exists():
        raise FileNotFoundError(path)

    frames = 0
    positive = 0
    total_reflections = 0
    beyond = {t: 0 for t in THRESHOLDS}
    max_distance = 0.0

    print(f"\nProcessing: {name}")

    with path.open("rb") as f:
        while True:
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete frame header")

            length = int.from_bytes(header, "little")
            payload = f.read(length)

            if len(payload) != length:
                raise ValueError("Incomplete OSI message")

            view = SensorView()
            view.ParseFromString(payload)
            frames += 1

            for sensor in view.lidar_sensor_view:
                for reflection in sensor.reflection:

                    total_reflections += 1

                    strength = reflection.signal_strength
                    tof = reflection.time_of_flight

                    if not (
                        math.isfinite(strength)
                        and math.isfinite(tof)
                        and strength > 0
                        and tof > 0
                    ):
                        continue

                    distance = C * tof / 2
                    positive += 1
                    max_distance = max(max_distance, distance)

                    for threshold in THRESHOLDS:
                        if distance > threshold:
                            beyond[threshold] += 1

            if frames % 200 == 0:
                print(f"Processed {frames} frames")

    percentage_valid = (
        100 * positive / total_reflections
        if total_reflections else 0
    )

    print(f"\n{name}")
    print(f"Frames: {frames}")
    print(f"Total LiDAR reflections: {total_reflections}")
    print(f"Positive reflections: {positive}")
    print(f"Positive return rate: {percentage_valid:.3f}%")
    print(f"Max positive distance: {max_distance:.3f} m")

    for threshold in THRESHOLDS:
        count = beyond[threshold]
        percent = 100 * count / positive if positive else 0

        print(
            f"Beyond {threshold:.0f} m: "
            f"{count} ({percent:.3f}% of positive returns)"
        )

        results.append({
            "experiment": name,
            "frames": frames,
            "total_reflections": total_reflections,
            "positive_reflections": positive,
            "positive_return_rate_pct": percentage_valid,
            "threshold_m": threshold,
            "positive_beyond_threshold": count,
            "pct_positive_beyond_threshold": percent,
            "maximum_positive_distance_m": max_distance
        })

output = (
    PROJECT / "data/processed"
    / "task08_lidar_before_vs_after_fix.csv"
)

output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

print("\n================================")
print("POST-FIX VALIDATION COMPLETE")
print("Saved:", output)
print("================================")
