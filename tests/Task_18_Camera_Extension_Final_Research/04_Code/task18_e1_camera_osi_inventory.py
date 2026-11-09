import csv
import struct
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"

OUT = (
    ROOT / "tests" /
    "Task_18_Camera_Extension_Final_Research" /
    "02_CSV_Data" /
    "task18_e1_camera_osi_inventory.csv"
)

from osi3.osi_sensorview_pb2 import SensorView

def read_messages(path, limit=10):
    with path.open("rb") as f:
        for _ in range(limit):
            header = f.read(4)
            if len(header) < 4:
                break

            size = struct.unpack("<I", header)[0]

            if size <= 0 or size > 100_000_000:
                raise ValueError(
                    f"Invalid message size: {size}"
                )

            payload = f.read(size)

            if len(payload) != size:
                break

            msg = SensorView()
            msg.ParseFromString(payload)
            yield msg

def analyze_file(path):
    result = {
        "Recording": str(path.parent.name),
        "File": path.name,
        "FramesChecked": 0,
        "CameraSensorViews": 0,
        "CameraViewsWithData": 0,
        "LiDARViews": 0,
        "RadarViews": 0,
        "Status": "NOT_CHECKED",
    }

    try:
        for msg in read_messages(path):
            result["FramesChecked"] += 1

            for sensor in msg.camera_sensor_view:
                result["CameraSensorViews"] += 1

                if sensor.ByteSize() > 0:
                    result["CameraViewsWithData"] += 1

            result["LiDARViews"] += len(
                msg.lidar_sensor_view
            )

            result["RadarViews"] += len(
                msg.radar_sensor_view
            )

        if result["CameraSensorViews"] > 0:
            result["Status"] = "CAMERA_PRESENT_CHECK_PAYLOAD"
        else:
            result["Status"] = "NO_CAMERA_IN_SAMPLE"

    except Exception as exc:
        result["Status"] = "ERROR: " + str(exc)[:120]

    return result

def main():
    print("\n=== TASK 18.E1 CAMERA DATA INVENTORY ===")

    files = sorted(RAW.rglob("*_sv_*.osi"))

    print("SensorView recordings found:", len(files))

    if not files:
        print("No SensorView files found.")
        print("Check the data/raw directory.")
        return

    rows = []

    for path in files:
        row = analyze_file(path)
        rows.append(row)

        print(
            path.parent.name,
            "| Camera:",
            row["CameraSensorViews"],
            "| LiDAR:",
            row["LiDARViews"],
            "| Radar:",
            row["RadarViews"],
            "|",
            row["Status"]
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== SUMMARY ===")
    print("Recording files examined:", len(rows))

    print(
        "Files with camera views:",
        sum(r["CameraSensorViews"] > 0 for r in rows)
    )

    print("CSV saved:", OUT)

if __name__ == "__main__":
    main()
