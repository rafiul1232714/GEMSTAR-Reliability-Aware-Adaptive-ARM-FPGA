import csv
import struct
import hashlib
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

selected = {0, 50, 100, 150, 200, 250,
            300, 350, 400, 423, 424, 450}

# Hypothesis only: conventional two-way light travel time
C = 299792458.0

rows = []
distance_arrays = {}
reflection_hashes = {}

with source.open("rb") as stream:
    frame = 0

    while True:
        header = stream.read(4)
        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete record header")

        length = struct.unpack("<I", header)[0]

        if not (0 < length <= 250_000_000):
            raise ValueError(f"Invalid record length: {length}")

        if frame not in selected:
            stream.seek(length, 1)
            frame += 1
            continue

        payload = stream.read(length)
        if len(payload) != length:
            raise ValueError("Truncated OSI payload")

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(payload)

        if not sv.lidar_sensor_view:
            raise ValueError(f"Missing LiDAR frame {frame}")

        lidar = sv.lidar_sensor_view[0]

        tof = np.asarray(
            [r.time_of_flight for r in lidar.reflection],
            dtype=np.float64
        )

        # Hypothetical distance, not yet validated against GEMSTAR source.
        distance = tof * C / 2.0
        distance_arrays[frame] = distance

        # Hash exact serialized reflection contents, not entire SensorView.
        reflection_bytes = b"".join(
            struct.pack("<I", len(b)) + b
            for b in (
                r.SerializeToString(deterministic=True)
                for r in lidar.reflection
            )
        )
        reflection_hashes[frame] = hashlib.sha256(
            reflection_bytes
        ).hexdigest()

        finite = np.isfinite(distance)

        zero = finite & (tof == 0)
        near_zero = finite & (tof > 0) & (distance < 0.01)
        short = finite & (distance >= 0.01) & (distance < 0.5)
        candidate = finite & (distance >= 0.5) & (distance <= 200)
        beyond = finite & (distance > 200)

        candidate_values = distance[candidate]

        row = {
            "Frame": frame,
            "TotalRays": len(tof),
            "ZeroTOF": int(zero.sum()),
            "NearZeroUnder1cm": int(near_zero.sum()),
            "Short1cmTo50cm": int(short.sum()),
            "Candidate0p5To200m": int(candidate.sum()),
            "Beyond200m": int(beyond.sum()),
            "NonFinite": int((~finite).sum()),
            "CandidateMedianM": (
                float(np.median(candidate_values))
                if len(candidate_values) else float("nan")
            ),
            "CandidateMaxM": (
                float(np.max(candidate_values))
                if len(candidate_values) else float("nan")
            )
        }
        rows.append(row)

        print(
            f"Frame {frame:3d}: zero={row['ZeroTOF']:4d}, "
            f"near-zero={row['NearZeroUnder1cm']:4d}, "
            f"short={row['Short1cmTo50cm']:4d}, "
            f"candidate={row['Candidate0p5To200m']:4d}, "
            f"median={row['CandidateMedianM']:.3f} m"
        )

        frame += 1

out_csv = base / "02_CSV_Data" / "task19_1c_tof_validity.csv"

with out_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

fig, ax = plt.subplots(figsize=(10, 5))

for frame in [0, 150, 423, 450]:
    values = distance_arrays[frame]
    values = values[
        np.isfinite(values) & (values >= 0.5) & (values <= 200)
    ]
    if len(values):
        ax.hist(
            values, bins=50, histtype="step",
            linewidth=1.5, label=f"Frame {frame}"
        )

ax.set_xlabel("Hypothetical range from round-trip TOF (m)")
ax.set_ylabel("Number of reflections")
ax.set_title("Task 19 - GEMSTAR LiDAR range distribution")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()

out_png = (
    base / "01_Graphs" / "task19_1c_tof_range_distribution.png"
)
fig.savefig(out_png, dpi=180)
plt.close(fig)

same_reflections = (
    reflection_hashes[423] == reflection_hashes[424]
)

print("\n=== TASK 19.1C COMPLETE ===")
print("Frames analyzed:", len(rows))
print("Frame 423 and 424 exact reflection match:", same_reflections)
print("CSV saved:", out_csv.is_file())
print("Graph saved:", out_png.is_file())
print("\nNOTE: Distances assume conventional round-trip TOF.")
print("GEMSTAR's actual TOF semantics remain to be verified.")
