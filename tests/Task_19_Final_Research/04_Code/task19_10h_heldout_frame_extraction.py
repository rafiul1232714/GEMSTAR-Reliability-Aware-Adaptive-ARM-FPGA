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

TARGETS = [25, 75, 125, 175, 225, 275, 325, 425]
TARGET_SET = set(TARGETS)

SPEED_OF_LIGHT = 299705543.0
INVALID_ID = (1 << 64) - 1

H_RAYS = 251
V_RAYS = 21
EXPECTED_RAYS = H_RAYS * V_RAYS

def extract(frame_index, sv):
    if len(sv.lidar_sensor_view) != 1:
        raise RuntimeError(
            f"Unexpected LiDAR count in frame {frame_index}"
        )

    reflections = sv.lidar_sensor_view[0].reflection

    if len(reflections) != EXPECTED_RAYS:
        raise RuntimeError(
            f"Unexpected reflection count in frame {frame_index}"
        )

    rows = []

    for i, reflection in enumerate(reflections):
        tof = float(reflection.time_of_flight)
        strength = float(reflection.signal_strength)
        oid = int(reflection.object_id.value)

        distance = tof * SPEED_OF_LIGHT / 2.0

        if not (
            math.isfinite(distance)
            and math.isfinite(strength)
            and 0.5 <= distance <= 200.0
            and strength > 0.0
            and oid != INVALID_ID
        ):
            continue

        h_index = i % H_RAYS
        v_index = i // H_RAYS

        horizontal = math.radians(
            -45.0 + 90.0 * h_index / (H_RAYS - 1)
        )

        vertical = math.radians(
            -10.0 + 20.0 * v_index / (V_RAYS - 1)
        )

        x = distance * math.cos(vertical) * math.cos(horizontal)
        y = -distance * math.cos(vertical) * math.sin(horizontal)
        z = distance * math.sin(vertical)

        rows.append({
            "FrameIndex": frame_index,
            "RayIndex": i,
            "RangeM": distance,
            "SignalStrength": strength,
            "ObjectID": oid,
            "X": x,
            "Y": y,
            "Z": z,
        })

    filename = (
        f"task19_10h_frame{frame_index:03d}_candidate_xyz.csv"
    )

    output = CLOUD_DIR / filename

    with output.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "FrameIndex",
                "RayIndex",
                "RangeM",
                "SignalStrength",
                "ObjectID",
                "X",
                "Y",
                "Z",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    roi_points = sum(
        0 <= r["X"] <= 20 and -6 <= r["Y"] <= 6
        for r in rows
    )

    # Frozen scheduler rule, for input-only decisions.
    if roi_points < 1600 or roi_points > 2200:
        decision = "Full-reference fallback"
    else:
        decision = "Voxel-assisted"

    return {
        "FrameIndex": frame_index,
        "TotalRays": EXPECTED_RAYS,
        "CandidatePoints": len(rows),
        "ROIPoints": roi_points,
        "UniqueObjectIDs": len(
            {r["ObjectID"] for r in rows}
        ),
        "FrozenRuleDecision": decision,
        "CandidateCSV": str(output),
    }

assert SOURCE.is_file(), f"Missing OSI file: {SOURCE}"

CLOUD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

results = []
index = 0

print("\n=== TASK 19.10H HELD-OUT FRAME EXTRACTION ===")

with SOURCE.open("rb") as f:
    while True:
        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Truncated OSI header")

        length = struct.unpack("<I", header)[0]

        if not 0 < length <= 100_000_000:
            raise RuntimeError("Invalid record length")

        if index not in TARGET_SET:
            f.seek(length, 1)
            index += 1
            continue

        payload = f.read(length)

        if len(payload) != length:
            raise RuntimeError("Truncated SensorView")

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(payload)

        row = extract(index, sv)
        results.append(row)

        print(
            f"Frame {index:3d} | "
            f"valid={row['CandidatePoints']:4d} | "
            f"ROI={row['ROIPoints']:4d} | "
            f"IDs={row['UniqueObjectIDs']} | "
            f"rule={row['FrozenRuleDecision']}"
        )

        index += 1

found = {r["FrameIndex"] for r in results}

if found != TARGET_SET:
    raise RuntimeError(
        f"Missing frames: {sorted(TARGET_SET - found)}"
    )

results.sort(key=lambda r: r["FrameIndex"])

output = DATA_DIR / "task19_10h_heldout_frame_inventory.csv"

with output.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

print("\n=== TASK 19.10H COMPLETE ===")
print("Total SensorView records:", index)
print("Held-out frames:", len(results))
print("CSV point clouds saved:", len(results))
print("Inventory saved:", output.is_file())
