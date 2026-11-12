from pathlib import Path
from collections import Counter
import csv
import json
import math

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

BASE = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
)

DATA = BASE / "C02_V2_EKF_Input_53Frames_V1"

TASK26 = TESTS / "Task_26_Final_Research"

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_5B_sensor_alignment_audit.json"
)

FILES = {
    "selected": "selected_frames.csv",
    "lidar": "lidar_points.csv",
    "radar": "radar_returns.csv",
    "tracks": "lidar_temporal_tracks_v1.csv",
    "ekf": "lidar_radar_camera_ekf_track2_v1.csv",
}

CAMERA_FRAMES = {
    0: "clean_camera_01_frame00000.png",
    530: "clean_camera_02_frame00530.png",
    1060: "clean_camera_03_frame01060.png",
    1591: "clean_camera_04_frame01591.png",
    2121: "clean_camera_05_frame02121.png",
}

TOLERANCE_S = 1e-6

def read_csv(name):
    path = DATA / FILES[name]
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(newline="", encoding="utf-8-sig") as stream:
        yield from csv.DictReader(stream)

def main():
    if REPORT.exists():
        raise FileExistsError(
            f"Existing audit report preserved: {REPORT}"
        )

    selected = {}
    for row in read_csv("selected"):
        frame = int(row["frame"])
        if frame in selected:
            raise RuntimeError("Duplicate selected frame")
        selected[frame] = float(row["time_s"])

    if len(selected) != 53:
        raise RuntimeError("Expected 53 selected frames")

    counts = {}
    mismatches = {}
    frames_seen = {}

    for name in ("lidar", "radar", "tracks", "ekf"):
        count = Counter()
        mismatch_count = 0
        unknown_frame_count = 0

        for row in read_csv(name):
            frame = int(row["frame"])
            count[frame] += 1

            if frame not in selected:
                unknown_frame_count += 1
                continue

            actual_time = float(row["time_s"])
            expected_time = selected[frame]

            if (
                not math.isfinite(actual_time)
                or abs(actual_time - expected_time) > TOLERANCE_S
            ):
                mismatch_count += 1

        counts[name] = sum(count.values())
        mismatches[name] = {
            "timestamp_mismatches": mismatch_count,
            "unknown_frame_rows": unknown_frame_count,
        }
        frames_seen[name] = set(count)

    camera_dir = BASE / "Camera_NoVisualizer_V2_2122"

    camera_found = {
        frame for frame, filename in CAMERA_FRAMES.items()
        if (camera_dir / filename).is_file()
    }

    selected_frames = set(selected)

    common_lidar_radar = (
        selected_frames
        & frames_seen["lidar"]
        & frames_seen["radar"]
    )

    common_all_available = (
        common_lidar_radar
        & frames_seen["tracks"]
        & frames_seen["ekf"]
        & camera_found
    )

    print("=== TASK 26.5B SENSOR ALIGNMENT AUDIT ===")

    print("SELECTED_FRAMES:", len(selected))

    for name in ("lidar", "radar", "tracks", "ekf"):
        print(f"{name.upper()}_ROWS:", counts[name])
        print(
            f"{name.upper()}_UNIQUE_FRAMES:",
            len(frames_seen[name])
        )
        print(
            f"{name.upper()}_TIMESTAMP_MISMATCHES:",
            mismatches[name]["timestamp_mismatches"]
        )
        print(
            f"{name.upper()}_UNKNOWN_FRAME_ROWS:",
            mismatches[name]["unknown_frame_rows"]
        )

    print("DECODED_CAMERA_FRAMES:", len(camera_found))

    print(
        "COMMON_LIDAR_RADAR_FRAMES:",
        len(common_lidar_radar)
    )

    print(
        "COMMON_ALL_AVAILABLE_FRAMES:",
        len(common_all_available)
    )

    print(
        "COMMON_ALL_FRAME_IDS:",
        sorted(common_all_available)
    )

    report = {
        "task": "26.5B",
        "timestamp_tolerance_seconds": TOLERANCE_S,
        "selected_frames": len(selected),
        "row_counts": counts,
        "alignment_findings": mismatches,
        "unique_frame_counts": {
            key: len(value)
            for key, value in frames_seen.items()
        },
        "decoded_camera_frames": sorted(camera_found),
        "common_lidar_radar_frames":
            sorted(common_lidar_radar),
        "common_all_available_frames":
            sorted(common_all_available),
        "note": (
            "Frame and timestamp agreement alone does not "
            "prove sensor calibration, successful association, "
            "fusion accuracy or an executable live pipeline."
        ),
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with REPORT.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)

    print("INPUT_FILES_MODIFIED: NO")
    print("TASK26_5B_SENSOR_ALIGNMENT_AUDIT_DONE")
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
