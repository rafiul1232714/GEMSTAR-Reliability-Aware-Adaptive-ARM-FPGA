from pathlib import Path
import csv
import json
import math
from statistics import mean

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

DATA = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
    / "C02_V2_EKF_Input_53Frames_V1"
)

ROOT = TESTS / "Task_26_Final_Research"

GT_FILE = DATA / "gt_center_comparison_track2_v1.csv"
EKF_FILE = DATA / "lidar_radar_camera_ekf_track2_v1.csv"
IDENTITY_FILE = DATA / "gt_track2_identity_audit_v1.csv"

FRAME_OUTPUT = (
    ROOT / "02_CSV_Data"
    / "task26_6C_ekf_position_errors_by_frame.csv"
)
SUMMARY_OUTPUT = (
    ROOT / "02_CSV_Data"
    / "task26_6C_ekf_position_error_summary.csv"
)
REPORT_OUTPUT = (
    ROOT / "06_Research_Findings"
    / "task26_6C_ekf_position_error_report.json"
)

METHODS = {
    "lidar_only": (
        "lidar_only_x_m",
        "lidar_only_y_m",
        "lidar_center_error_m"
    ),
    "radar_assisted": (
        "radar_x_m",
        "radar_y_m",
        "radar_center_error_m"
    ),
    "camera_experimental": (
        "camera_aided_x_m",
        "camera_aided_y_m",
        "camera_center_error_m"
    )
}

def load_by_frame(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))

    indexed = {}

    for row in rows:
        frame = int(row["frame"])
        if frame in indexed:
            raise RuntimeError(f"Duplicate frame: {frame}")
        indexed[frame] = row

    return indexed

def finite(row, key):
    value = float(row[key])
    if not math.isfinite(value):
        raise RuntimeError(f"Nonfinite field: {key}")
    return value

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

def main():
    outputs = [FRAME_OUTPUT, SUMMARY_OUTPUT, REPORT_OUTPUT]

    for path in outputs:
        if path.exists():
            raise FileExistsError(
                f"Research output already exists: {path}"
            )

    for path in (GT_FILE, EKF_FILE, IDENTITY_FILE):
        if not path.is_file():
            raise FileNotFoundError(path)

    gt = load_by_frame(GT_FILE)
    ekf = load_by_frame(EKF_FILE)
    identity = load_by_frame(IDENTITY_FILE)

    common = sorted(set(gt) & set(ekf) & set(identity))

    if len(gt) != 23 or len(ekf) != 24 or len(common) != 23:
        raise RuntimeError("Unexpected GT/EKF coverage")

    if set(gt) != set(identity):
        raise RuntimeError("GT and identity frames differ")

    frame_rows = []
    measured = {key: [] for key in METHODS}
    checks = 0
    accepted_camera_frames = []

    for frame in common:
        g = gt[frame]
        e = ekf[frame]
        ident = identity[frame]

        if abs(
            finite(g, "time_s") - finite(e, "time_s")
        ) > 1e-6:
            raise RuntimeError(
                f"GT/EKF timestamp mismatch at {frame}"
            )

        if abs(
            finite(g, "time_s") - finite(ident, "time_s")
        ) > 1e-6:
            raise RuntimeError(
                f"GT/identity timestamp mismatch at {frame}"
            )

        if (
            ident["gt_target_id"] != "76897"
            or ident["nearest_gt_id"] != "76897"
            or ident["nearest_is_target"].lower() != "true"
            or ident["evaluation_only"].upper() != "YES"
            or g["comparison_reference"] != "GT_OBJECT_CENTER"
        ):
            raise RuntimeError(
                f"Unverified diagnostic identity at {frame}"
            )

        gx = finite(g, "gt_center_x_ego_m")
        gy = finite(g, "gt_center_y_ego_m")

        item = {
            "frame": frame,
            "time_s": finite(g, "time_s"),
            "gt_target_id": 76897,
            "gt_center_x_ego_m": gx,
            "gt_center_y_ego_m": gy,
            "radar_status": e["radar_status"],
            "camera_status": e["camera_status"]
        }

        if e["camera_status"] == "EXPERIMENTAL_ACCEPTED":
            accepted_camera_frames.append(frame)

        for name, (xfield, yfield, reference) in METHODS.items():
            dx = finite(e, xfield) - gx
            dy = finite(e, yfield) - gy
            distance = math.hypot(dx, dy)

            archived = finite(g, reference)

            if not math.isclose(
                distance, archived,
                rel_tol=1e-8,
                abs_tol=1e-7
            ):
                raise RuntimeError(
                    f"Archived diagnostic mismatch: {name}, {frame}"
                )

            checks += 1

            item[f"{name}_x_error_m"] = dx
            item[f"{name}_y_error_m"] = dy
            item[f"{name}_center_error_m"] = distance

            measured[name].append({
                "dx": dx,
                "dy": dy,
                "distance": distance
            })

        frame_rows.append(item)

    if accepted_camera_frames != [530]:
        raise RuntimeError("Unexpected Camera acceptance frames")

    summary_rows = []

    for name, entries in measured.items():
        dx = [v["dx"] for v in entries]
        dy = [v["dy"] for v in entries]
        distance = [v["distance"] for v in entries]

        # 2D position RMSE against the GT object center.
        rmse = math.sqrt(
            mean(d * d for d in distance)
        )

        summary_rows.append({
            "method": name,
            "observations": len(entries),
            "position_rmse_m_diagnostic": rmse,
            "mean_center_error_m": mean(distance),
            "max_center_error_m": max(distance),
            "mean_x_error_m": mean(dx),
            "mean_y_error_m": mean(dy),
            "reference": "GT_OBJECT_CENTER",
            "validation_status": "EXPLORATORY_NOT_VALIDATED"
        })

    # Quantify relative differences without claiming
    # a causal fusion advantage or superiority.
    row_by_name = {r["method"]: r for r in summary_rows}

    lidar_rmse = row_by_name[
        "lidar_only"
    ]["position_rmse_m_diagnostic"]

    radar_rmse = row_by_name[
        "radar_assisted"
    ]["position_rmse_m_diagnostic"]

    camera_rmse = row_by_name[
        "camera_experimental"
    ]["position_rmse_m_diagnostic"]

    print("=== TASK 26.6C EKF POSITION ERROR ANALYSIS ===")
    print("COMMON_GT_EKF_FRAMES:", len(common))
    print("GT_TARGET_ID:", 76897)
    print("REFERENCE_TYPE: GT_OBJECT_CENTER")
    print("NUMERICAL_CHECKS_PASSED:", checks)
    print("CAMERA_EXPERIMENTAL_UPDATE_FRAMES:", accepted_camera_frames)

    for row in summary_rows:
        print(
            row["method"].upper() + "_RMSE_M:",
            f'{row["position_rmse_m_diagnostic"]:.6f}'
        )
        print(
            row["method"].upper() + "_MEAN_ERROR_M:",
            f'{row["mean_center_error_m"]:.6f}'
        )

    print(
        "RADAR_MINUS_LIDAR_RMSE_M:",
        f"{radar_rmse - lidar_rmse:.6f}"
    )
    print(
        "CAMERA_MINUS_RADAR_RMSE_M:",
        f"{camera_rmse - radar_rmse:.6f}"
    )

    report = {
        "task": "26.6C",
        "experiment": "C02 moving-target Track 2",
        "reference": "GT_OBJECT_CENTER",
        "matched_frames": common,
        "target_id": 76897,
        "numerical_checks": checks,
        "camera_experimental_update_frames": accepted_camera_frames,
        "summary": summary_rows,
        "radar_minus_lidar_rmse_m": radar_rmse - lidar_rmse,
        "camera_minus_radar_rmse_m": camera_rmse - radar_rmse,
        "classification": "EXPLORATORY_NOT_VALIDATED",
        "limitations": [
            "GT coordinate transform labelled preliminary by original source.",
            "GT association uses evaluation-only target identity.",
            "Object-center versus visible LiDAR surface bias is not corrected.",
            "Camera update authorization is NO.",
            "GT actor velocity has six integrity warnings.",
            "No detection precision or recall is measured.",
            "No validated three-sensor accuracy is established.",
            "No ARM/FPGA or energy measurement is included."
        ],
        "historical_source_files_modified": False
    }

    write_csv(FRAME_OUTPUT, frame_rows)
    write_csv(SUMMARY_OUTPUT, summary_rows)

    REPORT_OUTPUT.parent.mkdir(
        parents=True, exist_ok=True
    )

    with REPORT_OUTPUT.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)

    print("OFFICIAL_ACCURACY_VALIDATED: NO")
    print("HISTORICAL_FILES_MODIFIED: NO")
    print("TASK26_6C_POSITION_ERROR_ANALYSIS_PASS")
    print("FRAME_CSV:", FRAME_OUTPUT)
    print("SUMMARY_CSV:", SUMMARY_OUTPUT)
    print("REPORT:", REPORT_OUTPUT)

if __name__ == "__main__":
    main()
