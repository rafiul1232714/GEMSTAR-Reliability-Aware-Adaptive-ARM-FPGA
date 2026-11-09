import csv
import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\gemstar\Output")
OUT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_23_Final_Research"
    r"\02_CSV_Data\task23_12C_01_camera_timing_audit.csv"
)

SCENARIOS = {
    "CLEAR": "*_sv_*_T23_12_CAMERA_CLEAR.osi",
    "FOG100": "*_sv_*_T23_12_CAMERA_FOG100.osi",
    "FOG20": "*_sv_*_T23_12_CAMERA_FOG20.osi",
}

rows = []

for scenario, pattern in SCENARIOS.items():

    matches = list(ROOT.glob(pattern))

    if len(matches) != 1:
        raise RuntimeError(
            f"{scenario}: expected one recording, found {len(matches)}"
        )

    path = matches[0]

    with path.open("rb") as stream:

        for index in range(10):

            header = stream.read(4)

            if len(header) != 4:
                raise RuntimeError(
                    f"{scenario}: incomplete header at frame {index}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError(
                    f"{scenario}: invalid frame size {size}"
                )

            data = stream.read(size)

            if len(data) != size:
                raise RuntimeError(
                    f"{scenario}: incomplete frame {index}"
                )

            msg = SensorView()
            msg.ParseFromString(data)

            timestamp = msg.timestamp

            seconds = timestamp.seconds + timestamp.nanos * 1e-9

            camera_count = len(msg.camera_sensor_view)

            image_bytes = (
                len(msg.camera_sensor_view[0].image_data)
                if camera_count else 0
            )

            rows.append({
                "scenario": scenario,
                "frame": index,
                "timestamp_seconds": f"{seconds:.9f}",
                "camera_count": camera_count,
                "image_bytes": image_bytes,
            })

            print(
                f"{scenario} FRAME={index} "
                f"TIME={seconds:.6f} "
                f"CAMERA_COUNT={camera_count} "
                f"BYTES={image_bytes}"
            )

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "scenario",
            "frame",
            "timestamp_seconds",
            "camera_count",
            "image_bytes"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV_SAVED={OUT}")
print(f"ROWS={len(rows)}")
print("TASK23_12C_01_CAMERA_TIMING_AUDIT_PASS")
