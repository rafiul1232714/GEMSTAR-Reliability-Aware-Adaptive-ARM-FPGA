import csv
import math
import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
OUT = ROOT / "tests/Task_28_Final_Research/02_CSV_Data/task28_3B4_zero_signal_identity.csv"
INVALID_ID = (1 << 64) - 1
C = 299792458.0
FRAMES = {0, 1, 2, 100, 350, 690, 704}

SCENARIOS = ["baseline_clear", "fog_postfix_validation"]

FIELDS = [
    "Scenario", "Frame", "RangeCandidates",
    "ZeroSignal", "ZeroWithInvalidID", "ZeroWithObjectID",
    "PositiveWithInvalidID", "PositiveWithObjectID",
    "ZeroWithNoObjectIDField"
]

def analyze(scenario, frame, sv):
    if len(sv.lidar_sensor_view) != 1:
        raise RuntimeError("Expected one LiDAR view")

    count = {
        "RangeCandidates": 0,
        "ZeroSignal": 0,
        "ZeroWithInvalidID": 0,
        "ZeroWithObjectID": 0,
        "PositiveWithInvalidID": 0,
        "PositiveWithObjectID": 0,
        "ZeroWithNoObjectIDField": 0
    }

    for r in sv.lidar_sensor_view[0].reflection:
        tof = float(r.time_of_flight)
        strength = float(r.signal_strength)

        if not math.isfinite(tof) or not math.isfinite(strength):
            raise RuntimeError("Nonfinite reflection")

        if tof <= 0 or C * tof / 2 <= 0.01:
            continue

        count["RangeCandidates"] += 1

        has_id = r.HasField("object_id")
        oid = int(r.object_id.value) if has_id else None

        if strength == 0:
            count["ZeroSignal"] += 1

            if not has_id:
                count["ZeroWithNoObjectIDField"] += 1
            elif oid == INVALID_ID:
                count["ZeroWithInvalidID"] += 1
            else:
                count["ZeroWithObjectID"] += 1

        elif strength > 0:
            if not has_id or oid == INVALID_ID:
                count["PositiveWithInvalidID"] += 1
            else:
                count["PositiveWithObjectID"] += 1

    return {"Scenario": scenario, "Frame": frame, **count}

def main():
    rows = []

    for scenario in SCENARIOS:
        sources = list((ROOT / "data/raw" / scenario).glob("*_sv_*.osi"))
        if len(sources) != 1:
            raise RuntimeError(f"Unexpected recording count: {scenario}")

        found = set()

        with sources[0].open("rb") as f:
            frame = 0

            while found != FRAMES:
                header = f.read(4)
                if not header:
                    break
                if len(header) != 4:
                    raise RuntimeError("Truncated header")

                size = struct.unpack("<I", header)[0]
                if not 0 < size <= 100_000_000:
                    raise RuntimeError("Invalid frame length")

                if frame not in FRAMES:
                    f.seek(size, 1)
                    frame += 1
                    continue

                payload = f.read(size)
                if len(payload) != size:
                    raise RuntimeError("Truncated frame")

                sv = osi_sensorview_pb2.SensorView()
                sv.ParseFromString(payload)
                rows.append(analyze(scenario, frame, sv))
                found.add(frame)
                frame += 1

        if found != FRAMES:
            raise RuntimeError(f"Missing frames in {scenario}")

    with OUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TASK 28.3B.4 RESULTS ===")

    for r in rows:
        print(
            f"{r['Scenario']} frame={r['Frame']} "
            f"zero={r['ZeroSignal']} "
            f"zero_invalid_id={r['ZeroWithInvalidID']} "
            f"zero_object_id={r['ZeroWithObjectID']} "
            f"zero_missing_id={r['ZeroWithNoObjectIDField']} "
            f"positive_object_id={r['PositiveWithObjectID']}"
        )

    print(f"\nCSV: {OUT}")
    print("STATUS: SUCCESS")

if __name__ == "__main__":
    main()
