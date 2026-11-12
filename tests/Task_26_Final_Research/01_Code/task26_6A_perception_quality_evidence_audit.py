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

SUMMARY = (
    TASK26 / "02_CSV_Data"
    / "task26_6A_quality_evidence_summary.csv"
)

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_6A_quality_evidence_report.json"
)

FILES = {
    "selected": DATA / "selected_frames.csv",
    "lidar": DATA / "lidar_clustering_summary_v1.csv",
    "tracks": DATA / "lidar_temporal_tracks_v1.csv",
    "ekf": DATA / "lidar_radar_camera_ekf_track2_v1.csv",
    "camera": DATA / "camera_bearing_track2_frame530_v1.csv",
}

def load_csv(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def count_status(rows, column):
    return dict(Counter(r[column] for r in rows))

def as_int(row, field):
    return int(row[field])

def main():
    for path in (SUMMARY, REPORT):
        if path.exists():
            raise FileExistsError(
                f"Existing research output preserved: {path}"
            )

    data = {
        key: load_csv(path)
        for key, path in FILES.items()
    }

    selected = data["selected"]
    lidar = data["lidar"]
    tracks = data["tracks"]
    ekf = data["ekf"]
    camera = data["camera"]

    if (
        len(selected) != 53
        or len(lidar) != 53
        or len(ekf) != 24
        or len(camera) != 1
    ):
        raise RuntimeError("Unexpected archived dataset sizes")

    selected_by_frame = {
        as_int(r, "frame"): r
        for r in selected
    }

    lidar_by_frame = {
        as_int(r, "frame"): r
        for r in lidar
    }

    ekf_by_frame = {
        as_int(r, "frame"): r
        for r in ekf
    }

    if (
        len(selected_by_frame) != len(selected)
        or len(lidar_by_frame) != len(lidar)
        or len(ekf_by_frame) != len(ekf)
    ):
        raise RuntimeError("Duplicate frame IDs")

    if set(selected_by_frame) != set(lidar_by_frame):
        raise RuntimeError("LiDAR frame coverage mismatch")

    if not set(ekf_by_frame).issubset(selected_by_frame):
        raise RuntimeError("EKF has unknown frame IDs")

    for frame, row in lidar_by_frame.items():
        actual = float(row["time_s"])
        expected = float(selected_by_frame[frame]["time_s"])

        if (
            not math.isfinite(actual)
            or abs(actual - expected) > 1e-6
        ):
            raise RuntimeError(
                f"LiDAR timestamp mismatch: frame {frame}"
            )

    track_frames = {
        as_int(row, "frame")
        for row in tracks
    }

    camera_row = camera[0]
    camera_frame = as_int(camera_row, "frame")

    if camera_frame != 530 or camera_frame not in ekf_by_frame:
        raise RuntimeError("Unexpected Camera measurement frame")

    camera_authorized = (
        camera_row["ekf_update_authorized"]
        .strip().upper() == "YES"
    )

    archived_camera_status = (
        ekf_by_frame[camera_frame]["camera_status"]
    )

    experimental_update_without_authorization = (
        archived_camera_status == "EXPERIMENTAL_ACCEPTED"
        and not camera_authorized
    )

    gt_counts = count_status(
        ekf, "ground_truth_validated"
    )

    radar_counts = count_status(
        ekf, "radar_status"
    )

    camera_counts = count_status(
        ekf, "camera_status"
    )

    frames_with_clusters = sum(
        int(r["clusters_found"]) > 0
        for r in lidar
    )

    retained_point_total = sum(
        int(r["retained_cluster_points"])
        for r in lidar
    )

    summary_rows = [
        {
            "metric": "selected_frames",
            "value": len(selected),
            "interpretation": "recorded reference coverage",
        },
        {
            "metric": "lidar_clustered_frames",
            "value": len(lidar),
            "interpretation": "algorithm output coverage",
        },
        {
            "metric": "frames_with_lidar_clusters",
            "value": frames_with_clusters,
            "interpretation": "cluster presence; not detection accuracy",
        },
        {
            "metric": "total_retained_cluster_points",
            "value": retained_point_total,
            "interpretation": "recorded processing output",
        },
        {
            "metric": "frames_with_temporal_tracks",
            "value": len(track_frames),
            "interpretation": "tracking coverage",
        },
        {
            "metric": "archived_ekf_frames",
            "value": len(ekf),
            "interpretation": "fusion output coverage",
        },
        {
            "metric": "ground_truth_validated_ekf_rows",
            "value": sum(
                r["ground_truth_validated"].strip().upper()
                == "YES" for r in ekf
            ),
            "interpretation": "validated EKF evidence",
        },
        {
            "metric": "camera_updates_authorized",
            "value": int(camera_authorized),
            "interpretation": "input authorization flag",
        },
        {
            "metric": "experimental_camera_update_unauthorized",
            "value": int(
                experimental_update_without_authorization
            ),
            "interpretation": "requires independent validation",
        },
    ]

    report = {
        "task": "26.6A",
        "scope": "C02 moving-target archived quality evidence",
        "input_paths": {
            key: str(path)
            for key, path in FILES.items()
        },
        "selected_frames": len(selected),
        "lidar_clustered_frames": len(lidar),
        "frames_with_lidar_clusters": frames_with_clusters,
        "frames_with_temporal_tracks": len(track_frames),
        "ekf_rows": len(ekf),
        "radar_status_counts": radar_counts,
        "camera_status_counts": camera_counts,
        "ground_truth_status_counts": gt_counts,
        "camera_measurement": {
            "frame": camera_frame,
            "status": camera_row["status"],
            "update_authorized": camera_authorized,
            "archived_ekf_status": archived_camera_status,
            "experimental_update_without_authorization":
                experimental_update_without_authorization,
        },
        "conclusion": (
            "Algorithm outputs and reproducibility are documented, "
            "but no EKF row is marked ground-truth validated. "
            "These records alone cannot establish perception accuracy."
        ),
        "limits": [
            "No object-detection precision or recall calculated.",
            "No tracking RMSE calculated.",
            "No false-positive or false-negative rate calculated.",
            "A cluster is not automatically a correct object detection.",
            "Experimental Camera update lacks authorization.",
            "No CPU versus FPGA accuracy comparison exists yet.",
            "No board-level energy measurement exists yet."
        ],
    }

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with SUMMARY.open(
        "x", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["metric", "value", "interpretation"]
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("=== TASK 26.6A QUALITY EVIDENCE AUDIT ===")
    print("SELECTED_FRAMES:", len(selected))
    print("LIDAR_CLUSTERED_FRAMES:", len(lidar))
    print("FRAMES_WITH_LIDAR_CLUSTERS:", frames_with_clusters)
    print("FRAMES_WITH_TEMPORAL_TRACKS:", len(track_frames))
    print("EKF_OUTPUT_ROWS:", len(ekf))
    print("RADAR_STATUS_COUNTS:", radar_counts)
    print("CAMERA_STATUS_COUNTS:", camera_counts)
    print("GROUND_TRUTH_STATUS_COUNTS:", gt_counts)
    print("CAMERA_UPDATE_AUTHORIZED:", camera_authorized)
    print(
        "UNAUTHORIZED_EXPERIMENTAL_CAMERA_UPDATE:",
        experimental_update_without_authorization
    )
    print("PERCEPTION_ACCURACY_ESTABLISHED: NO")
    print("HISTORICAL_INPUT_FILES_MODIFIED: NO")
    print("TASK26_6A_QUALITY_EVIDENCE_AUDIT_PASS")
    print("SUMMARY:", SUMMARY)
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
