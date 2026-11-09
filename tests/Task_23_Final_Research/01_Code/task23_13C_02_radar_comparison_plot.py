import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TASK = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
)

CSV = TASK / "02_CSV_Data" / (
    "task23_13B_03_radar_serialization_comparison.csv"
)

PNG = TASK / "03_Graphs" / (
    "task23_13C_02_radar_serialization_comparison.png"
)

if PNG.exists():
    raise RuntimeError("PNG already exists; refusing overwrite")

with CSV.open(newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 4:
    raise RuntimeError("Expected four Radar rays")

rows.sort(key=lambda r: int(r["Ray"]))

rays = [int(r["Ray"]) for r in rows]

if rays != [44, 45, 54, 55]:
    raise RuntimeError(f"Unexpected Radar rays: {rays}")

if any(r["Result"] != "PASS" for r in rows):
    raise RuntimeError("Radar comparison contains failed rows")

fields = [
    "BaselineGeometryM",
    "BaselineOSIM",
    "DisplacedGeometryM",
    "DisplacedOSIM",
    "GeometryChangeM",
    "OSIChangeM",
    "ChangeErrorM",
]

for row in rows:
    if not all(math.isfinite(float(row[k])) for k in fields):
        raise RuntimeError("Nonfinite comparison measurement")

x = np.arange(4)
width = 0.19

baseline_geometry = np.array([
    float(r["BaselineGeometryM"]) for r in rows
])
baseline_osi = np.array([
    float(r["BaselineOSIM"]) for r in rows
])
displaced_geometry = np.array([
    float(r["DisplacedGeometryM"]) for r in rows
])
displaced_osi = np.array([
    float(r["DisplacedOSIM"]) for r in rows
])
change_error_mm = np.array([
    float(r["ChangeErrorM"]) * 1000 for r in rows
])

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

axes[0].bar(
    x - 1.5 * width, baseline_geometry, width,
    label="Baseline geometry"
)
axes[0].bar(
    x - 0.5 * width, baseline_osi, width,
    label="Baseline OSI"
)
axes[0].bar(
    x + 0.5 * width, displaced_geometry, width,
    label="Displaced geometry"
)
axes[0].bar(
    x + 1.5 * width, displaced_osi, width,
    label="Displaced OSI"
)

axes[0].set_xticks(x)
axes[0].set_xticklabels(rays)
axes[0].set_xlabel("Radar ray index")
axes[0].set_ylabel("Range (m)")
axes[0].set_title("Geometric vs OSI Radar ranges")
axes[0].legend(fontsize=8)
axes[0].grid(axis="y", alpha=0.25)

axes[1].bar(x, change_error_mm)
axes[1].axhline(
    2.0, linestyle="--", color="red",
    label="Diagnostic tolerance (+2 mm)"
)
axes[1].axhline(
    -2.0, linestyle="--", color="red"
)

axes[1].set_xticks(x)
axes[1].set_xticklabels(rays)
axes[1].set_xlabel("Radar ray index")
axes[1].set_ylabel("OSI minus geometry displacement (mm)")
axes[1].set_title("Displacement serialization error")
axes[1].legend()
axes[1].grid(axis="y", alpha=0.25)

fig.suptitle(
    "Task 23.13 — Radar OSI Range Serialization Validation",
    fontsize=14
)

fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig(PNG, dpi=200)
plt.close(fig)

if not PNG.is_file() or PNG.stat().st_size < 10000:
    raise RuntimeError("PNG output missing or unexpectedly small")

print(f"PNG_SAVED={PNG}")
print(f"PNG_BYTES={PNG.stat().st_size}")
print(f"RAYS_PLOTTED={len(rays)}")
print(
    "MAX_ABS_DISPLACEMENT_ERROR_MM="
    f"{np.max(np.abs(change_error_mm)):.6f}"
)

print("TASK23_13C_02_RADAR_COMPARISON_PNG_PASS")
