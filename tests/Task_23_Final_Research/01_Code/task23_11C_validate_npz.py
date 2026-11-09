import csv
import numpy as np
from pathlib import Path

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

ROOT = TASK / "08_Processed_Data"

OUTPUT = (
    TASK / "02_CSV_Data"
    / "task23_11C_npz_integrity.csv"
)

rows = []

for folder in ["LiDAR_Range", "LiDAR_Source_Matched"]:

    for path in sorted((ROOT / folder).glob("*.npz")):

        problems = []

        with np.load(path, allow_pickle=False) as data:

            ranges = data["range_image_m"]
            mask = data["valid_mask"]
            points = data["points_sensor_m"]

            valid_count = int(np.count_nonzero(mask))
            point_count = len(points)

            if ranges.shape != (21, 251):
                problems.append("Unexpected range-image shape")

            if mask.shape != ranges.shape:
                problems.append("Mask shape mismatch")

            if mask.dtype != np.bool_:
                problems.append("Mask is not boolean")

            if points.ndim != 2 or points.shape[1] != 3:
                problems.append("Invalid point-cloud shape")

            if valid_count != point_count:
                problems.append("Valid-ray and point-count mismatch")

            if not np.all(np.isfinite(ranges[mask])):
                problems.append("Non-finite accepted range")

            if not np.all(
                (ranges[mask] >= 0.05)
                & (ranges[mask] <= 200.0)
            ):
                problems.append("Accepted range outside screening limits")

            if not np.all(np.isfinite(points)):
                problems.append("Non-finite 3D point")

            if "valid_ray_indices" in data:
                indices = data["valid_ray_indices"]

                if len(indices) != valid_count:
                    problems.append("Ray-index count mismatch")
                elif (
                    np.any(indices < 0)
                    or np.any(indices >= mask.size)
                    or not np.array_equal(
                        np.sort(indices),
                        np.flatnonzero(mask)
                    )
                ):
                    problems.append("Ray indices do not match mask")

            method_key = (
                "geometry_method"
                if "geometry_method" in data
                else "reconstruction_method"
            )

            method = str(data[method_key].item())

        rows.append({
            "Folder": folder,
            "File": path.name,
            "ValidRays": valid_count,
            "Points": point_count,
            "Method": method,
            "Status": "PASS" if not problems else "FAIL",
            "Problems": "; ".join(problems)
        })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "Folder", "File", "ValidRays",
            "Points", "Method", "Status", "Problems"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

passed = sum(r["Status"] == "PASS" for r in rows)

print("\n=== TASK 23.11.C NPZ VALIDATION ===")
print("Files checked:", len(rows))
print("Files passed:", passed)
print("Files failed:", len(rows) - passed)

for row in rows:
    print(
        row["Status"],
        row["File"],
        "Valid rays:", row["ValidRays"],
        "Points:", row["Points"],
        "Method:", row["Method"]
    )

    if row["Problems"]:
        print("  Issues:", row["Problems"])

print("\nCSV:", OUTPUT)
