import csv
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

SOURCE = (
    TASK / "08_Processed_Data"
    / "task23_04c_raw_lidar_measurements.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS_DIR = TASK / "06_Research_Findings"

NX = 251
NY = 21
C = 299792458.0

for folder in (CSV_DIR, GRAPH_DIR, FINDINGS_DIR):
    folder.mkdir(parents=True, exist_ok=True)

print("\n=== TASK 23.4D-1 RAY INDEX AUDIT ===")

if not SOURCE.is_file():
    raise FileNotFoundError(SOURCE)

# Analyze the raw measurements exported in Task 23.4C-1.
records = {}

with SOURCE.open(
    newline="", encoding="utf-8-sig"
) as handle:
    for row in csv.DictReader(handle):
        pair = int(row["PairID"])
        frame = int(row["Frame"])
        index = int(row["RayIndex"])

        key = (pair, frame)

        if key not in records:
            records[key] = {}

        records[key][index] = (
            float(row["TimeOfFlightS"]),
            float(row["SignalStrength"])
        )

summary = []
row_audit = []
maps = {}
rejected_sets = {}

for pair in (1, 2, 3):
    for frame in (0, 1, 25, 99):
        key = (pair, frame)
        data = records.get(key, {})

        if len(data) != NX * NY:
            raise RuntimeError(
                f"Pair {pair}, frame {frame}: "
                f"expected {NX * NY} rays, got {len(data)}"
            )

        expected_indices = set(range(NX * NY))
        if set(data) != expected_indices:
            raise RuntimeError(
                "Ray indices are missing or duplicated."
            )

        tof = np.array(
            [data[i][0] for i in range(NX * NY)],
            dtype=np.float64
        )
        strength = np.array(
            [data[i][1] for i in range(NX * NY)],
            dtype=np.float64
        )

        rng = C * tof / 2

        positive = (
            np.isfinite(tof)
            & np.isfinite(strength)
            & (tof > 0)
            & (strength > 0)
        )

        below = positive & (rng < 0.05)
        above = positive & (rng > 200)
        rejected = below | above

        # The row-major arrangement is an indexing
        # hypothesis; geometric orientation is not yet proven.
        image = rejected.reshape(NY, NX)

        maps[key] = image
        rejected_sets[key] = set(
            np.flatnonzero(rejected).tolist()
        )

        row_counts = image.sum(axis=1)

        for vertical_index, count in enumerate(row_counts):
            row_audit.append({
                "PairID": pair,
                "Frame": frame,
                "VerticalRowIndex": vertical_index,
                "RejectedRays": int(count),
                "HorizontalRaySlots": NX,
                "CompleteRejectedRow": bool(count == NX)
            })

        summary.append({
            "PairID": pair,
            "Frame": frame,
            "PositiveReturns": int(positive.sum()),
            "RejectedBelow005m": int(below.sum()),
            "RejectedAbove200m": int(above.sum()),
            "RejectedTotal": int(rejected.sum()),
            "CompleteRejectedRows": int(
                np.count_nonzero(row_counts == NX)
            ),
            "RowsContainingRejectedRays": int(
                np.count_nonzero(row_counts)
            ),
            "MinimumRejectedRangeM": (
                float(rng[rejected].min())
                if rejected.any() else None
            ),
            "MaximumRejectedRangeM": (
                float(rng[rejected].max())
                if rejected.any() else None
            )
        })

        print(
            f"Pair {pair} | Frame {frame:2d} | "
            f"Rejected={int(rejected.sum())} | "
            f"CompleteRows={int(np.count_nonzero(row_counts == NX))} | "
            f"AffectedRows={int(np.count_nonzero(row_counts))}"
        )

# Compare the exact rejected indices in frame zero.
sets = [rejected_sets[(p, 0)] for p in (1, 2, 3)]

same_indices = sets[0] == sets[1] == sets[2]

print("\n=== CROSS-RECORDING COMPARISON ===")
print("Frame-zero rejected indices identical:", same_indices)

for pair in (1, 2, 3):
    counts = maps[(pair, 0)].sum(axis=1)
    print(
        f"Pair {pair} rejected counts by vertical row:",
        counts.tolist()
    )

# Heatmap: rejected ray indices.
fig, axes = plt.subplots(
    3, 1, figsize=(12, 8),
    constrained_layout=True
)

for ax, pair in zip(axes, (1, 2, 3)):
    ax.imshow(
        maps[(pair, 0)],
        interpolation="nearest",
        aspect="auto",
        cmap="gray_r",
        vmin=0,
        vmax=1
    )
    ax.set_title(f"Pair {pair} - Frame 0 rejected rays")
    ax.set_ylabel("Provisional vertical row index")

axes[-1].set_xlabel("Horizontal ray index")
fig.suptitle(
    "LiDAR rejected-ray index maps (geometry unverified)"
)

map_path = (
    GRAPH_DIR / "task23_04d1_rejected_ray_maps.png"
)
fig.savefig(map_path, dpi=180)
plt.close(fig)

# Distribution of rejected rays by row.
fig, ax = plt.subplots(figsize=(10, 5))

for pair in (1, 2, 3):
    counts = maps[(pair, 0)].sum(axis=1)
    ax.plot(
        range(NY),
        counts,
        marker="o",
        label=f"Pair {pair}"
    )

ax.set_xlabel("Provisional vertical row index")
ax.set_ylabel("Rejected ray count")
ax.set_title("Frame-zero rejected returns by ray-grid row")
ax.grid(alpha=0.25)
ax.legend()
fig.tight_layout()

profile_path = (
    GRAPH_DIR / "task23_04d1_rejected_row_profile.png"
)
fig.savefig(profile_path, dpi=180)
plt.close(fig)

# Write summary CSVs.
summary_path = (
    CSV_DIR / "task23_04d1_ray_index_summary.csv"
)

rows_path = (
    CSV_DIR / "task23_04d1_vertical_row_audit.csv"
)

def write_csv(path, data):
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(data[0])
        )
        writer.writeheader()
        writer.writerows(data)

write_csv(summary_path, summary)
write_csv(rows_path, row_audit)

findings_path = (
    FINDINGS_DIR / "task23_04d1_ray_index_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.4D-1",
        "Source": str(SOURCE),
        "GridHypothesis": [NY, NX],
        "FrameZeroRejectedIndicesIdentical": same_indices,
        "Results": summary,
        "ScientificLimitations": [
            "The 21x251 arrangement is an indexing interpretation",
            "Beam angular positions remain unverified",
            "Identical rejected indices do not identify root cause",
            "No GroundTruth geometric comparison yet",
            "No proof of simulator initialization bug"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.4D-1 FINAL VERIFICATION ===")
print("Scans analyzed:", len(summary))
print("Frame-zero indices identical:", same_indices)
print("Summary CSV saved:", summary_path.is_file())
print("Row audit CSV saved:", rows_path.is_file())
print("Rejected-ray map saved:", map_path.is_file())
print("Row-profile graph saved:", profile_path.is_file())
print("Research findings saved:", findings_path.is_file())

print("\n=== TASK 23.4D-1 COMPLETE ===")
