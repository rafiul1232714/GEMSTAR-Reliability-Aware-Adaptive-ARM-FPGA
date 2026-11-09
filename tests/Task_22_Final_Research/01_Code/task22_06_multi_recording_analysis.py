import csv
import json
import sys
import statistics
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_22_Final_Research"
sys.path.insert(0, str(TASK / "01_Code"))

from task22_02_reusable_osi_reader import (
    iter_osi_messages, timestamp_ns,
    SensorView, GroundTruth
)

SOURCE = TASK / "02_CSV_Data" / "task22_04b_deduplicated_pair_summary.csv"
CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

LIMIT = 100

def load_messages(path, message_type):
    return {
        frame: msg
        for frame, msg, size in iter_osi_messages(
            path, message_type, LIMIT
        )
    }

def median_or_none(values):
    return statistics.median(values) if values else None

def save_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

print("\n=== TASK 22.6 MULTI-RECORDING ANALYSIS ===")

with SOURCE.open(newline="", encoding="utf-8-sig") as f:
    pairs = list(csv.DictReader(f))

print("Unique recording pairs:", len(pairs))

frame_rows = []
summaries = []
errors = []

for pair in pairs:
    pair_id = pair["PairID"]
    directory = Path(pair["ScenarioFolder"])
    sv_path = directory / pair["SensorViewFilename"]
    gt_path = directory / pair["GroundTruthFilename"]

    print(f"\n=== PAIR {pair_id} ===")
    print("SensorView:", sv_path.name)

    try:
        sv_data = load_messages(sv_path, SensorView)
        gt_data = load_messages(gt_path, GroundTruth)

        timestamps = []
        pair_rows = []

        for frame, sv in sorted(sv_data.items()):
            gt = gt_data.get(frame)
            sv_ns = timestamp_ns(sv)
            gt_ns = timestamp_ns(gt) if gt is not None else None

            cameras = list(sv.camera_sensor_view)
            lidars = list(sv.lidar_sensor_view)
            radars = list(sv.radar_sensor_view)

            image_bytes = sum(
                len(cam.image_data) for cam in cameras
            )

            lidar_returns = sum(
                len(lidar.reflection) for lidar in lidars
            )

            radar_returns = sum(
                len(radar.reflection) for radar in radars
            )

            positive_radar = sum(
                1
                for radar in radars
                for reflection in radar.reflection
                if reflection.time_of_flight > 0
                and reflection.signal_strength > 0
            )

            timestamps.append(sv_ns)

            row = {
                "PairID": pair_id,
                "Frame": frame,
                "SVTimestampNs": sv_ns,
                "GTTimestampNs": gt_ns if gt_ns is not None else "",
                "TimestampMatch": (
                    gt_ns == sv_ns
                    if gt_ns is not None else False
                ),
                "CameraEntries": len(cameras),
                "LiDAREntries": len(lidars),
                "RadarEntries": len(radars),
                "CameraImageBytes": image_bytes,
                "LiDARReflectionCount": lidar_returns,
                "RadarReflectionCount": radar_returns,
                "PositiveRadarReturns": positive_radar,
                "GTMovingObjects": (
                    len(gt.moving_object)
                    if gt is not None else ""
                )
            }

            pair_rows.append(row)
            frame_rows.append(row)

        intervals_ms = [
            (timestamps[i] - timestamps[i - 1]) / 1e6
            for i in range(1, len(timestamps))
        ]

        summary = {
            "PairID": pair_id,
            "Recording": sv_path.name,
            "Frames": len(pair_rows),
            "CameraEntryFrames": sum(
                r["CameraEntries"] > 0 for r in pair_rows
            ),
            "CameraImageDataFrames": sum(
                r["CameraImageBytes"] > 0 for r in pair_rows
            ),
            "LiDAREntryFrames": sum(
                r["LiDAREntries"] > 0 for r in pair_rows
            ),
            "LiDARReflectionFrames": sum(
                r["LiDARReflectionCount"] > 0
                for r in pair_rows
            ),
            "RadarEntryFrames": sum(
                r["RadarEntries"] > 0 for r in pair_rows
            ),
            "PositiveRadarFrames": sum(
                r["PositiveRadarReturns"] > 0
                for r in pair_rows
            ),
            "TotalLiDARReflections": sum(
                r["LiDARReflectionCount"] for r in pair_rows
            ),
            "TotalPositiveRadarReturns": sum(
                r["PositiveRadarReturns"] for r in pair_rows
            ),
            "TimestampMatches": sum(
                r["TimestampMatch"] for r in pair_rows
            ),
            "MedianMessageIntervalMs": median_or_none(
                intervals_ms
            ),
            "MaxMessageIntervalMs": (
                max(intervals_ms) if intervals_ms else None
            ),
            "MedianGTMovingObjects": median_or_none([
                r["GTMovingObjects"] for r in pair_rows
                if r["GTMovingObjects"] != ""
            ])
        }

        summaries.append(summary)

        print("Frames:", summary["Frames"])
        print(
            "Camera image-data frames:",
            summary["CameraImageDataFrames"]
        )
        print(
            "LiDAR reflection frames:",
            summary["LiDARReflectionFrames"]
        )
        print(
            "Positive radar frames:",
            summary["PositiveRadarFrames"]
        )
        print(
            "Timestamp matches:",
            summary["TimestampMatches"]
        )
        print(
            "Median message interval (ms):",
            summary["MedianMessageIntervalMs"]
        )

    except Exception as exc:
        error = f"Pair {pair_id}: {type(exc).__name__}: {exc}"
        errors.append(error)
        print("ERROR:", error)

frame_csv = CSV_DIR / "task22_06_frame_metrics.csv"
summary_csv = CSV_DIR / "task22_06_recording_comparison.csv"

frame_columns = [
    "PairID", "Frame", "SVTimestampNs", "GTTimestampNs",
    "TimestampMatch", "CameraEntries", "LiDAREntries",
    "RadarEntries", "CameraImageBytes",
    "LiDARReflectionCount", "RadarReflectionCount",
    "PositiveRadarReturns", "GTMovingObjects"
]

summary_columns = [
    "PairID", "Recording", "Frames",
    "CameraEntryFrames", "CameraImageDataFrames",
    "LiDAREntryFrames", "LiDARReflectionFrames",
    "RadarEntryFrames", "PositiveRadarFrames",
    "TotalLiDARReflections", "TotalPositiveRadarReturns",
    "TimestampMatches", "MedianMessageIntervalMs",
    "MaxMessageIntervalMs", "MedianGTMovingObjects"
]

save_csv(frame_csv, frame_rows, frame_columns)
save_csv(summary_csv, summaries, summary_columns)

graph_paths = []

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if summaries:
        labels = [f"Pair {s['PairID']}" for s in summaries]
        x = np.arange(len(labels))
        width = 0.24

        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.bar(
            x - width,
            [s["CameraImageDataFrames"] for s in summaries],
            width, label="Camera image data"
        )
        ax.bar(
            x,
            [s["LiDARReflectionFrames"] for s in summaries],
            width, label="LiDAR reflections"
        )
        ax.bar(
            x + width,
            [s["PositiveRadarFrames"] for s in summaries],
            width, label="Positive radar returns"
        )

        ax.set_xticks(x, labels)
        ax.set_ylabel("Frames with populated data")
        ax.set_title(
            "Task 22.6 - Multi-recording sensor data coverage"
        )
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        fig.tight_layout()
        path = GRAPH_DIR / "task22_06_sensor_coverage.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        graph_paths.append(str(path))

        fig, ax = plt.subplots(figsize=(9, 5))
        values = [
            s["MedianMessageIntervalMs"] or 0
            for s in summaries
        ]

        ax.bar(labels, values)
        ax.set_ylabel("Median recorded-message interval (ms)")
        ax.set_title(
            "Task 22.6 - Recorded-message timing comparison"
        )
        ax.grid(axis="y", alpha=0.3)

        fig.tight_layout()
        path = GRAPH_DIR / "task22_06_message_timing.png"
        fig.savefig(path, dpi=180)
        plt.close(fig)
        graph_paths.append(str(path))

except ImportError as exc:
    print("Graph generation unavailable:", exc)

report = {
    "Task": "22.6",
    "RecordingPairsRequested": len(pairs),
    "RecordingPairsProcessed": len(summaries),
    "FramesProcessed": len(frame_rows),
    "Errors": errors,
    "Summaries": summaries,
    "GraphsCreated": graph_paths,
    "ScientificLimitations": [
        "First 100 frames only",
        "Image bytes present does not prove valid image decoding",
        "LiDAR reflection count does not establish geometric accuracy",
        "Positive radar returns do not establish object detection",
        "Recorded-message intervals are not CPU or FPGA latency",
        "Folder names do not establish verified scenario conditions",
        "No energy or perception accuracy measurement"
    ]
}

json_path = FINDINGS / "task22_06_analysis_findings.json"
json_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 22.6 FINAL SUMMARY ===")
print("Unique pairs requested:", len(pairs))
print("Pairs processed:", len(summaries))
print("Frames processed:", len(frame_rows))
print("Processing errors:", len(errors))
print("Frame CSV saved:", frame_csv.is_file())
print("Comparison CSV saved:", summary_csv.is_file())
print("Graphs created:", len(graph_paths))
print("Findings JSON saved:", json_path.is_file())
print("\n=== TASK 22.6 COMPLETE ===")
