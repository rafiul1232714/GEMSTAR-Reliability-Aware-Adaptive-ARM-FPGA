
# TASK 13.6B - RADAR ASSOCIATION ROBUSTNESS
# MOR100 frame 150
#
# Uses Task 13.6A results. Tests association
# sensitivity to GT box interpretation.
#
# This does NOT assign confirmed vehicle identities.

from pathlib import Path
import csv
from collections import defaultdict

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"

DATA = TASK / "02_CSV_Data"
FIND = TASK / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FIND.mkdir(parents=True, exist_ok=True)

INPUT = DATA / "task13_6a_radar_gt_distances.csv"

with INPUT.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise RuntimeError("No Radar candidates found")

results = []

for row in rows:
    da = float(row["distance_model_a_m"])
    db = float(row["distance_model_b_m"])

    # The following labels are geometric diagnostics,
    # not calibrated probabilistic confidence scores.
    if da <= 0.5 and db <= 0.5:
        label = "NEAR_UNDER_BOTH_MODELS"
    elif da <= 0.5 and db > 0.5:
        label = "SENSITIVE_TO_BOX_MODEL"
    elif da > 0.5 and db <= 0.5:
        label = "NEAR_ONLY_MODEL_B"
    else:
        label = "NOT_NEAR_TARGET"

    results.append({
        "frame": int(row["frame"]),
        "ray_index": int(row["ray_index"]),
        "range_m": float(row["range_m"]),
        "signal_strength": float(row["signal_strength"]),
        "distance_a_m": da,
        "distance_b_m": db,
        "association_diagnostic": label
    })

output = DATA / "task13_6b_radar_association_robustness.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0])
    )
    writer.writeheader()
    writer.writerows(results)

groups = defaultdict(list)
for row in results:
    groups[row["association_diagnostic"]].append(row)

print("\n===== TASK 13.6B - RADAR ASSOCIATION =====")
print("Frame:", 150)
print("Total radar candidates:", len(results))

for label in (
    "NEAR_UNDER_BOTH_MODELS",
    "SENSITIVE_TO_BOX_MODEL",
    "NEAR_ONLY_MODEL_B",
    "NOT_NEAR_TARGET"
):
    matches = groups[label]
    print(f"\n{label}: {len(matches)}")
    print("  Ray indices:", [
        r["ray_index"] for r in matches
    ])

print("\nGeometrically robust candidates:")
for row in groups["NEAR_UNDER_BOTH_MODELS"]:
    print(
        f"Ray {row['ray_index']}: "
        f"range={row['range_m']:.3f} m, "
        f"Model A distance={row['distance_a_m']:.3f} m, "
        f"Model B distance={row['distance_b_m']:.3f} m"
    )

find_file = FIND / "task13_6b_radar_association_findings.txt"

find_file.write_text(
    "\n".join([
        "TASK 13.6B - RADAR ASSOCIATION ROBUSTNESS",
        "",
        "Diagnostic threshold: 0.5 m",
        "Models A/B differ in box-size interpretation.",
        "These are geometric proximity labels only.",
        "",
        *[
            f"{label}: {len(groups[label])}"
            for label in (
                "NEAR_UNDER_BOTH_MODELS",
                "SENSITIVE_TO_BOX_MODEL",
                "NEAR_ONLY_MODEL_B",
                "NOT_NEAR_TARGET"
            )
        ],
        "",
        "LIMITATIONS",
        "Cross-run actor-origin offset remains provisional.",
        "Object identity has not been confirmed.",
        "Radar return independence is not established.",
        "No calibrated association probability is given.",
        "Camera-LiDAR-Radar fusion remains unvalidated."
    ]) + "\n",
    encoding="utf-8"
)

print("\nSaved:", output)
print("Saved:", find_file)
print("TASK 13.6B COMPLETED")
