import csv
import math
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_20_Final_Research"
)

DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"
GRAPHS.mkdir(parents=True, exist_ok=True)

FRAME = 10

radar_file = DATA / "task20_28_radar_world_points.csv"
gt_file = DATA / "task20_13_gt_objects.csv"

with radar_file.open(encoding="utf-8-sig", newline="") as f:
    radar_rows = list(csv.DictReader(f))

with gt_file.open(encoding="utf-8-sig", newline="") as f:
    gt_rows = list(csv.DictReader(f))

radar_by_scenario = defaultdict(list)
gt_by_scenario = defaultdict(list)

for row in radar_rows:
    if int(row["FrameIndex"]) == FRAME:
        radar_by_scenario[row["Recording"]].append(row)

for row in gt_rows:
    if int(row["FrameIndex"]) == FRAME:
        gt_by_scenario[row["Recording"]].append(row)

scenarios = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_mor100",
    "fog_postfix_validation",
]

summary = []

print("\n=== TASK 20.29 RADAR / GT VISUALIZATION ===")

for scenario in scenarios:
    radar = radar_by_scenario[scenario]
    objects = gt_by_scenario[scenario]

    moving = [
        row for row in objects
        if row["Kind"] == "MOVING"
    ]

    rx = [float(row["WorldX"]) for row in radar]
    ry = [float(row["WorldY"]) for row in radar]

    fig, ax = plt.subplots(figsize=(9, 7))

    if radar:
        ax.scatter(
            rx, ry,
            s=20, alpha=0.7,
            label="Radar candidate returns"
        )

    for obj in moving:
        x = float(obj["X"])
        y = float(obj["Y"])
        obj_id = obj["ObjectID"]

        ax.scatter(
            [x], [y],
            marker="x",
            s=110,
            linewidths=2,
            label=f"GT moving object {obj_id}"
        )

        ax.annotate(
            obj_id, (x, y),
            xytext=(5, 6),
            textcoords="offset points",
            fontsize=9
        )

    # Focus the plot on moving-object centres and
    # radar points, not huge stationary map geometry.
    all_x = rx + [float(o["X"]) for o in moving]
    all_y = ry + [float(o["Y"]) for o in moving]

    if all_x and all_y:
        xmin, xmax = min(all_x), max(all_x)
        ymin, ymax = min(all_y), max(all_y)

        pad_x = max(2.0, (xmax-xmin)*0.1)
        pad_y = max(2.0, (ymax-ymin)*0.1)

        ax.set_xlim(xmin-pad_x, xmax+pad_x)
        ax.set_ylim(ymin-pad_y, ymax+pad_y)

    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("OSI world X (m)")
    ax.set_ylabel("OSI world Y (m)")
    ax.set_title(
        f"{scenario} | Frame {FRAME}\n"
        "Provisional radar points vs GT object centres"
    )
    ax.legend(fontsize=8, loc="best")

    fig.tight_layout()

    image = (
        GRAPHS /
        f"task20_29_{scenario}_frame{FRAME:03d}.png"
    )

    fig.savefig(image, dpi=170)
    plt.close(fig)

    # Nearest-centre distance is for visualization
    # diagnostics ONLY, not detection accuracy.
    distances = []

    for x, y in zip(rx, ry):
        if moving:
            distances.append(
                min(
                    math.hypot(
                        x-float(obj["X"]),
                        y-float(obj["Y"])
                    )
                    for obj in moving
                )
            )

    distances.sort()

    median_distance = (
        distances[len(distances)//2]
        if distances else None
    )

    summary.append({
        "Recording": scenario,
        "Frame": FRAME,
        "RadarCandidatePoints": len(radar),
        "GTMovingObjects": len(moving),
        "MedianNearestMovingObjectCentreDistanceM":
            median_distance,
        "PlotSaved": image.is_file(),
        "Interpretation": "Diagnostic only; not accuracy"
    })

    print(
        f"{scenario:28s}"
        f" | Radar={len(radar):3d}"
        f" | GT objects={len(moving):2d}"
        f" | Plot={image.is_file()}"
    )

summary_file = (
    DATA / "task20_29_radar_gt_visual_diagnostics.csv"
)

with summary_file.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summary[0])
    )
    writer.writeheader()
    writer.writerows(summary)

print("\n=== TASK 20.29 COMPLETE ===")
print(
    "Plots saved:",
    sum(row["PlotSaved"] for row in summary)
)
print("Summary saved:", summary_file.is_file())
print("Radar accuracy validated:", False)
print("Energy measured:", False)
