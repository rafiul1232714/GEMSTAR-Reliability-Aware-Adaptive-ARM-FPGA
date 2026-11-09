import csv
import math
import struct
import numpy as np
from pathlib import Path
from collections import Counter
from osi3.osi_sensorview_pb2 import SensorView

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
OSI = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

FRAME = 530
C = 299792458.0
BIN_WIDTH = 2.0
MIN_LIDAR_POINTS = 5
MIN_DEPTH_FRACTION = 0.70
RADAR_GATE_M = 1.5

with (BASE / "C02_V2_Frame0530_Deduplicated_Detections.csv").open(
    newline="", encoding="utf-8-sig"
) as f:
    boxes = list(csv.DictReader(f))

with OSI.open("rb") as f:
    for index in range(FRAME + 1):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")
        size = struct.unpack("<I", header)[0]
        if size <= 0:
            raise RuntimeError("Invalid OSI message size")
        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Incomplete OSI payload")

sv = SensorView()
sv.ParseFromString(payload)

if len(sv.lidar_sensor_view) != 1:
    raise RuntimeError("Expected one LiDAR sensor")
if len(sv.radar_sensor_view) != 1:
    raise RuntimeError("Expected one Radar sensor")

lidar = sv.lidar_sensor_view[0]
radar = sv.radar_sensor_view[0]
cfg = lidar.view_configuration

nh = int(cfg.number_of_rays_horizontal)
nv = int(cfg.number_of_rays_vertical)

if (nh, nv) != (251, 21):
    raise RuntimeError("Unexpected LiDAR grid")

if len(lidar.reflection) != nh * nv:
    raise RuntimeError("Unexpected LiDAR reflection count")

# Nominal mounts in vehicle coordinates, meters.
LIDAR_MOUNT = (2.6, 0.0, 0.7)
RADAR_MOUNT = (2.0, 0.0, 0.8)
CAMERA_MOUNT = (0.7, 0.0, 1.6)

# Unreal camera nominal HFOV 90 degrees, 640x480 pixels.
FX = FY = 320.0
CX, CY = 320.0, 240.0

lidar_points = []

for i, ref in enumerate(lidar.reflection):
    tof = float(ref.time_of_flight)
    if not math.isfinite(tof) or tof <= 0:
        continue

    r = C * tof / 2
    if not math.isfinite(r) or r <= 0.01:
        continue

    hi = i % nh
    vi = i // nh

    yaw = -cfg.field_of_view_horizontal / 2 + (
        hi * cfg.field_of_view_horizontal / (nh - 1)
    )
    pitch = -cfg.field_of_view_vertical / 2 + (
        vi * cfg.field_of_view_vertical / (nv - 1)
    )

    sx = r * math.cos(pitch) * math.cos(yaw)
    sy = r * math.cos(pitch) * math.sin(yaw)
    sz = r * math.sin(pitch)

    # OSI vehicle convention: Y positive left.
    x = LIDAR_MOUNT[0] + sx
    y = LIDAR_MOUNT[1] - sy
    z = LIDAR_MOUNT[2] + sz

    # Camera perspective coordinates.
    depth = x - CAMERA_MOUNT[0]
    if depth <= 0:
        continue

    u = CX - FX * (y - CAMERA_MOUNT[1]) / depth
    v = CY - FY * (z - CAMERA_MOUNT[2]) / depth

    if 0 <= u < 640 and 0 <= v < 480:
        lidar_points.append((u, v, r, x, y, z))

radar_points = []

for ref in radar.reflection:
    tof = float(ref.time_of_flight)
    if not math.isfinite(tof) or tof <= 0:
        continue

    r = C * tof / 2
    if not math.isfinite(r) or r <= 0.01:
        continue

    yaw = float(ref.source_horizontal_angle)
    pitch = float(ref.source_vertical_angle)

    if not math.isfinite(yaw) or not math.isfinite(pitch):
        continue

    x = RADAR_MOUNT[0] + r * math.cos(pitch) * math.cos(yaw)
    y = RADAR_MOUNT[1] - r * math.cos(pitch) * math.sin(yaw)
    z = RADAR_MOUNT[2] + r * math.sin(pitch)

    radar_points.append((
        x, y, z, r, float(ref.doppler_shift)
    ))

print("=== TASK 24.8.5 RESULTS ===")
print("FRAME=", FRAME)
print("LIDAR_PROJECTED_POINTS=", len(lidar_points))
print("RADAR_VALID_RETURNS=", len(radar_points))
print("CAMERA_HYPOTHESES=", len(boxes))

rows = []

for box_id, box in enumerate(boxes):
    x1, y1, x2, y2 = (
        float(box[k]) for k in ("X1", "Y1", "X2", "Y2")
    )

    inside = [
        p for p in lidar_points
        if x1 <= p[0] <= x2 and y1 <= p[1] <= y2
    ]

    bins = Counter(
        int(math.floor(p[2] / BIN_WIDTH))
        for p in inside
    )

    if bins:
        dominant_bin, count = max(
            bins.items(),
            key=lambda kv: (kv[1], -kv[0])
        )
    else:
        dominant_bin, count = None, 0

    fraction = count / len(inside) if inside else 0.0

    candidate = []
    if (
        dominant_bin is not None
        and count >= MIN_LIDAR_POINTS
        and fraction >= MIN_DEPTH_FRACTION
    ):
        candidate = [
            p for p in inside
            if int(math.floor(p[2] / BIN_WIDTH)) == dominant_bin
        ]

    matched_radar = 0
    nearest_radar_m = float("nan")
    candidate_xyz = [float("nan")] * 3

    if candidate:
        lp = np.array([p[3:6] for p in candidate])
        candidate_xyz = np.median(lp, axis=0).tolist()

        if radar_points:
            rp = np.array([p[:3] for p in radar_points])

            # Per Radar return, nearest candidate LiDAR point.
            distances = np.linalg.norm(
                rp[:, None, :] - lp[None, :, :],
                axis=2
            ).min(axis=1)

            matched_radar = int(
                np.count_nonzero(distances <= RADAR_GATE_M)
            )
            nearest_radar_m = float(distances.min())

    status = (
        "SPATIAL_CANDIDATE_RADAR_SUPPORTED"
        if candidate and matched_radar > 0
        else "LIDAR_CAMERA_DEPTH_CANDIDATE_ONLY"
        if candidate
        else "REJECTED_INSUFFICIENT_DEPTH_CONSISTENCY"
    )

    row = {
        "frame": FRAME,
        "camera_hypothesis": box_id,
        "camera_class_uncertain": box["RepresentativeClass"],
        "original_classes": box["OriginalClasses"],
        "camera_confidence": box["Confidence"],
        "lidar_points_in_box": len(inside),
        "dominant_depth_start_m": (
            dominant_bin * BIN_WIDTH
            if dominant_bin is not None else ""
        ),
        "dominant_depth_points": count,
        "dominant_depth_fraction": round(fraction, 5),
        "lidar_candidate_points": len(candidate),
        "lidar_x_m": candidate_xyz[0],
        "lidar_y_m": candidate_xyz[1],
        "lidar_z_m": candidate_xyz[2],
        "radar_returns_near_candidate": matched_radar,
        "nearest_radar_distance_m": nearest_radar_m,
        "status": status
    }
    rows.append(row)

    print()
    print("HYPOTHESIS=", box_id)
    print("ORIGINAL_CLASSES=", box["OriginalClasses"])
    print("POINTS_IN_CAMERA_BOX=", len(inside))
    print("DOMINANT_DEPTH_POINTS=", count)
    print("DOMINANT_DEPTH_FRACTION=", round(fraction, 4))
    print("LIDAR_CANDIDATE_POINTS=", len(candidate))
    print("RADAR_RETURNS_NEAR_CANDIDATE=", matched_radar)
    print("NEAREST_RADAR_DISTANCE_M=", nearest_radar_m)
    print("STATUS=", status)

out = BASE / "C02_V2_ThreeSensor_Association_Frame0530_V1.csv"

with out.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print()
print("OUTPUT_CSV=", out)
print("MODEL=NOMINAL_UNCALIBRATED")
print("RADAR_GATE_M=", RADAR_GATE_M)
print("DOPPLER_USED_FOR_ASSOCIATION=NO")
print("SIMULATOR_OBJECT_IDS_USED=NO")
print("ASSOCIATION_STATUS=EXPLORATORY_SPATIAL_ONLY")
print("ORIGINAL_INPUTS_MODIFIED=NO")
print("TASK24_08_05_ASSOCIATION_COMPLETE")