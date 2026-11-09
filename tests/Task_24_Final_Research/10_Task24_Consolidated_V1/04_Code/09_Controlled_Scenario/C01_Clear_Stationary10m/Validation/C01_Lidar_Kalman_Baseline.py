import csv
import math
import os

INPUT = os.environ["C01_INPUT_CSV"]
OUTPUT = os.environ["C01_OUTPUT_CSV"]

# Provisional parameters; calibrate in later experiments.
MEASUREMENT_STD_M = 0.15
ACCELERATION_STD_MPS2 = 1.0
GATE_CHI2_2D = 9.21

def transpose(A):
    return [list(row) for row in zip(*A)]

def multiply(A, B):
    BT = transpose(B)
    return [
        [sum(a*b for a,b in zip(row,col)) for col in BT]
        for row in A
    ]

def add(A, B):
    return [
        [a+b for a,b in zip(ra,rb)]
        for ra,rb in zip(A,B)
    ]

def subtract(A, B):
    return [
        [a-b for a,b in zip(ra,rb)]
        for ra,rb in zip(A,B)
    ]

def diag(values):
    return [
        [v if i==j else 0.0 for j in range(len(values))]
        for i,v in enumerate(values)
    ]

def inverse2(A):
    a,b = A[0]
    c,d = A[1]
    determinant = a*d-b*c
    if determinant <= 1e-15:
        raise RuntimeError("Invalid innovation covariance")
    return [
        [d/determinant, -b/determinant],
        [-c/determinant, a/determinant]
    ]

I = diag([1.0, 1.0, 1.0, 1.0])

H = [
    [1.0,0.0,0.0,0.0],
    [0.0,1.0,0.0,0.0]
]

HT = transpose(H)

R = diag([
    MEASUREMENT_STD_M**2,
    MEASUREMENT_STD_M**2
])

with open(INPUT, newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise RuntimeError("Input CSV is empty")

# Initialize from first actual LiDAR measurement, not GT.
first = rows[0]
if first["association_status"] != "MATCHED":
    raise RuntimeError("First measurement is not associated")

x = [
    [float(first["centroid_x_m"])],
    [float(first["centroid_y_m"])],
    [0.0],
    [0.0]
]

P = diag([0.25, 0.25, 4.0, 4.0])

last_t = float(first["timestamp_s"])
results = []
accepted = 0
rejected = 0
max_innovation = 0.0

for index, row in enumerate(rows):
    t = float(row["timestamp_s"])
    dt = t-last_t if index > 0 else 0.0

    if index > 0 and (dt <= 0 or dt > 2.0):
        raise RuntimeError("Invalid timestamp interval")

    # Constant-velocity transition.
    F = [
        [1.0,0.0,dt,0.0],
        [0.0,1.0,0.0,dt],
        [0.0,0.0,1.0,0.0],
        [0.0,0.0,0.0,1.0]
    ]

    # Discrete white-acceleration process noise.
    a = dt**4/4
    b = dt**3/2
    c = dt**2

    q = ACCELERATION_STD_MPS2**2

    Q = [
        [q*a,0.0,q*b,0.0],
        [0.0,q*a,0.0,q*b],
        [q*b,0.0,q*c,0.0],
        [0.0,q*b,0.0,q*c]
    ]

    x_pred = multiply(F,x)
    P_pred = add(
        multiply(multiply(F,P),transpose(F)),
        Q
    )

    innovation_norm = None
    mahalanobis_sq = None
    status = "PREDICT_ONLY"

    if row["association_status"] == "MATCHED":
        z = [
            [float(row["centroid_x_m"])],
            [float(row["centroid_y_m"])]
        ]

        predicted_z = multiply(H,x_pred)
        innovation = subtract(z,predicted_z)

        S = add(
            multiply(multiply(H,P_pred),HT),
            R
        )

        S_inv = inverse2(S)

        mahalanobis_sq = multiply(
            multiply(transpose(innovation),S_inv),
            innovation
        )[0][0]

        innovation_norm = math.hypot(
            innovation[0][0],
            innovation[1][0]
        )

        max_innovation = max(
            max_innovation,innovation_norm
        )

        if mahalanobis_sq <= GATE_CHI2_2D:
            K = multiply(
                multiply(P_pred,HT),S_inv
            )

            x = add(
                x_pred,multiply(K,innovation)
            )

            # Joseph covariance update for stability.
            KH = multiply(K,H)
            A = subtract(I,KH)

            P = add(
                multiply(multiply(A,P_pred),transpose(A)),
                multiply(multiply(K,R),transpose(K))
            )

            accepted += 1
            status = "ACCEPTED"
        else:
            x = x_pred
            P = P_pred
            rejected += 1
            status = "GATED_OUT"
    else:
        x = x_pred
        P = P_pred

    speed = math.hypot(x[2][0],x[3][0])

    results.append({
        "track_id": row["track_id"],
        "timestamp_s": t,
        "dt_s": dt,
        "measurement_x_m": row["centroid_x_m"],
        "measurement_y_m": row["centroid_y_m"],
        "filtered_x_m": x[0][0],
        "filtered_y_m": x[1][0],
        "filtered_vx_mps": x[2][0],
        "filtered_vy_mps": x[3][0],
        "filtered_speed_mps": speed,
        "position_std_x_m": math.sqrt(max(P[0][0],0)),
        "position_std_y_m": math.sqrt(max(P[1][1],0)),
        "innovation_norm_m": (
            innovation_norm if innovation_norm is not None else ""
        ),
        "mahalanobis_sq": (
            mahalanobis_sq if mahalanobis_sq is not None else ""
        ),
        "update_status": status
    })

    last_t = t

with open(OUTPUT,"x",newline="",encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

speeds = [r["filtered_speed_mps"] for r in results]

print("INPUT_MEASUREMENTS=",len(rows))
print("FILTERED_SAMPLES=",len(results))
print("ACCEPTED_UPDATES=",accepted)
print("REJECTED_UPDATES=",rejected)
print("TRACKING_MODEL=CONSTANT_VELOCITY")
print("FILTER_TYPE=LINEAR_KALMAN_FILTER")
print("MEASUREMENT_STD_ASSUMPTION_M=",MEASUREMENT_STD_M)
print("ACCELERATION_STD_ASSUMPTION_MPS2=",ACCELERATION_STD_MPS2)

print("\n=== STATIONARY TRACK RESULTS ===")
print("INITIAL_TIME_S=",round(results[0]["timestamp_s"],6))
print("FINAL_TIME_S=",round(results[-1]["timestamp_s"],6))
print("MAX_ESTIMATED_SPEED_MPS=",round(max(speeds),8))
print("FINAL_ESTIMATED_SPEED_MPS=",round(speeds[-1],8))
print("MAX_INNOVATION_M=",round(max_innovation,8))

last = results[-1]

print("FINAL_FILTERED_X_M=",round(last["filtered_x_m"],6))
print("FINAL_FILTERED_Y_M=",round(last["filtered_y_m"],6))
print("FINAL_POSITION_STD_X_M=",
      round(last["position_std_x_m"],6))
print("FINAL_POSITION_STD_Y_M=",
      round(last["position_std_y_m"],6))

print("\n=== OUTPUT ===")
print("RESULT_CSV=",OUTPUT)
print("GROUND_TRUTH_USED=NO")
print("VEHICLE_CENTER_ESTIMATED=NO")
print("MOVING_TARGET_VALIDATED=NO")
print("THREE_SENSOR_FUSION_IMPLEMENTED=NO")
print("ORIGINAL_OSI_FILES_MODIFIED=NO")
print("TASK24_05_KALMAN_BASELINE_COMPLETE")
