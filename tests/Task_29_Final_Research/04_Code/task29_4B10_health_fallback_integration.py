import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
T25 = ROOT / "tests" / "Task_25_Final_Research"
T29 = ROOT / "tests" / "Task_29_Final_Research"

POLICY = T25 / "02_CSV_Data" / "task25_64_fallback_policy_rules.csv"
REPLAY = T25 / "02_CSV_Data" / "task25_replay_samples.csv"
REFERENCE = T25 / "02_CSV_Data" / "task25_65_fallback_decisions.csv"

OUTPUT = T29 / "02_CSV_Data" / "task29_4B10_scheduler_health_states.csv"
REPORT = T29 / "06_Research_Findings" / "task29_4B10_health_fallback_report.json"

def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError("Existing Task 29 output preserved")

    rules = read_csv(POLICY)
    replay = read_csv(REPLAY)
    archived = read_csv(REFERENCE)

    if (len(rules), len(replay), len(archived)) != (21, 168, 168):
        raise RuntimeError("Unexpected Task 25 evidence counts")

    mapping = {}
    for row in rules:
        key = (row["Domain"], row["ObservedStatus"])
        if key in mapping:
            raise RuntimeError("Duplicate policy mapping")
        mapping[key] = row["Action"]

    reference = {}
    for row in archived:
        key = (row["scenario"], row["sample"])
        if key in reference:
            raise RuntimeError("Duplicate archived decision")
        reference[key] = row

    output = []

    for row in replay:
        key = (row["scenario"], row["sample"])
        if key not in reference:
            raise RuntimeError(f"Missing archived decision: {key}")

        lidar = row["lidar_used"].strip()
        radar = row["radar_status"].strip()
        camera = row["camera_status"].strip()

        def action(domain, status):
            key2 = (domain, status)
            if key2 not in mapping:
                raise RuntimeError(f"Unmapped sensor status: {key2}")
            return mapping[key2]

        la = action("LiDARReplay", lidar)
        ra = action("RadarReplay", radar)
        ca = action("CameraReplay", camera)

        lidar_available = la == "USE_IF_ELIGIBLE"
        radar_excluded = ra == "EXCLUDE_UPDATE"
        camera_excluded = ca == "EXCLUDE_UPDATE"

        reasons = []
        if not lidar_available:
            reasons.append("LIDAR_NOT_USED")
        if radar_excluded:
            reasons.append("RADAR_" + radar)
        if camera_excluded:
            reasons.append("CAMERA_" + camera)
        if ra == "NO_UPDATE":
            reasons.append("RADAR_NO_UPDATE")
        if ca == "NO_UPDATE":
            reasons.append("CAMERA_NO_UPDATE")
        if ca == "EXPERIMENTAL_CANDIDATE":
            reasons.append("CAMERA_EXPERIMENTAL_ONLY")

        if not lidar_available:
            mode = "HOLD_OR_ALERT"
            permission = "WITHHOLD_VALID_RESULT"
        elif radar_excluded or camera_excluded:
            mode = "DEGRADED_CANDIDATE"
            permission = "PROVISIONAL_ONLY"
        else:
            mode = "NORMAL_CANDIDATE"
            permission = "PROVISIONAL_ONLY"

        reason_codes = "|".join(reasons) if reasons else "NO_EXPLICIT_FAULT"

        old = reference[key]

        checks = {
            "frame": row["frame"],
            "time_s": row["time_s"],
            "lidar_action": la,
            "radar_action": ra,
            "camera_action": ca,
            "controller_mode": mode,
            "result_permission": permission,
            "reason_codes": reason_codes,
        }

        for field, value in checks.items():
            if str(old[field]) != str(value):
                raise AssertionError(
                    f"{key}, {field}: computed={value}, archived={old[field]}"
                )

        output.append({
            "scenario": row["scenario"],
            "sample": row["sample"],
            "frame": row["frame"],
            "time_s": row["time_s"],
            "lidar_status": lidar,
            "radar_status": radar,
            "camera_status": camera,
            "lidar_action": la,
            "radar_action": ra,
            "camera_action": ca,
            "controller_mode": mode,
            "result_permission": permission,
            "quality_authorization": "UNVERIFIED",
            "reason_codes": reason_codes,
            "scheduler_placement": "NOT_IMPLEMENTED",
            "processing_latency_ms": "",
            "sensor_timing_origin": "TASK25_TRACK2_REPLAY",
            "fpga_cost_source": "UNAVAILABLE",
        })

    if len(output) != 168:
        raise RuntimeError("Expected 168 health states")

    modes = Counter(x["controller_mode"] for x in output)

    if modes["HOLD_OR_ALERT"] != 9:
        raise RuntimeError("Archived fallback count mismatch")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)

    report = {
        "task": "29.4B.10",
        "status": "PASS",
        "policy_rules": len(rules),
        "health_state_rows": len(output),
        "archived_fallback_decisions_match": True,
        "modes": dict(modes),
        "quality_authorization": "UNVERIFIED",
        "cpu_latency_joined": False,
        "cpu_fpga_scheduler_implemented": False,
        "energy_measured": False,
        "source": "TASK25_ARCHIVED_REPLAY_AND_FALLBACK",
    }

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("POLICY_RULES:", len(rules))
    print("HEALTH_STATES:", len(output))

    for mode in (
        "NORMAL_CANDIDATE",
        "DEGRADED_CANDIDATE",
        "HOLD_OR_ALERT"
    ):
        print(mode + ":", modes[mode])

    print("ARCHIVED_FALLBACK_MATCH: PASS")
    print("QUALITY_AUTHORIZATION: UNVERIFIED")
    print("CPU_FPGA_SCHEDULER: NOT YET")
    print("TASK 29.4B.10: PASS")

if __name__ == "__main__":
    main()
