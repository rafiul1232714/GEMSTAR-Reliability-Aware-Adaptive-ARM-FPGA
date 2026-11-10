import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_25_Final_Research"
)

DATA = ROOT / "02_CSV_Data"
POLICY = DATA / "task25_64_fallback_policy_rules.csv"
REPLAY = DATA / "task25_replay_samples.csv"

OUTPUT = DATA / "task25_65_fallback_decisions.csv"
SUMMARY = DATA / "task25_66_fallback_scenario_summary.csv"

def load_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

rules = load_csv(POLICY)
samples = load_csv(REPLAY)

if len(rules) != 21:
    raise RuntimeError(f"Expected 21 policy rules, found {len(rules)}")

if len(samples) != 168:
    raise RuntimeError(f"Expected 168 replay samples, found {len(samples)}")

mapping = {}

for rule in rules:
    key = (rule["Domain"], rule["ObservedStatus"])
    if key in mapping:
        raise RuntimeError(f"Duplicate policy rule: {key}")
    mapping[key] = rule["Action"]

def action(domain, status):
    key = (domain, str(status).strip())
    if key not in mapping:
        raise RuntimeError(f"Unmapped status: {key}")
    return mapping[key]

required_columns = {
    "scenario", "sample", "frame", "time_s",
    "lidar_used", "radar_status", "camera_status",
    "radar_nis", "camera_nis"
}

if not samples or not required_columns.issubset(samples[0]):
    raise RuntimeError("Replay input schema mismatch")

scenario_rows = defaultdict(list)
seen = set()

for row in samples:
    key = (row["scenario"], row["sample"])
    if key in seen:
        raise RuntimeError(f"Duplicate replay sample: {key}")
    seen.add(key)
    scenario_rows[row["scenario"]].append(row)

if len(scenario_rows) != 7:
    raise RuntimeError("Expected seven replay scenarios")

if any(len(rows) != 24 for rows in scenario_rows.values()):
    raise RuntimeError("Expected 24 samples per scenario")

def optional_finite_number(text):
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None

decisions = []

for row in samples:
    lidar = row["lidar_used"].strip()
    radar = row["radar_status"].strip()
    camera = row["camera_status"].strip()

    lidar_action = action("LiDARReplay", lidar)
    radar_action = action("RadarReplay", radar)
    camera_action = action("CameraReplay", camera)

    lidar_available = lidar_action == "USE_IF_ELIGIBLE"
    radar_candidate = radar_action == "CANDIDATE_UPDATE"
    camera_experimental = (
        camera_action == "EXPERIMENTAL_CANDIDATE"
    )

    radar_excluded = radar_action == "EXCLUDE_UPDATE"
    camera_excluded = camera_action == "EXCLUDE_UPDATE"

    explicit_degradation = (
        radar_excluded or camera_excluded
    )

    reasons = []

    if not lidar_available:
        reasons.append("LIDAR_NOT_USED")

    if radar_excluded:
        reasons.append("RADAR_" + radar)

    if camera_excluded:
        reasons.append("CAMERA_" + camera)

    if radar_action == "NO_UPDATE":
        reasons.append("RADAR_NO_UPDATE")

    if camera_action == "NO_UPDATE":
        reasons.append("CAMERA_NO_UPDATE")

    if camera_experimental:
        reasons.append("CAMERA_EXPERIMENTAL_ONLY")

    if not lidar_available:
        mode = "HOLD_OR_ALERT"
        result_permission = "WITHHOLD_VALID_RESULT"
    elif explicit_degradation:
        mode = "DEGRADED_CANDIDATE"
        result_permission = "PROVISIONAL_ONLY"
    else:
        mode = "NORMAL_CANDIDATE"
        result_permission = "PROVISIONAL_ONLY"

    radar_nis = optional_finite_number(row["radar_nis"])
    camera_nis = optional_finite_number(row["camera_nis"])

    decisions.append({
        "scenario": row["scenario"],
        "sample": row["sample"],
        "frame": row["frame"],
        "time_s": row["time_s"],
        "lidar_used": lidar,
        "radar_status": radar,
        "camera_status": camera,
        "lidar_action": lidar_action,
        "radar_action": radar_action,
        "camera_action": camera_action,
        "radar_candidate": int(radar_candidate),
        "camera_experimental_candidate": int(camera_experimental),
        "radar_nis_finite": int(radar_nis is not None),
        "camera_nis_finite": int(camera_nis is not None),
        "controller_mode": mode,
        "result_permission": result_permission,
        "quality_authorization": "UNVERIFIED",
        "reason_codes": (
            "|".join(reasons) if reasons else "NO_EXPLICIT_FAULT"
        ),
    })

if len(decisions) != 168:
    raise RuntimeError("Incorrect decision count")

def write_csv(path, rows):
    if not rows:
        raise RuntimeError(f"No output rows: {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

summary = []

for scenario in sorted(scenario_rows):
    group = [
        r for r in decisions if r["scenario"] == scenario
    ]
    modes = Counter(r["controller_mode"] for r in group)

    summary.append({
        "scenario": scenario,
        "samples": len(group),
        "normal_candidate": modes["NORMAL_CANDIDATE"],
        "degraded_candidate": modes["DEGRADED_CANDIDATE"],
        "hold_or_alert": modes["HOLD_OR_ALERT"],
        "lidar_unavailable": sum(
            r["lidar_used"] == "0" for r in group
        ),
        "radar_excluded": sum(
            r["radar_action"] == "EXCLUDE_UPDATE"
            for r in group
        ),
        "camera_excluded": sum(
            r["camera_action"] == "EXCLUDE_UPDATE"
            for r in group
        ),
        "quality_authorization": "UNVERIFIED",
    })

if len(summary) != 7:
    raise RuntimeError("Incorrect scenario summary count")

if sum(r["hold_or_alert"] for r in summary) != 9:
    raise RuntimeError("Unexpected LiDAR fallback count")

if any(
    r["normal_candidate"] + r["degraded_candidate"]
    + r["hold_or_alert"] != 24
    for r in summary
):
    raise RuntimeError("Scenario mode totals do not match")

write_csv(OUTPUT, decisions)
write_csv(SUMMARY, summary)

if len(load_csv(OUTPUT)) != 168:
    raise RuntimeError("Decision output verification failed")

if len(load_csv(SUMMARY)) != 7:
    raise RuntimeError("Summary output verification failed")

total = Counter(r["controller_mode"] for r in decisions)

print("\n=== TASK 25.7D FALLBACK CONTROLLER ===")
print("POLICY_RULES_VERIFIED:", len(rules))
print("SCENARIOS_PROCESSED:", len(summary))
print("REPLAY_SAMPLES_PROCESSED:", len(decisions))
print("NORMAL_CANDIDATE:", total["NORMAL_CANDIDATE"])
print("DEGRADED_CANDIDATE:", total["DEGRADED_CANDIDATE"])
print("HOLD_OR_ALERT:", total["HOLD_OR_ALERT"])
print("QUALITY_AUTHORIZATION: UNVERIFIED")
print("ENERGY_SAVINGS_CLAIMED: NO")
print("\nSCENARIO BREAKDOWN:")

for row in summary:
    print(
        row["scenario"],
        "NORMAL=", row["normal_candidate"],
        "DEGRADED=", row["degraded_candidate"],
        "HOLD=", row["hold_or_alert"],
    )

print("\nTASK25_07D_FALLBACK_CONTROLLER_PASS")
print("Decisions:", OUTPUT)
print("Summary:", SUMMARY)
