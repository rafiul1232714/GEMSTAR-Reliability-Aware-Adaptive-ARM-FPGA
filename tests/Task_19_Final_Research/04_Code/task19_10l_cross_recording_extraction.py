import csv
import math
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_19_Final_Research"

RAW = ROOT / "data" / "raw"
OUT = BASE / "08_Extracted_PointClouds" / "task19_10l_cross_recording"
DATA = BASE / "02_CSV_Data"

OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_postfix_validation",
]

C = 299705543.0
INVALID_ID = (1 << 64) - 1

H_RAYS = 251
V_RAYS = 21
EXPECTED = H_RAYS * V_RAYS

LOW_ROI = 1600
HIGH_ROI = 2200

FIELDS = [
    "FrameIndex",
    "RayIndex",
    "ObjectID",
    "RangeM",
    "SignalStrength",
    "X",
    "Y",
    "Z",
]

def reconstruct(sv, frame_index):

    if len(sv.lidar_sensor_view) != 1:
        raise ValueError("Expected exactly one LiDAR sensor")

    reflections = sv.lidar_sensor_view[0].reflection

    if len(reflections) != EXPECTED:
        raise ValueError(
            f"Expected {EXPECTED} reflections, got {len(reflections)}"
        )

    rows = []

    for i, r in enumerate(reflections):

        distance = float(r.time_of_flight) * C / 2.0
        strength = float(r.signal_strength)
        oid = int(r.object_id.value)

        valid = (
            math.isfinite(distance)
            and math.isfinite(strength)
            and 0.5 <= distance <= 200.0
            and strength > 0.0
            and oid != INVALID_ID
        )

        if not valid:
            continue

        hi = i % H_RAYS
        vi = i // H_RAYS

        h = math.radians(-45.0 + hi * 90.0 / 250.0)
        v = math.radians(-10.0 + vi * 20.0 / 20.0)

        x = distance * math.cos(v) * math.cos(h)
        y = -distance * math.cos(v) * math.sin(h)
        z = distance * math.sin(v)

        rows.append({
            "FrameIndex": frame_index,
            "RayIndex": i,
            "ObjectID": oid,
            "RangeM": distance,
            "SignalStrength": strength,
            "X": x,
            "Y": y,
            "Z": z,
        })

    return rows

results = []

print("\n=== TASK 19.10L CROSS-RECORDING EXTRACTION ===")

for scenario in SCENARIOS:

    files = sorted(
        (RAW / scenario).glob("*_sv_*.osi")
    )

    if len(files) != 1:
        raise RuntimeError(
            f"{scenario}: expected one SensorView recording, "
            f"found {len(files)}"
        )

    source = files[0]
    scenario_out = OUT / scenario
    scenario_out.mkdir(parents=True, exist_ok=True)

    print(f"\nScenario: {scenario}")
    print(f"Recording: {source.name}")

    frame = 0
    selected = 0

    with source.open("rb") as f:

        while True:

            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Truncated OSI header")

            length = struct.unpack("<I", header)[0]

            if not 0 < length <= 100_000_000:
                raise RuntimeError(
                    f"Invalid frame length: {length}"
                )

            # Fixed interval chosen before evaluation.
            if frame % 50 != 0:
                f.seek(length, 1)
                frame += 1
                continue

            payload = f.read(length)

            if len(payload) != length:
                raise RuntimeError(
                    f"Truncated frame {frame}"
                )

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            rows = reconstruct(sv, frame)

            roi_count = sum(
                0 <= r["X"] <= 20
                and -6 <= r["Y"] <= 6
                for r in rows
            )

            if roi_count < LOW_ROI or roi_count > HIGH_ROI:
                decision = "Full-reference fallback"
            else:
                decision = "Voxel-assisted"

            filename = (
                f"task19_10l_frame{frame:03d}_candidate_xyz.csv"
            )

            destination = scenario_out / filename

            with destination.open(
                "w", newline="", encoding="utf-8"
            ) as output_file:

                writer = csv.DictWriter(
                    output_file,
                    fieldnames=FIELDS
                )
                writer.writeheader()
                writer.writerows(rows)

            result = {
                "Scenario": scenario,
                "Recording": source.name,
                "FrameIndex": frame,
                "TotalRays": EXPECTED,
                "CandidatePoints": len(rows),
                "ROIPoints": roi_count,
                "UniqueObjectIDs": len({
                    r["ObjectID"] for r in rows
                }),
                "FrozenRuleDecision": decision,
                "CandidateCSV": str(destination),
            }

            results.append(result)
            selected += 1

            print(
                f"Frame {frame:3d} | "
                f"valid={len(rows):4d} | "
                f"ROI={roi_count:4d} | "
                f"rule={decision}"
            )

            frame += 1

    print(
        f"Completed {scenario}: "
        f"{frame} total frames, {selected} selected"
    )

inventory = DATA / "task19_10l_cross_recording_inventory.csv"

with inventory.open(
    "w", newline="", encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=list(results[0].keys())
    )

    writer.writeheader()
    writer.writerows(results)

print("\n=== TASK 19.10L COMPLETE ===")
print("Selected clouds:", len(results))

for scenario in SCENARIOS:

    selected_rows = [
        r for r in results if r["Scenario"] == scenario
    ]

    full = sum(
        r["FrozenRuleDecision"] == "Full-reference fallback"
        for r in selected_rows
    )

    voxel = len(selected_rows) - full

    print(
        f"{scenario}: "
        f"{len(selected_rows)} frames, "
        f"full={full}, voxel={voxel}"
    )

print("Inventory saved:", inventory.is_file())
print("Output folder:", OUT)
