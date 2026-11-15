import csv
import math
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"

OUT = (
    ROOT / "tests" / "Task_28_Final_Research"
    / "02_CSV_Data" / "task28_3A_candidate_return_pilot.csv"
)

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
]

MAX_FRAMES = 100
C = 299792458.0
MIN_RANGE_M = 0.01

FIELDS = [
    "Scenario", "Recording", "Frame", "Timestamp_ns",
    "Sensor", "RawReflections", "CandidateReturns",
    "PositiveSignalCandidates", "ZeroTOF",
    "NearZeroReturns", "CandidatePct", "PositiveSignalPct"
]


def analyze_sensor(scenario, filename, frame, timestamp, sensor, view):
    raw = len(view.reflection)

    candidate = 0
    positive_signal = 0
    zero_tof = 0
    near_zero = 0

    for reflection in view.reflection:
        tof = float(reflection.time_of_flight)
        signal = float(reflection.signal_strength)
        doppler = float(reflection.doppler_shift)

        if not all(math.isfinite(x) for x in (tof, signal, doppler)):
            raise RuntimeError(
                f"Nonfinite measurement: {scenario} "
                f"{sensor} frame={frame}"
            )

        distance = C * tof / 2.0

        if tof <= 0:
            zero_tof += 1

        elif distance <= MIN_RANGE_M:
            near_zero += 1

        else:
            # Same candidate definition as the Task 24
            # full-measurement extractor.
            candidate += 1

            if signal > 0:
                positive_signal += 1

    return {
        "Scenario": scenario,
        "Recording": filename,
        "Frame": frame,
        "Timestamp_ns": timestamp,
        "Sensor": sensor,
        "RawReflections": raw,
        "CandidateReturns": candidate,
        "PositiveSignalCandidates": positive_signal,
        "ZeroTOF": zero_tof,
        "NearZeroReturns": near_zero,
        "CandidatePct": round(
            100 * candidate / raw, 4
        ) if raw else 0,
        "PositiveSignalPct": round(
            100 * positive_signal / raw, 4
        ) if raw else 0,
    }


def main():
    if OUT.exists():
        raise RuntimeError(f"Output already exists: {OUT}")

    temporary = OUT.with_name(OUT.name + ".partial")

    if temporary.exists():
        raise RuntimeError(f"Partial output exists: {temporary}")

    totals = {}

    try:
        with temporary.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

            for scenario in SCENARIOS:
                files = sorted(
                    (RAW / scenario).glob("*_sv_*.osi")
                )

                if len(files) != 1:
                    raise RuntimeError(
                        f"{scenario}: expected one SV file, "
                        f"found {len(files)}"
                    )

                source = files[0]
                rows = []

                with source.open("rb") as stream:
                    for frame in range(MAX_FRAMES):
                        header = stream.read(4)

                        if not header:
                            break

                        if len(header) != 4:
                            raise RuntimeError("Truncated OSI header")

                        size = struct.unpack("<I", header)[0]

                        if not 0 < size <= 100_000_000:
                            raise RuntimeError(
                                f"Invalid OSI frame size: {size}"
                            )

                        payload = stream.read(size)

                        if len(payload) != size:
                            raise RuntimeError(
                                f"Truncated OSI frame {frame}"
                            )

                        sv = osi_sensorview_pb2.SensorView()
                        sv.ParseFromString(payload)

                        timestamp = (
                            int(sv.timestamp.seconds) * 1_000_000_000
                            + int(sv.timestamp.nanos)
                        )

                        for sensor, views in [
                            ("LiDAR", sv.lidar_sensor_view),
                            ("Radar", sv.radar_sensor_view),
                        ]:
                            if len(views) != 1:
                                raise RuntimeError(
                                    f"{scenario} frame {frame}: "
                                    f"expected one {sensor} view"
                                )

                            result = analyze_sensor(
                                scenario, source.name, frame,
                                timestamp, sensor, views[0]
                            )

                            writer.writerow(result)
                            rows.append(result)

                frames = len(rows) // 2

                if frames == 0:
                    raise RuntimeError(
                        f"No frames decoded for {scenario}"
                    )

                totals[scenario] = (frames, rows)

        temporary.rename(OUT)

    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    print("\n=== TASK 28.3A PILOT RESULTS ===")

    for scenario, (frames, rows) in totals.items():
        print(f"\nScenario: {scenario}")
        print(f"Frames: {frames}")

        for sensor in ("LiDAR", "Radar"):
            selected = [
                r for r in rows if r["Sensor"] == sensor
            ]

            mean_candidates = sum(
                r["CandidateReturns"] for r in selected
            ) / len(selected)

            mean_positive = sum(
                r["PositiveSignalCandidates"]
                for r in selected
            ) / len(selected)

            mean_raw = sum(
                r["RawReflections"] for r in selected
            ) / len(selected)

            print(
                f"{sensor}: raw/frame={mean_raw:.2f}, "
                f"candidates/frame={mean_candidates:.2f}, "
                f"positive-signal/frame={mean_positive:.2f}"
            )

    print(f"\nCSV: {OUT}")
    print("STATUS: TASK 28.3A PILOT SUCCESS")


if __name__ == "__main__":
    main()
