import csv
import math
import struct
from collections import Counter
from pathlib import Path
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

lidar = sv.lidar_sensor_view[0]
cfg = lidar.view_configuration

nh = int(cfg.number_of_rays_horizontal)
nv = int(cfg.number_of_rays_vertical)

if (nh, nv) != (251, 21):
    raise RuntimeError("Unexpected LiDAR grid")

c = 299792458.0
points = []

for index, ref in enumerate(lidar.reflection):
    tof = float(ref.time_of_flight)

    if not math.isfinite(tof) or tof <= 0:
        continue

    distance = c * tof / 2

    if not math.isfinite(distance) or distance <= 0.01:
        continue

    hi = index % nh
    vi = index // nh

    yaw = (
        -cfg.field_of_view_horizontal / 2
        + hi * cfg.field_of_view_horizontal / (nh - 1)
    )

    pitch = (
        -cfg.field_of_view_vertical / 2
        + vi * cfg.field_of_view_vertical / (nv - 1)
    )

    x = distance * math.cos(pitch) * math.cos(yaw) + 1.90
    y = distance * math.cos(pitch) * math.sin(yaw)
    z = distance * math.sin(pitch) - 0.90

    if x <= 0:
        continue

    u = 320 + 320 * y / x
    v = 240 - 320 * z / x

    if 0 <= u < 640 and 0 <= v < 480:
        points.append((u, v, distance))

print("=== TASK 24.7.17 RESULTS ===")
print("FRAME=530")
print("PROJECTED_POINTS=", len(points))
print("DEPTH_BIN_WIDTH_M=2.0")

for row in boxes:
    x1, y1, x2, y2 = (
        float(row[k]) for k in ("X1", "Y1", "X2", "Y2")
    )

    inside = [
        p for p in points
        if x1 <= p[0] <= x2 and y1 <= p[1] <= y2
    ]

    bins = Counter(
        int(p[2] // 2) * 2 for p in inside
    )

    print()
    print("CLASS=", row["ClassName"])
    print("CONFIDENCE=", row["Confidence"])
    print("TOTAL_INSIDE_BOX=", len(inside))

    for start, count in sorted(
        bins.items(),
        key=lambda item: (-item[1], item[0])
    )[:8]:
        print(
            f"DEPTH_BIN={start:.1f}-{start+2:.1f}m "
            f"COUNT={count}"
        )

    if bins:
        dominant_start, dominant_count = bins.most_common(1)[0]
        print("DOMINANT_BIN_START_M=", dominant_start)
        print("DOMINANT_BIN_POINTS=", dominant_count)
        print(
            "DOMINANT_BIN_FRACTION=",
            round(dominant_count / len(inside), 4)
        )

print()
print("SIMULATOR_IDS_USED=NO")
print("ASSOCIATION_STATUS=DIAGNOSTIC_ONLY")
print("OSI_MODIFIED=NO")
print("TASK24_07_17_DEPTH_CONSISTENCY_COMPLETE")