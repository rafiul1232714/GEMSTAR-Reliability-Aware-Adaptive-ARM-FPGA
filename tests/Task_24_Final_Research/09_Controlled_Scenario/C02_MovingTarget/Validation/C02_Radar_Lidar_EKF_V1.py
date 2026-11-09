import csv
import math
import sys
import numpy as np

TRACK_CSV, RADAR_CSV, BASE_CSV, OUT_CSV = sys.argv[1:5]

# Preserve Kalman V1 assumptions for matched comparison.
LIDAR_POSITION_STD_M = 0.60
PROCESS_ACCEL_STD_MPS2 = 1.00
INITIAL_POSITION_STD_M = 1.00
INITIAL_VELOCITY_STD_MPS = 2.00

# Preliminary Radar noise assumption, not calibrated.
RADAR_SPEED_STD_MPS = 0.35
RADAR_NIS_GATE = 9.0

# Controlled stationary-ego approximation.
RADAR_X_M = 2.0
RADAR_Y_M = 0.0

H_L = np.array([
    [1., 0., 0., 0.],
    [0., 1., 0., 0.]
])

R_L = np.eye(2) * LIDAR_POSITION_STD_M**2
I = np.eye(4)

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

track_rows = read_csv(TRACK_CSV)
radar_rows = read_csv(RADAR_CSV)
baseline_rows = read_csv(BASE_CSV)

if len(track_rows) != 53 or len(baseline_rows) != 53:
    raise RuntimeError("Unexpected sample count")

radar_by_time = {}

for r in radar_rows:
    key = round(float(r["requested_time_s"]), 3)

    if key in radar_by_time:
        raise RuntimeError("Duplicate Radar timestamp")

    radar_by_time[key] = r

def radar_model(state):
    x, y, vx, vy = state
    dx = x - RADAR_X_M
    dy = y - RADAR_Y_M

    radius = math.hypot(dx, dy)

    if radius < 0.1:
        raise RuntimeError("Radar model singular near sensor")

    ux, uy = dx/radius, dy/radius
    predicted_speed = ux*vx + uy*vy

    H = np.array([[
        (vx - predicted_speed*ux)/radius,
        (vy - predicted_speed*uy)/radius,
        ux,
        uy
    ]])

    return predicted_speed, H

def covariance_update(state, P, H, R, innovation):
    S = H @ P @ H.T + R
    K = np.linalg.solve(S, H @ P).T

    state = state + K @ innovation

    A = I - K @ H
    P = A @ P @ A.T + K @ R @ K.T
    P = 0.5 * (P + P.T)

    return state, P

state = None
P = None
previous_time = None
results = []

for row, baseline in zip(track_rows, baseline_rows):

    requested = round(float(row["requested_time_s"]), 3)
    t = float(row["sensor_time_s"])

    if abs(float(baseline["sensor_time_s"]) - t) > 1e-5:
        raise RuntimeError("Kalman V1 timestamps do not match")

    has_lidar = row["status"] in ("INITIALIZED", "ASSOCIATED")

    if has_lidar:
        z_lidar = np.array([
            float(row["selected_x_m"]),
            float(row["selected_y_m"])
        ])

    if state is None:
        if not has_lidar:
            raise RuntimeError("Missing initial LiDAR measurement")

        state = np.array([
            z_lidar[0], z_lidar[1], 0., 0.
        ])

        P = np.diag([
            INITIAL_POSITION_STD_M**2,
            INITIAL_POSITION_STD_M**2,
            INITIAL_VELOCITY_STD_MPS**2,
            INITIAL_VELOCITY_STD_MPS**2
        ])

        lidar_status = "INITIALIZED"

    else:
        dt = t - previous_time

        if not 0 < dt < 5:
            raise RuntimeError("Invalid time interval")

        F = np.array([
            [1., 0., dt, 0.],
            [0., 1., 0., dt],
            [0., 0., 1., 0.],
            [0., 0., 0., 1.]
        ])

        G = np.array([
            [0.5*dt*dt, 0.],
            [0., 0.5*dt*dt],
            [dt, 0.],
            [0., dt]
        ])

        Q = PROCESS_ACCEL_STD_MPS2**2 * (G @ G.T)

        state = F @ state
        P = F @ P @ F.T + Q

        lidar_status = "PREDICTED_ONLY"

        if has_lidar:
            innovation = z_lidar - H_L @ state

            state, P = covariance_update(
                state, P, H_L, R_L, innovation
            )

            lidar_status = "UPDATED"

    previous_time = t

    # Radar update follows LiDAR at the same sampled timestamp.
    radar_status = "NOT_AVAILABLE"
    radar_measured = None
    radar_predicted = None
    radar_innovation = None
    radar_nis = None
    radar_matches = 0

    r = radar_by_time.get(requested)

    if r is not None:
        if abs(float(r["sensor_time_s"]) - t) > 0.1:
            raise RuntimeError("Radar/LiDAR timestamp mismatch")

        radar_matches = int(r["track_matched_nonzero"])

        value = r["mean_matched_radial_speed_mps"]

        if radar_matches > 0 and str(value).strip():
            radar_measured = float(value)

            radar_predicted, H_R = radar_model(state)

            radar_innovation = radar_measured - radar_predicted

            R_R = np.array([[RADAR_SPEED_STD_MPS**2]])

            S = float((H_R @ P @ H_R.T)[0, 0] + R_R[0, 0])
            radar_nis = radar_innovation**2 / S

            if radar_nis <= RADAR_NIS_GATE:
                state, P = covariance_update(
                    state,
                    P,
                    H_R,
                    R_R,
                    np.array([radar_innovation])
                )

                radar_status = "ACCEPTED"
            else:
                radar_status = "REJECTED_BY_GATE"

    result = {
        "requested_time_s": requested,
        "sensor_time_s": round(t, 6),
        "lidar_status": lidar_status,
        "radar_status": radar_status,
        "radar_matched_returns": radar_matches,
        "radar_measured_speed_mps": radar_measured,
        "radar_predicted_speed_mps": radar_predicted,
        "radar_innovation_mps": radar_innovation,
        "radar_nis": radar_nis,
        "ekf_x_m": float(state[0]),
        "ekf_y_m": float(state[1]),
        "ekf_vx_mps": float(state[2]),
        "ekf_vy_mps": float(state[3]),
        "ekf_speed_mps": math.hypot(state[2], state[3]),
        "ekf_std_x_m": math.sqrt(max(P[0, 0], 0.)),
        "ekf_std_y_m": math.sqrt(max(P[1, 1], 0.)),
        "kalman_v1_x_m": float(baseline["kalman_x_m"]),
        "kalman_v1_y_m": float(baseline["kalman_y_m"]),
        "diagnostic_target_purity":
            row["diagnostic_target_purity"]
    }

    results.append(result)

def clean(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 6)
    return value

with open(OUT_CSV, "x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows({
        k: clean(v) for k, v in r.items()
    } for r in results)

accepted = [
    r for r in results
    if r["radar_status"] == "ACCEPTED"
]

rejected = [
    r for r in results
    if r["radar_status"] == "REJECTED_BY_GATE"
]

print("TOTAL_SAMPLES=", len(results))
print("RADAR_UPDATES_ACCEPTED=", len(accepted))
print("RADAR_UPDATES_REJECTED=", len(rejected))
print("RADAR_UNAVAILABLE_SAMPLES=",
      sum(r["radar_status"] == "NOT_AVAILABLE" for r in results))

print("\n=== RADAR UPDATE DETAILS ===")

for r in results:
    if r["radar_status"] != "NOT_AVAILABLE":
        print(
            "TIME=", r["requested_time_s"],
            "MATCHED=", r["radar_matched_returns"],
            "STATUS=", r["radar_status"],
            "MEASURED_MPS=", round(r["radar_measured_speed_mps"], 4),
            "PREDICTED_MPS=", round(r["radar_predicted_speed_mps"], 4),
            "INNOVATION_MPS=", round(r["radar_innovation_mps"], 4),
            "NIS=", round(r["radar_nis"], 4)
        )

print("\n=== SELECTED TRACK ESTIMATES ===")

for r in results:
    if r["requested_time_s"] in (5., 7., 9., 10., 15., 20., 25., 28.):
        print(
            "TIME=", r["requested_time_s"],
            "EKF_X=", round(r["ekf_x_m"], 4),
            "EKF_Y=", round(r["ekf_y_m"], 4),
            "EKF_SPEED=", round(r["ekf_speed_mps"], 4),
            "RADAR=", r["radar_status"]
        )

print("\nRADAR_MEASUREMENT_NOISE_CALIBRATED=NO")
print("RADAR_SAMPLES_ONLY_IN_EARLY_SEQUENCE=YES")
print("EXACT_SENSOR_EXTRINSICS_VALIDATED=NO")
print("GROUND_TRUTH_USED_BY_EKF=NO")
print("OBJECT_IDS_USED_BY_EKF=NO")
print("GROUND_TRUTH_RMSE_EVALUATED=NO")
print("OUTPUT_CSV=", OUT_CSV)
print("TASK24_05_04N_RADAR_ASSISTED_EKF_COMPLETE")
