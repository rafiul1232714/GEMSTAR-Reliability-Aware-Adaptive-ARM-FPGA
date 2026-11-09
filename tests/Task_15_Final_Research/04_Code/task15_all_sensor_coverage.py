from pathlib import Path
import csv
import sys

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_15_Final_Research"
MANIFEST = TASK / "02_CSV_Data" / "task15_dataset_manifest.csv"
OUTPUT = TASK / "02_CSV_Data" / "task15_all_sensor_coverage.csv"

MAX_MESSAGE_BYTES = 256 * 1024 * 1024


def analyze(path):
    counts = {
        "TotalFrames": 0,
        "CameraViewFrames": 0,
        "LiDARViewFrames": 0,
        "RadarViewFrames": 0,
        "CameraPayloadFrames": 0,
        "LiDARPayloadFrames": 0,
        "RadarPayloadFrames": 0,
    }

    with path.open("rb") as f:
        while True:
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Truncated header")

            size = int.from_bytes(header, "little")
            if not 0 < size <= MAX_MESSAGE_BYTES:
                raise ValueError(f"Invalid message size: {size}")

            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated payload")

            sv = SensorView()
            sv.ParseFromString(payload)

            counts["TotalFrames"] += 1
            cameras = sv.camera_sensor_view
            lidars = sv.lidar_sensor_view
            radars = sv.radar_sensor_view

            counts["CameraViewFrames"] += bool(cameras)
            counts["LiDARViewFrames"] += bool(lidars)
            counts["RadarViewFrames"] += bool(radars)

            counts["CameraPayloadFrames"] += any(
                bool(c.image_data) for c in cameras
            )
            counts["LiDARPayloadFrames"] += any(
                len(l.reflection) > 0 for l in lidars
            )
            counts["RadarPayloadFrames"] += any(
                len(r.reflection) > 0 for r in radars
            )
    return counts


def main():
    with MANIFEST.open(newline="", encoding="utf-8-sig") as f:
        manifest = list(csv.DictReader(f))

    # One representative per identical file content.
    selected = {}
    for row in manifest:
        if row["FileType"] != "SensorView":
            continue

        hash_value = row["SHA256"]
        path = Path(row["FullPath"])

        if hash_value not in selected:
            selected[hash_value] = path
        elif str(path).lower().find(r"\data\raw\\") >= 0:
            selected[hash_value] = path

    results = []
    for i, (sha, path) in enumerate(selected.items(), start=1):
        print(f"[{i}/{len(selected)}] {path.name}", flush=True)

        record = {
            "Recording": path.name,
            "FullPath": str(path),
            "SHA256": sha,
            "Status": "OK",
            "Error": "",
        }

        try:
            record.update(analyze(path))
        except Exception as e:
            record["Status"] = "ERROR"
            record["Error"] = str(e)

        results.append(record)

    columns = [
        "Recording", "FullPath", "SHA256", "Status", "Error",
        "TotalFrames", "CameraViewFrames", "LiDARViewFrames",
        "RadarViewFrames", "CameraPayloadFrames",
        "LiDARPayloadFrames", "RadarPayloadFrames",
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)

    print("\n=== TASK 15 ALL SENSOR COVERAGE ===")
    print("Recordings analyzed:", len(results))
    print("Successful:", sum(r["Status"] == "OK" for r in results))
    print("Errors:", sum(r["Status"] == "ERROR" for r in results))
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()