import csv
import math
import struct
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project")
OUTPUT = ROOT / "gemstar" / "Output"
TASK = ROOT / "sensor-health-monitor" / "tests" / "Task_23_Final_Research"

CSV_PATH = (
    TASK / "02_CSV_Data"
    / "task23_13B_02_radar_calibration_ranges.csv"
)

FILES = {
    "BASELINE_CANDIDATE":
        "20261103T164111Z_sv_380_X_1352_GEMSTARADAR.osi",
    "DISPLACED_CANDIDATE":
        "20261103T181207Z_sv_380_X_1062_GEMSTARADAR.osi",
}

RAYS = (44, 45, 54, 55)
C = 299792458.0
MAX_FRAMES = 10

if CSV_PATH.exists():
    raise RuntimeError("CSV already exists; refusing overwrite")

rows = []

for scenario, filename in FILES.items():

    path = OUTPUT / filename

    if not path.is_file():
        raise FileNotFoundError(path)

    print(f"\n=== {scenario} ===")
    print(f"FILE={filename}")
    print(f"BYTES={path.stat().st_size}")

    frames = 0

    with path.open("rb") as f:
        for frame_index in range(MAX_FRAMES):

            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Truncated OSI length header")

            message_size = struct.unpack("<I", header)[0]

            if message_size <= 0 or message_size > 100_000_000:
                raise RuntimeError(
                    f"Invalid OSI message size: {message_size}"
                )

            payload = f.read(message_size)

            if len(payload) != message_size:
                raise RuntimeError("Truncated OSI message")

            sv = SensorView()
            sv.ParseFromString(payload)

            radar_count = len(sv.radar_sensor_view)

            if radar_count != 1:
                raise RuntimeError(
                    f"{scenario} frame {frame_index}: "
                    f"expected one Radar SensorView, got {radar_count}"
                )

            radar = sv.radar_sensor_view[0]
            reflections = radar.reflection

            if len(reflections) <= max(RAYS):
                raise RuntimeError("Insufficient Radar reflection slots")

            print(
                f"FRAME={frame_index} "
                f"RADAR_REFLECTION_SLOTS={len(reflections)}"
            )

            for ray in RAYS:

                reflection = reflections[ray]

                tof = float(reflection.time_of_flight)
                strength = float(reflection.signal_strength)

                positive = (
                    math.isfinite(tof)
                    and tof > 0
                    and math.isfinite(strength)
                    and strength > 0
                )

                range_m = C * tof / 2.0 if positive else None

                rows.append({
                    "Scenario": scenario,
                    "FileName": filename,
                    "Frame": frame_index,
                    "Ray": ray,
                    "TimeOfFlightS": tof,
                    "SignalStrength": strength,
                    "PositiveReturn": positive,
                    "RangeM": range_m if range_m is not None else "",
                })

                print(
                    f"  RAY={ray} "
                    f"TOF={tof:.12g} "
                    f"STRENGTH={strength:.8g} "
                    f"POSITIVE={positive} "
                    f"RANGE_M={range_m}"
                )

            frames += 1

    print(f"FRAMES_INSPECTED={frames}")

    if frames == 0:
        raise RuntimeError(f"No frames decoded for {scenario}")

with CSV_PATH.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV_SAVED={CSV_PATH}")
print(f"TOTAL_RAY_SAMPLES={len(rows)}")
print("TASK23_13B_02_RADAR_OSI_DECODE_PASS")
