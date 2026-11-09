import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView, GroundTruth
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)
CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

CSV_DIR.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

FRAMES = (24, 25, 26, 98, 99)
TARGET_FRAMES = (25, 99)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def timestamp_ns(message):
    """Read a populated OSI protobuf timestamp, if present."""
    if message is None or not hasattr(message, "DESCRIPTOR"):
        return None

    if "timestamp" not in message.DESCRIPTOR.fields_by_name:
        return None

    # Avoid treating an absent protobuf message as timestamp zero.
    present = {
        descriptor.name for descriptor, _ in message.ListFields()
    }

    if "timestamp" not in present:
        return None

    ts = message.timestamp

    if not hasattr(ts, "seconds") or not hasattr(ts, "nanos"):
        return None

    return (
        int(ts.seconds) * 1_000_000_000 +
        int(ts.nanos)
    )


def extract_frames(path, cls):
    return {
        frame: msg
        for frame, msg, _ in iter_osi_messages(
            Path(path), cls, 100
        )
        if frame in FRAMES
    }


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


manifest = {
    int(r["PairID"]): r
    for r in read_csv(MANIFEST)
}

rows = []

print("\n=== TASK 23.5D-2 TIMESTAMP AUDIT ===")

for pair in (1, 2, 3):
    entry = manifest[pair]

    sv_frames = extract_frames(
        entry["SensorViewPath"], SensorView
    )
    gt_frames = extract_frames(
        entry["GroundTruthPath"], GroundTruth
    )

    for frame in FRAMES:
        if frame not in sv_frames or frame not in gt_frames:
            raise RuntimeError(
                f"Missing paired frame: Pair {pair}, Frame {frame}"
            )

        sv = sv_frames[frame]
        gt = gt_frames[frame]

        radar_count = len(sv.radar_sensor_view)
        lidar_count = len(sv.lidar_sensor_view)

        if radar_count != 1 or lidar_count != 1:
            raise RuntimeError(
                f"Unexpected sensor entries P{pair}/F{frame}: "
                f"Radar={radar_count}, LiDAR={lidar_count}"
            )

        sv_ns = timestamp_ns(sv)
        gt_ns = timestamp_ns(gt)

        radar_ns = timestamp_ns(sv.radar_sensor_view[0])
        lidar_ns = timestamp_ns(sv.lidar_sensor_view[0])

        delta_ms = (
            (sv_ns - gt_ns) / 1e6
            if sv_ns is not None and gt_ns is not None
            else None
        )

        sensor_delta_ms = (
            (radar_ns - lidar_ns) / 1e6
            if radar_ns is not None and lidar_ns is not None
            else None
        )

        rows.append({
            "PairID": pair,
            "Frame": frame,
            "TargetFrame": frame in TARGET_FRAMES,
            "RadarEntries": radar_count,
            "LiDAREntries": lidar_count,
            "SensorViewTimestampNs": sv_ns,
            "GroundTruthTimestampNs": gt_ns,
            "RadarOwnTimestampNs": radar_ns,
            "LiDAROwnTimestampNs": lidar_ns,
            "SensorViewGroundTruthDeltaMs": delta_ms,
            "RadarLiDAROwnDeltaMs": sensor_delta_ms,
            "SharedSensorViewContainer": True,
            "IndependentSensorTimingVerified": (
                sensor_delta_ms is not None
            ),
        })

        print(
            f"Pair {pair} | Frame {frame:02d} | "
            f"SV={sv_ns} | GT={gt_ns} | "
            f"SV-GT={delta_ms} ms | "
            f"RadarOwn={radar_ns} | LiDAROwn={lidar_ns}"
        )


# Examine progression using the SensorView timestamps.
progression = []

for pair in (1, 2, 3):
    pair_rows = sorted(
        [r for r in rows if r["PairID"] == pair],
        key=lambda r: r["Frame"]
    )

    for left, right in zip(pair_rows[:-1], pair_rows[1:]):
        # Only evaluate adjacent frame numbers.
        if right["Frame"] - left["Frame"] != 1:
            continue

        a = left["SensorViewTimestampNs"]
        b = right["SensorViewTimestampNs"]

        delta_ms = (
            (b - a) / 1e6
            if a is not None and b is not None
            else None
        )

        progression.append({
            "PairID": pair,
            "FromFrame": left["Frame"],
            "ToFrame": right["Frame"],
            "TimestampStepMs": delta_ms,
            "StrictlyIncreasing": (
                delta_ms > 0 if delta_ms is not None else None
            ),
        })


csv_path = CSV_DIR / (
    "task23_05d2_radar_lidar_timestamps.csv"
)

progression_path = CSV_DIR / (
    "task23_05d2_timestamp_progression.csv"
)

write_csv(csv_path, rows)
write_csv(progression_path, progression)

target = [
    r for r in rows if r["TargetFrame"]
]

paired_deltas = [
    r["SensorViewGroundTruthDeltaMs"]
    for r in target
    if r["SensorViewGroundTruthDeltaMs"] is not None
]

own_deltas = [
    r["RadarLiDAROwnDeltaMs"]
    for r in target
    if r["RadarLiDAROwnDeltaMs"] is not None
]

findings = {
    "Task": "23.5D-2",
    "Status": "RECORDED_TIMESTAMP_AUDIT",
    "RecordingPairs": 3,
    "FramesInspected": len(rows),
    "TargetFrameComparisons": len(target),
    "TargetFramesWithSVGTDelta": len(paired_deltas),
    "TargetFramesWithIndependentSensorDelta": len(own_deltas),
    "AllAvailableSVGTTimestampsEqual": (
        all(abs(v) < 1e-9 for v in paired_deltas)
        if paired_deltas else None
    ),
    "TimestampProgression": progression,
    "Interpretation": (
        "Radar and LiDAR are contained in the same "
        "SensorView message. Container timestamps alone "
        "do not establish identical physical acquisition times."
    ),
    "Limitations": [
        "Same frame index is not independent synchronization proof",
        "Sensor-level timestamps may be unavailable",
        "OSI timestamp equality does not rule out sensor latency",
        "No measurement of real-time end-to-end delay",
        "Sensor fusion accuracy remains unverified"
    ]
}

json_path = FINDINGS / (
    "task23_05d2_timestamp_findings.json"
)

json_path.write_text(
    json.dumps(findings, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.5D-2 FINAL VERIFICATION ===")
print("Frames inspected:", len(rows))
print("Target frame comparisons:", len(target))
print(
    "Available SV-GT target timestamp comparisons:",
    len(paired_deltas)
)
print(
    "Available independent Radar-LiDAR comparisons:",
    len(own_deltas)
)
print(
    "All available SV-GT timestamps equal:",
    findings["AllAvailableSVGTTimestampsEqual"]
)
print("Timestamp CSV saved:", csv_path.is_file())
print("Progression CSV saved:", progression_path.is_file())
print("Findings JSON saved:", json_path.is_file())

if len(rows) != 15 or len(target) != 6:
    raise RuntimeError("Unexpected frame audit count")

print("\n=== TASK 23.5D-2 COMPLETE ===")
