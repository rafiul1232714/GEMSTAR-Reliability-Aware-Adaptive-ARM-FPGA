
# TASK 13.3S - VERTICAL ORIGIN CALIBRATION
# GEMSTAR MOR100, frame 150
#
# Tests the independently measured vehicle-origin Z offset.
# Does not overwrite previous measurements.
#
# NOTE:
# The calibration was measured in a new simulation run.
# Transfer to MOR100 is a hypothesis, not yet proof.

from pathlib import Path
import csv
import statistics
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"

DATA = TASK / "02_CSV_Data"
GRAPHS = TASK / "01_Graphs"
FINDINGS = TASK / "06_Research_Findings"
CODE = TASK / "04_Code"

for folder in (DATA, GRAPHS, FINDINGS, CODE):
    folder.mkdir(parents=True, exist_ok=True)

INPUT = DATA / "task13_3d_lidar_actor_join.csv"

# Measured using TASK13_ORIGIN logging.
# Unreal actor origin -> bounds center Z offset.
ORIGIN_OFFSET_Z_M = 0.82620

FLAT_ACTOR = "83185"

with INPUT.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise RuntimeError("Input CSV is empty.")

result = []

for row in rows:
    original_z = float(row["world_z_m"])

    # The previous reconstruction was based on
    # the GT bounds center. Subtract the measured
    # vertical actor-to-bounds offset.
    corrected_z = original_z - ORIGIN_OFFSET_Z_M

    result.append({
        "frame": int(float(row["frame"])),
        "ray_index": int(float(row["ray_index"])),
        "actor_id_diagnostic":
            row["unreal_actor_id_diagnostic"],
        "original_world_z_m": original_z,
        "corrected_world_z_m": corrected_z,
        "correction_applied_m": ORIGIN_OFFSET_Z_M,
        "inside_old_gt_box":
            int(float(row["inside_gt_box"]))
    })

flat = [
    r for r in result
    if r["actor_id_diagnostic"] == FLAT_ACTOR
]

if not flat:
    raise RuntimeError("Flat-surface actor not found.")

before = [r["original_world_z_m"] for r in flat]
after = [r["corrected_world_z_m"] for r in flat]

print("\n===== TASK 13.3S - VERTICAL CALIBRATION =====")
print("Flat-surface actor:", FLAT_ACTOR)
print("Points:", len(flat))

print(
    "Original median Z:",
    f"{statistics.median(before):.6f} m"
)

print(
    "Corrected median Z:",
    f"{statistics.median(after):.6f} m"
)

print(
    "Applied Z correction:",
    f"{ORIGIN_OFFSET_Z_M:.6f} m"
)

print(
    "Maximum corrected height deviation:",
    f"{max(abs(z - statistics.median(after)) for z in after):.9f} m"
)

# Save point-level CSV.
point_file = DATA / "task13_3s_vertical_calibrated_lidar.csv"

with point_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(result[0])
    )
    writer.writeheader()
    writer.writerows(result)

# Save graph.
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(
    before, bins=20, alpha=0.6,
    label="Before calibration"
)

ax.hist(
    after, bins=20, alpha=0.6,
    label="After Z correction"
)

ax.axvline(0, linestyle="--", label="Z = 0 m")

ax.set_xlabel("Reconstructed world Z (m)")
ax.set_ylabel("Point count")
ax.set_title(
    "Task 13.3S - Actor 83185 Vertical Origin Calibration"
)
ax.legend()
ax.grid(True)

fig.tight_layout()

graph_file = GRAPHS / "task13_3s_vertical_calibration.png"
fig.savefig(graph_file, dpi=250)
plt.close(fig)

# Save research findings.
findings_file = (
    FINDINGS / "task13_3s_vertical_calibration_findings.txt"
)

findings_file.write_text(
    "\n".join([
        "TASK 13.3S - VERTICAL ORIGIN CALIBRATION",
        "",
        "Measured actor-to-bounds Z offset: 0.82620 m",
        f"Original plane median Z: {statistics.median(before):.9f} m",
        f"Corrected plane median Z: {statistics.median(after):.9f} m",
        "",
        "LIMITATIONS",
        "The offset came from a separate diagnostic run.",
        "A horizontal surface at Z~0 supports a ground hypothesis",
        "but does not independently establish actor identity.",
        "Horizontal actor-to-bounds offsets remain uncalibrated.",
        "Original sensor-to-GT timestamps remain unverified.",
        "No target-vehicle association is claimed."
    ]) + "\n",
    encoding="utf-8"
)

shutil.copy2(
    Path(__file__), CODE / Path(__file__).name
)

print("\nSaved:", point_file)
print("Saved:", graph_file)
print("Saved:", findings_file)
print("TASK 13.3S COMPLETED")
