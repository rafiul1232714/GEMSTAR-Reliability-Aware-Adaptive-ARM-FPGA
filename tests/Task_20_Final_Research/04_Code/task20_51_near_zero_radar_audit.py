import csv
import json
import math
import struct
from collections import Counter
from pathlib import Path
from statistics import median

from osi3.osi_sensorview_pb2 import SensorView

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_20_Final_Research")
SOURCE = Path(r"E:\GEMSTAR_Project\gemstar\Output\20261102T180104Z_sv_380_X_806_GEMSTAR.osi")
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

SPEED_OF_LIGHT = 299705543.0
FRAME_LIMIT = 100
THRESHOLD_M = 0.001

near_zero = []
all_valid = []
slot_count = 0
nonpositive = 0
frames_read = 0

print("\n=== TASK 20.51 NEAR-ZERO RADAR AUDIT ===")

with SOURCE.open("rb") as f:
    for frame in range(FRAME_LIMIT):
        header = f.read(4)
        if not header:
            break
        if len(header) != 4:
            raise ValueError("Incomplete OSI frame header")

        size = struct.unpack("<I", header)[0]
        if not 0 < size < 100_000_000:
            raise ValueError(f"Invalid message size: {size}")

        payload = f.read(size)
        if len(payload) != size:
            raise ValueError("Incomplete OSI frame")

        sv = SensorView()
        sv.ParseFromString(payload)
        frames_read += 1

        for radar_idx, view in enumerate(sv.radar_sensor_view):
            for ref_idx, ref in enumerate(view.reflection):
                slot_count += 1

                tof = float(ref.time_of_flight)
                strength = float(ref.signal_strength)

                if not all(map(math.isfinite, [tof, strength])):
                    continue

                if tof <= 0 or strength <= 0:
                    nonpositive += 1
                    continue

                distance = tof * SPEED_OF_LIGHT / 2
                all_valid.append(distance)

                if distance < THRESHOLD_M:
                    near_zero.append({
                        "Frame": frame,
                        "RadarIndex": radar_idx,
                        "ReflectionIndex": ref_idx,
                        "TimeOfFlightSeconds": format(tof, ".17g"),
                        "RangeMetres": format(distance, ".17g"),
                        "SignalStrength": format(strength, ".17g"),
                        "AzimuthDeg": round(math.degrees(
                            ref.source_horizontal_angle), 6),
                        "ElevationDeg": round(math.degrees(
                            ref.source_vertical_angle), 6),
                        "DopplerHz": format(
                            float(ref.doppler_shift), ".17g")
                    })

by_frame = Counter(r["Frame"] for r in near_zero)
by_ray = Counter(r["ReflectionIndex"] for r in near_zero)

csv_path = DATA / "task20_51_near_zero_returns.csv"
json_path = FINDINGS / "task20_51_near_zero_audit.json"

columns = [
    "Frame", "RadarIndex", "ReflectionIndex",
    "TimeOfFlightSeconds", "RangeMetres",
    "SignalStrength", "AzimuthDeg",
    "ElevationDeg", "DopplerHz"
]

with csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(near_zero)

summary = {
    "Task": "20.51",
    "SourceRecording": str(SOURCE),
    "FramesRead": frames_read,
    "ReflectionSlots": slot_count,
    "PositiveSignalAndTOFReturns": len(all_valid),
    "NearZeroThresholdM": THRESHOLD_M,
    "NearZeroReturns": len(near_zero),
    "NearZeroAffectedFrames": len(by_frame),
    "NearZeroFrameCounts": dict(by_frame),
    "NearZeroRayCounts": dict(by_ray),
    "MinimumNearZeroRangeM": (
        min(float(r["RangeMetres"]) for r in near_zero)
        if near_zero else None
    ),
    "MedianNearZeroRangeM": (
        median(float(r["RangeMetres"]) for r in near_zero)
        if near_zero else None
    ),
    "CauseEstablished": False,
    "DetectionAccuracyValidated": False,
    "HardwareEnergyMeasured": False
}

json_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("Frames inspected:", frames_read)
print("Reflection slots:", slot_count)
print("Candidate returns:", len(all_valid))
print("Near-zero returns (<1 mm):", len(near_zero))
print("Affected frames:", len(by_frame))
print("Most frequent ray indices:",
      by_ray.most_common(10))

print("\n=== FIRST 10 NEAR-ZERO EXAMPLES ===")
for row in near_zero[:10]:
    print(
        f"Frame={row['Frame']}, "
        f"Ray={row['ReflectionIndex']}, "
        f"Range={row['RangeMetres']} m, "
        f"Signal={row['SignalStrength']}, "
        f"Azimuth={row['AzimuthDeg']} deg, "
        f"Elevation={row['ElevationDeg']} deg"
    )

print("\n=== TASK 20.51 COMPLETE ===")
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Cause established:", False)
print("Radar detection accuracy validated:", False)
print("Energy measured:", False)
