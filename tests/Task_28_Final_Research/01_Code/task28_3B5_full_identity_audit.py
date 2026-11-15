import csv
import math
import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_28_Final_Research"
OUT = TASK / "02_CSV_Data" / "task28_3B5_full_identity_audit.csv"
REFERENCE = TASK / "02_CSV_Data" / "task28_3A2_full_candidate_returns.csv"

SCENARIO = "fog_postfix_validation"
INVALID_ID = (1 << 64) - 1
C = 299792458.0

FIELDS = [
    "Frame", "Timestamp_ns", "RangeCandidates",
    "ZeroSignalInvalidID", "ZeroSignalObjectID",
    "ZeroSignalMissingID", "PositiveSignalObjectID",
    "PositiveSignalInvalidOrMissingID",
    "OtherSignalCandidates", "IdentityConsistent"
]

def main():
    if OUT.exists():
        raise RuntimeError(f"Output already exists: {OUT}")

    sources = sorted(
        (ROOT / "data" / "raw" / SCENARIO).glob("*_sv_*.osi")
    )
    if len(sources) != 1:
        raise RuntimeError("Expected exactly one fog-postfix SV file")

    with REFERENCE.open(newline="", encoding="utf-8-sig") as f:
        reference = {
            int(r["Frame"]): r
            for r in csv.DictReader(f)
            if r["Scenario"] == SCENARIO and r["Sensor"] == "LiDAR"
        }

    if len(reference) != 705:
        raise RuntimeError("Expected 705 reference LiDAR frames")

    totals = {name: 0 for name in FIELDS[2:-1]}
    rows = []

    with sources[0].open("rb") as f:
        frame = 0

        while True:
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise RuntimeError("Truncated frame header")

            size = struct.unpack("<I", header)[0]
            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid frame size")

            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError("Truncated payload")

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            if len(sv.lidar_sensor_view) != 1:
                raise RuntimeError(f"LiDAR view missing at frame {frame}")

            counts = {name: 0 for name in totals}

            for reflection in sv.lidar_sensor_view[0].reflection:
                tof = float(reflection.time_of_flight)
                strength = float(reflection.signal_strength)

                if not math.isfinite(tof) or not math.isfinite(strength):
                    raise RuntimeError("Nonfinite LiDAR measurement")

                if tof <= 0 or C * tof / 2 <= 0.01:
                    continue

                counts["RangeCandidates"] += 1

                has_id = reflection.HasField("object_id")
                oid = int(reflection.object_id.value) if has_id else None
                valid_id = has_id and oid != INVALID_ID

                if strength == 0:
                    if not has_id:
                        counts["ZeroSignalMissingID"] += 1
                    elif valid_id:
                        counts["ZeroSignalObjectID"] += 1
                    else:
                        counts["ZeroSignalInvalidID"] += 1
                elif strength > 0:
                    if valid_id:
                        counts["PositiveSignalObjectID"] += 1
                    else:
                        counts["PositiveSignalInvalidOrMissingID"] += 1
                else:
                    counts["OtherSignalCandidates"] += 1

            ref = reference.get(frame)
            if ref is None:
                raise RuntimeError(f"Reference frame missing: {frame}")

            ref_candidates = int(ref["CandidateReturns"])
            ref_positive = int(ref["PositiveSignalCandidates"])

            observed_positive = (
                counts["PositiveSignalObjectID"] +
                counts["PositiveSignalInvalidOrMissingID"]
            )

            consistent = (
                counts["RangeCandidates"] == ref_candidates
                and observed_positive == ref_positive
                and sum(
                    v for k, v in counts.items()
                    if k != "RangeCandidates"
                ) == counts["RangeCandidates"]
                and counts["ZeroSignalObjectID"] == 0
                and counts["ZeroSignalMissingID"] == 0
                and counts["PositiveSignalInvalidOrMissingID"] == 0
                and counts["OtherSignalCandidates"] == 0
            )

            if not consistent:
                raise RuntimeError(
                    f"Identity/reference mismatch at frame {frame}: {counts}"
                )

            timestamp = (
                int(sv.timestamp.seconds) * 1_000_000_000
                + int(sv.timestamp.nanos)
            )

            rows.append({
                "Frame": frame,
                "Timestamp_ns": timestamp,
                **counts,
                "IdentityConsistent": 1
            })

            for key in totals:
                totals[key] += counts[key]

            frame += 1

    if len(rows) != 705:
        raise RuntimeError(f"Unexpected frame count: {len(rows)}")

    temporary = OUT.with_name(OUT.name + ".partial")

    if temporary.exists():
        raise RuntimeError(f"Partial output already exists: {temporary}")

    try:
        with temporary.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        temporary.rename(OUT)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    print("\n=== TASK 28.3B.5 RESULTS ===")
    print(f"Frames verified: {len(rows)}")

    for key, value in totals.items():
        print(f"{key}: {value}")

    print(f"CSV: {OUT}")
    print("STATUS: FULL IDENTITY AUDIT PASS")

if __name__ == "__main__":
    main()
