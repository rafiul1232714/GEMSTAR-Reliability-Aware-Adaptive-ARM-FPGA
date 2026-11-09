import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"
PROCESSED = TASK / "08_Processed_Data" / "Radar_Measurements"

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS, PROCESSED):
    folder.mkdir(parents=True, exist_ok=True)

C = 299792458.0
FRAMES = {0, 1, 25, 99}
RADIAL_SPEED_FLAG_MPS = 100.0

def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as f:
    manifest = list(csv.DictReader(f))

measurements = []
summaries = []

print("\n=== TASK 23.5C-1 RADAR RECONSTRUCTION ===")

for entry in manifest:
    pair = int(entry["PairID"])
    path = Path(entry["SensorViewPath"])

    found_frames = set()

    for frame, sv, _ in iter_osi_messages(
        path, SensorView, 100
    ):
        if frame not in FRAMES:
            continue

        found_frames.add(frame)

        if len(sv.radar_sensor_view) != 1:
            raise RuntimeError(
                f"Pair {pair}, frame {frame}: "
                "expected one Radar sensor view"
            )

        radar = sv.radar_sensor_view[0]
        cfg = radar.view_configuration

        frequency = float(cfg.emitter_frequency)
        nx = int(cfg.number_of_rays_horizontal)
        ny = int(cfg.number_of_rays_vertical)

        if frequency <= 0 or not math.isfinite(frequency):
            raise RuntimeError("Invalid emitter frequency")

        if nx * ny != len(radar.reflection):
            raise RuntimeError(
                f"Ray-grid mismatch: pair {pair}, frame {frame}"
            )

        positive_ranges = []
        equivalent_speeds = []
        positive_count = 0
        flagged_speed_count = 0

        for index, reflection in enumerate(radar.reflection):
            tof = float(reflection.time_of_flight)
            strength = float(reflection.signal_strength)
            doppler = float(reflection.doppler_shift)

            azimuth = float(reflection.source_horizontal_angle)
            elevation = float(reflection.source_vertical_angle)

            positive = (
                math.isfinite(tof) and tof > 0
                and math.isfinite(strength) and strength > 0
            )

            range_m = None
            radial_mps = None
            flagged_speed = False

            if positive:
                if not all(math.isfinite(v) for v in (
                    doppler, azimuth, elevation
                )):
                    raise RuntimeError(
                        f"Nonfinite Radar field: "
                        f"pair {pair}, frame {frame}, ray {index}"
                    )

                range_m = C * tof / 2.0
                radial_mps = doppler * C / (2.0 * frequency)

                positive_ranges.append(range_m)
                equivalent_speeds.append(radial_mps)
                positive_count += 1

                flagged_speed = (
                    abs(radial_mps) > RADIAL_SPEED_FLAG_MPS
                )
                flagged_speed_count += int(flagged_speed)

            measurements.append({
                "PairID": pair,
                "Frame": frame,
                "RayIndex": index,
                "HorizontalIndex": index % nx,
                "VerticalIndex": index // nx,
                "TimeOfFlightS": tof,
                "SignalStrength": strength,
                "DopplerShiftHz": doppler,
                "HorizontalAngleRad": azimuth,
                "VerticalAngleRad": elevation,
                "PositiveReturn": positive,
                "RangeM": range_m,
                "DopplerEquivalentRadialVelocityMps": radial_mps,
                "SpeedAbove100Mps": flagged_speed,
            })

        summary = {
            "PairID": pair,
            "Frame": frame,
            "TotalSlots": len(radar.reflection),
            "PositiveReturns": positive_count,
            "EmitterFrequencyHz": frequency,
            "MountX": float(cfg.mounting_position.position.x),
            "MountY": float(cfg.mounting_position.position.y),
            "MountZ": float(cfg.mounting_position.position.z),
            "MedianRangeM": (
                float(np.median(positive_ranges))
                if positive_ranges else None
            ),
            "MaximumRangeM": (
                float(np.max(positive_ranges))
                if positive_ranges else None
            ),
            "MedianEquivalentRadialVelocityMps": (
                float(np.median(equivalent_speeds))
                if equivalent_speeds else None
            ),
            "MaximumAbsEquivalentRadialVelocityMps": (
                float(np.max(np.abs(equivalent_speeds)))
                if equivalent_speeds else None
            ),
            "SpeedAbove100MpsCount": flagged_speed_count,
        }

        summaries.append(summary)

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Positive={positive_count:3d} | "
            f"MedianRange={summary['MedianRangeM']} | "
            f"MedianRadialMps="
            f"{summary['MedianEquivalentRadialVelocityMps']} | "
            f"SpeedFlags={flagged_speed_count}"
        )

    if found_frames != FRAMES:
        raise RuntimeError(
            f"Pair {pair}: expected frames {sorted(FRAMES)}, "
            f"found {sorted(found_frames)}"
        )

measurement_path = CSV_DIR / (
    "task23_05c1_radar_measurements.csv"
)
summary_path = CSV_DIR / (
    "task23_05c1_radar_frame_summary.csv"
)

write_csv(
    measurement_path, measurements, list(measurements[0])
)
write_csv(
    summary_path, summaries, list(summaries[0])
)

# Preserve machine-readable numeric arrays for later processing.
np.savez_compressed(
    PROCESSED / "task23_05c1_radar_sampled_measurements.npz",
    pair=np.array([r["PairID"] for r in measurements]),
    frame=np.array([r["Frame"] for r in measurements]),
    ray_index=np.array([r["RayIndex"] for r in measurements]),
    valid=np.array([r["PositiveReturn"] for r in measurements]),
    range_m=np.array([
        np.nan if r["RangeM"] is None else r["RangeM"]
        for r in measurements
    ]),
    radial_velocity_mps=np.array([
        np.nan if r["DopplerEquivalentRadialVelocityMps"] is None
        else r["DopplerEquivalentRadialVelocityMps"]
        for r in measurements
    ]),
)

# Graph 1: positive returns by frame.
fig, ax = plt.subplots(figsize=(9, 5))

for pair in sorted(set(r["PairID"] for r in summaries)):
    sample = [
        r for r in summaries if r["PairID"] == pair
    ]
    ax.plot(
        [r["Frame"] for r in sample],
        [r["PositiveReturns"] for r in sample],
        marker="o", label=f"Pair {pair}"
    )

ax.set_title("Radar positive returns by sampled frame")
ax.set_xlabel("Frame")
ax.set_ylabel("Positive TOF and signal-strength returns")
ax.legend()
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(
    GRAPH_DIR / "task23_05c1_radar_positive_returns.png",
    dpi=180
)
plt.close(fig)

# Graph 2: range and Doppler-equivalent velocity distributions.
valid = [r for r in measurements if r["PositiveReturn"]]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(
    [r["RangeM"] for r in valid],
    bins=40
)
axes[0].set_title("Candidate Radar range")
axes[0].set_xlabel("Range (m)")
axes[0].set_ylabel("Return count")

axes[1].hist(
    [
        r["DopplerEquivalentRadialVelocityMps"]
        for r in valid
    ],
    bins=40
)
axes[1].set_title("Doppler-equivalent radial velocity")
axes[1].set_xlabel("Calculated radial velocity (m/s)")
axes[1].set_ylabel("Return count")

for ax in axes:
    ax.grid(alpha=0.2)

fig.tight_layout()
fig.savefig(
    GRAPH_DIR / "task23_05c1_radar_range_doppler.png",
    dpi=180
)
plt.close(fig)

total_positive = sum(
    r["PositiveReturns"] for r in summaries
)
total_flags = sum(
    r["SpeedAbove100MpsCount"] for r in summaries
)

findings_path = FINDINGS / (
    "task23_05c1_radar_reconstruction_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.5C-1",
        "FramesAnalyzed": len(summaries),
        "ReflectionSlotsAnalyzed": len(measurements),
        "PositiveReturns": total_positive,
        "HighEquivalentSpeedFlags": total_flags,
        "HighSpeedThresholdMps": RADIAL_SPEED_FLAG_MPS,
        "Equations": {
            "RangeM": "299792458 * time_of_flight / 2",
            "RadialMps": (
                "doppler_shift * 299792458 "
                "/ (2 * emitter_frequency)"
            ),
        },
        "ScientificStatus": "SOURCE_EQUATION_RECONSTRUCTION",
        "Limitations": [
            "Positive returns are not verified detections",
            "Doppler-equivalent velocity may contain simulator artifacts",
            "Threshold above 100 m/s is diagnostic, not a validity rule",
            "No 3D Radar points calculated in this subtask",
            "No independent target GroundTruth velocity validation",
            "Pair 4 has a different mounting configuration",
            "Frame zero analyzed separately from steady-state data",
            "No hardware energy or latency measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5C-1 FINAL VERIFICATION ===")
print("Radar entries analyzed:", len(summaries))
print("Total reflection slots:", len(measurements))
print("Positive returns:", total_positive)
print("High equivalent-speed flags:", total_flags)
print("Measurement CSV:", measurement_path.is_file())
print("Summary CSV:", summary_path.is_file())
print("NPZ file:", (
    PROCESSED / "task23_05c1_radar_sampled_measurements.npz"
).is_file())
print("Research JSON:", findings_path.is_file())
print("Graphs:", len(list(
    GRAPH_DIR.glob("task23_05c1_*.png")
)))

if len(summaries) != 16 or len(measurements) != 1600:
    raise RuntimeError("Unexpected Radar sample count")

print("\n=== TASK 23.5C-1 COMPLETE ===")
