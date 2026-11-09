import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages,
    SensorView,
)

MANIFEST = (
    TASK / "05_Raw_Data_References"
    / "task23_01_source_manifest.csv"
)

OUTPUT = (
    TASK / "08_Processed_Data"
    / "task23_04c_raw_lidar_measurements.csv"
)

CONFIG_OUTPUT = (
    TASK / "04_Configurations"
    / "task23_04c_lidar_scan_configuration.csv"
)

FINDINGS = (
    TASK / "06_Research_Findings"
    / "task23_04c1_export_findings.json"
)

FRAMES = {0, 1, 25, 99}
C = 299792458.0
MIN_RANGE = 0.05
MAX_RANGE = 200.0

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
CONFIG_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
FINDINGS.parent.mkdir(parents=True, exist_ok=True)

columns = [
    "PairID",
    "Frame",
    "RayIndex",
    "TimeOfFlightS",
    "SignalStrength",
    "PythonRangeM",
    "PythonPositive",
    "PythonScreened",
]

config_columns = [
    "PairID",
    "Frame",
    "HorizontalRays",
    "VerticalRays",
    "HorizontalFovRad",
    "VerticalFovRad",
    "MountX",
    "MountY",
    "MountZ",
    "ReflectionSlots",
]

print("\n=== TASK 23.4C-1 RAW LIDAR EXPORT ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as handle:
    pairs = list(csv.DictReader(handle))

total_rows = 0
config_rows = []
pair_results = []

with OUTPUT.open(
    "w", newline="", encoding="utf-8"
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=columns
    )

    writer.writeheader()

    for pair in pairs:
        pair_id = pair["PairID"]
        source = Path(pair["SensorViewPath"])

        print(f"\n=== PAIR {pair_id} ===")

        frames_seen = 0
        exported = 0
        positive_count = 0
        screened_count = 0

        for frame, message, size in iter_osi_messages(
            source, SensorView, 100
        ):
            if frame not in FRAMES:
                continue

            frames_seen += 1

            if not message.lidar_sensor_view:
                print(
                    f"Frame {frame}: LiDAR unavailable"
                )
                continue

            lidar = message.lidar_sensor_view[0]
            cfg = lidar.view_configuration

            nx = int(cfg.number_of_rays_horizontal)
            ny = int(cfg.number_of_rays_vertical)

            if nx * ny != len(lidar.reflection):
                raise ValueError(
                    f"Pair {pair_id} frame {frame}: "
                    "reflection count mismatch"
                )

            mount = cfg.mounting_position.position

            config_rows.append({
                "PairID": pair_id,
                "Frame": frame,
                "HorizontalRays": nx,
                "VerticalRays": ny,
                "HorizontalFovRad":
                    cfg.field_of_view_horizontal,
                "VerticalFovRad":
                    cfg.field_of_view_vertical,
                "MountX": mount.x,
                "MountY": mount.y,
                "MountZ": mount.z,
                "ReflectionSlots": len(lidar.reflection)
            })

            for index, reflection in enumerate(
                lidar.reflection
            ):
                tof = float(
                    reflection.time_of_flight
                )

                strength = float(
                    reflection.signal_strength
                )

                finite = (
                    math.isfinite(tof)
                    and math.isfinite(strength)
                )

                positive = (
                    finite
                    and tof > 0
                    and strength > 0
                )

                # Reference output for later independent
                # MATLAB comparison.
                distance = C * tof / 2.0 if finite else math.nan

                screened = (
                    positive
                    and MIN_RANGE <= distance <= MAX_RANGE
                )

                if positive:
                    positive_count += 1

                if screened:
                    screened_count += 1

                writer.writerow({
                    "PairID": pair_id,
                    "Frame": frame,
                    "RayIndex": index,
                    "TimeOfFlightS": tof,
                    "SignalStrength": strength,
                    "PythonRangeM": (
                        distance if screened else ""
                    ),
                    "PythonPositive": int(positive),
                    "PythonScreened": int(screened),
                })

                exported += 1

        if frames_seen != len(FRAMES):
            raise RuntimeError(
                f"Pair {pair_id}: expected "
                f"{len(FRAMES)} frames, found {frames_seen}"
            )

        pair_results.append({
            "PairID": pair_id,
            "FramesExamined": frames_seen,
            "ExportedRows": exported,
            "PositiveReturns": positive_count,
            "ScreenedReturns": screened_count,
        })

        total_rows += exported

        print("Frames examined:", frames_seen)
        print("Exported measurements:", exported)
        print("Positive returns:", positive_count)
        print("Screened returns:", screened_count)

with CONFIG_OUTPUT.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle, fieldnames=config_columns
    )
    writer.writeheader()
    writer.writerows(config_rows)

FINDINGS.write_text(
    json.dumps({
        "Task": "23.4C-1",
        "Description": (
            "Original LiDAR time-of-flight export "
            "for independent MATLAB reconstruction"
        ),
        "SampledFrames": sorted(FRAMES),
        "SpeedOfLightMPerS": C,
        "MinimumScreeningRangeM": MIN_RANGE,
        "MaximumScreeningRangeM": MAX_RANGE,
        "ExportedRows": total_rows,
        "PairResults": pair_results,
        "ScientificLimitations": [
            "Beam direction geometry remains hypothetical",
            "Positive returns are not verified detections",
            "Frame zero requires separate interpretation",
            "Range thresholds are preliminary screening choices",
            "No power or energy measurements"
        ]
    }, indent=2),
    encoding="utf-8"
)

expected = 3 * len(FRAMES) * 5271

print("\n=== TASK 23.4C-1 FINAL VERIFICATION ===")
print("Recording pairs:", len(pairs))
print("Exported raw LiDAR rows:", total_rows)
print("Expected populated LiDAR rows:", expected)
print("Raw CSV saved:", OUTPUT.is_file())
print("Configuration CSV saved:", CONFIG_OUTPUT.is_file())
print("Research findings saved:", FINDINGS.is_file())

if total_rows != expected:
    raise RuntimeError(
        "Unexpected raw measurement row count"
    )

print("\n=== TASK 23.4C-1 COMPLETE ===")
