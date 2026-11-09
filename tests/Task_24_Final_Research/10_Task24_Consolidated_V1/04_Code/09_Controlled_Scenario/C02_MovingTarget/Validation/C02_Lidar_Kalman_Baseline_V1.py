import csv
import math
import os
import sys
import numpy as np

INPUT = sys.argv[1]
OUTPUT = sys.argv[2]

# Initial engineering assumptions, not calibrated noise.
POSITION_STD_M = 0.60
ACCELERATION_STD_MPS2 = 1.00
INITIAL_POSITION_STD_M = 1.00
INITIAL_VELOCITY_STD_MPS = 2.00

with open(INPUT, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise RuntimeError("Input CSV is empty")

H = np.array([
    [1., 0., 0., 0.],
    [0., 1., 0., 0.]
])

I = np.eye(4)
R = np.eye(2) * POSITION_STD_M**2

state = None
P = None
previous_time = None

results = []

def number_or_blank(value):
    if value is None or str(value).strip() == "":
        return None
    return float(value)

def rounded(value):
    return round(float(value), 6)

for row in rows:
    t = float(row["sensor_time_s"])
    status = row["status"]

    mx = number_or_blank(row["selected_x_m"])
    my = number_or_blank(row["selected_y_m"])

    has_measurement = (
        status in ("INITIALIZED", "ASSOCIATED")
        and mx is not None
        and my is not None
    )

    if state is None:
        if not has_measurement:
            raise RuntimeError("First sample has no initial measurement")

        state = np.array([mx, my, 0., 0.])
        P = np.diag([
            INITIAL_POSITION_STD_M**2,
            INITIAL_POSITION_STD_M**2,
            INITIAL_VELOCITY_STD_MPS**2,
            INITIAL_VELOCITY_STD_MPS**2
        ])

        previous_time = t
        update_status = "INITIALIZED"
        innovation_norm = None
        dt = 0.0

    else:
        dt = t - previous_time
        if not 0 < dt < 5:
            raise RuntimeError("Invalid timestamp interval")

        F = np.array([
            [1., 0., dt, 0.],
            [0., 1., 0., dt],
            [0., 0., 1., 0.],
            [0., 0., 0., 1.]
        ])

        # White acceleration noise in the constant-velocity model.
        G = np.array([
            [0.5 * dt * dt, 0.],
            [0., 0.5 * dt * dt],
            [dt, 0.],
            [0., dt]
        ])

        Q = (ACCELERATION_STD_MPS2**2) * (G @ G.T)

        state = F @ state
        P = F @ P @ F.T + Q

        update_status = "PREDICTED_ONLY"
        innovation_norm = None

        if has_measurement:
            z = np.array([mx, my])
            innovation = z - H @ state
            S = H @ P @ H.T + R

            K = np.linalg.solve(S, H @ P).T
            state = state + K @ innovation

            # Joseph covariance update, numerically stable.
            A = I - K @ H
            P = A @ P @ A.T + K @ R @ K.T
            P = 0.5 * (P + P.T)

            innovation_norm = float(np.linalg.norm(innovation))
            update_status = "UPDATED"

        previous_time = t

    results.append({
        "requested_time_s": row["requested_time_s"],
        "sensor_time_s": row["sensor_time_s"],
        "dt_s": rounded(dt),
        "heuristic_status": status,
        "kalman_status": update_status,
        "measurement_x_m": "" if mx is None else rounded(mx),
        "measurement_y_m": "" if my is None else rounded(my),
        "kalman_x_m": rounded(state[0]),
        "kalman_y_m": rounded(state[1]),
        "kalman_vx_mps": rounded(state[2]),
        "kalman_vy_mps": rounded(state[3]),
        "kalman_speed_mps": rounded(
            math.hypot(state[2], state[3])
        ),
        "position_std_x_m": rounded(math.sqrt(max(P[0, 0], 0))),
        "position_std_y_m": rounded(math.sqrt(max(P[1, 1], 0))),
        "innovation_norm_m": (
            "" if innovation_norm is None
            else rounded(innovation_norm)
        ),
        "diagnostic_target_purity": row["diagnostic_target_purity"]
    })

with open(OUTPUT, "x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

print("TOTAL_SAMPLES=", len(results))
print("KALMAN_MEASUREMENT_UPDATES=",
      sum(r["kalman_status"] == "UPDATED" for r in results))
print("KALMAN_PREDICTION_ONLY=",
      sum(r["kalman_status"] == "PREDICTED_ONLY" for r in results))

print("\n=== SELECTED SAMPLES ===")
for r in results:
    if float(r["requested_time_s"]) in (
        2, 5, 7, 10, 15, 20, 25, 26, 26.5, 27, 28
    ):
        print(
            "TIME=", r["requested_time_s"],
            "STATUS=", r["kalman_status"],
            "X=", r["kalman_x_m"],
            "Y=", r["kalman_y_m"],
            "SPEED_MPS=", r["kalman_speed_mps"],
            "STD_X_M=", r["position_std_x_m"],
            "INNOVATION_M=", r["innovation_norm_m"]
        )

print("\nPROCESS_NOISE_ASSUMED=YES")
print("MEASUREMENT_NOISE_ASSUMED=YES")
print("KALMAN_DATA_ASSOCIATION_IMPLEMENTED=NO")
print("GROUND_TRUTH_USED_BY_FILTER=NO")
print("OBJECT_ID_USED_BY_FILTER=NO")
print("GROUND_TRUTH_RMSE_EVALUATED=NO")
print("OUTPUT_CSV=", OUTPUT)
print("TASK24_05_05_C02_KALMAN_BASELINE_COMPLETE")
