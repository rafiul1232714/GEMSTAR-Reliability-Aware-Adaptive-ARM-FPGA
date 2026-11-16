import csv
import hashlib
import struct
from pathlib import Path
from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_28_Final_Research"

OUT = (
    TASK / "02_CSV_Data"
    / "task28_3D1_camera_payload_pilot.csv"
)

SCENARIOS = [
    "baseline_clear",
    "fog_postfix_validation"
]

MAX_FRAMES = 10

FIELDS = [
    "Scenario", "Frame", "Timestamp_ns",
    "Width", "Height", "ImageBytes",
    "BytesPerPixelRatio", "SHA256",
    "ImageRepeated", "First16Hex"
]


def process(scenario):
    folder = ROOT / "data" / "raw" / scenario

    files = sorted(folder.glob("*_sv_*.osi"))

    if len(files) != 1:
        raise RuntimeError(
            f"{scenario}: expected one SV recording, "
            f"found {len(files)}"
        )

    rows = []
    previous_digest = None

    with files[0].open("rb") as stream:
        for frame in range(MAX_FRAMES):
            header = stream.read(4)

            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Truncated OSI header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid OSI frame length")

            payload = stream.read(size)

            if len(payload) != size:
                raise RuntimeError("Truncated OSI payload")

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            if len(sv.camera_sensor_view) != 1:
                raise RuntimeError(
                    f"{scenario}: expected one Camera view"
                )

            camera = sv.camera_sensor_view[0]

            width = int(
                camera.view_configuration
                .number_of_pixels_horizontal
            )
            height = int(
                camera.view_configuration
                .number_of_pixels_vertical
            )

            if width <= 0 or height <= 0:
                raise RuntimeError("Invalid image dimensions")

            image = bytes(camera.image_data)

            if len(image) == 0:
                raise RuntimeError(
                    f"Empty Camera image at frame {frame}"
                )

            digest = hashlib.sha256(image).hexdigest()

            timestamp = (
                int(sv.timestamp.seconds) * 1_000_000_000
                + int(sv.timestamp.nanos)
            )

            rows.append({
                "Scenario": scenario,
                "Frame": frame,
                "Timestamp_ns": timestamp,
                "Width": width,
                "Height": height,
                "ImageBytes": len(image),
                "BytesPerPixelRatio": round(
                    len(image) / (width * height), 6
                ),
                "SHA256": digest,
                "ImageRepeated": int(
                    previous_digest == digest
                ) if previous_digest is not None else 0,
                "First16Hex": image[:16].hex()
            })

            previous_digest = digest

    if len(rows) != MAX_FRAMES:
        raise RuntimeError(
            f"{scenario}: expected {MAX_FRAMES} frames"
        )

    return rows


def main():
    if OUT.exists():
        raise RuntimeError("Output already exists")

    rows = []

    for scenario in SCENARIOS:
        rows.extend(process(scenario))

    # Write only after both recordings pass inspection.
    with OUT.open(
        "x", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=FIELDS
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TASK 28.3D.1 CAMERA PILOT ===")

    for scenario in SCENARIOS:
        selected = [
            r for r in rows
            if r["Scenario"] == scenario
        ]

        first = selected[0]
        repeated = sum(
            r["ImageRepeated"] for r in selected
        )

        print(f"\nScenario: {scenario}")
        print(f"Frames: {len(selected)}")
        print(
            f"Resolution: {first['Width']} x "
            f"{first['Height']}"
        )
        print(f"Image bytes/frame: {first['ImageBytes']}")
        print(
            f"Bytes/pixel ratio: "
            f"{first['BytesPerPixelRatio']}"
        )
        print(f"Repeated image payloads: {repeated}")
        print(
            f"First 16 image bytes: "
            f"{first['First16Hex']}"
        )

    print("\n=== CAMERA PROTOBUF FIELDS ===")

    fields = (
        osi_sensorview_pb2.SensorView
        .DESCRIPTOR.fields_by_name
    )

    print(
        "SensorView camera field: "
        + str("camera_sensor_view" in fields)
    )

    example = osi_sensorview_pb2.SensorView()

    for field in (
        example.camera_sensor_view.add()
        .DESCRIPTOR.fields
    ):
        print(
            f"{field.name}: type={field.type}"
        )

    print(f"\nCSV: {OUT}")
    print("STATUS: TASK 28.3D.1 SUCCESS")
    print(
        "NOTE: Bytes/pixel ratio alone "
        "does not establish image encoding."
    )


if __name__ == "__main__":
    main()
