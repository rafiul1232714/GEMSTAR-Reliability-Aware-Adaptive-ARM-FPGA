import csv
import math
import statistics
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
OUT = (
    ROOT / "tests" / "Task_28_Final_Research"
    / "02_CSV_Data" / "task28_3B2_signal_strength_diagnostic.csv"
)

C = 299792458.0
MIN_RANGE_M = 0.01

SCENARIOS = {
    "baseline_clear": [0, 1, 2, 100, 350, 690, 704],
    "fog_postfix_validation": [0, 1, 2, 100, 350, 690, 704],
}

FIELDS = [
    "Scenario", "Recording", "Frame", "Timestamp_ns",
    "TotalReflections", "RangeCandidates",
    "SignalNegative", "SignalZero", "SignalPositive",
    "NonCandidateReflections", "SignalMin",
    "SignalMedian", "SignalMax",
    "SignalP05", "SignalP95", "PositivePct",
    "NonpositivePct", "ZeroSignalWithPositiveTOF",
    "NegativeSignalWithPositiveTOF"
]


def percentile(values, fraction):
    if not values:
        return float("nan")

    values = sorted(values)
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)

    return (
        values[lower]
        + (values[upper] - values[lower]) * (position - lower)
    )


def analyze(scenario, recording, frame, sv):
    if len(sv.lidar_sensor_view) != 1:
        raise RuntimeError(
            f"{scenario}, frame {frame}: expected one LiDAR view"
        )

    reflections = sv.lidar_sensor_view[0].reflection
    signals = []

    zero = negative = positive = 0
    zero_tof_positive = negative_tof_positive = 0
    non_candidate = 0

    for reflection in reflections:
        tof = float(reflection.time_of_flight)
        signal = float(reflection.signal_strength)
        doppler = float(reflection.doppler_shift)

        if not all(map(math.isfinite, (tof, signal, doppler))):
            raise RuntimeError(
                f"Nonfinite LiDAR value at frame {frame}"
            )

        distance = C * tof / 2.0

        if tof <= 0 or distance <= MIN_RANGE_M:
            non_candidate += 1
            continue

        signals.append(signal)

        if signal < 0:
            negative += 1
            negative_tof_positive += 1
        elif signal == 0:
            zero += 1
            zero_tof_positive += 1
        else:
            positive += 1

    candidates = len(signals)

    if candidates != negative + zero + positive:
        raise RuntimeError("Signal classification mismatch")

    timestamp = (
        int(sv.timestamp.seconds) * 1_000_000_000
        + int(sv.timestamp.nanos)
    )

    return {
        "Scenario": scenario,
        "Recording": recording,
        "Frame": frame,
        "Timestamp_ns": timestamp,
        "TotalReflections": len(reflections),
        "RangeCandidates": candidates,
        "SignalNegative": negative,
        "SignalZero": zero,
        "SignalPositive": positive,
        "NonCandidateReflections": non_candidate,
        "SignalMin": min(signals) if signals else "",
        "SignalMedian": statistics.median(signals) if signals else "",
        "SignalMax": max(signals) if signals else "",
        "SignalP05": percentile(signals, 0.05),
        "SignalP95": percentile(signals, 0.95),
        "PositivePct": round(
            100 * positive / candidates, 3
        ) if candidates else 0,
        "NonpositivePct": round(
            100 * (negative + zero) / candidates, 3
        ) if candidates else 0,
        "ZeroSignalWithPositiveTOF": zero_tof_positive,
        "NegativeSignalWithPositiveTOF": negative_tof_positive,
    }


def process(scenario, selected):
    sources = sorted((RAW / scenario).glob("*_sv_*.osi"))

    if len(sources) != 1:
        raise RuntimeError(
            f"{scenario}: expected one SV recording"
        )

    source = sources[0]
    requested = set(selected)
    found = set()
    results = []

    with source.open("rb") as stream:
        frame = 0

        while requested - found:
            header = stream.read(4)

            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Truncated OSI header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid OSI payload size")

            if frame not in requested:
                stream.seek(size, 1)
                frame += 1
                continue

            payload = stream.read(size)

            if len(payload) != size:
                raise RuntimeError("Truncated OSI payload")

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            results.append(
                analyze(scenario, source.name, frame, sv)
            )

            found.add(frame)
            frame += 1

    if found != requested:
        raise RuntimeError(
            f"{scenario}: missing frames {sorted(requested - found)}"
        )

    return results


def main():
    if OUT.exists():
        raise RuntimeError("Diagnostic CSV already exists")

    temporary = OUT.with_name(OUT.name + ".partial")

    if temporary.exists():
        raise RuntimeError("Partial output already exists")

    rows = []

    for scenario, frames in SCENARIOS.items():
        print(f"Inspecting {scenario}...", flush=True)
        rows.extend(process(scenario, frames))

    try:
        with temporary.open(
            "x", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        temporary.rename(OUT)

    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    print("\n=== TASK 28.3B.2 RESULTS ===")

    for row in rows:
        print(
            f"{row['Scenario']} | frame={row['Frame']:3d}"
            f" | candidates={row['RangeCandidates']:4d}"
            f" | negative={row['SignalNegative']:4d}"
            f" | zero={row['SignalZero']:4d}"
            f" | positive={row['SignalPositive']:4d}"
            f" | positive%={row['PositivePct']:6.2f}"
            f" | median={row['SignalMedian']}"
        )

    print(f"\nCSV: {OUT}")
    print("STATUS: TASK 28.3B.2 SUCCESS")


if __name__ == "__main__":
    main()
