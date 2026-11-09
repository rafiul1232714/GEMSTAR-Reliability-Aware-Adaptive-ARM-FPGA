import csv
import math
import statistics
import struct
from pathlib import Path
from collections import Counter

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"

BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

MAX_FRAMES = 100

# Speed of light in vacuum for a dimensional audit.
# This does not establish GEMSTAR's internal TOF units.
C = 299792458.0

def messages(path):
    with path.open("rb") as f:
        for index in range(MAX_FRAMES):
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete message header")

            size = struct.unpack("<I", header)[0]

            if not (0 < size < 100_000_000):
                raise ValueError(
                    f"Invalid message size: {size}"
                )

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Incomplete message body")

            msg = SensorView()
            msg.ParseFromString(payload)

            yield index, msg

def median_or_none(values):
    return (
        statistics.median(values)
        if values else None
    )

def fmt(value):
    if value is None:
        return "N/A"
    return f"{value:.6g}"

def write_csv(path, rows):
    if not rows:
        return

    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

def main():

    print("\n=== TASK 20.2 RADAR MEASUREMENT AUDIT ===")

    files = sorted(RAW.rglob("*_sv_*.osi"))

    frame_rows = []
    reflection_rows = []
    scenario_rows = []

    for path in files:
        scenario = path.parent.name

        print("\nRecording:", scenario)

        frame_count = 0
        total_reflections = 0
        positive_count = 0

        all_positive_tof = []
        all_positive_strength = []
        all_doppler = []

        positions = set()

        for frame_index, msg in messages(path):
            frame_count += 1

            for radar_index, radar in enumerate(
                msg.radar_sensor_view
            ):

                cfg = radar.view_configuration

                position = cfg.mounting_position.position

                mount = (
                    round(position.x, 6),
                    round(position.y, 6),
                    round(position.z, 6)
                )

                positions.add(mount)

                count = 0
                valid_numeric = 0
                positive_tof = 0
                positive_strength = 0
                candidate_returns = 0
                nonzero_doppler = 0

                frame_tof = []
                frame_range = []
                frame_strength = []

                for index, reflection in enumerate(
                    radar.reflection
                ):

                    count += 1
                    total_reflections += 1

                    tof = float(
                        reflection.time_of_flight
                    )
                    strength = float(
                        reflection.signal_strength
                    )
                    doppler = float(
                        reflection.doppler_shift
                    )
                    azimuth = float(
                        reflection.source_horizontal_angle
                    )
                    elevation = float(
                        reflection.source_vertical_angle
                    )

                    finite = all(math.isfinite(x) for x in (
                        tof, strength, doppler,
                        azimuth, elevation
                    ))

                    if finite:
                        valid_numeric += 1
                        all_doppler.append(doppler)

                    if finite and tof > 0:
                        positive_tof += 1

                    if finite and strength > 0:
                        positive_strength += 1

                    # A preliminary candidate for further
                    # investigation, NOT confirmed detection.
                    candidate = (
                        finite
                        and tof > 0
                        and strength > 0
                    )

                    range_if_seconds = (
                        C * tof / 2
                        if finite and tof > 0
                        else None
                    )

                    if candidate:
                        candidate_returns += 1
                        positive_count += 1
                        frame_tof.append(tof)
                        frame_strength.append(strength)
                        frame_range.append(
                            range_if_seconds
                        )
                        all_positive_tof.append(tof)
                        all_positive_strength.append(
                            strength
                        )

                    if finite and doppler != 0:
                        nonzero_doppler += 1

                    reflection_rows.append({
                        "Recording": scenario,
                        "File": path.name,
                        "FrameIndex": frame_index,
                        "RadarIndex": radar_index,
                        "ReflectionIndex": index,
                        "SignalStrength": strength,
                        "TimeOfFlightRaw": tof,
                        "DopplerShiftRaw": doppler,
                        "AzimuthRad": azimuth,
                        "ElevationRad": elevation,
                        "FiniteFields": int(finite),
                        "CandidateReturn": int(candidate),
                        "RangeIfTOFSecondsM":
                            range_if_seconds,
                        "MountX": mount[0],
                        "MountY": mount[1],
                        "MountZ": mount[2],
                    })

                frame_rows.append({
                    "Recording": scenario,
                    "FrameIndex": frame_index,
                    "RadarIndex": radar_index,
                    "Reflections": count,
                    "FiniteMeasurements": valid_numeric,
                    "PositiveTOF": positive_tof,
                    "PositiveStrength": positive_strength,
                    "CandidateReturns": candidate_returns,
                    "NonzeroDoppler": nonzero_doppler,
                    "MedianCandidateTOF":
                        median_or_none(frame_tof),
                    "MedianRangeIfTOFSecondsM":
                        median_or_none(frame_range),
                    "MedianCandidateStrength":
                        median_or_none(frame_strength),
                    "MountX": mount[0],
                    "MountY": mount[1],
                    "MountZ": mount[2],
                })

        scenario_candidate = [
            r for r in frame_rows
            if r["Recording"] == scenario
        ]

        median_tof = median_or_none(
            all_positive_tof
        )

        median_range = (
            C * median_tof / 2
            if median_tof is not None
            else None
        )

        nonzero_all_doppler = sum(
            math.isfinite(x) and x != 0
            for x in all_doppler
        )

        summary = {
            "Recording": scenario,
            "FramesChecked": frame_count,
            "RadarViewsChecked":
                len(scenario_candidate),
            "TotalReflections": total_reflections,
            "CandidateReturns": positive_count,
            "CandidatePercent": (
                100 * positive_count / total_reflections
                if total_reflections else 0
            ),
            "MedianCandidateTOF": median_tof,
            "MinCandidateTOF": (
                min(all_positive_tof)
                if all_positive_tof else None
            ),
            "MaxCandidateTOF": (
                max(all_positive_tof)
                if all_positive_tof else None
            ),
            "MedianRangeIfSecondsM": median_range,
            "NonzeroDopplerCount": nonzero_all_doppler,
            "MountingPositions": ";".join(
                str(p) for p in sorted(positions)
            ),
        }

        scenario_rows.append(summary)

        print("Frames checked:", frame_count)
        print("Reflections:", total_reflections)
        print("Candidate returns:", positive_count)
        print(
            "Candidate return %:",
            f"{summary['CandidatePercent']:.2f}"
        )
        print("Median raw TOF:", fmt(median_tof))
        print(
            "Median range if TOF is seconds (m):",
            fmt(median_range)
        )
        print(
            "Nonzero Doppler values:",
            nonzero_all_doppler
        )
        print(
            "Mounting positions:",
            summary["MountingPositions"]
        )

    frame_file = (
        DATA / "task20_2_radar_frame_statistics.csv"
    )

    reflection_file = (
        DATA / "task20_2_radar_reflection_samples.csv"
    )

    scenario_file = (
        DATA / "task20_2_radar_scenario_summary.csv"
    )

    write_csv(frame_file, frame_rows)
    write_csv(reflection_file, reflection_rows)
    write_csv(scenario_file, scenario_rows)

    print("\n=== TASK 20.2 COMPLETE ===")
    print("Recordings:", len(files))
    print("Frames:", sum(
        x["FramesChecked"] for x in scenario_rows
    ))
    print("Reflections inspected:", len(reflection_rows))
    print("Frame CSV:", frame_file.is_file())
    print("Reflection CSV:", reflection_file.is_file())
    print("Scenario CSV:", scenario_file.is_file())

    print("\nIMPORTANT:")
    print("CandidateReturn is only a numerical filter.")
    print("It is not a ground-truth radar detection.")
    print("Ranges assume TOF is in seconds.")
    print("We must verify GEMSTAR radar source units")
    print("before treating ranges as physical distances.")

if __name__ == "__main__":
    main()
