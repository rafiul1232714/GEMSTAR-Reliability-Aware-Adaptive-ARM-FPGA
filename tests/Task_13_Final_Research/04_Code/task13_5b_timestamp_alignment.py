
# TASK 13.5B - TIMESTAMP ALIGNMENT
# Compare LiDAR, Radar and Ground Truth timestamps.
# Read-only input. Saves results separately under Task 13.

from pathlib import Path
import csv
import statistics

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

SOURCE = (
    ROOT / "tests" / "Task_11_Final_Research" /
    "02_CSV_Data"
)

OUTPUT = (
    ROOT / "tests" / "Task_13_Final_Research" /
    "02_CSV_Data"
)
OUTPUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "lidar": SOURCE / "task11_lidar_measurements.csv",
    "radar": SOURCE / "task11_radar_measurements.csv",
    "gt": SOURCE / "task11_groundtruth_objects.csv",
}


def load_timestamps(path):
    frames = {}
    inconsistent = set()

    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            frame = int(row["frame"])
            time_s = float(row["time_s"])

            if frame in frames:
                if abs(frames[frame] - time_s) > 1e-9:
                    inconsistent.add(frame)
            else:
                frames[frame] = time_s

    return frames, inconsistent


datasets = {}
inconsistencies = {}

for name, path in FILES.items():
    if not path.exists():
        raise FileNotFoundError(path)

    datasets[name], inconsistencies[name] = (
        load_timestamps(path)
    )

all_frames = sorted(
    set().union(*(set(d) for d in datasets.values()))
)

results = []

for frame in all_frames:
    tl = datasets["lidar"].get(frame)
    tr = datasets["radar"].get(frame)
    tg = datasets["gt"].get(frame)

    def diff_ms(a, b):
        if a is None or b is None:
            return None
        return abs(a - b) * 1000.0

    dlr = diff_ms(tl, tr)
    dlg = diff_ms(tl, tg)
    drg = diff_ms(tr, tg)

    diffs = [
        d for d in (dlr, dlg, drg)
        if d is not None
    ]

    results.append({
        "frame": frame,
        "lidar_time_s": tl,
        "radar_time_s": tr,
        "gt_time_s": tg,
        "lidar_radar_diff_ms": dlr,
        "lidar_gt_diff_ms": dlg,
        "radar_gt_diff_ms": drg,
        "max_pairwise_diff_ms":
            max(diffs) if diffs else None,
        "all_three_present": int(
            tl is not None
            and tr is not None
            and tg is not None
        ),
    })

output = OUTPUT / "task13_5b_timestamp_alignment.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0])
    )
    writer.writeheader()
    writer.writerows(results)

complete = [
    row for row in results
    if row["all_three_present"]
]

max_diffs = [
    row["max_pairwise_diff_ms"]
    for row in complete
]

print("\n===== TASK 13.5B - TIMESTAMP ALIGNMENT =====")

for name in ("lidar", "radar", "gt"):
    print(f"\n{name.upper()}")
    print("Frames with records:", len(datasets[name]))
    print(
        "Frames with inconsistent timestamps:",
        len(inconsistencies[name])
    )

print("\nTotal unique frames:", len(all_frames))
print("Frames with all three datasets:", len(complete))

if complete:
    print(
        "Median maximum timestamp difference:",
        f"{statistics.median(max_diffs):.9f} ms"
    )
    print(
        "Worst maximum timestamp difference:",
        f"{max(max_diffs):.9f} ms"
    )

    exact = sum(d <= 1e-6 for d in max_diffs)
    print("Frames aligned within 1 nanosecond:", exact)

print("\nFrame 150:")
match = next(
    (r for r in results if r["frame"] == 150),
    None
)
print(match if match else "Not present in all files")

print("\nSaved:", output)
print("TASK 13.5B COMPLETED")
