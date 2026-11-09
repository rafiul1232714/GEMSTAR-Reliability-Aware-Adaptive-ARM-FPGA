import csv
import math
from pathlib import Path
from collections import defaultdict
from statistics import median

import numpy as np

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

TRACK_ID = 2
C = 299792458.0
CARRIER_HZ = 77e9

LIDAR_STD_M = 0.60
RADAR_STD_MPS = 2.0  # Exploratory, NOT calibrated
PROCESS_ACCEL_STD_MPS2 = 1.0
RADAR_NIS_GATE = 9.0
MIN_NONZERO_RADAR_RETURNS = 2

RADAR_X_M = 2.0
RADAR_Y_M = 0.0

H_L = np.array([
    [1., 0., 0., 0.],
    [0., 1., 0., 0.]
])

I = np.eye(4)

def load(name):
    with (DIR / name).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

observations = [
    r for r in load("lidar_temporal_tracks_v1.csv")
    if int(r["track_id"]) == TRACK_ID
]

observations.sort(key=lambda r: float(r["time_s"]))

if len(observations) != 24:
    raise RuntimeError("Unexpected Track 2 observation count")

if len({
    int(r["frame"]) for r in observations
}) != len(observations):
    raise RuntimeError("Duplicate Track 2 frame")

radar_by_frame = defaultdict(list)

for r in load("radar_track_matches_v1.csv"):
    if int(r["track_id"]) != TRACK_ID:
        continue

    doppler = float(r["doppler_shift_raw"])

    if not math.isfinite(doppler):
        raise RuntimeError("Non-finite Doppler")

    if abs(doppler) <= 1e-9:
        continue

    frame = int(r["frame"])
    radar_by_frame[frame].append(
        (float(r["time_s"]), doppler)
    )

def lidar_covariance(point_count):
    n = int(point_count)

    if n <= 0:
        raise RuntimeError("Invalid LiDAR point count")

    factor = min(2.0, max(1.0, 12.0 / n))

    return np.eye(2) * (LIDAR_STD_M * factor)**2

def predict(x, P, dt):
    F = np.array([
        [1., 0., dt, 0.],
        [0., 1., 0., dt],
        [0., 0., 1., 0.],
        [0., 0., 0., 1.]
    ])

    q = PROCESS_ACCEL_STD_MPS2**2

    Q = q * np.array([
        [dt**4/4, 0., dt**3/2, 0.],
        [0., dt**4/4, 0., dt**3/2],
        [dt**3/2, 0., dt**2, 0.],
        [0., dt**3/2, 0., dt**2]
    ])

    return F @ x, F @ P @ F.T + Q

def update(x, P, H, innovation, R):
    S = H @ P @ H.T + R
    K = P @ H.T @ np.linalg.inv(S)

    x2 = x + K @ innovation

    # Joseph covariance form for numerical stability.
    A = I - K @ H
    P2 = A @ P @ A.T + K @ R @ K.T

    return x2, (P2 + P2.T) / 2

def radar_model(x):
    dx = x[0] - RADAR_X_M
    dy = x[1] - RADAR_Y_M
    radius = math.hypot(dx, dy)

    if radius < 0.1:
        raise RuntimeError("Track too close to Radar origin")

    ux = dx / radius
    uy = dy / radius

    predicted = ux*x[2] + uy*x[3]

    H = np.array([[
        (x[2] - predicted*ux) / radius,
        (x[3] - predicted*uy) / radius,
        ux,
        uy
    ]])

    return predicted, H

first = observations[0]

initial_x = np.array([
    float(first["x_m"]),
    float(first["y_m"]),
    0.,
    0.
])

initial_P = np.diag([1., 1., 4., 4.])

xl, Pl = initial_x.copy(), initial_P.copy()
xr, Pr = initial_x.copy(), initial_P.copy()

previous_time = None
results = []
accepted = 0
rejected = 0
insufficient = 0
no_nonzero = 0

for index, row in enumerate(observations):
    frame = int(row["frame"])
    t = float(row["time_s"])

    z = np.array([
        float(row["x_m"]),
        float(row["y_m"])
    ])

    R_L = lidar_covariance(row["point_count"])

    if index > 0:
        dt = t - previous_time

        if dt <= 0:
            raise RuntimeError("Non-increasing timestamps")

        xl, Pl = predict(xl, Pl, dt)
        xr, Pr = predict(xr, Pr, dt)

        xl, Pl = update(
            xl, Pl, H_L, z - H_L @ xl, R_L
        )
        xr, Pr = update(
            xr, Pr, H_L, z - H_L @ xr, R_L
        )

    previous_time = t

    values = radar_by_frame.get(frame, [])
    radar_status = "NOT_AVAILABLE"

    measured = float("nan")
    predicted = float("nan")
    nis = float("nan")
    innovation = float("nan")

    if values:
        if any(abs(rt - t) > 1e-4 for rt, _ in values):
            raise RuntimeError(
                f"Radar/LiDAR timestamp mismatch: {frame}"
            )

        speeds = [
            fd * C / (2 * CARRIER_HZ)
            for _, fd in values
        ]
        measured = float(median(speeds))

        if len(values) < MIN_NONZERO_RADAR_RETURNS:
            radar_status = "INSUFFICIENT_RETURNS"
            insufficient += 1
        else:
            predicted, H_R = radar_model(xr)
            innovation = measured - predicted

            R_R = np.array([[RADAR_STD_MPS**2]])
            S = float((H_R @ Pr @ H_R.T)[0, 0]
                      + R_R[0, 0])

            nis = innovation**2 / S

            if nis <= RADAR_NIS_GATE:
                xr, Pr = update(
                    xr, Pr, H_R,
                    np.array([innovation]), R_R
                )
                radar_status = "ACCEPTED"
                accepted += 1
            else:
                radar_status = "REJECTED_BY_NIS"
                rejected += 1
    else:
        no_nonzero += 1

    results.append({
        "frame": frame,
        "time_s": t,
        "lidar_x_m": z[0],
        "lidar_y_m": z[1],
        "lidar_cluster_points": int(row["point_count"]),
        "radar_nonzero_returns": len(values),
        "radar_status": radar_status,
        "radar_measured_mps": measured,
        "radar_predicted_mps": predicted,
        "radar_innovation_mps": innovation,
        "radar_nis": nis,
        "lidar_only_x_m": xl[0],
        "lidar_only_y_m": xl[1],
        "lidar_only_vx_mps": xl[2],
        "lidar_only_vy_mps": xl[3],
        "lidar_only_std_x_m": math.sqrt(Pl[0, 0]),
        "radar_ekf_x_m": xr[0],
        "radar_ekf_y_m": xr[1],
        "radar_ekf_vx_mps": xr[2],
        "radar_ekf_vy_mps": xr[3],
        "radar_ekf_std_x_m": math.sqrt(Pr[0, 0]),
        "state_difference_m": math.hypot(
            xr[0]-xl[0], xr[1]-xl[1]
        ),
        "evaluation_status": "NOT_GROUND_TRUTH_VALIDATED"
    })

output = DIR / "lidar_radar_ekf_track2_v1.csv"

with output.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

max_difference = max(
    r["state_difference_m"] for r in results
)

summary = f"""TASK 24.9.5D - MATCHED EKF DEVELOPMENT BASELINE
=================================================
Recording: clean V2, 2122 frames
Selected development frames: 53
Evaluated provisional Track ID: {TRACK_ID}
Matched Track 2 observations: {len(results)}
LiDAR-only and LiDAR-Radar inputs: same position sequence

Radar carrier: 77 GHz (verified in recorded OSI)
Radar velocity sigma: {RADAR_STD_MPS} m/s (exploratory)
Radar NIS gate: {RADAR_NIS_GATE}
Minimum nonzero Radar returns: {MIN_NONZERO_RADAR_RETURNS}

Radar accepted: {accepted}
Radar rejected by NIS: {rejected}
Radar insufficient returns: {insufficient}
No nonzero Radar measurement: {no_nonzero}

Maximum position difference between estimators:
{max_difference:.6f} m

Caution:
This is NOT a Ground Truth accuracy comparison.
Radar and LiDAR associations remain provisional.
The 2.0 m/s Radar uncertainty is not calibrated.
No Camera update has been performed.
No object ID from Ground Truth is used.
The model assumes stationary ego or ego-compensated positions.
This experiment only processes Track 2 observations.
"""

report = DIR / "lidar_radar_ekf_track2_summary_v1.txt"

with report.open("x", encoding="utf-8") as f:
    f.write(summary)

print("=== TASK 24.9.5D RESULTS ===")
print("TRACK_ID=", TRACK_ID)
print("MATCHED_OBSERVATIONS=", len(results))
print("RADAR_UPDATES_ACCEPTED=", accepted)
print("RADAR_UPDATES_REJECTED=", rejected)
print("RADAR_INSUFFICIENT_RETURNS=", insufficient)
print("RADAR_WITHOUT_NONZERO_MEASUREMENT=", no_nonzero)
print("MAX_ESTIMATOR_POSITION_DIFFERENCE_M=",
      round(max_difference, 6))

print("\n=== RADAR UPDATE DETAILS ===")
for r in results:
    if r["radar_nonzero_returns"] > 0:
        print(
            f"FRAME={r['frame']} "
            f"RETURNS={r['radar_nonzero_returns']} "
            f"STATUS={r['radar_status']} "
            f"MEASURED_MPS={r['radar_measured_mps']:.3f} "
            f"NIS={r['radar_nis']:.4f}"
        )

print("OUTPUT_CSV=", output)
print("REPORT=", report)
print("GROUND_TRUTH_ACCURACY_EVALUATED=NO")
print("CAMERA_UPDATES_PERFORMED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_09_05D_EKF_BASELINE_COMPLETE")