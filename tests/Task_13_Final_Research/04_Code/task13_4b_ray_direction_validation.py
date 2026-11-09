
# TASK 13.4B - LIDAR RAY DIRECTION VALIDATION
# MOR100 frame 150
#
# Compares two ray-angle sign conventions against the
# previously reconstructed ego-frame point coordinates.
#
# This is a consistency check, not a final calibration.

from pathlib import Path
import csv
import math
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

CSV = (
    ROOT / "tests" / "Task_11_Final_Research" /
    "02_CSV_Data" / "task11_lidar_frame150_geometry.csv"
)

NH = 251
NV = 21
HFOV = math.radians(90)
VFOV = math.radians(20)

# Configured LiDAR mounting position in ego coordinates.
# Unreal Y is reversed in OSI coordinates.
MOUNT = (2.60, 0.0, 0.70)


def load_rows():
    with CSV.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


rows = load_rows()

print("\n===== TASK 13.4B - RAY DIRECTION VALIDATION =====")
print("Recorded valid returns:", len(rows))

results = {}

for sign_name, y_sign in [
    ("Unreal_to_OSI_Y_inverted", -1),
    ("Y_not_inverted", 1)
]:
    errors = []

    for row in rows:
        ray = int(row["ray_index"])
        h = ray % NH
        v = ray // NH

        if not (0 <= h < NH and 0 <= v < NV):
            raise RuntimeError(
                f"Unexpected ray index: {ray}"
            )

        az = -HFOV/2 + h * HFOV/(NH-1)
        el = -VFOV/2 + v * VFOV/(NV-1)

        distance = float(row["range_m"])

        # Unreal forward-vector convention:
        dx = math.cos(el) * math.cos(az)
        dy = y_sign * math.cos(el) * math.sin(az)
        dz = math.sin(el)

        expected = (
            MOUNT[0] + distance*dx,
            MOUNT[1] + distance*dy,
            MOUNT[2] + distance*dz
        )

        observed = (
            float(row["x_ego_m"]),
            float(row["y_ego_m"]),
            float(row["z_ego_m"])
        )

        error = math.dist(expected, observed)
        errors.append(error)

    results[sign_name] = errors

    print(f"\nConvention: {sign_name}")
    print(f"  Median error: {statistics.median(errors):.6f} m")
    print(f"  Mean error:   {statistics.mean(errors):.6f} m")
    print(f"  Max error:    {max(errors):.6f} m")

best = min(
    results,
    key=lambda name: statistics.median(results[name])
)

print("\nBest tested convention:", best)
print("\nTASK 13.4B COMPLETED")
