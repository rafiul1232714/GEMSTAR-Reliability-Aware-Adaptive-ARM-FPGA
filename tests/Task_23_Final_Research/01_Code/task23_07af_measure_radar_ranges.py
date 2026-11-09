import csv
import struct
from pathlib import Path
from statistics import median

from osi3 import osi_sensorview_pb2

C = 299792458.0

sv_file = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T155916Z_sv_380_X_2393_GEMSTARADAR.osi"
)

csv_file = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests"
    r"\Task_23_Final_Research\02_CSV_Data"
    r"\task23_07af_radar_range_measurements.csv"
)

selected_rays = {44, 45, 54, 55}

rows = []
ranges = []
frames = 0

with sv_file.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]
        payload = f.read(size)

        if len(payload) != size:
            raise ValueError("Truncated OSI payload")

        message = osi_sensorview_pb2.SensorView()
        message.ParseFromString(payload)

        frames += 1

        for view_id, radar in enumerate(message.radar_sensor_view):
            for ray_id in selected_rays:
                if ray_id >= len(radar.reflection):
                    continue

                reflection = radar.reflection[ray_id]

                range_m = (
                    C * reflection.time_of_flight / 2.0
                )

                valid = range_m > 0

                rows.append({
                    "Frame": frames,
                    "RadarView": view_id,
                    "RayIndex": ray_id,
                    "Range_m": range_m,
                    "ValidReturn": int(valid),
                    "SignalStrength": reflection.signal_strength,
                    "DopplerShift": reflection.doppler_shift,
                    "Azimuth_rad": reflection.source_horizontal_angle,
                    "Elevation_rad": reflection.source_vertical_angle
                })

                if valid:
                    ranges.append(range_m)

csv_file.parent.mkdir(parents=True, exist_ok=True)

columns = [
    "Frame", "RadarView", "RayIndex", "Range_m",
    "ValidReturn", "SignalStrength", "DopplerShift",
    "Azimuth_rad", "Elevation_rad"
]

with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 23.7AF — RADAR RANGE EXTRACTION ===")
print("Frames processed:", frames)
print("Rows written:", len(rows))
print("Valid near-center returns:", len(ranges))

if ranges:
    print(f"Median near-center range: {median(ranges):.4f} m")
    print(f"Minimum range: {min(ranges):.4f} m")
    print(f"Maximum range: {max(ranges):.4f} m")

print("CSV saved:", csv_file)
print("Status: EXTRACTION_COMPLETE_ACCURACY_NOT_YET_VALIDATED")
