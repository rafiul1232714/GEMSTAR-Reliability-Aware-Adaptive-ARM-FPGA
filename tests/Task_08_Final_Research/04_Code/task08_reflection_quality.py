
from pathlib import Path
import csv
import math

from osi3.osi_sensorview_pb2 import SensorView

PROJECT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
C = 299792458.0

DATASETS = {
    "fog": PROJECT / "data/raw/baseline_fog_working_radar"
           / "20261027T152743Z_sv_380_X_794_GEMSTAR.osi",

    "clear": PROJECT / "data/raw/baseline_clear"
             / "20261027T205013Z_sv_380_X_829_GEMSTAR.osi",
}

OUTPUT = (
    PROJECT / "data/processed"
    / "task08_reflection_quality.csv"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def summarize(reflections):
    valid = [
        r for r in reflections
        if math.isfinite(r.signal_strength)
        and math.isfinite(r.time_of_flight)
        and r.signal_strength > 0
        and r.time_of_flight > 0
    ]

    if not valid:
        return 0, "", "", ""

    strengths = [r.signal_strength for r in valid]

    ranges = [
        C * r.time_of_flight / 2
        for r in valid
    ]

    return (
        len(valid),
        sum(strengths) / len(strengths),
        sum(ranges) / len(ranges),
        max(ranges)
    )


with OUTPUT.open("w", newline="", encoding="utf-8") as out:
    writer = csv.writer(out)

    writer.writerow([
        "weather",
        "frame",
        "time_s",
        "lidar_valid",
        "lidar_mean_strength",
        "lidar_mean_range_m",
        "lidar_max_range_m",
        "radar_valid",
        "radar_mean_strength",
        "radar_mean_range_m",
        "radar_max_range_m"
    ])

    for weather, path in DATASETS.items():
        print(f"\nProcessing {weather}: {path.name}")

        frame = 0

        with path.open("rb") as source:
            while True:
                header = source.read(4)

                if not header:
                    break

                if len(header) != 4:
                    raise ValueError("Incomplete header")

                length = int.from_bytes(header, "little")
                payload = source.read(length)

                if len(payload) != length:
                    raise ValueError("Incomplete OSI message")

                view = SensorView()
                view.ParseFromString(payload)

                frame += 1

                time_s = (
                    view.timestamp.seconds
                    + view.timestamp.nanos / 1e9
                    if view.HasField("timestamp")
                    else ""
                )

                lidar = [
                    r
                    for sensor in view.lidar_sensor_view
                    for r in sensor.reflection
                ]

                radar = [
                    r
                    for sensor in view.radar_sensor_view
                    for r in sensor.reflection
                ]

                lidar_result = summarize(lidar)
                radar_result = summarize(radar)

                writer.writerow([
                    weather,
                    frame,
                    time_s,
                    *lidar_result,
                    *radar_result
                ])

                if frame % 100 == 0:
                    print(f"Processed {frame} frames")

        print(f"{weather} completed: {frame} frames")

print("\nTASK 8.12 COMPLETED")
print("Saved:", OUTPUT)
