import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_20_Final_Research"
)

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"
DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

targets_file = DATA / "task20_31_external_moving_candidates.csv"
geometry_file = DATA / "task20_30_radar_geometry_details.csv"

def load_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

targets = load_csv(targets_file)
geometry = load_csv(geometry_file)

# Sensor origins were reconstructed from nested host
# pose and radar mounting position in Task 20.30.
origins = {}
conflicts = set()

for row in geometry:
    key = (row["Recording"], int(row["Frame"]),
           int(row["RadarIndex"]))
    xyz = tuple(float(row[c]) for c in (
        "SensorOriginX", "SensorOriginY", "SensorOriginZ"
    ))

    if key in origins and math.dist(origins[key], xyz) > 1e-6:
        conflicts.add(key)
    else:
        origins[key] = xyz

results = []
counts = defaultdict(list)

print("\n=== TASK 20.32 EXTERNAL TARGET RANGE AUDIT ===")

for obj in targets:
    scenario = obj["Recording"]
    frame = int(obj["Frame"])
    target_xyz = tuple(float(obj[c]) for c in ("X", "Y", "Z"))

    available = [
        (key, origin) for key, origin in origins.items()
        if key[0] == scenario and key[1] == frame
        and key not in conflicts
    ]

    if not available:
        results.append({
            "Recording": scenario,
            "Frame": frame,
            "ObjectID": obj["ID"],
            "RadarIndex": "",
            "CenterDistanceM": "",
            "Status": "NO_RADAR_ORIGIN"
        })
        counts[scenario].append(None)
        continue

    for key, origin in available:
        d = math.dist(origin, target_xyz)
        results.append({
            "Recording": scenario,
            "Frame": frame,
            "ObjectID": obj["ID"],
            "RadarIndex": key[2],
            "CenterDistanceM": round(d, 6),
            "Status": "DISTANCE_COMPUTED"
        })
        counts[scenario].append(d)

summaries = []

for scenario in sorted({r["Recording"] for r in targets}):
    values = [v for v in counts[scenario] if v is not None]

    item = {
        "Recording": scenario,
        "TargetObservations": len(counts[scenario]),
        "DistancesComputed": len(values),
        "MissingOrigin": counts[scenario].count(None),
        "MinCenterDistanceM": min(values) if values else None,
        "MedianCenterDistanceM": median(values) if values else None,
        "MaxCenterDistanceM": max(values) if values else None
    }
    summaries.append(item)

    print(
        f"{scenario:28s}"
        f" | Targets={item['TargetObservations']:3d}"
        f" | Distances={len(values):3d}"
        f" | Missing={item['MissingOrigin']:3d}"
        f" | Min={item['MinCenterDistanceM']}"
        f" | Median={item['MedianCenterDistanceM']}"
        f" | Max={item['MaxCenterDistanceM']}"
    )

def save_csv(path, records, columns):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

detail_path = DATA / "task20_32_target_center_distances.csv"
summary_path = DATA / "task20_32_target_range_summary.csv"
report_path = FINDINGS / "task20_32_target_range_audit.json"

save_csv(detail_path, results, [
    "Recording", "Frame", "ObjectID", "RadarIndex",
    "CenterDistanceM", "Status"
])

save_csv(summary_path, summaries, [
    "Recording", "TargetObservations", "DistancesComputed",
    "MissingOrigin", "MinCenterDistanceM",
    "MedianCenterDistanceM", "MaxCenterDistanceM"
])

report_path.write_text(
    json.dumps({
        "Task": "20.32",
        "Summary": summaries,
        "InconsistentSensorOrigins": len(conflicts),
        "Limitations": [
            "GT centre distance, not distance to object surface",
            "Radar maximum range not independently confirmed",
            "Field of view and occlusion not checked",
            "GT and radar sampling-time uncertainty remains",
            "No object-association accuracy measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.32 COMPLETE ===")
print("Target observations:", len(targets))
print("Distance records:", len(results))
print("Inconsistent sensor origins:", len(conflicts))
print("Details saved:", detail_path.is_file())
print("Summary saved:", summary_path.is_file())
print("JSON saved:", report_path.is_file())
print("Radar accuracy validated:", False)
print("Energy measured:", False)
