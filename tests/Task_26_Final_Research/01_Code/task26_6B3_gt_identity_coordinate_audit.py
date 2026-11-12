from pathlib import Path
import csv
import json
import math
import statistics

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

DATA = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
    / "C02_V2_EKF_Input_53Frames_V1"
)

TASK26 = TESTS / "Task_26_Final_Research"

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_6B3_gt_identity_coordinate_audit.json"
)

NAMES = {
    "gt": "gt_center_comparison_track2_v1.csv",
    "identity": "gt_track2_identity_audit_v1.csv",
    "velocity": "gt_ekf_velocity_comparison_v1.csv",
    "integrity": "ego_gt_velocity_integrity_audit_v1.csv",
    "ekf": "lidar_radar_camera_ekf_track2_v1.csv",
}

def read_indexed(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError(f"Empty CSV: {path}")

    index = {}

    for row in rows:
        frame = int(row["frame"])

        if frame in index:
            raise RuntimeError(
                f"Duplicate frame {frame}: {path.name}"
            )

        index[frame] = row

    return index

def number(row, field):
    value = float(row[field])

    if not math.isfinite(value):
        raise RuntimeError(
            f"Non-finite value in {field}"
        )

    return value

def near(a, b, tol=1e-7):
    return math.isclose(a, b, rel_tol=1e-8, abs_tol=tol)

def main():
    if REPORT.exists():
        raise FileExistsError(
            f"Existing research report preserved: {REPORT}"
        )

    tables = {}

    for key, filename in NAMES.items():
        path = DATA / filename

        if not path.is_file():
            raise FileNotFoundError(path)

        tables[key] = read_indexed(path)

    gt = tables["gt"]
    identity = tables["identity"]
    velocity = tables["velocity"]
    integrity = tables["integrity"]
    ekf = tables["ekf"]

    common = sorted(
        set(gt)
        & set(identity)
        & set(velocity)
        & set(integrity)
        & set(ekf)
    )

    if len(common) != 23:
        raise RuntimeError(
            f"Expected 23 common frames; found {len(common)}"
        )

    failures = []
    target_ids = set()
    nearest_ids = set()
    model_names = set()
    ego_ids = set()
    gt_positions = []
    times = []
    identity_count = 0
    reference_error_count = 0
    comparison_only_count = 0
    reported_motion_flags = 0

    for frame in common:
        g = gt[frame]
        i = identity[frame]
        v = velocity[frame]
        e = ekf[frame]
        a = integrity[frame]

        stamps = [
            number(row, "time_s")
            for row in (g, i, v, e, a)
        ]

        if max(stamps) - min(stamps) > 1e-6:
            failures.append(
                f"Frame {frame}: timestamp mismatch"
            )

        target_ids.add(i["gt_target_id"])
        nearest_ids.add(i["nearest_gt_id"])
        model_names.add(i["gt_target_model"])
        ego_ids.add(g["ego_id"])

        if i["nearest_is_target"].strip().lower() == "true":
            identity_count += 1
        else:
            failures.append(
                f"Frame {frame}: nearest GT is not target"
            )

        if i["gt_target_id"] != i["nearest_gt_id"]:
            failures.append(
                f"Frame {frame}: target and nearest IDs differ"
            )

        if i["evaluation_only"].strip().upper() == "YES":
            comparison_only_count += 1

        if (
            a["reported_zero_during_measured_motion"]
            .strip().lower() == "true"
        ):
            reported_motion_flags += 1

        gx = number(g, "gt_center_x_ego_m")
        gy = number(g, "gt_center_y_ego_m")

        gt_positions.append((gx, gy))
        times.append(stamps[0])

        # Check that independent GT-related CSV tables
        # carry numerically consistent coordinates.
        pairs = [
            (
                number(v, "gt_center_x_ego_m"),
                number(v, "gt_center_y_ego_m")
            ),
            (
                number(a, "target_x_ego_m"),
                number(a, "target_y_ego_m")
            )
        ]

        for px, py in pairs:
            if not (near(gx, px) and near(gy, py)):
                failures.append(
                    f"Frame {frame}: GT coordinate disagreement"
                )

        # Recompute recorded 2D error, but do not
        # interpret it as validated perception accuracy.
        estimates = [
            ("lidar", "lidar_only_x_m", "lidar_only_y_m"),
            ("radar", "radar_x_m", "radar_y_m"),
            ("camera", "camera_aided_x_m", "camera_aided_y_m")
        ]

        for label, xcol, ycol in estimates:
            dx = number(e, xcol) - gx
            dy = number(e, ycol) - gy
            distance = math.hypot(dx, dy)

            recorded = number(
                g, f"{label}_center_error_m"
            )

            if not near(distance, recorded):
                failures.append(
                    f"Frame {frame}: {label} error disagreement"
                )
            else:
                reference_error_count += 1

        if g["comparison_reference"] != "GT_OBJECT_CENTER":
            failures.append(
                f"Frame {frame}: unexpected GT reference"
            )

    if len(target_ids) != 1 or len(nearest_ids) != 1:
        failures.append("Multiple GT identity values")

    if len(ego_ids) != 1 or len(model_names) != 1:
        failures.append("Unexpected ego or model variations")

    x_values = [p[0] for p in gt_positions]
    y_values = [p[1] for p in gt_positions]

    movement_steps = [
        math.hypot(
            gt_positions[k][0] - gt_positions[k-1][0],
            gt_positions[k][1] - gt_positions[k-1][1]
        )
        for k in range(1, len(gt_positions))
    ]

    position_spread = math.hypot(
        max(x_values) - min(x_values),
        max(y_values) - min(y_values)
    )

    print("=== TASK 26.6B.3 GT CONSISTENCY AUDIT ===")
    print("COMMON_FRAMES:", len(common))
    print("TARGET_IDS:", sorted(target_ids))
    print("NEAREST_GT_IDS:", sorted(nearest_ids))
    print("TARGET_MODELS:", sorted(model_names))
    print("EGO_IDS:", sorted(ego_ids))
    print("NEAREST_TARGET_MATCH_COUNT:", identity_count)
    print("EVALUATION_ONLY_ROWS:", comparison_only_count)
    print("RECOMPUTED_ERROR_CHECKS_PASSED:", reference_error_count)
    print("EXPECTED_ERROR_CHECKS:", 3 * len(common))
    print("GT_X_RANGE_M:", min(x_values), max(x_values))
    print("GT_Y_RANGE_M:", min(y_values), max(y_values))
    print("GT_POSITION_SPREAD_M:", position_spread)
    print(
        "GT_NONZERO_DISPLACEMENT_STEPS:",
        sum(step > 1e-4 for step in movement_steps)
    )
    print(
        "ZERO_VELOCITY_DURING_MOTION_FLAGS:",
        reported_motion_flags
    )
    print("CONSISTENCY_FAILURES:", len(failures))

    for failure in failures[:20]:
        print("FAILURE:", failure)

    result = {
        "task": "26.6B.3",
        "common_frames": common,
        "target_ids": sorted(target_ids),
        "nearest_gt_ids": sorted(nearest_ids),
        "target_models": sorted(model_names),
        "ego_ids": sorted(ego_ids),
        "nearest_target_matches": identity_count,
        "evaluation_only_rows": comparison_only_count,
        "recomputed_error_checks_passed": reference_error_count,
        "expected_error_checks": 3 * len(common),
        "gt_x_range_m": [min(x_values), max(x_values)],
        "gt_y_range_m": [min(y_values), max(y_values)],
        "gt_position_spread_m": position_spread,
        "gt_nonzero_displacement_steps": sum(
            step > 1e-4 for step in movement_steps
        ),
        "zero_velocity_during_motion_flags": reported_motion_flags,
        "consistency_failures": failures,
        "ground_truth_provenance_verified": False,
        "coordinate_transform_independently_verified": False,
        "official_tracking_rmse_calculated": False,
        "historical_files_modified": False
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    with REPORT.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("GT_PROVENANCE_VERIFIED: NO")
    print("COORDINATE_TRANSFORM_VERIFIED: NO")
    print("OFFICIAL_TRACKING_RMSE_CALCULATED: NO")
    print("HISTORICAL_FILES_MODIFIED: NO")
    print("REPORT:", REPORT)

    if failures:
        print("TASK26_6B3_GT_CONSISTENCY_AUDIT_REVIEW_REQUIRED")
    else:
        print("TASK26_6B3_GT_CONSISTENCY_AUDIT_PASS")

if __name__ == "__main__":
    main()
