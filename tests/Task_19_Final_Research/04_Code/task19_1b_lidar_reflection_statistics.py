import csv
import struct
from pathlib import Path
from collections import Counter

import numpy as np
from osi3 import osi_sensorview_pb2

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
base = root / "tests" / "Task_19_Final_Research"

source = (
    root / "data" / "raw" / "fog_mor100"
    / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

selected = {
    0, 50, 100, 150, 200, 250,
    300, 350, 400, 423, 424, 450
}

rows = []

with source.open("rb") as stream:
    frame_index = 0

    while True:
        header = stream.read(4)
        if not header:
            break

        if len(header) != 4:
            raise ValueError("Incomplete record header")

        length = struct.unpack("<I", header)[0]
        data = stream.read(length)

        if len(data) != length:
            raise ValueError("Incomplete record payload")

        if frame_index not in selected:
            frame_index += 1
            continue

        sv = osi_sensorview_pb2.SensorView()
        sv.ParseFromString(data)

        if not sv.lidar_sensor_view:
            print(f"Frame {frame_index}: No LiDAR view")
            frame_index += 1
            continue

        lidar = sv.lidar_sensor_view[0]
        reflections = lidar.reflection

        tof = np.array(
            [r.time_of_flight for r in reflections],
            dtype=np.float64
        )

        strength = np.array(
            [r.signal_strength for r in reflections],
            dtype=np.float64
        )

        object_ids = [
            int(r.object_id.value)
            for r in reflections
            if r.HasField("object_id")
        ]

        positive = tof[np.isfinite(tof) & (tof > 0)]
        finite = np.isfinite(tof)

        row = {
            "Frame": frame_index,
            "Reflections": len(reflections),
            "FiniteTOF": int(finite.sum()),
            "ZeroTOF": int(np.sum(tof == 0)),
            "PositiveTOF": len(positive),
            "TOF_Min": float(np.min(tof)) if len(tof) else 0,
            "TOF_Median": float(np.median(tof)) if len(tof) else 0,
            "TOF_Max": float(np.max(tof)) if len(tof) else 0,
            "Strength_Min": float(np.min(strength)) if len(strength) else 0,
            "Strength_Median": float(np.median(strength)) if len(strength) else 0,
            "Strength_Max": float(np.max(strength)) if len(strength) else 0,
            "DistinctObjectIDs": len(set(object_ids)),
            "ObjectIDZero": object_ids.count(0),
        }

        rows.append(row)

        print(
            f"Frame {frame_index:3d} | "
            f"reflections={len(reflections):5d} | "
            f"positive TOF={len(positive):5d} | "
            f"TOF median={row['TOF_Median']:.6e} | "
            f"TOF max={row['TOF_Max']:.6e} | "
            f"objects={row['DistinctObjectIDs']}"
        )

        if frame_index == 0:
            print("\nFirst 10 reflection samples:")
            for i, r in enumerate(reflections[:10]):
                oid = (
                    r.object_id.value
                    if r.HasField("object_id")
                    else "MISSING"
                )
                print(
                    f"{i:2d}: "
                    f"TOF={r.time_of_flight:.9e}, "
                    f"strength={r.signal_strength:.6f}, "
                    f"object_id={oid}"
                )
            print()

        frame_index += 1

output = (
    base / "02_CSV_Data"
    / "task19_1b_lidar_reflection_statistics.csv"
)

if rows:
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

print("\n=== TASK 19.1B COMPLETE ===")
print("Selected frames analyzed:", len(rows))
print("CSV saved:", output.is_file())
print("CSV:", output)
