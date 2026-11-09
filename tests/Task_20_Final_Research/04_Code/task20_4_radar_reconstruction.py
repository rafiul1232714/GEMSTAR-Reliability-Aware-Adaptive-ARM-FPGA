import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"
FINDINGS = BASE / "06_Research_Findings"

SOURCE = DATA / "task20_2_radar_reflection_samples.csv"

# Constants verified in GEMSTAR SimpleRadar.cpp / .h
C_GEMSTAR = 299705543.0
RADAR_FREQUENCY_HZ = 77000000000.0

if not SOURCE.is_file():
    raise FileNotFoundError(
        "Task 20.2 CSV missing: " + str(SOURCE)
    )

def median_or_none(values):
    return statistics.median(values) if values else None

def fmt(value):
    return "N/A" if value is None else f"{value:.6f}"

print("\n=== TASK 20.4 RADAR RECONSTRUCTION ===")

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    raw_rows = list(csv.DictReader(f))

results = []
groups = defaultdict(list)
rejected = defaultdict(int)

for row in raw_rows:
    scenario = row["Recording"]

    if row["CandidateReturn"] != "1":
        rejected[scenario] += 1
        continue

    tof = float(row["TimeOfFlightRaw"])
    doppler = float(row["DopplerShiftRaw"])
    azimuth = float(row["AzimuthRad"])
    elevation = float(row["ElevationRad"])
    strength = float(row["SignalStrength"])

    if not all(math.isfinite(v) for v in
               (tof, doppler, azimuth, elevation, strength)):
        rejected[scenario] += 1
        continue

    # Reverse GEMSTAR's distance / TOF equation.
    distance = tof * C_GEMSTAR / 2.0

    # Reverse GEMSTAR's Doppler equation.
    radial_velocity = (
        doppler * C_GEMSTAR /
        (2.0 * RADAR_FREQUENCY_HZ)
    )

    # Provisional local spherical-coordinate mapping.
    # Axis convention still requires source-code validation.
    x = distance * math.cos(elevation) * math.cos(azimuth)
    y = distance * math.cos(elevation) * math.sin(azimuth)
    z = distance * math.sin(elevation)

    residual = abs(
        math.sqrt(x*x + y*y + z*z) - distance
    )

    result = {
        "Recording": scenario,
        "FrameIndex": row["FrameIndex"],
        "RadarIndex": row["RadarIndex"],
        "ReflectionIndex": row["ReflectionIndex"],
        "DistanceM": distance,
        "RadialVelocityMps": radial_velocity,
        "AzimuthRad": azimuth,
        "ElevationRad": elevation,
        "LocalX": x,
        "LocalY": y,
        "LocalZ": z,
        "SignalStrength": strength,
        "ReconstructionResidualM": residual,
        "CoordinateConventionVerified": False,
        "GroundTruthValidated": False,
    }

    results.append(result)
    groups[scenario].append(result)

if not results:
    raise RuntimeError("No candidate radar returns found.")

def save_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

output = DATA / "task20_4_radar_reconstructed_returns.csv"
save_csv(output, results)

summary = []

for scenario in sorted(set(r["Recording"] for r in raw_rows)):
    group = groups[scenario]

    distances = [r["DistanceM"] for r in group]
    velocities = [r["RadialVelocityMps"] for r in group]
    residuals = [r["ReconstructionResidualM"] for r in group]

    item = {
        "Recording": scenario,
        "ReconstructedReturns": len(group),
        "RejectedEntries": rejected[scenario],
        "MedianDistanceM": median_or_none(distances),
        "MedianRadialVelocityMps": median_or_none(velocities),
        "MaxReconstructionResidualM": (
            max(residuals) if residuals else None
        ),
    }
    summary.append(item)

    print(
        f"{scenario:30s} "
        f"| Returns={len(group):5d} "
        f"| Range={fmt(item['MedianDistanceM'])} m "
        f"| Velocity={fmt(item['MedianRadialVelocityMps'])} m/s"
    )

summary_file = DATA / "task20_4_radar_reconstruction_summary.csv"
save_csv(summary_file, summary)

# Plot first valid frame from baseline_clear
plot_group = groups.get("baseline_clear", [])

if plot_group:
    frame_id = min(int(r["FrameIndex"]) for r in plot_group)

    points = [
        r for r in plot_group
        if int(r["FrameIndex"]) == frame_id
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    sc = axes[0].scatter(
        [r["LocalX"] for r in points],
        [r["LocalY"] for r in points],
        c=[r["DistanceM"] for r in points],
        s=35
    )

    axes[0].scatter([0], [0], marker="x", s=100)
    axes[0].set_title("Provisional radar-local reflections")
    axes[0].set_xlabel("Local X (m)")
    axes[0].set_ylabel("Local Y (m)")
    axes[0].axis("equal")
    axes[0].grid(alpha=0.3)
    fig.colorbar(sc, ax=axes[0], label="Range (m)")

    axes[1].scatter(
        [r["DistanceM"] for r in points],
        [r["RadialVelocityMps"] for r in points],
        s=35
    )

    axes[1].set_title("Range-Doppler scatter")
    axes[1].set_xlabel("Range (m)")
    axes[1].set_ylabel("Radial velocity (m/s)")
    axes[1].grid(alpha=0.3)

    fig.suptitle(
        "GEMSTAR Radar Reconstruction - "
        "Coordinate convention unverified"
    )
    fig.tight_layout()

    graph = GRAPHS / "task20_4_radar_reconstruction.png"
    fig.savefig(graph, dpi=180, bbox_inches="tight")
    plt.close(fig)
else:
    graph = None

report = {
    "Task": "20.4",
    "InputRows": len(raw_rows),
    "ReconstructedReturns": len(results),
    "SourceLightSpeedMps": C_GEMSTAR,
    "SourceFrequencyHz": RADAR_FREQUENCY_HZ,
    "MaximumSphericalResidualM": max(
        r["ReconstructionResidualM"] for r in results
    ),
    "CoordinateConventionVerified": False,
    "GroundTruthAccuracyValidated": False,
    "EnergyMeasured": False,
    "OutputCSV": str(output),
    "Graph": str(graph) if graph else None,
}

report_file = FINDINGS / "task20_4_validation.json"
report_file.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.4 COMPLETE ===")
print("Input reflections:", len(raw_rows))
print("Reconstructed returns:", len(results))
print("Maximum spherical residual (m):",
      report["MaximumSphericalResidualM"])
print("Results CSV saved:", output.is_file())
print("Summary CSV saved:", summary_file.is_file())
print("Graph saved:",
      graph is not None and graph.is_file())
print("Validation JSON saved:", report_file.is_file())
print("Script saved:", Path(__file__).is_file())

print("\nNOTE:")
print("Coordinate axes and physical detection accuracy")
print("are not yet independently validated.")
print("No FPGA energy has been measured.")
