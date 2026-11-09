import csv
import math
import struct
from collections import Counter
from pathlib import Path
from statistics import median
from osi3.osi_sensorview_pb2 import SensorView

base = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

osi = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

with (base / "C02_V2_YOLO_Frame0530.csv").open(
    newline="", encoding="utf-8"
) as f:
    boxes = list(csv.DictReader(f))

with osi.open("rb") as f:
    for frame in range(531):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Incomplete header")
        size = struct.unpack("<I", header)[0]
        if size <= 0:
            raise RuntimeError("Invalid message length")
        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Incomplete payload")

sv = SensorView()
sv.ParseFromString(payload)

if len(sv.lidar_sensor_view) != 1:
    raise RuntimeError("Expected one LiDAR")

lidar = sv.lidar_sensor_view[0]
cfg = lidar.view_configuration

nh = int(cfg.number_of_rays_horizontal)
nv = int(cfg.number_of_rays_vertical)

if (nh, nv) != (251, 21) or len(lidar.reflection) != nh * nv:
    raise RuntimeError("Unexpected LiDAR grid")

fx = fy = 320.0
cx, cy = 320.0, 240.0
c = 299792458.0

projected = []

for index, ref in enumerate(lidar.reflection):
    tof = float(ref.time_of_flight)
    if not math.isfinite(tof) or tof <= 0:
        continue

    distance = c * tof / 2
    if not math.isfinite(distance) or distance <= 0.01:
        continue

    hi = index % nh
    vi = index // nh

    yaw = -cfg.field_of_view_horizontal/2 + (
        hi * cfg.field_of_view_horizontal/(nh-1)
    )
    pitch = -cfg.field_of_view_vertical/2 + (
        vi * cfg.field_of_view_vertical/(nv-1)
    )

    x = distance*math.cos(pitch)*math.cos(yaw) + 1.90
    y = distance*math.cos(pitch)*math.sin(yaw)
    z = distance*math.sin(pitch) - 0.90

    if x <= 0:
        continue

    u = cx + fx*y/x
    v = cy - fy*z/x

    if not (0 <= u < 640 and 0 <= v < 480):
        continue

    obj_id = (
        int(ref.object_id.value)
        if ref.HasField("object_id")
        else None
    )

    projected.append((u, v, distance, obj_id))

print("=== TASK 24.7.16 RESULTS ===")
print("FRAME=530")
print("TOTAL_PROJECTED_POINTS=", len(projected))
print("YOLO_BOX_COUNT=", len(boxes))

for row in boxes:
    x1 = float(row["X1"])
    y1 = float(row["Y1"])
    x2 = float(row["X2"])
    y2 = float(row["Y2"])

    inside = [
        p for p in projected
        if x1 <= p[0] <= x2 and y1 <= p[1] <= y2
    ]

    print()
    print("CLASS=", row["ClassName"])
    print("CONFIDENCE=", row["Confidence"])
    print("BBOX=", (x1, y1, x2, y2))
    print("LIDAR_POINTS_INSIDE_BOX=", len(inside))

    if inside:
        distances = [p[2] for p in inside]
        print("MIN_RANGE_M=", round(min(distances), 3))
        print("MEDIAN_RANGE_M=", round(median(distances), 3))
        print("MAX_RANGE_M=", round(max(distances), 3))

        # Diagnostic-only simulator labels; do not use in fusion.
        ids = Counter(
            p[3] for p in inside if p[3] is not None
        )
        print("GT_DIAGNOSTIC_OBJECT_IDS=", ids.most_common(5))
    else:
        print("NO_PROJECTED_LIDAR_POINTS_IN_BOX")

print()
print("MODEL=NOMINAL_UNCALIBRATED")
print("ASSOCIATION_STATUS=DIAGNOSTIC_ONLY")
print("SIMULATOR_OBJECT_IDS_USED_FOR_ASSOCIATION=NO")
print("FILES_MODIFIED=NO")
print("TASK24_07_16_OVERLAP_AUDIT_COMPLETE")