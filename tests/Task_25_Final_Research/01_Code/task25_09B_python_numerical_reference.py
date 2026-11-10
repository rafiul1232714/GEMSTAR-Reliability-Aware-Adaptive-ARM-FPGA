import csv
import math
import statistics
import hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_25_Final_Research"
)

DATA = ROOT / "02_CSV_Data"
AUDIT = ROOT / "05_Raw_Data_References"

OUT = DATA / "task25_80_python_numerical_reference.csv"
MANIFEST = AUDIT / "task25_77_crosscheck_dataset_manifest.csv"

INPUTS = {
    "fallback": "task25_65_fallback_decisions.csv",
    "association": "task25_33_association_distance_analysis.csv",
    "ekf": "task25_40_ekf_consistency_audit.csv",
    "nis": "task25_43_validated_radar_nis.csv",
    "gates": "task25_73_quality_gate_specification.csv",
}

def read_csv(path):
    if not path.is_file():
        raise RuntimeError(f"Missing file: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

manifest_rows = read_csv(MANIFEST)
manifest = {}

for row in manifest_rows:
    name = row["Filename"]
    if name in manifest:
        raise RuntimeError(f"Duplicate manifest filename: {name}")
    manifest[name] = row

tables = {}

for key, name in INPUTS.items():
    path = DATA / name

    if name not in manifest:
        raise RuntimeError(f"Missing hash manifest entry: {name}")

    if sha256(path) != manifest[name]["SHA256"].upper():
        raise RuntimeError(f"SHA256 mismatch: {name}")

    rows = read_csv(path)

    if len(rows) != int(manifest[name]["Rows"]):
        raise RuntimeError(f"Manifest row-count mismatch: {name}")

    tables[key] = rows

D = tables["fallback"]
A = tables["association"]
E = tables["ekf"]
N = tables["nis"]
G = tables["gates"]

assert len(D) == 168
assert len(A) == 162
assert len(E) == 23
assert len(N) == 24
assert len(G) == 6

def finite(value):
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None

    return result if math.isfinite(result) else None

def checked_numbers(rows, field):
    values = [finite(r[field]) for r in rows]

    if any(x is None for x in values):
        raise RuntimeError(f"Missing/nonfinite value: {field}")

    return values

metrics = {}

def record(name, value):
    if name in metrics:
        raise RuntimeError(f"Duplicate metric: {name}")

    if not math.isfinite(float(value)):
        raise RuntimeError(f"Nonfinite metric: {name}")

    metrics[name] = value

# 1. Fallback decisions
mode_counts = Counter(r["controller_mode"] for r in D)

expected_modes = {
    "NORMAL_CANDIDATE",
    "DEGRADED_CANDIDATE",
    "HOLD_OR_ALERT",
}

if set(mode_counts) != expected_modes:
    raise RuntimeError("Unexpected fallback controller mode")

if any(r["quality_authorization"] != "UNVERIFIED" for r in D):
    raise RuntimeError("Unexpected quality authorization")

record("fallback_total", len(D))
record("fallback_normal", mode_counts["NORMAL_CANDIDATE"])
record("fallback_degraded", mode_counts["DEGRADED_CANDIDATE"])
record("fallback_hold", mode_counts["HOLD_OR_ALERT"])

# 2. Association distances
if set(r["Sensor"] for r in A) != {"LiDAR", "Radar"}:
    raise RuntimeError("Unexpected association sensor label")

lidar = [
    r for r in A
    if r["Sensor"] == "LiDAR" and r["Status"] == "MATCHED"
]

radar = [
    r for r in A
    if r["Sensor"] == "Radar"
    and r["Status"] == "PROVISIONAL_RADAR_SPATIAL_MATCH"
]

if len(lidar) != 74 or len(radar) != 65:
    raise RuntimeError("Unexpected association evidence counts")

lidar_distances = checked_numbers(lidar, "Distance_m")
radar_distances = checked_numbers(radar, "Distance_m")

if any(x < 0 for x in lidar_distances + radar_distances):
    raise RuntimeError("Negative association distance")

record("association_lidar_matched", len(lidar))
record("association_radar_provisional", len(radar))
record("association_lidar_mean_distance_m",
       statistics.mean(lidar_distances))
record("association_radar_mean_gap_m",
       statistics.mean(radar_distances))

# 3. EKF residual statistics
lidar_res = checked_numbers(E, "LiDAR_ResidualX_m")
radar_res = checked_numbers(E, "Radar_ResidualX_m")
lidar_sigma = checked_numbers(E, "LiDAR_SigmaX_m")
radar_sigma = checked_numbers(E, "Radar_SigmaX_m")

if any(x <= 0 for x in lidar_sigma + radar_sigma):
    raise RuntimeError("Non-positive reported sigma")

record("ekf_gt_rows", len(E))
record("ekf_lidar_mean_signed_residual_x_m",
       statistics.mean(lidar_res))
record("ekf_radar_mean_signed_residual_x_m",
       statistics.mean(radar_res))
record("ekf_lidar_mean_sigma_x_m",
       statistics.mean(lidar_sigma))
record("ekf_radar_mean_sigma_x_m",
       statistics.mean(radar_sigma))

# 4. Radar NIS
valid_nis = []

for row in N:
    valid = str(row["NIS_Valid"]).strip().lower() == "true"
    value = finite(row["Radar_NIS"])

    if valid:
        if row["Radar_Status"] != "ACCEPTED" or value is None:
            raise RuntimeError("Inconsistent accepted Radar NIS")
        valid_nis.append(value)
    elif value is not None:
        raise RuntimeError("Finite Radar NIS marked unavailable")

if len(valid_nis) != 4:
    raise RuntimeError("Expected exactly four finite accepted NIS")

record("radar_nis_rows", len(N))
record("radar_nis_finite_accepted", len(valid_nis))
record("radar_nis_mean_accepted",
       statistics.mean(valid_nis))

# 5. Quality gate authorization
if len(set(row["GateID"] for row in G)) != 6:
    raise RuntimeError("Duplicate quality gate")

record("quality_gate_total", len(G))
record(
    "quality_gate_authorized",
    sum(row["Authorization"] == "PASS" for row in G)
)

# Save calculated metrics, without modifying input CSVs.
rows = [
    {
        "Metric": name,
        "PythonValue": format(float(value), ".17g"),
        "Unit": (
            "m" if name.endswith("_m")
            else "count" if isinstance(value, int)
            else "dimensionless"
        ),
    }
    for name, value in metrics.items()
]

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["Metric", "PythonValue", "Unit"]
    )
    writer.writeheader()
    writer.writerows(rows)

saved = read_csv(OUT)

if len(saved) != len(metrics):
    raise RuntimeError("Metric file verification failed")

print("\n=== TASK 25.9B PYTHON NUMERICAL REFERENCE ===")
print("SOURCE_DATASETS_HASH_VERIFIED:", len(INPUTS))
print("METRICS_CALCULATED:", len(metrics))

for row in saved:
    print(f"{row['Metric']}: {row['PythonValue']}")

print("CROSS_LANGUAGE_AGREEMENT: NOT_YET_TESTED")
print("ORIGINAL_DATASETS_MODIFIED: NO")
print("TASK25_09B_PYTHON_REFERENCE_PASS")
print("Saved:", OUT)
