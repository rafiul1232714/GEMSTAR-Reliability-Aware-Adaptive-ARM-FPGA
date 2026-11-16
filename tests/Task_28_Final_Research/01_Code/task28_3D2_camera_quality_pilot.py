import csv
import hashlib
import math
import struct
import zlib
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_28_Final_Research"
OUT = TASK / "02_CSV_Data/task28_3D2_camera_quality_pilot.csv"
PLOTS = TASK / "04_Plots/Camera_Image_Pilot"

SCENARIOS = [
    "baseline_clear",
    "fog_postfix_validation",
]

MAX_FRAMES = 10
PREVIEW_FRAME = 1

FIELDS = [
    "Scenario", "Frame", "Width", "Height",
    "Timestamp_ns", "Channel0Mean", "Channel1Mean",
    "Channel2Mean", "MeanIntensity", "IntensityStd",
    "DarkPixelPct", "BrightPixelPct",
    "SampledEdgeMagnitude", "RepeatedImage"
]


def png_chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(
            ">I", zlib.crc32(kind + data) & 0xffffffff
        )
    )


def write_png(path, width, height, data, swap_channels):
    """
    Two visual hypotheses:
    original bytes interpreted as RGB,
    or original bytes interpreted as BGR.
    This does not verify the true encoding.
    """
    if path.exists():
        raise RuntimeError(f"Preview exists: {path}")

    stride = width * 3
    rows = bytearray()

    for y in range(height):
        row = data[y * stride:(y + 1) * stride]
        rows.append(0)  # PNG no-filter row

        if swap_channels:
            transformed = bytearray(row)
            transformed[0::3] = row[2::3]
            transformed[2::3] = row[0::3]
            rows.extend(transformed)
        else:
            rows.extend(row)

    output = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(
            b"IHDR",
            struct.pack(
                ">IIBBBBB",
                width, height, 8, 2, 0, 0, 0
            )
        )
        + png_chunk(
            b"IDAT", zlib.compress(bytes(rows), 6)
        )
        + png_chunk(b"IEND", b"")
    )

    with path.open("xb") as f:
        f.write(output)


def metrics(image, width, height):
    """
    Provisional packed 3-channel interpretation.

    MeanIntensity uses the arithmetic mean of the
    three channels, so swapping R and B leaves it
    unchanged. These are image characteristics,
    not ground-truth detection quality.
    """
    if len(image) != width * height * 3:
        raise RuntimeError("Unexpected image data length")

    n = width * height

    channel_means = [
        sum(image[i::3]) / n for i in range(3)
    ]

    # 256-bin histogram of mean channel intensity.
    histogram = [0] * 256
    dark = 0
    bright = 0

    # Spatial sampling for an inexpensive detail proxy.
    step = 4
    previous_sampled_row = None
    edge_sum = 0.0
    edge_count = 0

    for y in range(height):
        horizontal_previous = None
        sampled_row = []

        for x in range(width):
            p = (y * width + x) * 3

            a = image[p]
            b = image[p + 1]
            c = image[p + 2]

            intensity = (a + b + c) / 3.0

            if a <= 5 and b <= 5 and c <= 5:
                dark += 1

            if a >= 250 and b >= 250 and c >= 250:
                bright += 1

            histogram[min(255, int(intensity))] += 1

            if y % step == 0 and x % step == 0:
                sampled_row.append(intensity)

                if horizontal_previous is not None:
                    edge_sum += abs(
                        intensity - horizontal_previous
                    )
                    edge_count += 1

                horizontal_previous = intensity

        if y % step == 0:
            if previous_sampled_row is not None:
                for current, previous in zip(
                    sampled_row, previous_sampled_row
                ):
                    edge_sum += abs(current - previous)
                    edge_count += 1

            previous_sampled_row = sampled_row

    mean_value = sum(
        intensity * count
        for intensity, count in enumerate(histogram)
    ) / n

    # Histogram quantization makes these descriptive
    # metrics approximate to < 1 intensity unit.
    variance = sum(
        count * (intensity - mean_value) ** 2
        for intensity, count in enumerate(histogram)
    ) / n

    return {
        "Channel0Mean": round(channel_means[0], 4),
        "Channel1Mean": round(channel_means[1], 4),
        "Channel2Mean": round(channel_means[2], 4),
        "MeanIntensity": round(mean_value, 4),
        "IntensityStd": round(math.sqrt(variance), 4),
        "DarkPixelPct": round(100 * dark / n, 4),
        "BrightPixelPct": round(100 * bright / n, 4),
        "SampledEdgeMagnitude": round(
            edge_sum / edge_count, 4
        ) if edge_count else 0.0,
    }


def process(scenario):
    sources = sorted(
        (ROOT / "data/raw" / scenario).glob("*_sv_*.osi")
    )

    if len(sources) != 1:
        raise RuntimeError(
            f"{scenario}: expected one recording"
        )

    results = []
    previous_hash = None

    with sources[0].open("rb") as stream:
        for frame in range(MAX_FRAMES):
            header = stream.read(4)

            if len(header) != 4:
                raise RuntimeError(
                    f"Missing/truncated frame {frame}"
                )

            length = struct.unpack("<I", header)[0]

            if not 0 < length <= 100_000_000:
                raise RuntimeError("Invalid OSI frame length")

            payload = stream.read(length)

            if len(payload) != length:
                raise RuntimeError("Truncated OSI payload")

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            if len(sv.camera_sensor_view) != 1:
                raise RuntimeError("Expected one Camera view")

            camera = sv.camera_sensor_view[0]
            config = camera.view_configuration

            width = int(
                config.number_of_pixels_horizontal
            )
            height = int(
                config.number_of_pixels_vertical
            )

            image = bytes(camera.image_data)

            if width != 640 or height != 480:
                raise RuntimeError(
                    f"Unexpected resolution: {width}x{height}"
                )

            digest = hashlib.sha256(image).digest()

            timestamp = (
                int(sv.timestamp.seconds) * 1_000_000_000
                + int(sv.timestamp.nanos)
            )

            record = {
                "Scenario": scenario,
                "Frame": frame,
                "Width": width,
                "Height": height,
                "Timestamp_ns": timestamp,
                **metrics(image, width, height),
                "RepeatedImage": int(
                    digest == previous_hash
                ) if previous_hash is not None else 0,
            }

            results.append(record)
            previous_hash = digest

            if frame == PREVIEW_FRAME:
                for label, swap in [
                    ("rgb_assumption", False),
                    ("bgr_assumption", True),
                ]:
                    filename = (
                        f"task28_3D2_{scenario}"
                        f"_frame{frame:04d}_{label}.png"
                    )

                    write_png(
                        PLOTS / filename,
                        width,
                        height,
                        image,
                        swap
                    )

    return results


def main():
    if OUT.exists():
        raise RuntimeError("Output CSV already exists")

    planned = [
        PLOTS / (
            f"task28_3D2_{scenario}_frame0001_{mode}.png"
        )
        for scenario in SCENARIOS
        for mode in ["rgb_assumption", "bgr_assumption"]
    ]

    if any(p.exists() for p in planned):
        raise RuntimeError(
            "Preview output exists; no overwrite"
        )

    rows = []

    for scenario in SCENARIOS:
        print(f"Analyzing {scenario}...", flush=True)
        rows.extend(process(scenario))

    with OUT.open(
        "x", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TASK 28.3D.2 CAMERA QUALITY PILOT ===")

    for scenario in SCENARIOS:
        subset = [
            r for r in rows
            if r["Scenario"] == scenario
        ]

        def average(field):
            return sum(
                r[field] for r in subset
            ) / len(subset)

        print(f"\nScenario: {scenario}")
        print(f"Frames: {len(subset)}")
        print(
            f"Mean intensity: "
            f"{average('MeanIntensity'):.3f}"
        )
        print(
            f"Intensity std: "
            f"{average('IntensityStd'):.3f}"
        )
        print(
            f"Sampled edge magnitude: "
            f"{average('SampledEdgeMagnitude'):.3f}"
        )
        print(
            f"Repeated images: "
            f"{sum(r['RepeatedImage'] for r in subset)}"
        )

    print(f"\nCSV: {OUT}")
    print(f"Preview directory: {PLOTS}")
    print("Preview files: 4 PNG")
    print("STATUS: TASK 28.3D.2 SUCCESS")
    print(
        "NOTE: Channel order is provisional."
    )
    print(
        "NOTE: Image characteristics are not "
        "detection accuracy."
    )


if __name__ == "__main__":
    main()
