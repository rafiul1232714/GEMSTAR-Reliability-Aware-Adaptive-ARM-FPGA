import csv
import json
import math
import struct
from pathlib import Path
from statistics import median

from osi3.osi_sensorview_pb2 import SensorView

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261102T180104Z_sv_380_X_806_GEMSTAR.osi"
)

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_20_Final_Research"
)

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

C = 299705543.0
LIMIT = 100

ranges = []
rows = []
frames_checked = 0
reflection_slots = 0
positive_tof = 0

print("\n=== TASK 20.49 RADAR 50M VALIDATION ===")

with SOURCE.open("rb") as f:

    for frame in range(LIMIT):

        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete frame header")

        size = struct.unpack("<I", header)[0]

        if not 0 < size < 100_000_000:
            raise ValueError(
                f"Invalid OSI record length: {size}"
            )

        payload = f.read(size)

        if len(payload) != size:
            raise ValueError("Truncated OSI message")

        sv = SensorView()
        sv.ParseFromString(payload)

        frames_checked += 1

        for radar_index, view in enumerate(
            sv.radar_sensor_view
        ):

            for index, reflection in enumerate(
                view.reflection
            ):

                reflection_slots += 1

                tof = float(reflection.time_of_flight)
                signal = float(reflection.signal_strength)

                if math.isfinite(tof) and tof > 0:
                    positive_tof += 1

                if not (
                    math.isfinite(tof)
                    and math.isfinite(signal)
                    and tof > 0
                    and signal > 0
                ):
                    continue

                distance = tof * C / 2

                if not math.isfinite(distance):
                    continue

                ranges.append(distance)

                rows.append({
                    "Frame": frame,
                    "RadarIndex": radar_index,
                    "ReflectionIndex": index,
                    "RangeM": round(distance, 6),
                    "SignalStrength": signal,
                    "Beyond10m": distance > 10,
                    "Beyond20m": distance > 20,
                    "Beyond30m": distance > 30,
                    "Beyond40m": distance > 40
                })

def above(threshold):
    return sum(value > threshold for value in ranges)

summary = {
    "Task": "20.49",
    "Source": str(SOURCE),
    "FramesChecked": frames_checked,
    "ReflectionSlots": reflection_slots,
    "PositiveTimeOfFlightSlots": positive_tof,
    "ValidCandidateReturns": len(ranges),
    "Beyond10m": above(10),
    "Beyond20m": above(20),
    "Beyond30m": above(30),
    "Beyond40m": above(40),
    "MinimumRangeM": min(ranges) if ranges else None,
    "MedianRangeM": median(ranges) if ranges else None,
    "MaximumRangeM": max(ranges) if ranges else None,
    "Runtime50mConfigurationPreviouslyLogged": True,
    "DetectionAccuracyValidated": False,
    "HardwareEnergyMeasured": False
}

csv_path = DATA / "task20_49_50m_radar_returns.csv"
json_path = FINDINGS / "task20_49_50m_radar_validation.json"

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f, fieldnames=[
            "Frame", "RadarIndex",
            "ReflectionIndex", "RangeM",
            "SignalStrength", "Beyond10m",
            "Beyond20m", "Beyond30m",
            "Beyond40m"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("Frames checked:", frames_checked)
print("Reflection slots:", reflection_slots)
print("Valid candidate returns:", len(ranges))
print("Returns beyond 10 m:", above(10))
print("Returns beyond 20 m:", above(20))
print("Returns beyond 30 m:", above(30))
print("Returns beyond 40 m:", above(40))

if ranges:
    print("Minimum range:", round(min(ranges), 4), "m")
    print("Median range:", round(median(ranges), 4), "m")
    print("Maximum range:", round(max(ranges), 4), "m")

print("\n=== TASK 20.49 COMPLETE ===")
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Radar detection accuracy validated:", False)
print("Energy measured:", False)
