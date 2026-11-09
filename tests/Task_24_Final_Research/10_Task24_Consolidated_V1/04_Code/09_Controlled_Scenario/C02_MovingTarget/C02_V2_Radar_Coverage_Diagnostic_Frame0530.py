import csv
import math
import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

base = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

osi = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

association = base / "C02_V2_ThreeSensor_Association_Frame0530_V1.csv"

with association.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

candidates = [
    r for r in rows
    if int(r["lidar_candidate_points"]) > 0
]

if not candidates:
    raise RuntimeError("No LiDAR-Camera candidate available")

with osi.open("rb") as f:
    for i in range(531):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")
        size = struct.unpack("<I", header)[0]
        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Incomplete OSI message")

sv = SensorView()
sv.ParseFromString(payload)

if len(sv.radar_sensor_view) != 1:
    raise RuntimeError("Expected exactly one Radar sensor")

radar = sv.radar_sensor_view[0]
cfg = radar.view_configuration

C = 299792458.0

valid = []

for ref in radar.reflection:
    tof = float(ref.time_of_flight)
    if not math.isfinite(tof) or tof <= 0:
        continue

    distance = C * tof / 2
    yaw = float(ref.source_horizontal_angle)
    pitch = float(ref.source_vertical_angle)

    if not all(math.isfinite(v) for v in (distance, yaw, pitch)):
        continue
    if distance <= 0.01:
        continue

    x = 2.0 + distance * math.cos(pitch) * math.cos(yaw)
    y = -distance * math.cos(pitch) * math.sin(yaw)
    z = 0.8 + distance * math.sin(pitch)

    valid.append((distance, yaw, pitch, x, y, z))

print("=== TASK 24.8.6 RESULTS ===")
print("FRAME=530")
print("RADAR_VALID_RETURNS=", len(valid))

if valid:
    ranges = [p[0] for p in valid]

    print("RADAR_MIN_RANGE_M=", round(min(ranges), 4))
    print("RADAR_MAX_RANGE_M=", round(max(ranges), 4))

    for low, high in [(0, 10), (10, 20), (20, 25),
                      (25, 30), (30, 40), (40, 60),
                      (60, 100), (100, 1000)]:
        count = sum(low <= r < high for r in ranges)
        print(f"RADAR_RANGE_{low}_{high}M=", count)

print("RADAR_HFOV_DEG=", round(math.degrees(
    cfg.field_of_view_horizontal), 4))
print("RADAR_VFOV_DEG=", round(math.degrees(
    cfg.field_of_view_vertical), 4))

for row in candidates:
    x = float(row["lidar_x_m"])
    y = float(row["lidar_y_m"])
    z = float(row["lidar_z_m"])

    dx = x - 2.0
    dy = y
    dz = z - 0.8

    horizontal_distance = math.hypot(dx, dy)
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)

    # OSI vehicle Y is left; sensor yaw positive is right.
    bearing = -math.atan2(dy, dx)
    elevation = math.atan2(dz, horizontal_distance)

    nominal_hfov = cfg.field_of_view_horizontal / 2
    nominal_vfov = cfg.field_of_view_vertical / 2

    inside_nominal_fov = (
        dx > 0
        and abs(bearing) <= nominal_hfov
        and abs(elevation) <= nominal_vfov
    )

    print()
    print("CAMERA_HYPOTHESIS=", row["camera_hypothesis"])
    print("ORIGINAL_CLASSES=", row["original_classes"])
    print("LIDAR_CANDIDATE_XYZ_M=", (round(x, 3),
                                      round(y, 3),
                                      round(z, 3)))
    print("CANDIDATE_RADAR_RANGE_M=", round(distance, 4))
    print("CANDIDATE_RADAR_BEARING_DEG=",
          round(math.degrees(bearing), 4))
    print("CANDIDATE_RADAR_ELEVATION_DEG=",
          round(math.degrees(elevation), 4))
    print("CANDIDATE_INSIDE_NOMINAL_FOV=", inside_nominal_fov)

    if valid:
        nearest = min(
            valid,
            key=lambda p: math.dist((x, y, z), p[3:6])
        )

        nearest_distance = math.dist((x, y, z), nearest[3:6])

        print("NEAREST_RADAR_POINT_RANGE_M=",
              round(nearest[0], 4))
        print("NEAREST_RADAR_POINT_YAW_DEG=",
              round(math.degrees(nearest[1]), 4))
        print("NEAREST_RADAR_POINT_PITCH_DEG=",
              round(math.degrees(nearest[2]), 4))
        print("NEAREST_RADAR_POINT_SPATIAL_GAP_M=",
              round(nearest_distance, 4))

        range_near = sum(
            abs(p[0] - distance) <= 2.0 for p in valid
        )
        bearing_near = sum(
            abs(math.degrees(p[1] - bearing)) <= 10.0
            for p in valid
        )

        print("RADAR_RETURNS_WITHIN_2M_RANGE=", range_near)
        print("RADAR_RETURNS_WITHIN_10DEG_BEARING=", bearing_near)

print()
print("SIMULATOR_OBJECT_IDS_USED=NO")
print("ASSOCIATION_STATUS=DIAGNOSTIC_ONLY")
print("INPUT_FILES_MODIFIED=NO")
print("TASK24_08_06_RADAR_DIAGNOSTIC_COMPLETE")