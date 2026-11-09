
from pathlib import Path
import csv
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

DATA = (
    ROOT / "tests"
    / "Task_11_Final_Research"
    / "02_CSV_Data"
)

CLUSTERS = DATA / "task11_lidar_cluster_labels_frame101.csv"
MEASUREMENTS = DATA / "task11_lidar_measurements.csv"

# Step 1: Read diagnostic simulator IDs for frame 101
object_ids = {}

with MEASUREMENTS.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if int(row["frame"]) == 101:
            key = (
                int(row["frame"]),
                int(row["ray_index"])
            )
            object_ids[key] = row["object_id_diagnostic"]

# Step 2: Compare DBSCAN cluster membership with IDs
counts = Counter()
total = Counter()

with CLUSTERS.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cluster = int(row["cluster_id"])
        key = (
            int(row["frame"]),
            int(row["ray_index"])
        )

        object_id = object_ids.get(key, "UNKNOWN")

        counts[(cluster, object_id)] += 1
        total[cluster] += 1

# Step 3: Display results
print("\nTASK 11.5G - CLUSTER VALIDATION")

for cluster in sorted(total):
    print(f"\nCluster {cluster}: {total[cluster]} points")

    for (c, obj), count in counts.most_common():
        if c == cluster:
            percentage = 100 * count / total[cluster]
            print(
                f"  Simulator object {obj}: "
                f"{count} points ({percentage:.2f}%)"
            )

# Step 4: Save research results
output = DATA / "task11_cluster_objectid_validation.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "cluster_id",
        "object_id_diagnostic",
        "point_count",
        "percentage"
    ])

    for (cluster, obj), count in sorted(counts.items()):
        percentage = 100 * count / total[cluster]
        writer.writerow([
            cluster, obj, count, percentage
        ])

print("\nSaved:", output)
print("TASK 11.5G COMPLETED")
