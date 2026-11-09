import csv
import math
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_19_Final_Research"

SOURCE = (
    ROOT / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

CLOUD_DIR = BASE / "08_Extracted_PointClouds"
DATA_DIR = BASE / "02_CSV_Data"

CLOUD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

FRAMES = [0, 50, 100, 150, 200, 250, 350, 450]
TARGETS = set(FRAMES)

# From GEMSTAR SimpleLidar.cpp / SimpleLidar.h
SPEED_OF_LIGHT = 299705543.0

HORIZONTAL_RAYS = 251
VERTICAL_RAYS = 21
EXPECTED_RAYS = HORIZONTAL_RAYS * VERTICAL_RAYS

H_MIN = -45.0
H_MAX = 45.0
V_MIN = -10.0
V_MAX = 10.0

MIN_RANGE = 0.5
MAX_RANGE = 200.0

INVALID_OBJECT_ID = (1 << 64) - 1

def get_id(value):
    if hasattr(value, "value"):
        return int(value.value)
    return int(value)

def reconstruct(frame_index, sv):
    if len(sv.lidar_sensor_view) != 1:
        raise RuntimeError(
            f"Frame {frame_index}: expected 1 LiDAR sensor, "
            f"got {len(sv.lidar_sensor_view)}"
        )

    reflections = sv.lidar_sensor_view[0].reflection

    if len(reflections) != EXPECTED_RAYS:
        raise RuntimeError(
            f"Frame {frame_index}: unexpected ray count "
            f"{len(reflections)}"
        )

    candidates = []
    all_rows = []

    positive_tof = 0
    positive_signal = 0

    for ray_index, reflection in enumerate(reflections):

        tof = float(reflection.time_of_flight)
        strength = float(reflection.signal_strength)

        object_id = get_id(reflection.object_id)

        h_index = ray_index % HORIZONTAL_RAYS
        v_index = ray_index // HORIZONTAL_RAYS

        h_deg = H_MIN + h_index * (
            (H_MAX - H_MIN) / (HORIZONTAL_RAYS - 1)
        )

        v_deg = V_MIN + v_index * (
            (V_MAX - V_MIN) / (VERTICAL_RAYS - 1)
        )

        h = math.radians(h_deg)
        v = math.radians(v_deg)

        distance = tof * SPEED_OF_LIGHT / 2.0

        x = distance * math.cos(v) * math.cos(h)
        y = -distance * math.cos(v) * math.sin(h)
        z = distance * math.sin(v)

        if tof > 0:
            positive_tof += 1

        if strength > 0:
            positive_signal += 1

        valid = (
            math.isfinite(distance)
            and math.isfinite(strength)
            and MIN_RANGE <= distance <= MAX_RANGE
            and strength > 0
            and object_id != INVALID_OBJECT_ID
        )

        row = {
            "FrameIndex": frame_index,
            "RayIndex": ray_index,
            "HorizontalIndex": h_index,
            "VerticalIndex": v_index,
            "HorizontalAngleDeg": h_deg,
            "VerticalAngleDeg": v_deg,
            "TimeOfFlight": tof,
            "RangeM": distance,
            "SignalStrength": strength,
            "ObjectID": object_id,
            "X": x,
            "Y": y,
            "Z": z,
            "ValidCandidate": int(valid),
        }

        all_rows.append(row)

        if valid:
            candidates.append(row)

    prefix = f"task19_10b_frame{frame_index:03d}"

    all_file = CLOUD_DIR / f"{prefix}_all_rays.csv"
    valid_file = CLOUD_DIR / f"{prefix}_candidate_xyz.csv"

    fieldnames = list(all_rows[0].keys())

    for destination, records in (
        (all_file, all_rows),
        (valid_file, candidates),
    ):
        with destination.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    return {
        "FrameIndex": frame_index,
        "TotalReflections": len(reflections),
        "PositiveTOF": positive_tof,
        "PositiveSignal": positive_signal,
        "ValidCandidatePoints": len(candidates),
        "RejectedReflections": len(reflections) - len(candidates),
        "CandidateFractionPercent": round(
            100.0 * len(candidates) / len(reflections), 3
        ),
        "UniqueCandidateObjectIDs": len(
            {row["ObjectID"] for row in candidates}
        ),
        "CandidateCSV": str(valid_file),
        "AllRaysCSV": str(all_file),
    }

assert SOURCE.is_file(), f"Missing OSI recording: {SOURCE}"

print("\n=== TASK 19.10B MULTI-FRAME RECONSTRUCTION ===")

results = []
frame_index = 0

with SOURCE.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Truncated OSI record header")

        length = struct.unpack("<I", header)[0]

        if length <= 0 or length > 100_000_000:
            raise RuntimeError(
                f"Invalid record length at frame {frame_index}"
            )

        if frame_index not in TARGETS:
            f.seek(length, 1)
            frame_index += 1
            continue

        payload = f.read(length)

        if len(payload) != length:
            raise RuntimeError(
                f"Truncated OSI frame {frame_index}"
            )

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(payload)

        result = reconstruct(frame_index, sv)
        results.append(result)

        print(
            f"Frame {frame_index:3d}: "
            f"rays={result['TotalReflections']}, "
            f"valid={result['ValidCandidatePoints']}, "
            f"rejected={result['RejectedReflections']}, "
            f"objectIDs={result['UniqueCandidateObjectIDs']}"
        )

        frame_index += 1

observed = {r["FrameIndex"] for r in results}

if observed != TARGETS:
    raise RuntimeError(
        f"Missing requested frames: {sorted(TARGETS - observed)}"
    )

results.sort(key=lambda r: r["FrameIndex"])

summary_file = (
    DATA_DIR / "task19_10b_multiframe_xyz_summary.csv"
)

with summary_file.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

print("\n=== FRAME 150 CROSS-CHECK ===")

frame150 = next(
    r for r in results if r["FrameIndex"] == 150
)

print(
    "New frame 150 candidate points:",
    frame150["ValidCandidatePoints"]
)
print("Previous Task 19.2A candidate points: 2044")

if frame150["ValidCandidatePoints"] == 2044:
    print("Frame 150 count verification: PASS")
else:
    print("Frame 150 count verification: DIFFERENT")
    print("Investigate before benchmarking.")

print("\n=== TASK 19.10B COMPLETE ===")
print("Frames reconstructed:", len(results))
print("Total OSI records:", frame_index)
print("Summary CSV saved:", summary_file.is_file())
print("Candidate CSVs saved:", len(results))
print("All-ray CSVs saved:", len(results))
