import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import median

import numpy as np

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget")
DIR = Path('E:\\GEMSTAR_Project\\sensor-health-monitor\\tests\\Task_26_Final_Research\\03_Configurations\\Task26_5I_EKF_Sandbox\\Input_Output')
C = 299792458.0
FREQUENCY = 77e9
RADAR_POS = (2.0, 0.0)
CAMERA_X = 0.7

RADAR_SIGMA = 2.0
RADAR_NIS_GATE = 9.0
CAMERA_NIS_GATE = 9.0
MIN_RADAR_RETURNS = 2

H_L = np.array([[1., 0., 0., 0.],
                [0., 1., 0., 0.]])
I = np.eye(4)

def load(name):
    with (DIR / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))

def update(x, P, H, residual, R):
    S = H @ P @ H.T + R
    K = P @ H.T @ np.linalg.inv(S)
    new_x = x + K @ residual
    A = I - K @ H
    new_P = A @ P @ A.T + K @ R @ K.T
    return new_x, (new_P + new_P.T) / 2

def predict(x, P, dt):
    F = np.array([[1., 0., dt, 0.],
                  [0., 1., 0., dt],
                  [0., 0., 1., 0.],
                  [0., 0., 0., 1.]])
    Q = np.array([
        [dt**4/4, 0., dt**3/2, 0.],
        [0., dt**4/4, 0., dt**3/2],
        [dt**3/2, 0., dt**2, 0.],
        [0., dt**3/2, 0., dt**2]
    ])
    return F @ x, F @ P @ F.T + Q

def lidar_noise(n):
    factor = min(2.0, max(1.0, 12.0 / n))
    return np.eye(2) * (0.60 * factor)**2

def radar_model(x):
    dx, dy = x[0] - RADAR_POS[0], x[1] - RADAR_POS[1]
    r = math.hypot(dx, dy)
    if r < 0.1:
        raise RuntimeError("Radar model singular")
    ux, uy = dx/r, dy/r
    v = ux*x[2] + uy*x[3]
    H = np.array([[(x[2]-v*ux)/r,
                   (x[3]-v*uy)/r, ux, uy]])
    return v, H

def camera_model(x):
    dx, dy = x[0] - CAMERA_X, x[1]
    d2 = dx*dx + dy*dy
    if dx <= 0 or d2 < 0.01:
        raise RuntimeError("Camera geometry invalid")
    predicted = math.atan2(-dy, dx)
    H = np.array([[dy/d2, -dx/d2, 0., 0.]])
    return predicted, H

track = sorted(
    [r for r in load("lidar_temporal_tracks_v1.csv")
     if int(r["track_id"]) == 2],
    key=lambda r: float(r["time_s"])
)
radar = defaultdict(list)
for r in load("radar_track_matches_v1.csv"):
    if int(r["track_id"]) == 2:
        fd = float(r["doppler_shift_raw"])
        if abs(fd) > 1e-9:
            radar[int(r["frame"])].append(
                (float(r["time_s"]), fd)
            )

cam = load("camera_bearing_track2_frame530_v1.csv")
old = load("lidar_radar_ekf_track2_v1.csv")

if len(track) != 24 or len(old) != 24 or len(cam) != 1:
    raise RuntimeError("Unexpected input row counts")

if cam[0]["status"] != "BEARING_GEOMETRICALLY_COMPATIBLE_NOT_CALIBRATED":
    raise RuntimeError("Camera candidate failed geometry check")
if int(cam[0]["frame"]) != 530 or int(cam[0]["track_id"]) != 2:
    raise RuntimeError("Unexpected Camera track/frame")

camera_angle = float(cam[0]["camera_bearing_rad"])
camera_sigma = max(
    0.05, float(cam[0]["assumed_bearing_sigma_rad"])
)

x0 = np.array([
    float(track[0]["x_m"]), float(track[0]["y_m"]),
    0., 0.
])
P0 = np.diag([1., 1., 4., 4.])

# A, B, C share the same initialization and LiDAR observations.
states = [x0.copy() for _ in range(3)]
covs = [P0.copy() for _ in range(3)]
results = []

camera_status = "NOT_ATTEMPTED"
camera_nis = float("nan")
camera_residual = float("nan")
camera_updates = 0
max_baseline_error = 0.0

for i, row in enumerate(track):
    frame = int(row["frame"])
    t = float(row["time_s"])
    z = np.array([float(row["x_m"]), float(row["y_m"])])
    R_L = lidar_noise(int(row["point_count"]))

    if i:
        dt = t - float(track[i-1]["time_s"])
        if dt <= 0:
            raise RuntimeError("Non-increasing timestamps")
        for j in range(3):
            states[j], covs[j] = predict(states[j], covs[j], dt)
            states[j], covs[j] = update(
                states[j], covs[j], H_L,
                z - H_L @ states[j], R_L
            )

    values = radar.get(frame, [])
    radar_status = "NOT_AVAILABLE"
    if values:
        if any(abs(rt-t) > 1e-4 for rt, _ in values):
            raise RuntimeError("Radar timestamp mismatch")

        if len(values) < MIN_RADAR_RETURNS:
            radar_status = "INSUFFICIENT_RETURNS"
        else:
            measurement = median(
                fd*C/(2*FREQUENCY) for _,fd in values
            )
            decisions = []
            for j in (1, 2):
                expected, H = radar_model(states[j])
                innovation = measurement - expected
                R = np.array([[RADAR_SIGMA**2]])
                S = float((H @ covs[j] @ H.T)[0,0] + R[0,0])
                nis = innovation**2/S
                if nis <= RADAR_NIS_GATE:
                    states[j], covs[j] = update(
                        states[j], covs[j], H,
                        np.array([innovation]), R
                    )
                    decisions.append("ACCEPTED")
                else:
                    decisions.append("REJECTED_BY_NIS")
            if i <= next(
                k for k,r in enumerate(track)
                if int(r["frame"]) == 530
            ) and decisions[0] != decisions[1]:
                raise RuntimeError("Radar baseline diverged")
            radar_status = decisions[0]

    if frame == 530:
        expected, H = camera_model(states[2])
        camera_residual = wrap(camera_angle - expected)
        R_C = np.array([[camera_sigma**2]])
        S_C = float((H @ covs[2] @ H.T)[0,0] + R_C[0,0])
        camera_nis = camera_residual**2 / S_C

        if camera_nis <= CAMERA_NIS_GATE:
            states[2], covs[2] = update(
                states[2], covs[2], H,
                np.array([camera_residual]), R_C
            )
            camera_status = "EXPERIMENTAL_ACCEPTED"
            camera_updates += 1
        else:
            camera_status = "REJECTED_BY_NIS"

    previous = old[i]
    if int(previous["frame"]) != frame:
        raise RuntimeError("Baseline frame mismatch")

    for j, fields in enumerate([
        ("lidar_only_x_m", "lidar_only_y_m",
         "lidar_only_vx_mps", "lidar_only_vy_mps"),
        ("radar_ekf_x_m", "radar_ekf_y_m",
         "radar_ekf_vx_mps", "radar_ekf_vy_mps")
    ]):
        for k, field in enumerate(fields):
            error = abs(states[j][k] - float(previous[field]))
            max_baseline_error = max(max_baseline_error, error)
            if error > 1e-5:
                raise RuntimeError(
                    f"Baseline reproduction mismatch: {field}, frame {frame}"
                )

    results.append({
        "frame":frame, "time_s":t,
        "radar_status":radar_status,
        "camera_status":camera_status if frame == 530 else "NO_UPDATE",
        "lidar_x_m":z[0], "lidar_y_m":z[1],
        "lidar_only_x_m":states[0][0],
        "lidar_only_y_m":states[0][1],
        "radar_x_m":states[1][0],
        "radar_y_m":states[1][1],
        "camera_aided_x_m":states[2][0],
        "camera_aided_y_m":states[2][1],
        "camera_aided_vx_mps":states[2][2],
        "camera_aided_vy_mps":states[2][3],
        "camera_aided_std_x_m":math.sqrt(covs[2][0,0]),
        "camera_vs_radar_position_difference_m":math.hypot(
            states[2][0]-states[1][0],
            states[2][1]-states[1][1]
        ),
        "ground_truth_validated":"NO"
    })

with (DIR/"lidar_radar_camera_ekf_track2_v1.csv").open(
    "x", newline="", encoding="utf-8"
) as f:
    w = csv.DictWriter(f, fieldnames=list(results[0]))
    w.writeheader()
    w.writerows(results)

print("=== TASK 24.9.6B RESULTS ===")
print("OBSERVATIONS=",len(results))
print("BASELINE_REPRODUCTION_MAX_ERROR=",max_baseline_error)
print("CAMERA_UPDATE_FRAME=530")
print("CAMERA_NIS=",round(camera_nis,6))
print("CAMERA_INNOVATION_DEG=",round(
    math.degrees(camera_residual),6))
print("CAMERA_ASSUMED_SIGMA_DEG=",round(
    math.degrees(camera_sigma),6))
print("CAMERA_STATUS=",camera_status)
print("CAMERA_UPDATES=",camera_updates)
print("MAX_CAMERA_VS_RADAR_POSITION_DIFFERENCE_M=",
      round(max(
          r["camera_vs_radar_position_difference_m"]
          for r in results
      ),6))
print("OUTPUT=",DIR/"lidar_radar_camera_ekf_track2_v1.csv")
print("CAMERA_CALIBRATED=NO")
print("GROUND_TRUTH_ACCURACY_EVALUATED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_09_06B_CAMERA_EKF_COMPLETE")