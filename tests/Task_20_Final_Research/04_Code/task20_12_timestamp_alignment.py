import csv
import json
import struct
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

MAX_FRAMES = 100

def read_frames(path, message_type):
    with path.open("rb") as f:
        for index in range(MAX_FRAMES):
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size < 100_000_000:
                raise ValueError("Invalid message size")

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Truncated OSI message")

            msg = message_type()
            msg.ParseFromString(payload)

            timestamp = msg.timestamp

            # Integer nanoseconds avoid floating-point
            # subtraction errors.
            timestamp_ns = (
                int(timestamp.seconds) * 1_000_000_000
                + int(timestamp.nanos)
            )

            yield {
                "FrameIndex": index,
                "TimestampNs": timestamp_ns,
                "Message": msg,
            }

def save_csv(path, rows):
    if not rows:
        return False

    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    return path.is_file()

def main():
    print("\n=== TASK 20.12 TIMESTAMP ALIGNMENT ===")

    gt_files = sorted(RAW.rglob("*_gt_*.osi"))
    sv_files = sorted(RAW.rglob("*_sv_*.osi"))

    by_scenario = {}

    for path in gt_files:
        by_scenario.setdefault(
            path.parent.name, {}
        ).setdefault("GT", []).append(path)

    for path in sv_files:
        by_scenario.setdefault(
            path.parent.name, {}
        ).setdefault("SV", []).append(path)

    rows = []
    summaries = []

    for scenario, group in sorted(
        by_scenario.items()
    ):
        gt_paths = group.get("GT", [])
        sv_paths = group.get("SV", [])

        # Avoid arbitrarily choosing from multiple
        # candidate files.
        if len(gt_paths) != 1 or len(sv_paths) != 1:
            print(
                f"{scenario:28s} | SKIPPED "
                f"GT={len(gt_paths)} SV={len(sv_paths)}"
            )
            continue

        gt = list(read_frames(
            gt_paths[0], GroundTruth
        ))

        sv = list(read_frames(
            sv_paths[0], SensorView
        ))

        gt_by_time = {}

        for frame in gt:
            gt_by_time.setdefault(
                frame["TimestampNs"], []
            ).append(frame)

        matched = 0
        unmatched = 0
        ambiguous = 0

        for radar_frame in sv:
            ts = radar_frame["TimestampNs"]
            candidates = gt_by_time.get(ts, [])

            if len(candidates) == 1:
                gt_frame = candidates[0]
                status = "MATCHED"
                matched += 1

            elif len(candidates) == 0:
                gt_frame = None
                status = "UNMATCHED"
                unmatched += 1

            else:
                gt_frame = None
                status = "AMBIGUOUS"
                ambiguous += 1

            rows.append({
                "Recording": scenario,
                "RadarFrameIndex":
                    radar_frame["FrameIndex"],
                "RadarTimestampNs": ts,
                "GroundTruthFrameIndex": (
                    gt_frame["FrameIndex"]
                    if gt_frame else ""
                ),
                "GroundTruthTimestampNs": (
                    gt_frame["TimestampNs"]
                    if gt_frame else ""
                ),
                "MatchStatus": status,
                "RadarViews": len(
                    radar_frame["Message"].radar_sensor_view
                ),
                "MovingObjects": (
                    len(gt_frame["Message"].moving_object)
                    if gt_frame else ""
                ),
                "StationaryObjects": (
                    len(gt_frame["Message"].stationary_object)
                    if gt_frame else ""
                ),
            })

        summary = {
            "Recording": scenario,
            "RadarFramesChecked": len(sv),
            "GTFramesChecked": len(gt),
            "Matched": matched,
            "Unmatched": unmatched,
            "Ambiguous": ambiguous,
            "ExactMatchPercent": (
                100 * matched / len(sv)
                if sv else 0
            ),
        }

        summaries.append(summary)

        print(
            f"{scenario:28s}"
            f" | Radar={len(sv):3d}"
            f" | GT={len(gt):3d}"
            f" | Matched={matched:3d}"
            f" | Unmatched={unmatched:3d}"
            f" | Ambiguous={ambiguous:3d}"
            f" | Exact={summary['ExactMatchPercent']:.1f}%"
        )

    match_file = (
        DATA / "task20_12_timestamp_matches.csv"
    )

    summary_file = (
        DATA / "task20_12_timestamp_summary.csv"
    )

    save_csv(match_file, rows)
    save_csv(summary_file, summaries)

    report = {
        "Task": "20.12",
        "CheckedPairs": len(summaries),
        "TotalMatchedFrames": sum(
            x["Matched"] for x in summaries
        ),
        "TotalUnmatchedFrames": sum(
            x["Unmatched"] for x in summaries
        ),
        "TotalAmbiguousFrames": sum(
            x["Ambiguous"] for x in summaries
        ),
        "AllCheckedRadarFramesMatched": bool(
            summaries
        ) and all(
            x["Matched"] == x["RadarFramesChecked"]
            and x["Ambiguous"] == 0
            for x in summaries
        ),
        "RadarToObjectAssociationVerified": False,
        "GroundTruthAccuracyMeasured": False,
        "EnergyMeasured": False,
    }

    report_path = (
        FINDINGS / "task20_12_timestamp_validation.json"
    )

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print("\n=== TASK 20.12 COMPLETE ===")
    print("Recording pairs checked:", len(summaries))
    print("Matched frames:", report["TotalMatchedFrames"])
    print("Unmatched frames:", report["TotalUnmatchedFrames"])
    print("Ambiguous frames:", report["TotalAmbiguousFrames"])
    print(
        "All checked frames matched:",
        report["AllCheckedRadarFramesMatched"]
    )
    print("Match CSV saved:", match_file.is_file())
    print("Summary CSV saved:", summary_file.is_file())
    print("JSON saved:", report_path.is_file())

    print("\nLIMITATIONS:")
    print("Only the first 100 frames per file checked.")
    print("Exact timestamp equality does not itself")
    print("prove sensor accuracy or object association.")
    print("No energy measurement yet.")

if __name__ == "__main__":
    main()
