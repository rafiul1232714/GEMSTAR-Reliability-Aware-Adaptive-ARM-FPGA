import csv
import json
import math
import struct
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_20_Final_Research")
SOURCE = Path(r"E:\GEMSTAR_Project\gemstar\Output\20261102T180104Z_sv_380_X_806_GEMSTAR.osi")
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

TARGET_ID = 76765
FRAMES = set(range(95, 100))
C = 299705543.0

with (DATA / "task20_52_external_gt_50m.csv").open(
    newline="", encoding="utf-8-sig"
) as f:
    targets = {
        int(row["Frame"]): row
        for row in csv.DictReader(f)
        if int(row["ObjectID"]) == TARGET_ID
        and int(row["Frame"]) in FRAMES
    }

def rotate(x, y, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return c*x-s*y, s*x+c*y

def angular_error(a, b):
    return math.atan2(math.sin(a-b), math.cos(a-b))

results = []

print("\n=== TASK 20.55 RADAR RAY ALIGNMENT ===")

with SOURCE.open("rb") as f:
    for frame in range(100):
        header = f.read(4)
        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete OSI frame header")

        size = struct.unpack("<I", header)[0]
        if not 0 < size < 100_000_000:
            raise RuntimeError("Invalid frame size")

        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Truncated frame")

        if frame not in FRAMES or frame not in targets:
            continue

        sv = SensorView()
        sv.ParseFromString(payload)

        if not sv.HasField("global_ground_truth"):
            print(f"Frame {frame}: no host ground truth")
            continue

        ngt = sv.global_ground_truth
        if not ngt.HasField("host_vehicle_id"):
            print(f"Frame {frame}: no host ID")
            continue

        host_id = ngt.host_vehicle_id.value
        hosts = [
            o for o in ngt.moving_object
            if o.id.value == host_id
        ]

        if not hosts:
            print(f"Frame {frame}: host pose missing")
            continue

        host = hosts[0]
        hp = host.base.position
        ho = host.base.orientation

        if abs(ho.pitch) > 1e-6 or abs(ho.roll) > 1e-6:
            print(f"Frame {frame}: unsupported host rotation")
            continue

        target = targets[frame]
        tx, ty, tz = (
            float(target[k]) for k in ("X", "Y", "Z")
        )

        for radar_index, view in enumerate(sv.radar_sensor_view):
            if not view.HasField("view_configuration"):
                continue

            cfg = view.view_configuration
            mp = cfg.mounting_position.position
            mo = cfg.mounting_position.orientation

            if any(abs(v) > 1e-6 for v in (
                mo.yaw, mo.pitch, mo.roll
            )):
                print(f"Frame {frame}: unsupported mount rotation")
                continue

            mx, my = rotate(mp.x, mp.y, ho.yaw)
            sx = hp.x + mx
            sy = hp.y + my
            sz = hp.z + mp.z

            # Transform target centre into OSI radar-local axes.
            dx, dy = rotate(
                tx-sx, ty-sy, -ho.yaw
            )
            dz = tz-sz

            distance = math.sqrt(dx*dx+dy*dy+dz*dz)

            # GEMSTAR radar azimuth is in Unreal's local axes.
            az = math.atan2(-dy, dx)
            el = math.atan2(dz, math.hypot(dx,dy))

            # Reflection angles represent configured ray directions.
            ray_directions = [
                (i, float(r.source_horizontal_angle),
                 float(r.source_vertical_angle), r)
                for i, r in enumerate(view.reflection)
            ]

            if not ray_directions:
                continue

            def error(ray):
                _, a, e, _ = ray
                return math.hypot(
                    angular_error(a, az),
                    e-el
                )

            nearest = min(ray_directions, key=error)
            idx, ray_az, ray_el, reflection = nearest

            tof = float(reflection.time_of_flight)
            signal = float(reflection.signal_strength)
            ray_range = (
                tof*C/2
                if math.isfinite(tof) and tof > 0
                else None
            )

            angular_separation = math.degrees(error(nearest))

            row = {
                "Frame": frame,
                "ObjectID": TARGET_ID,
                "RadarIndex": radar_index,
                "TargetCenterRangeM": round(distance, 5),
                "TargetAzimuthDeg": round(math.degrees(az), 4),
                "TargetElevationDeg": round(math.degrees(el), 4),
                "NearestRayIndex": idx,
                "RayAzimuthDeg": round(math.degrees(ray_az), 4),
                "RayElevationDeg": round(math.degrees(ray_el), 4),
                "AngularSeparationDeg": round(angular_separation, 4),
                "NearestRayRangeM": (
                    round(ray_range, 5)
                    if ray_range is not None else ""
                ),
                "NearestRaySignal": signal,
                "NearestRayPositiveReturn": bool(
                    ray_range is not None
                    and signal > 0
                )
            }

            results.append(row)

            print(
                f"Frame={frame} | "
                f"Target={distance:.2f}m | "
                f"AngularGap={angular_separation:.2f}deg | "
                f"Ray={idx} | "
                f"RayRange={row['NearestRayRangeM']}m | "
                f"Signal={signal:.4f}"
            )

csv_path = DATA / "task20_55_ray_alignment.csv"
json_path = FINDINGS / "task20_55_ray_alignment.json"

with csv_path.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "Frame", "ObjectID", "RadarIndex",
        "TargetCenterRangeM", "TargetAzimuthDeg",
        "TargetElevationDeg", "NearestRayIndex",
        "RayAzimuthDeg", "RayElevationDeg",
        "AngularSeparationDeg", "NearestRayRangeM",
        "NearestRaySignal", "NearestRayPositiveReturn"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

json_path.write_text(
    json.dumps({
        "Task": "20.55",
        "TargetID": TARGET_ID,
        "Frames": sorted(FRAMES),
        "Results": results,
        "Limitations": [
            "GT target centres are not collision surfaces",
            "Nearest angular ray may hit another object",
            "Coordinate transform requires independent validation",
            "GT pose timing uncertainty remains"
        ],
        "DetectionAccuracyValidated": False
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.55 COMPLETE ===")
print("Observations evaluated:", len(results))
print("CSV saved:", csv_path.is_file())
print("JSON saved:", json_path.is_file())
print("Radar detection accuracy validated:", False)
