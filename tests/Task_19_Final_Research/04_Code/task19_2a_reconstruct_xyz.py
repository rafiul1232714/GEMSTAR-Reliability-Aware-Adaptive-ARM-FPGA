import csv
import struct
from pathlib import Path

import numpy as np
from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

target_frame = 150
C = 299705543.0

with source.open("rb") as stream:
    for frame in range(target_frame + 1):
        header = stream.read(4)
        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        length = struct.unpack("<I", header)[0]

        if frame == target_frame:
            payload = stream.read(length)
            if len(payload) != length:
                raise RuntimeError("Truncated OSI frame")
            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)
        else:
            stream.seek(length, 1)

lidar = sv.lidar_sensor_view[0]
cfg = lidar.view_configuration

nh = cfg.number_of_rays_horizontal
nv = cfg.number_of_rays_vertical

assert nh > 1 and nv > 1
assert len(lidar.reflection) == nh * nv

azimuth = np.linspace(
    -cfg.field_of_view_horizontal / 2,
    cfg.field_of_view_horizontal / 2,
    nh
)

elevation = np.linspace(
    -cfg.field_of_view_vertical / 2,
    cfg.field_of_view_vertical / 2,
    nv
)

full_path = (
    base / "02_CSV_Data" /
    "task19_2a_frame150_all_rays.csv"
)

valid_path = (
    base / "08_Extracted_PointClouds" /
    "task19_2a_frame150_candidate_xyz.csv"
)

full_path.parent.mkdir(parents=True, exist_ok=True)
valid_path.parent.mkdir(parents=True, exist_ok=True)

headers = [
    "Frame", "RayIndex", "HorizontalIndex", "VerticalIndex",
    "AzimuthDeg", "ElevationDeg", "RangeM",
    "X", "Y", "Z", "SignalStrength", "ObjectID",
    "CandidateValid"
]

count_valid = 0

with full_path.open("w", newline="", encoding="utf-8") as fa, \
     valid_path.open("w", newline="", encoding="utf-8") as fv:

    all_writer = csv.writer(fa)
    valid_writer = csv.writer(fv)

    all_writer.writerow(headers)
    valid_writer.writerow(headers)

    for index, reflection in enumerate(lidar.reflection):
        hi = index % nh
        vi = index // nh

        phi = float(azimuth[hi])
        theta = float(elevation[vi])

        distance = reflection.time_of_flight * C / 2.0
        strength = reflection.signal_strength

        oid = (
            int(reflection.object_id.value)
            if reflection.HasField("object_id")
            else -1
        )

        # Unreal forward X, yaw-positive Y.
        # OSI conversion reverses Unreal Y.
        x = distance * np.cos(theta) * np.cos(phi)
        y = -distance * np.cos(theta) * np.sin(phi)
        z = distance * np.sin(theta)

        candidate = (
            np.isfinite(distance)
            and 0.5 <= distance <= 200.0
            and np.isfinite(strength)
            and strength > 0.0
            and oid >= 0
            and oid != (2**64 - 1)
        )

        row = [
            target_frame, index, hi, vi,
            np.degrees(phi), np.degrees(theta),
            distance, x, y, z, strength, oid,
            int(candidate)
        ]

        all_writer.writerow(row)

        if candidate:
            valid_writer.writerow(row)
            count_valid += 1

print("\n=== TASK 19.2A XYZ RECONSTRUCTION ===")
print("Frame:", target_frame)
print("Total rays:", nh * nv)
print("Candidate points:", count_valid)
print("All-ray CSV saved:", full_path.is_file())
print("Candidate XYZ CSV saved:", valid_path.is_file())
print("Candidate CSV:", valid_path)
print("\nCoordinates are sensor-local reconstruction.")
print("World-coordinate alignment remains unvalidated.")
