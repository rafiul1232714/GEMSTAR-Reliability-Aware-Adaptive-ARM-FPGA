
# TASK 13.2B - Coordinate convention diagnostic
# Compares existing Task 11 and Task 13 reconstructions.
# Does not overwrite original data.

from pathlib import Path
import csv
import shutil
import math
import statistics

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
TASK11 = ROOT / "tests" / "Task_11_Final_Research"
TASK13 = ROOT / "tests" / "Task_13_Final_Research"

DATA = TASK13 / "02_CSV_Data"
CODE = TASK13 / "04_Code"
FIND = TASK13 / "06_Research_Findings"

for folder in (DATA, CODE, FIND):
    folder.mkdir(parents=True, exist_ok=True)

FILES = {
    "lidar": (
        TASK11 / "02_CSV_Data"
        / "task11_lidar_frame150_geometry.csv",
        DATA / "task13_2a_lidar_common_frame.csv"
    ),
    "radar": (
        TASK11 / "02_CSV_Data"
        / "task11_frame150_radar_cluster_association.csv",
        DATA / "task13_2a_radar_common_frame.csv"
    )
}


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def xyz(row):
    return tuple(float(row[k]) for k in (
        "x_ego_m", "y_ego_m", "z_ego_m"
    ))


def point_error(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def examine(name, old_path, new_path):
    old = read_csv(old_path)
    new = read_csv(new_path)

    if len(old) != len(new):
        raise RuntimeError(
            f"{name}: row counts differ: "
            f"{len(old)} vs {len(new)}. "
            "Cannot safely compare by row."
        )

    # Check measurement alignment before row-wise comparison.
    for i, (a, b) in enumerate(zip(old, new)):
        if int(float(a["frame"])) != int(float(b["frame"])):
            raise RuntimeError(f"{name}: frame mismatch at row {i}")

        if name == "lidar":
            if int(float(a["ray_index"])) != int(float(b["ray_index"])):
                raise RuntimeError(
                    f"LiDAR: ray-index mismatch at row {i}"
                )

        if abs(float(a["range_m"]) -
               float(b["range_m"])) > 1e-6:
            raise RuntimeError(
                f"{name}: range mismatch at row {i}"
            )

    rows = []
    hypotheses = {
        "unchanged": [],
        "reverse_y": [],
        "reverse_x": [],
        "reverse_z": [],
        "reverse_xy": [],
        "reverse_yz": [],
        "reverse_xz": [],
        "reverse_xyz": [],
    }

    signed_differences = [[], [], []]

    for a, b in zip(old, new):
        p_old = xyz(a)
        p_new = xyz(b)

        x, y, z = p_new

        candidates = {
            "unchanged": (x, y, z),
            "reverse_y": (x, -y, z),
            "reverse_x": (-x, y, z),
            "reverse_z": (x, y, -z),
            "reverse_xy": (-x, -y, z),
            "reverse_yz": (x, -y, -z),
            "reverse_xz": (-x, y, -z),
            "reverse_xyz": (-x, -y, -z),
        }

        for label, point in candidates.items():
            hypotheses[label].append(
                point_error(p_old, point)
            )

        for axis in range(3):
            signed_differences[axis].append(
                p_old[axis] - p_new[axis]
            )

        rows.append({
            "sensor": name,
            "frame": a["frame"],
            "ray_index": a.get("ray_index", ""),
            "range_m": a["range_m"],
            "old_x": p_old[0],
            "old_y": p_old[1],
            "old_z": p_old[2],
            "new_x": p_new[0],
            "new_y": p_new[1],
            "new_z": p_new[2],
            "error_original_m": hypotheses["unchanged"][-1],
            "error_reverse_y_m": hypotheses["reverse_y"][-1],
        })

    results = []

    for label, errors in hypotheses.items():
        results.append({
            "sensor": name,
            "hypothesis": label,
            "mean_error_m": statistics.mean(errors),
            "max_error_m": max(errors)
        })

    results.sort(key=lambda r: r["mean_error_m"])

    offsets = [
        statistics.mean(values)
        for values in signed_differences
    ]

    print(f"\n=== {name.upper()} ===")
    print(f"Rows verified: {len(rows)}")

    print("Mean old-minus-new XYZ offsets (m):")
    print("  X: %.6f" % offsets[0])
    print("  Y: %.6f" % offsets[1])
    print("  Z: %.6f" % offsets[2])

    print("\nCandidate coordinate-sign comparisons:")
    for r in results:
        print(
            f"  {r['hypothesis']:14s} "
            f"mean={r['mean_error_m']:9.5f} m  "
            f"max={r['max_error_m']:9.5f} m"
        )

    return rows, results, offsets


all_rows = []
all_results = []
notes = []

print("\n===== TASK 13.2B COORDINATE DIAGNOSTIC =====")

for sensor, (old_path, new_path) in FILES.items():
    for path in (old_path, new_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    rows, results, offsets = examine(
        sensor, old_path, new_path
    )

    all_rows.extend(rows)
    all_results.extend(results)

    best = results[0]

    notes.append(
        f"{sensor.upper()}: lowest unadjusted sign-hypothesis "
        f"mean error is {best['mean_error_m']:.6f} m "
        f"({best['hypothesis']})."
    )


def save_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)


save_csv(
    DATA / "task13_2b_coordinate_point_differences.csv",
    all_rows
)

save_csv(
    DATA / "task13_2b_sign_hypothesis_summary.csv",
    all_results
)

findings = [
    "TASK 13.2B - COORDINATE DIAGNOSTIC",
    "",
    *notes,
    "",
    "Interpretation:",
    "The hypotheses compare numerical agreement with Task 11.",
    "They do not establish which coordinate frame is correct.",
    "Simple axis flips can also require translation adjustments.",
    "OSI-to-Unreal and sensor mounting transforms still",
    "require independent verification.",
    "No object-level sensor correspondence is established.",
]

(FIND / "task13_2b_coordinate_diagnostic_findings.txt").write_text(
    "\n".join(findings) + "\n",
    encoding="utf-8"
)

shutil.copy2(
    Path(__file__),
    CODE / Path(__file__).name
)

print("\nCSV files and findings saved in Task 13 archive.")
print("TASK 13.2B COMPLETED")
