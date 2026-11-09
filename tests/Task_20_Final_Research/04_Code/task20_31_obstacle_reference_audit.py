import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_20_Final_Research")
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"
DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

gt_path = DATA / "task20_14_gt_classified_objects.csv"
radar_path = DATA / "task20_28_radar_world_points.csv"

with gt_path.open(encoding="utf-8-sig", newline="") as f:
    gt_rows = list(csv.DictReader(f))

with radar_path.open(encoding="utf-8-sig", newline="") as f:
    radar_rows = list(csv.DictReader(f))

# Host identity is taken from radar SensorView's
# nested host_vehicle_id, exported in Task 20.28.
host_by_frame = defaultdict(set)
radar_counts = Counter()

for row in radar_rows:
    key = (row["Recording"], int(row["FrameIndex"]))
    host_by_frame[key].add(row["HostID"])
    radar_counts[key] += 1

# Auditing moving-object candidates only.
# Stationary map geometry needs separate ray validation.
candidates = []
summary = []

scenarios = sorted(set(r["Recording"] for r in gt_rows))

print("\n=== TASK 20.31 OBSTACLE REFERENCE AUDIT ===")

for scenario in scenarios:
    rows = [
        r for r in gt_rows
        if r["Recording"] == scenario
    ]

    nonhost = []
    excluded_host = 0
    helpers = 0
    nohost_frames = set()
    frames = set()

    for r in rows:
        frame = int(r["Frame"])
        frames.add(frame)

        if r["Kind"] != "MOVING":
            continue

        key = (scenario, frame)
        hosts = host_by_frame.get(key, set())

        if not hosts:
            nohost_frames.add(frame)
            continue

        if r["ID"] in hosts:
            excluded_host += 1
            continue

        # FollowVehicleCamera was identified in
        # previous source and model-reference audits.
        if r["ID"] not in hosts and (
            r["ObjectType"] == "TYPE_VEHICLE"
            and float(r["Length"]) >= 9
            and float(r["Width"]) >= 9
        ):
            helpers += 1
            continue

        nonhost.append(r)
        candidates.append(r)

    unique_ids = sorted({r["ID"] for r in nonhost})
    radar_total = sum(
        count for (name, _), count in radar_counts.items()
        if name == scenario
    )

    record = {
        "Recording": scenario,
        "GTFrames": len(frames),
        "FramesWithoutRecordedHost": len(nohost_frames),
        "ExcludedHostEntries": excluded_host,
        "ExcludedLikelyHelperEntries": helpers,
        "OtherMovingObjectEntries": len(nonhost),
        "OtherMovingObjectUniqueIDs": len(unique_ids),
        "RadarCandidateReturns": radar_total,
        "ExternalDetectionAccuracyValidated": False
    }
    summary.append(record)

    print(
        f"{scenario:28s}"
        f" | Host={excluded_host:3d}"
        f" | Helper={helpers:3d}"
        f" | OtherMoving={len(nonhost):3d}"
        f" | OtherIDs={len(unique_ids):3d}"
        f" | Radar={radar_total:5d}"
    )

def write_csv(path, records, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

candidate_path = DATA / "task20_31_external_moving_candidates.csv"
summary_path = DATA / "task20_31_obstacle_reference_summary.csv"
report_path = FINDINGS / "task20_31_obstacle_reference_audit.json"

write_csv(candidate_path, candidates,
          list(gt_rows[0].keys()))
write_csv(summary_path, summary, list(summary[0].keys()))

report_path.write_text(
    json.dumps({
        "Task": "20.31",
        "Summary": summary,
        "Limitations": [
            "Only first 100 frames",
            "Heuristic helper exclusion requires confirmation",
            "Stationary geometry not yet ray-associated",
            "Absence of candidates is not absence of obstacles",
            "No detection accuracy or energy measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.31 COMPLETE ===")
print("External moving-object entries:", len(candidates))
print("Candidate CSV saved:", candidate_path.is_file())
print("Summary CSV saved:", summary_path.is_file())
print("JSON report saved:", report_path.is_file())
print("Radar detection accuracy validated:", False)
