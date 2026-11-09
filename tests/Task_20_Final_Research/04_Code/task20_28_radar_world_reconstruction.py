import csv
import json
import math
import struct
from collections import Counter
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

C_GEMSTAR = 299705543.0
FREQUENCY_HZ = 77e9
LIMIT = 100
ANGLE_TOL = 1e-6

def present(msg, name):
    return name in {
        f.name for f, _ in msg.ListFields()
    }

def frames(path):
    with path.open("rb") as f:
        for index in range(LIMIT):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete header")

            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI size")

            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated OSI message")

            msg = SensorView()
            msg.ParseFromString(payload)
            yield index, msg

def timestamp_ns(msg):
    return (
        int(msg.timestamp.seconds) * 1_000_000_000
        + int(msg.timestamp.nanos)
    )

def rotate_yaw(x, y, yaw):
    c = math.cos(yaw)
    s = math.sin(yaw)
    return c*x - s*y, s*x + c*y

def is_level(orientation):
    return (
        abs(orientation.pitch) < ANGLE_TOL
        and abs(orientation.roll) < ANGLE_TOL
    )

def get_host(sv):
    if not present(sv, "global_ground_truth"):
        return None, "NO_HOST_POSE"

    gt = sv.global_ground_truth

    if not present(gt, "host_vehicle_id"):
        return None, "NO_HOST_ID"

    host_id = int(gt.host_vehicle_id.value)

    objects = [
        obj for obj in gt.moving_object
        if int(obj.id.value) == host_id
        and present(obj.base, "position")
        and present(obj.base, "orientation")
    ]

    if not objects:
        return None, "NO_HOST_OBJECT"

    # GEMSTAR can export duplicate host entries.
    first = objects[0]

    a = first.base.position
    o = first.base.orientation

    for other in objects[1:]:
        b = other.base.position
        q = other.base.orientation

        difference = max(
            abs(a.x-b.x), abs(a.y-b.y), abs(a.z-b.z),
            abs(o.yaw-q.yaw),
            abs(o.pitch-q.pitch),
            abs(o.roll-q.roll)
        )

        if difference > 1e-6:
            return None, "INCONSISTENT_HOST_COPIES"

    if not is_level(o):
        return None, "NONLEVEL_HOST"

    return first, "OK"

rows = []
summaries = []

print("\n=== TASK 20.28 RADAR WORLD RECONSTRUCTION ===")

for path in sorted(RAW.rglob("*_sv_*.osi")):
    scenario = path.parent.name
    counts = Counter()
    start_rows = len(rows)

    for frame, sv in frames(path):
        counts["Frames"] += 1

        host, status = get_host(sv)

        if host is None:
            counts[status] += 1
            continue

        hp = host.base.position
        ho = host.base.orientation

        for radar_index, view in enumerate(
            sv.radar_sensor_view
        ):
            if not present(view, "view_configuration"):
                counts["NO_CONFIGURATION"] += 1
                continue

            cfg = view.view_configuration

            if not present(cfg, "mounting_position"):
                counts["NO_MOUNT"] += 1
                continue

            mount = cfg.mounting_position

            if (
                not present(mount, "position")
                or not present(mount, "orientation")
            ):
                counts["INCOMPLETE_MOUNT"] += 1
                continue

            mp = mount.position
            mo = mount.orientation

            # Initial, explicitly restricted yaw-only model.
            if not is_level(mo):
                counts["NONLEVEL_MOUNT"] += 1
                continue

            if abs(mo.yaw) >= ANGLE_TOL:
                counts["ROTATED_MOUNT_SKIPPED"] += 1
                continue

            counts["UsableRadarViews"] += 1

            for reflection_index, ref in enumerate(
                view.reflection
            ):
                counts["ReflectionSlots"] += 1

                tof = float(ref.time_of_flight)
                signal = float(ref.signal_strength)
                doppler = float(ref.doppler_shift)
                az = float(ref.source_horizontal_angle)
                el = float(ref.source_vertical_angle)

                if (
                    not all(map(math.isfinite, [
                        tof, signal, doppler, az, el
                    ]))
                    or tof <= 0
                    or signal <= 0
                ):
                    continue

                r = tof * C_GEMSTAR / 2.0
                velocity = (
                    doppler * C_GEMSTAR
                    / (2.0 * FREQUENCY_HZ)
                )

                # Unreal ray angles converted into OSI axes.
                lx = r * math.cos(el) * math.cos(az)
                ly = -r * math.cos(el) * math.sin(az)
                lz = r * math.sin(el)

                # Mount translation and host yaw in OSI.
                vx = mp.x + lx
                vy = mp.y + ly
                vz = mp.z + lz

                wx, wy = rotate_yaw(
                    vx, vy, float(ho.yaw)
                )

                wx += float(hp.x)
                wy += float(hp.y)
                wz = float(hp.z) + vz

                rows.append({
                    "Recording": scenario,
                    "FrameIndex": frame,
                    "TimestampNs": timestamp_ns(sv),
                    "HostID": int(host.id.value),
                    "RadarIndex": radar_index,
                    "ReflectionIndex": reflection_index,
                    "RangeM": r,
                    "RadialVelocityMps": velocity,
                    "LocalX": lx,
                    "LocalY_OSI": ly,
                    "LocalZ": lz,
                    "WorldX": wx,
                    "WorldY": wy,
                    "WorldZ": wz,
                    "SignalStrength": signal
                })

                counts["CandidateReturns"] += 1

    summary = {
        "Recording": scenario,
        "Frames": counts["Frames"],
        "UsableRadarViews": counts["UsableRadarViews"],
        "ReflectionSlots": counts["ReflectionSlots"],
        "CandidateReturns": counts["CandidateReturns"],
        "NoHostPoseFrames": counts["NO_HOST_POSE"],
        "NoHostIDFrames": counts["NO_HOST_ID"],
        "NonlevelHostFrames": counts["NONLEVEL_HOST"],
        "InconsistentHostFrames":
            counts["INCONSISTENT_HOST_COPIES"],
        "SkippedNonlevelMountViews":
            counts["NONLEVEL_MOUNT"],
        "SkippedRotatedMountViews":
            counts["ROTATED_MOUNT_SKIPPED"],
    }

    summaries.append(summary)

    print(
        f"{scenario:28s}"
        f" | Frames={summary['Frames']:3d}"
        f" | Views={summary['UsableRadarViews']:3d}"
        f" | Candidates={summary['CandidateReturns']:5d}"
        f" | NoPose={summary['NoHostPoseFrames']:3d}"
    )

def save_csv(path, records, columns):
    with path.open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(records)

points_path = DATA / "task20_28_radar_world_points.csv"
summary_path = DATA / "task20_28_radar_world_summary.csv"
report_path = FINDINGS / "task20_28_world_reconstruction.json"

point_columns = [
    "Recording", "FrameIndex", "TimestampNs",
    "HostID", "RadarIndex", "ReflectionIndex",
    "RangeM", "RadialVelocityMps",
    "LocalX", "LocalY_OSI", "LocalZ",
    "WorldX", "WorldY", "WorldZ", "SignalStrength"
]

save_csv(points_path, rows, point_columns)
save_csv(summary_path, summaries, list(summaries[0]))

report = {
    "Task": "20.28",
    "CoordinateConvention": "OSI metres, right-handed",
    "SpeedOfLightMps": C_GEMSTAR,
    "EmitterFrequencyHz": FREQUENCY_HZ,
    "RotationModel": "Yaw-only; zero mount orientation",
    "WorldPoints": len(rows),
    "RecordingSummary": summaries,
    "Limitations": [
        "Only first 100 frames inspected per recording",
        "Radar/GT sampling-time discrepancy unresolved",
        "No radar-to-object associations validated",
        "No collision-geometry accuracy verified",
        "No measured FPGA energy savings"
    ],
    "WorldCoordinatesPhysicallyValidated": False,
    "RadarAccuracyValidated": False
}

report_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.28 COMPLETE ===")
print("World-coordinate candidate points:", len(rows))
print("Points CSV saved:", points_path.is_file())
print("Summary CSV saved:", summary_path.is_file())
print("JSON report saved:", report_path.is_file())
print("World-coordinate accuracy validated:", False)
print("Radar detection accuracy validated:", False)
print("Energy measured:", False)
