import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPHS = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"
OUTPUT = TASK / "08_Processed_Data" / "Radar_3D_Source_Matched"

MEASUREMENTS = CSV_DIR / "task23_05c1_radar_measurements.csv"
SUMMARY = CSV_DIR / "task23_05c1_radar_frame_summary.csv"
CONFIG = FINDINGS / "task23_05a_radar_configuration_findings.json"

for folder in (CSV_DIR, GRAPHS, FINDINGS, OUTPUT):
    folder.mkdir(parents=True, exist_ok=True)

C = 299792458.0
FRAMES = (0, 1, 25, 99)
PAIRS = (1, 2, 3, 4)
ANGLE_TOL = 1e-5
DISTANCE_TOL = 1e-8


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def save_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def as_positive(row):
    return row["PositiveReturn"].strip().lower() == "true"


print("\n=== TASK 23.5C-3 RADAR 3D RECONSTRUCTION ===")

measurements = read_csv(MEASUREMENTS)
summaries = read_csv(SUMMARY)

if not CONFIG.is_file():
    raise FileNotFoundError(CONFIG)

config_data = json.loads(CONFIG.read_text(encoding="utf-8-sig"))

frame_config = {
    (int(r["PairID"]), int(r["Frame"])): r
    for r in config_data["Records"]
}

frame_summary = {
    (int(r["PairID"]), int(r["Frame"])): r
    for r in summaries
}

measurements_by_frame = defaultdict(list)

for row in measurements:
    key = (int(row["PairID"]), int(row["Frame"]))
    measurements_by_frame[key].append(row)

point_rows = []
validation_rows = []
point_cache = {}
total_points = 0

for pair in PAIRS:
    for frame in FRAMES:
        key = (pair, frame)

        if key not in frame_config or key not in frame_summary:
            raise RuntimeError(f"Missing configuration: {key}")

        rows = sorted(
            measurements_by_frame[key],
            key=lambda r: int(r["RayIndex"])
        )

        if len(rows) != 100:
            raise RuntimeError(
                f"Expected 100 Radar slots in {key}; got {len(rows)}"
            )

        if [int(r["RayIndex"]) for r in rows] != list(range(100)):
            raise RuntimeError(f"Incorrect ray ordering: {key}")

        config = frame_config[key]["ViewConfiguration"]
        mount = config["mounting_position"]

        translation = np.array([
            float(mount["position"]["x"]),
            float(mount["position"]["y"]),
            float(mount["position"]["z"]),
        ], dtype=np.float64)

        orientation = np.array([
            float(mount["orientation"]["roll"]),
            float(mount["orientation"]["pitch"]),
            float(mount["orientation"]["yaw"]),
        ], dtype=np.float64)

        if not np.allclose(orientation, 0, atol=1e-9, rtol=0):
            raise RuntimeError(
                f"Nonzero Radar mount rotation in {key}; "
                "full rotation required."
            )

        nx = int(config["number_of_rays_horizontal"])
        ny = int(config["number_of_rays_vertical"])
        hfov = float(config["field_of_view_horizontal"])
        vfov = float(config["field_of_view_vertical"])

        if nx * ny != len(rows):
            raise RuntimeError(f"Radar scan dimensions mismatch: {key}")

        frequency = float(config["emitter_frequency"])

        if frequency <= 0 or not math.isfinite(frequency):
            raise RuntimeError(f"Invalid Radar frequency: {key}")

        ray_indices = np.array(
            [int(r["RayIndex"]) for r in rows],
            dtype=np.int32
        )

        azimuth_all = np.array(
            [float(r["HorizontalAngleRad"]) for r in rows],
            dtype=np.float64
        )

        elevation_all = np.array(
            [float(r["VerticalAngleRad"]) for r in rows],
            dtype=np.float64
        )

        # Verify indexing and reported angles independently
        # against the configured scan boundaries.
        az_expected = np.linspace(-hfov / 2, hfov / 2, nx)
        el_expected = np.linspace(-vfov / 2, vfov / 2, ny)

        expected_az_all = np.tile(az_expected, ny)
        expected_el_all = np.repeat(el_expected, nx)

        max_angle_error = float(max(
            np.max(np.abs(azimuth_all - expected_az_all)),
            np.max(np.abs(elevation_all - expected_el_all))
        ))

        if max_angle_error > ANGLE_TOL:
            raise RuntimeError(
                f"Recorded angle grid differs from source "
                f"configuration at {key}: {max_angle_error}"
            )

        valid_mask = np.array(
            [as_positive(r) for r in rows],
            dtype=bool
        )

        positive_rows = [
            r for r, valid in zip(rows, valid_mask) if valid
        ]

        valid_indices = ray_indices[valid_mask]

        ranges = np.array([
            float(r["RangeM"])
            for r in positive_rows
        ], dtype=np.float64)

        radial_velocity = np.array([
            float(r["DopplerEquivalentRadialVelocityMps"])
            for r in positive_rows
        ], dtype=np.float64)

        strength = np.array([
            float(r["SignalStrength"])
            for r in positive_rows
        ], dtype=np.float64)

        tof = np.array([
            float(r["TimeOfFlightS"])
            for r in positive_rows
        ], dtype=np.float64)

        doppler_hz = np.array([
            float(r["DopplerShiftHz"])
            for r in positive_rows
        ], dtype=np.float64)

        az = azimuth_all[valid_mask]
        el = elevation_all[valid_mask]

        if not all(np.isfinite(v).all() for v in (
            ranges, radial_velocity, strength, az, el
        )):
            raise RuntimeError(f"Nonfinite measurement: {key}")

        # Reconstruct the Unreal-local ray directions
        # from the angles recorded in the OSI message.
        x = ranges * np.cos(el) * np.cos(az)
        y_ue = ranges * np.cos(el) * np.sin(az)
        z = ranges * np.sin(el)

        sensor_ue = np.column_stack((x, y_ue, z))

        # GEMSTAR ToOSI.cpp:
        # x is preserved, y is negated, z is preserved.
        reflect_y = np.array([1.0, -1.0, 1.0])
        sensor_osi = sensor_ue * reflect_y

        # Zero mounting rotation verified above.
        vehicle_osi = sensor_osi + translation

        # Internal numerical checks.
        if len(ranges):
            reconstructed_range = np.linalg.norm(
                sensor_ue, axis=1
            )

            range_error = float(np.max(np.abs(
                reconstructed_range - ranges
            )))

            mount_error = float(np.max(np.abs(
                (vehicle_osi - translation) - sensor_osi
            )))

            tof_error = float(np.max(np.abs(
                ranges - C * tof / 2.0
            )))

            velocity_error = float(np.max(np.abs(
                radial_velocity -
                doppler_hz * C / (2.0 * frequency)
            )))
        else:
            range_error = 0.0
            mount_error = 0.0
            tof_error = 0.0
            velocity_error = 0.0

        passed = bool(
            range_error < DISTANCE_TOL
            and mount_error < DISTANCE_TOL
            and tof_error < DISTANCE_TOL
            and velocity_error < DISTANCE_TOL
        )

        if not passed:
            raise RuntimeError(
                f"Internal reconstruction check failed: {key}"
            )

        category = (
            "STARTUP_DIAGNOSTIC"
            if frame in (0, 1)
            else "STEADY_STATE_CANDIDATE"
        )

        npz_path = OUTPUT / (
            f"pair{pair}_frame{frame:03d}_radar_3d.npz"
        )

        np.savez_compressed(
            npz_path,
            valid_ray_indices=valid_indices,
            valid_mask=valid_mask,
            points_sensor_ue_m=sensor_ue,
            points_sensor_osi_m=sensor_osi,
            points_vehicle_osi_m=vehicle_osi,
            range_m=ranges,
            horizontal_angle_rad=az,
            vertical_angle_rad=el,
            signal_strength=strength,
            doppler_shift_hz=doppler_hz,
            doppler_equivalent_radial_velocity_mps=radial_velocity,
            mounting_position_osi_m=translation,
            mounting_orientation_rpy_rad=orientation,
            emitter_frequency_hz=np.array(frequency),
            quality_category=np.array(category),
        )

        point_cache[key] = vehicle_osi
        total_points += len(ranges)

        for i, ray in enumerate(valid_indices):
            point_rows.append({
                "PairID": pair,
                "Frame": frame,
                "QualityCategory": category,
                "RayIndex": int(ray),
                "HorizontalIndex": int(ray % nx),
                "VerticalIndex": int(ray // nx),
                "RangeM": float(ranges[i]),
                "AzimuthRad": float(az[i]),
                "ElevationRad": float(el[i]),
                "SensorOSI_X": float(sensor_osi[i, 0]),
                "SensorOSI_Y": float(sensor_osi[i, 1]),
                "SensorOSI_Z": float(sensor_osi[i, 2]),
                "VehicleOSI_X": float(vehicle_osi[i, 0]),
                "VehicleOSI_Y": float(vehicle_osi[i, 1]),
                "VehicleOSI_Z": float(vehicle_osi[i, 2]),
                "DopplerShiftHz": float(doppler_hz[i]),
                "EquivalentRadialVelocityMps": float(radial_velocity[i]),
                "SignalStrength": float(strength[i]),
            })

        validation_rows.append({
            "PairID": pair,
            "Frame": frame,
            "QualityCategory": category,
            "TotalSlots": len(rows),
            "ReconstructedPoints": len(ranges),
            "MountX": float(translation[0]),
            "MountY": float(translation[1]),
            "MountZ": float(translation[2]),
            "MaximumAngleGridErrorRad": max_angle_error,
            "MaximumRangeErrorM": range_error,
            "MaximumMountErrorM": mount_error,
            "MaximumTOFErrorM": tof_error,
            "MaximumVelocityErrorMps": velocity_error,
            "ValidationPass": passed,
        })

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"Points={len(ranges):3d} | "
            f"Category={category} | "
            f"RangeError={range_error:.3e} | "
            f"AngleError={max_angle_error:.3e} | "
            f"PASS={passed}"
        )


# Save the reconstructed positive-return measurements.
points_csv = CSV_DIR / "task23_05c3_radar_3d_points.csv"
summary_csv = CSV_DIR / "task23_05c3_radar_3d_validation.csv"

save_csv(points_csv, point_rows, list(point_rows[0]))
save_csv(summary_csv, validation_rows, list(validation_rows[0]))


# Graph 1: spatial distribution, Pair 1 Frame 25.
sample = point_cache[(1, 25)]
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

if len(sample):
    ax.scatter(
        sample[:, 0], sample[:, 1], sample[:, 2],
        s=20, alpha=0.8
    )

ax.set_xlabel("Vehicle OSI X (m)")
ax.set_ylabel("Vehicle OSI Y (m)")
ax.set_zlabel("Vehicle OSI Z (m)")
ax.set_title("Pair 1 / Frame 25 - Reconstructed Radar points")
fig.tight_layout()
fig.savefig(
    GRAPHS / "task23_05c3_radar_3d_pair1_frame25.png",
    dpi=180
)
plt.close(fig)


# Graph 2: XY projection across the first three pairs.
fig, ax = plt.subplots(figsize=(10, 7))

for pair in (1, 2, 3):
    pts = point_cache[(pair, 25)]
    if len(pts):
        ax.scatter(
            pts[:, 0], pts[:, 1],
            s=16, alpha=0.6,
            label=f"Pair {pair}"
        )

ax.set_xlabel("Vehicle OSI X (m)")
ax.set_ylabel("Vehicle OSI Y (m)")
ax.set_title("Frame 25 - Radar vehicle-coordinate comparison")
ax.set_aspect("equal", adjustable="box")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(
    GRAPHS / "task23_05c3_radar_xy_pair_comparison.png",
    dpi=180
)
plt.close(fig)


# Graph 3: positive Radar point counts.
fig, ax = plt.subplots(figsize=(9, 5))

for pair in PAIRS:
    subset = [
        r for r in validation_rows if r["PairID"] == pair
    ]
    ax.plot(
        [r["Frame"] for r in subset],
        [r["ReconstructedPoints"] for r in subset],
        marker="o",
        label=f"Pair {pair}"
    )

ax.set_xlabel("Sampled frame")
ax.set_ylabel("Reconstructed candidate points")
ax.set_title("Radar point availability by frame")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()
fig.savefig(
    GRAPHS / "task23_05c3_radar_point_counts.png",
    dpi=180
)
plt.close(fig)


startup_points = sum(
    r["ReconstructedPoints"]
    for r in validation_rows
    if r["QualityCategory"] == "STARTUP_DIAGNOSTIC"
)

steady_points = sum(
    r["ReconstructedPoints"]
    for r in validation_rows
    if r["QualityCategory"] == "STEADY_STATE_CANDIDATE"
)

findings_path = FINDINGS / (
    "task23_05c3_radar_3d_reconstruction_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.5C-3",
        "Status": "SOURCE_MATCHED_RADAR_3D_INTERNAL_VALIDATION",
        "TotalRadarPoints": total_points,
        "StartupDiagnosticPoints": startup_points,
        "SteadyStateCandidatePoints": steady_points,
        "FramesProcessed": len(validation_rows),
        "SourceEquations": {
            "Range": "c * time_of_flight / 2",
            "LocalX": "range*cos(elevation)*cos(azimuth)",
            "LocalY_UE": "range*cos(elevation)*sin(azimuth)",
            "LocalZ": "range*sin(elevation)",
            "OSIConversion": "x, -y, z",
            "VehicleCoordinates": (
                "OSI local points + recorded mounting translation"
            )
        },
        "Validation": {
            "AllNumericalChecksPassed": all(
                r["ValidationPass"] for r in validation_rows
            ),
            "Frames": validation_rows
        },
        "ScientificLimitations": [
            "Radar points represent simulator ray returns",
            "Not independently verified object detections",
            "Frames 0 and 1 remain startup diagnostics",
            "Frame 1 Doppler velocity anomalies remain unresolved",
            "Pair 4 has a different mounting configuration",
            "No Radar world-frame alignment performed here",
            "No independent GroundTruth geometric accuracy measurement",
            "No hardware latency or energy measurement"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5C-3 FINAL VERIFICATION ===")
print("Radar entries processed:", len(validation_rows))
print("Reconstructed positive points:", total_points)
print("Startup diagnostic points:", startup_points)
print("Steady-state candidate points:", steady_points)
print("All numerical checks passed:", all(
    r["ValidationPass"] for r in validation_rows
))
print("3D point CSV:", points_csv.is_file())
print("Validation CSV:", summary_csv.is_file())
print("Research JSON:", findings_path.is_file())
print("NPZ files:", len(list(OUTPUT.glob("*radar_3d.npz"))))
print("Graphs:", len(list(GRAPHS.glob("task23_05c3_*.png"))))

if len(validation_rows) != 16:
    raise RuntimeError("Expected 16 Radar frame entries")

if total_points != 544:
    raise RuntimeError(
        "Radar point count does not match Task 23.5C-1"
    )

if steady_points != 237:
    raise RuntimeError(
        "Steady-state count does not match Task 23.5C-2"
    )

print("\n=== TASK 23.5C-3 COMPLETE ===")
