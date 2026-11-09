import csv
import math
import struct
from pathlib import Path
from collections import defaultdict
from statistics import median
from osi3.osi_sensorview_pb2 import SensorView

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

OSI = Path(
    r"E:\GEMSTAR_Project\gemstar\Output\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

C = 299792458.0
EXPECTED_FREQUENCY_HZ = 77e9
TRACK_ID = 2
RADAR_X_M = 2.0
RADAR_Y_M = 0.0

def load(name):
    with (DIR / name).open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

# Read the recorded Radar configuration at frame 245.
with OSI.open("rb") as f:
    for frame in range(246):
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Incomplete OSI header")

        size = struct.unpack("<I", header)[0]
        if size <= 0:
            raise RuntimeError("Invalid OSI message size")

        if frame < 245:
            f.seek(size, 1)
        else:
            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError("Incomplete OSI payload")

sv = SensorView()
sv.ParseFromString(payload)

if len(sv.radar_sensor_view) != 1:
    raise RuntimeError("Expected one Radar view")

frequency = float(
    sv.radar_sensor_view[0].view_configuration.emitter_frequency
)

if not math.isfinite(frequency) or frequency <= 0:
    raise RuntimeError("Invalid recorded Radar carrier frequency")

if not math.isclose(
    frequency, EXPECTED_FREQUENCY_HZ, rel_tol=1e-6
):
    raise RuntimeError(
        f"Unexpected recorded frequency: {frequency}"
    )

track = [
    {
        "frame": int(r["frame"]),
        "t": float(r["time_s"]),
        "x": float(r["x_m"]),
        "y": float(r["y_m"])
    }
    for r in load("lidar_temporal_tracks_v1.csv")
    if int(r["track_id"]) == TRACK_ID
]
track.sort(key=lambda r: r["t"])

if len(track) < 3:
    raise RuntimeError("Insufficient temporal observations")

# Estimate signed radial velocity from LiDAR position changes.
# Centered finite differences for interior observations.
lidar_velocity = {}

for i, current in enumerate(track):
    a = track[max(0, i-1)]
    b = track[min(len(track)-1, i+1)]

    dt = b["t"] - a["t"]

    if dt <= 0:
        raise RuntimeError("Invalid temporal spacing")

    vx = (b["x"] - a["x"]) / dt
    vy = (b["y"] - a["y"]) / dt

    dx = current["x"] - RADAR_X_M
    dy = current["y"] - RADAR_Y_M

    distance = math.hypot(dx, dy)

    if distance <= 0:
        raise RuntimeError("Track at Radar origin")

    radial = (vx*dx + vy*dy) / distance

    lidar_velocity[current["frame"]] = {
        "radial_mps": radial,
        "vx": vx,
        "vy": vy
    }

# Use only nonzero Doppler returns provisionally matched
# to Track 2. Zero values are not treated as velocity updates.
grouped = defaultdict(list)

all_matches = load("radar_track_matches_v1.csv")

for r in all_matches:
    if int(r["track_id"]) != TRACK_ID:
        continue

    doppler_hz = float(r["doppler_shift_raw"])

    if not math.isfinite(doppler_hz):
        raise RuntimeError("Invalid Doppler frequency")

    if abs(doppler_hz) <= 1e-9:
        continue

    grouped[int(r["frame"])].append(doppler_hz)

results = []

for frame in sorted(grouped):
    if frame not in lidar_velocity:
        raise RuntimeError(
            f"Missing LiDAR track observation at frame {frame}"
        )

    doppler_values = grouped[frame]

    radar_velocities = [
        fd * C / (2 * frequency)
        for fd in doppler_values
    ]

    radar_mps = median(radar_velocities)
    lidar_mps = lidar_velocity[frame]["radial_mps"]

    results.append({
        "frame": frame,
        "track_id": TRACK_ID,
        "nonzero_radar_returns": len(doppler_values),
        "median_doppler_hz": round(median(doppler_values), 6),
        "radar_radial_velocity_mps": round(radar_mps, 6),
        "lidar_radial_velocity_mps": round(lidar_mps, 6),
        "signed_residual_mps": round(radar_mps - lidar_mps, 6),
        "absolute_residual_mps": round(abs(radar_mps - lidar_mps), 6),
        "same_sign": (
            radar_mps * lidar_mps > 0
            if abs(lidar_mps) > 1e-6 else ""
        ),
        "status": "DIAGNOSTIC_NOT_EKF_AUTHORIZED"
    })

if not results:
    raise RuntimeError("No nonzero Doppler observations matched")

output = DIR / "radar_lidar_velocity_consistency_v1.csv"

with output.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)

print("=== TASK 24.9.5C RESULTS ===")
print("RECORDED_CARRIER_FREQUENCY_HZ=", frequency)
print("RECORDED_CARRIER_FREQUENCY_GHZ=", frequency / 1e9)
print("TRACK_ID=", TRACK_ID)
print("TRACK_OBSERVATIONS=", len(track))
print("NONZERO_DOPPLER_FRAMES=", len(results))

for r in results:
    print(
        f"FRAME={r['frame']} "
        f"RETURNS={r['nonzero_radar_returns']} "
        f"RADAR_MPS={r['radar_radial_velocity_mps']} "
        f"LIDAR_MPS={r['lidar_radial_velocity_mps']} "
        f"ABS_RESIDUAL_MPS={r['absolute_residual_mps']} "
        f"SAME_SIGN={r['same_sign']}"
    )

print("MEDIAN_ABSOLUTE_RESIDUAL_MPS=", round(
    median(r["absolute_residual_mps"] for r in results), 6
))
print("OUTPUT_CSV=", output)
print("RADAR_UNIT_CONVERSION=HZ_TO_MPS")
print("LIDAR_VELOCITY_METHOD=CENTERED_FINITE_DIFFERENCE")
print("MEASUREMENT_VALIDATION=PRELIMINARY")
print("GROUND_TRUTH_USED=NO")
print("EKF_UPDATE_PERFORMED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_09_05C_DOPPLER_VALIDATION_COMPLETE")