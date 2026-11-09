from pathlib import Path
import struct

from osi3 import osi_sensorview_pb2

FILE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261103T152603Z_sv_380_X_1534_GEMSTARADAR.osi"
)

C = 299792458.0

with FILE.open("rb") as f:
    size = struct.unpack("<I", f.read(4))[0]
    payload = f.read(size)

msg = osi_sensorview_pb2.SensorView()
msg.ParseFromString(payload)

print("\n=== TASK 23.7V — RECORDED RADAR CONFIGURATION ===")

print("Radar views:", len(msg.radar_sensor_view))

for index, radar in enumerate(msg.radar_sensor_view):
    print("\nRADAR VIEW:", index)

    print("\n=== VIEW CONFIGURATION ===")
    print(radar.view_configuration)

    print("\n=== SELECTED REFLECTIONS ===")

    for i in [0, 10, 44, 45, 54, 55, 99]:
        if i >= len(radar.reflection):
            continue

        r = radar.reflection[i]
        distance = C * r.time_of_flight / 2.0

        print(
            f"Ray {i:3d} | "
            f"Range={distance:.4f} m | "
            f"Signal={r.signal_strength:.4f} | "
            f"Doppler={r.doppler_shift:.4f} | "
            f"Azimuth={r.source_horizontal_angle:.4f} rad | "
            f"Elevation={r.source_vertical_angle:.4f} rad"
        )

print("\n=== TASK 23.7V COMPLETE ===")
