import csv
import json
import math
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

INPUT = (
    TASK / "02_CSV_Data" /
    "task23_05c1_radar_measurements.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

if not INPUT.is_file():
    raise FileNotFoundError(INPUT)

with INPUT.open(
    newline="", encoding="utf-8-sig"
) as handle:
    measurements = list(csv.DictReader(handle))

def is_positive(row):
    return row["PositiveReturn"].lower() == "true"

def numerical_values(rows, column):
    return np.array([
        float(row[column])
        for row in rows
        if row[column] not in ("", "None")
    ], dtype=float)

def statistics(values):
    if not len(values):
        return {
            "Median": None,
            "P95": None,
            "Maximum": None
        }
    return {
        "Median": float(np.median(values)),
        "P95": float(np.percentile(values, 95)),
        "Maximum": float(np.max(values))
    }

print("\n=== TASK 23.5C-2 RADAR STARTUP AUDIT ===")

results = []
all_valid = 0
all_high_speed = 0

for pair in (1, 2, 3, 4):
    for frame in (0, 1, 25, 99):
        rows = [
            r for r in measurements
            if int(r["PairID"]) == pair
            and int(r["Frame"]) == frame
        ]

        if len(rows) != 100:
            raise RuntimeError(
                f"Expected 100 slots: pair {pair}, "
                f"frame {frame}; got {len(rows)}"
            )

        valid_rows = [r for r in rows if is_positive(r)]

        ranges = numerical_values(
            valid_rows, "RangeM"
        )

        velocities = numerical_values(
            valid_rows,
            "DopplerEquivalentRadialVelocityMps"
        )

        if not (
            len(ranges) == len(velocities)
            == len(valid_rows)
        ):
            raise RuntimeError(
                "Radar measurement count mismatch"
            )

        if (
            not np.isfinite(ranges).all()
            or not np.isfinite(velocities).all()
        ):
            raise RuntimeError(
                "Nonfinite reconstructed Radar values"
            )

        high_speed = int(np.count_nonzero(
            np.abs(velocities) > 100.0
        ))

        below_5cm = int(np.count_nonzero(
            ranges < 0.05
        ))

        if frame in (0, 1):
            category = "STARTUP_DIAGNOSTIC"
        else:
            category = "STEADY_STATE_CANDIDATE"

        range_stats = statistics(ranges)
        velocity_stats = statistics(np.abs(velocities))

        results.append({
            "PairID": pair,
            "Frame": frame,
            "Category": category,
            "RadarSlots": len(rows),
            "PositiveReturns": len(valid_rows),
            "RangeBelow005m": below_5cm,
            "VelocityAbove100mps": high_speed,
            "MedianRangeM": range_stats["Median"],
            "P95RangeM": range_stats["P95"],
            "MedianAbsVelocityMps": velocity_stats["Median"],
            "P95AbsVelocityMps": velocity_stats["P95"],
            "MaxAbsVelocityMps": velocity_stats["Maximum"],
        })

        all_valid += len(valid_rows)
        all_high_speed += high_speed

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Positive={len(valid_rows):3d} | "
            f"RangeBelow5cm={below_5cm:3d} | "
            f"SpeedAbove100mps={high_speed:3d} | "
            f"Category={category}"
        )

csv_path = CSV_DIR / (
    "task23_05c2_radar_startup_quality_audit.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

# Plot startup anomalies separately.
labels = [
    f"P{r['PairID']}/F{r['Frame']}"
    for r in results
]

indices = np.arange(len(results))

fig, axes = plt.subplots(
    2, 1, figsize=(12, 8), sharex=True
)

axes[0].bar(
    indices,
    [r["RangeBelow005m"] for r in results]
)
axes[0].set_ylabel("Returns with range < 0.05 m")
axes[0].set_title(
    "Radar startup anomaly audit"
)

axes[1].bar(
    indices,
    [r["VelocityAbove100mps"] for r in results]
)
axes[1].set_ylabel(
    "Returns with |radial speed| > 100 m/s"
)
axes[1].set_xticks(indices)
axes[1].set_xticklabels(
    labels, rotation=60, ha="right"
)

for ax in axes:
    ax.grid(axis="y", alpha=0.2)

fig.tight_layout()

graph_path = GRAPH_DIR / (
    "task23_05c2_radar_startup_anomalies.png"
)

fig.savefig(graph_path, dpi=180)
plt.close(fig)

steady_positive = sum(
    r["PositiveReturns"]
    for r in results
    if r["Category"] == "STEADY_STATE_CANDIDATE"
)

findings = {
    "Task": "23.5C-2",
    "TotalMeasurements": len(measurements),
    "PositiveReturns": all_valid,
    "HighSpeedFlags": all_high_speed,
    "SteadyStateCandidatePositiveReturns": steady_positive,
    "FrameQualityPolicy": {
        "Frame0": (
            "Keep for startup analysis; exclude from "
            "steady-state benchmarking"
        ),
        "Frame1": (
            "Keep for Doppler initialization analysis; "
            "exclude from steady-state benchmarking"
        ),
        "Frames25And99": (
            "Provisional steady-state candidates, "
            "not independently validated detections"
        )
    },
    "SourceCodeHypothesis": (
        "SimpleRadar.cpp firstTick branch sets "
        "currentVelocity to zero without updating "
        "oldPosition; later velocity may be biased."
    ),
    "ScientificLimitations": [
        "A high Doppler-equivalent speed is not proof of an implementation bug",
        "Near-zero ranges require a separate scene-level explanation",
        "Only four sampled frames per recording were analyzed",
        "Steady-state candidates are not externally validated",
        "No performance or energy benefit claimed"
    ]
}

json_path = FINDINGS / (
    "task23_05c2_radar_startup_findings.json"
)

json_path.write_text(
    json.dumps(findings, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5C-2 FINAL VERIFICATION ===")
print("Frames audited:", len(results))
print("Positive returns:", all_valid)
print("High-speed flags:", all_high_speed)
print(
    "Steady-state candidate returns:",
    steady_positive
)
print("Quality CSV saved:", csv_path.is_file())
print("Graph saved:", graph_path.is_file())
print("Findings JSON saved:", json_path.is_file())

if len(results) != 16 or len(measurements) != 1600:
    raise RuntimeError("Unexpected Radar sample count")

if all_valid != 544 or all_high_speed != 103:
    raise RuntimeError(
        "Results do not reproduce Task 23.5C-1"
    )

print("\n=== TASK 23.5C-2 COMPLETE ===")
