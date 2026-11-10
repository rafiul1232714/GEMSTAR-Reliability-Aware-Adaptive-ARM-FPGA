import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_25_Final_Research")
DATA = ROOT / "02_CSV_Data"

def read(name):
    with (DATA / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

replay = read("task25_replay_samples.csv")
decisions = read("task25_65_fallback_decisions.csv")
summary = read("task25_66_fallback_scenario_summary.csv")
policy = read("task25_64_fallback_policy_rules.csv")

assert len(replay) == len(decisions) == 168
assert len(summary) == 7
assert len(policy) == 21

lookup = {}
for rule in policy:
    key = (rule["Domain"], rule["ObservedStatus"])
    assert key not in lookup, f"Duplicate policy: {key}"
    lookup[key] = rule["Action"]

def expected_action(domain, value):
    return lookup[(domain, str(value).strip())]

original = {}
for row in replay:
    key = (row["scenario"], row["sample"])
    assert key not in original, f"Duplicate replay key: {key}"
    original[key] = row

checks = Counter()
observed = defaultdict(Counter)
issues = []

for decision in decisions:
    key = (decision["scenario"], decision["sample"])

    if key not in original:
        issues.append(f"Unknown decision key: {key}")
        continue

    source = original[key]

    for field in ("frame", "time_s", "lidar_used",
                  "radar_status", "camera_status"):
        if decision[field] != source[field]:
            issues.append(f"{key}: {field} mismatch")

    expected_actions = {
        "lidar_action": expected_action(
            "LiDARReplay", source["lidar_used"]
        ),
        "radar_action": expected_action(
            "RadarReplay", source["radar_status"]
        ),
        "camera_action": expected_action(
            "CameraReplay", source["camera_status"]
        ),
    }

    for field, expected in expected_actions.items():
        if decision[field] != expected:
            issues.append(f"{key}: incorrect {field}")
        else:
            checks["ACTION_MATCH"] += 1

    lidar_used = source["lidar_used"] == "1"
    degraded = (
        expected_actions["radar_action"] == "EXCLUDE_UPDATE"
        or expected_actions["camera_action"] == "EXCLUDE_UPDATE"
    )

    if not lidar_used:
        mode = "HOLD_OR_ALERT"
        permission = "WITHHOLD_VALID_RESULT"
    elif degraded:
        mode = "DEGRADED_CANDIDATE"
        permission = "PROVISIONAL_ONLY"
    else:
        mode = "NORMAL_CANDIDATE"
        permission = "PROVISIONAL_ONLY"

    if decision["controller_mode"] != mode:
        issues.append(f"{key}: wrong controller mode")
    else:
        checks["MODE_MATCH"] += 1

    if decision["result_permission"] != permission:
        issues.append(f"{key}: wrong output permission")
    else:
        checks["PERMISSION_MATCH"] += 1

    if decision["quality_authorization"] != "UNVERIFIED":
        issues.append(f"{key}: invalid quality authorization")
    else:
        checks["UNVERIFIED_CONFIRMED"] += 1

    observed[source["scenario"]][mode] += 1

summary_lookup = {r["scenario"]: r for r in summary}

if len(summary_lookup) != 7:
    issues.append("Duplicate scenario summary")

for scenario, counts in observed.items():
    if scenario not in summary_lookup:
        issues.append(f"Missing summary: {scenario}")
        continue

    row = summary_lookup[scenario]
    names = {
        "NORMAL_CANDIDATE": "normal_candidate",
        "DEGRADED_CANDIDATE": "degraded_candidate",
        "HOLD_OR_ALERT": "hold_or_alert",
    }
    for mode, column in names.items():
        if int(row[column]) != counts[mode]:
            issues.append(f"{scenario}: {column} mismatch")
        else:
            checks["SUMMARY_MATCH"] += 1

total = Counter(r["controller_mode"] for r in decisions)

if total != Counter({
    "NORMAL_CANDIDATE": 143,
    "DEGRADED_CANDIDATE": 16,
    "HOLD_OR_ALERT": 9
}):
    issues.append(f"Unexpected overall decisions: {dict(total)}")

audit = DATA / "task25_67_fallback_decision_audit.csv"
with audit.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Check", "Count"])
    for name, value in sorted(checks.items()):
        writer.writerow([name, value])
    writer.writerow(["ISSUE_COUNT", len(issues)])

print("\n=== TASK 25.7E FALLBACK DECISION AUDIT ===")
print("REPLAY_ROWS:", len(replay))
print("DECISION_ROWS:", len(decisions))
print("ACTION_MATCHES:", checks["ACTION_MATCH"])
print("MODE_MATCHES:", checks["MODE_MATCH"])
print("PERMISSION_MATCHES:", checks["PERMISSION_MATCH"])
print("QUALITY_FLAGS_VERIFIED:", checks["UNVERIFIED_CONFIRMED"])
print("SUMMARY_CHECKS:", checks["SUMMARY_MATCH"])
print("AUDIT_ISSUES:", len(issues))

if issues:
    for item in issues[:20]:
        print("ISSUE:", item)
    raise SystemExit("TASK25_07E_AUDIT_FAIL")

print("TASK25_07E_FALLBACK_AUDIT_PASS")
print("Saved:", audit)
