import csv
import math
import struct
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_19_Final_Research"

RAW = ROOT / "data" / "raw"
OUTPUT = BASE / "02_CSV_Data"
OUTPUT.mkdir(parents=True, exist_ok=True)

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_postfix_validation",
    "task05_fog_test",
]

LIGHT_SPEED = 299705543.0
INVALID_ID = (1 << 64) - 1
EXPECTED_RAYS = 5271

rows = []

print("\n=== TASK 19.10K INDEPENDENT RECORDING AUDIT ===")

for scenario in SCENARIOS:

    folder = RAW / scenario
    recordings = sorted(folder.glob("*_sv_*.osi"))

    if not recordings:
        print(f"\n{scenario}: no SensorView recording found")
        continue

    for path in recordings:

        print(f"\nScenario: {scenario}")
        print(f"Recording: {path.name}")

        frame_count = 0
        lidar_frames = 0
        ray_counts = set()

        samples = []

        with path.open("rb") as f:

            while True:

                header = f.read(4)

                if not header:
                    break

                if len(header) != 4:
                    raise RuntimeError(
                        f"Truncated header in {path.name}"
                    )

                length = struct.unpack("<I", header)[0]

                if not 0 < length <= 100_000_000:
                    raise RuntimeError(
                        f"Invalid record length at frame {frame_count}"
                    )

                payload = f.read(length)

                if len(payload) != length:
                    raise RuntimeError(
                        f"Truncated record at frame {frame_count}"
                    )

                sv = osi_sensorview_pb2.SensorView()
                sv.ParseFromString(payload)

                if len(sv.lidar_sensor_view) > 0:

                    lidar_frames += 1

                    reflections = sv.lidar_sensor_view[0].reflection
                    ray_counts.add(len(reflections))

                    # Sample every 50th frame, plus frame 0.
                    if frame_count % 50 == 0:

                        valid = 0
                        roi = 0

                        for i, r in enumerate(reflections):

                            distance = (
                                float(r.time_of_flight)
                                * LIGHT_SPEED / 2
                            )

                            strength = float(r.signal_strength)
                            oid = int(r.object_id.value)

                            if not (
                                math.isfinite(distance)
                                and math.isfinite(strength)
                                and 0.5 <= distance <= 200
                                and strength > 0
                                and oid != INVALID_ID
                            ):
                                continue

                            valid += 1

                            if len(reflections) == EXPECTED_RAYS:

                                hi = i % 251
                                vi = i // 251

                                h = math.radians(
                                    -45 + 90 * hi / 250
                                )

                                v = math.radians(
                                    -10 + 20 * vi / 20
                                )

                                x = (
                                    distance
                                    * math.cos(v)
                                    * math.cos(h)
                                )

                                y = (
                                    -distance
                                    * math.cos(v)
                                    * math.sin(h)
                                )

                                if 0 <= x <= 20 and -6 <= y <= 6:
                                    roi += 1

                        samples.append({
                            "Scenario": scenario,
                            "Recording": path.name,
                            "FrameIndex": frame_count,
                            "Reflections": len(reflections),
                            "ValidCandidates": valid,
                            "ROIPoints": roi,
                        })

                frame_count += 1

        print("Total frames:", frame_count)
        print("Frames with LiDAR:", lidar_frames)
        print("Observed reflection counts:", sorted(ray_counts))
        print("Sampled frames:", len(samples))

        for row in samples:
            print(
                f"  Frame {row['FrameIndex']:3d}: "
                f"valid={row['ValidCandidates']:4d}, "
                f"ROI={row['ROIPoints']:4d}"
            )

        rows.extend(samples)

output = OUTPUT / "task19_10k_independent_recording_audit.csv"

fields = [
    "Scenario",
    "Recording",
    "FrameIndex",
    "Reflections",
    "ValidCandidates",
    "ROIPoints",
]

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 19.10K COMPLETE ===")
print("Sampled records:", len(rows))
print("CSV saved:", output.is_file())
print("Output:", output)
