import csv
import hashlib
import struct
import zlib
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests/Task_28_Final_Research"

OUT = TASK / "04_Plots/Camera_YOLO_Comparison/Inputs"
MANIFEST = (
    TASK / "02_CSV_Data"
    / "task28_3D4B2_camera_image_manifest.csv"
)

SCENARIOS = {
    "baseline_clear": 829,
    "baseline_fog_working_radar": 794,
    "fog_mor100": 466,
    "fog_postfix_validation": 705,
}

FIELDS = [
    "Scenario", "Recording", "Frame", "Timestamp_ns",
    "Width", "Height", "ImageBytes", "ImageSHA256",
    "OutputPNG", "DecodingConvention"
]


def chunk(kind, payload):
    return (
        struct.pack(">I", len(payload))
        + kind + payload
        + struct.pack(
            ">I", zlib.crc32(kind + payload) & 0xffffffff
        )
    )


def save_png(path, pixels, width, height):
    if len(pixels) != width * height * 3:
        raise RuntimeError("Unexpected Camera image size")

    stride = width * 3
    scanlines = b"".join(
        b"\x00" + pixels[y*stride:(y+1)*stride]
        for y in range(height)
    )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        )
        + chunk(b"IDAT", zlib.compress(scanlines, 6))
        + chunk(b"IEND", b"")
    )

    with path.open("xb") as stream:
        stream.write(png)


def process(scenario, expected):
    sources = sorted(
        (ROOT / "data/raw" / scenario).glob("*_sv_*.osi")
    )

    if len(sources) != 1:
        raise RuntimeError(
            f"{scenario}: expected exactly one SensorView recording"
        )

    source = sources[0]

    selected = sorted(set(
        round(i * (expected - 1) / 4)
        for i in range(5)
    ))

    print(f"\nScenario: {scenario}")
    print(f"Selected frames: {selected}")

    records = []
    total_frames = 0

    with source.open("rb") as stream:
        while True:
            header = stream.read(4)

            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Truncated OSI header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid OSI message size")

            payload = stream.read(size)

            if len(payload) != size:
                raise RuntimeError("Truncated OSI message")

            if total_frames in selected:
                sv = SensorView()
                sv.ParseFromString(payload)

                if len(sv.camera_sensor_view) != 1:
                    raise RuntimeError(
                        f"Missing Camera: {scenario}, {total_frames}"
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

                pixels = bytes(camera.image_data)

                if (width, height) != (640, 480):
                    raise RuntimeError("Unexpected image dimensions")

                name = (
                    f"task28_3D4B2_{scenario}"
                    f"_frame{total_frames:05d}.png"
                )

                output = OUT / name

                save_png(
                    output, pixels, width, height
                )

                timestamp = (
                    int(sv.timestamp.seconds) * 1_000_000_000
                    + int(sv.timestamp.nanos)
                )

                records.append({
                    "Scenario": scenario,
                    "Recording": source.name,
                    "Frame": total_frames,
                    "Timestamp_ns": timestamp,
                    "Width": width,
                    "Height": height,
                    "ImageBytes": len(pixels),
                    "ImageSHA256": hashlib.sha256(
                        pixels
                    ).hexdigest(),
                    "OutputPNG": str(output),
                    "DecodingConvention": "Task24_RGB_assumption",
                })

                print(
                    f"  Frame {total_frames}: "
                    f"{width}x{height} saved"
                )

            total_frames += 1

    if total_frames != expected:
        raise RuntimeError(
            f"{scenario}: expected {expected} frames, "
            f"got {total_frames}"
        )

    if len(records) != 5:
        raise RuntimeError("Expected five images per scenario")

    return records


def main():
    if OUT.exists() or MANIFEST.exists():
        raise RuntimeError(
            "Outputs already exist; no overwrite permitted"
        )

    OUT.mkdir(parents=True, exist_ok=False)

    rows = []

    for scenario, expected in SCENARIOS.items():
        rows.extend(process(scenario, expected))

    if len(rows) != 20:
        raise RuntimeError("Expected exactly 20 images")

    with MANIFEST.open(
        "x", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=FIELDS
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\n=====================================")
    print("TASK 28.3D.4B.2 — CAMERA EXTRACTION")
    print("=====================================")
    print("Scenarios: 4")
    print(f"Images extracted: {len(rows)}")
    print(f"Image directory: {OUT}")
    print(f"Manifest: {MANIFEST}")
    print("Original recordings modified: NO")
    print("STATUS: TASK 28.3D.4B.2 SUCCESS")


if __name__ == "__main__":
    main()
