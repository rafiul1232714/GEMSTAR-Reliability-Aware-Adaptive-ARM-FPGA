import csv
import hashlib
import math
import statistics
import struct
from collections import defaultdict
from pathlib import Path

from osi3 import osi_sensorview_pb2

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_28_Final_Research"

OUT = TASK / "02_CSV_Data"
FRAME_CSV = OUT / "task28_3D3_full_camera_metrics.csv"
SUMMARY_CSV = OUT / "task28_3D3_camera_scenario_summary.csv"

SCENARIOS = {
    "baseline_clear": 829,
    "baseline_fog_working_radar": 794,
    "fog_mor100": 466,
    "fog_postfix_validation": 705,
}

SAMPLE_STEP = 8

FRAME_FIELDS = [
    "Scenario",
    "Recording",
    "Frame",
    "Timestamp_ns",
    "DT_ms",
    "Width",
    "Height",
    "ImageBytes",
    "ImageRepeated",
    "SampledPixels",
    "SampledIntensityMean",
    "SampledIntensityStd",
    "SampledEdgeMagnitude",
    "SampledDarkPct",
    "SampledBrightPct",
    "SampledChannel0Mean",
    "SampledChannel1Mean",
    "SampledChannel2Mean",
]

SUMMARY_FIELDS = [
    "Scenario",
    "Frames",
    "ImageBytesPerFrame",
    "RepeatedImages",
    "RepeatedImagePct",
    "MeanIntensity",
    "MedianIntensity",
    "P05Intensity",
    "P95Intensity",
    "MeanIntensityStd",
    "MeanEdgeMagnitude",
    "MeanDarkPct",
    "MeanBrightPct",
    "MedianDT_ms",
    "P95DT_ms",
]


def percentile(values, p):
    s = sorted(values)
    if not s:
        return float("nan")
    location = (len(s) - 1) * p
    lo = math.floor(location)
    hi = math.ceil(location)
    return s[lo] + (s[hi] - s[lo]) * (location - lo)


def image_metrics(image, width, height):
    """
    Assumes tightly packed three-byte pixel groups.
    No RGB/BGR channel-order claim is made.

    The channel-average intensity is invariant
    to swapping the first and third channels.

    Spatial sampling is deterministic: every 8th
    row and column. This is not object-detection
    accuracy or a calibrated sharpness metric.
    """
    if len(image) != width * height * 3:
        raise RuntimeError("Unexpected Camera payload length")

    intensities = []
    channel_sums = [0, 0, 0]
    dark = 0
    bright = 0
    edge_sum = 0.0
    edge_count = 0
    previous_row = None

    for y in range(0, height, SAMPLE_STEP):
        row = []
        last_horizontal = None

        for x in range(0, width, SAMPLE_STEP):
            index = (y * width + x) * 3

            a = image[index]
            b = image[index + 1]
            c = image[index + 2]

            channel_sums[0] += a
            channel_sums[1] += b
            channel_sums[2] += c

            intensity = (a + b + c) / 3.0
            intensities.append(intensity)
            row.append(intensity)

            if a <= 5 and b <= 5 and c <= 5:
                dark += 1

            if a >= 250 and b >= 250 and c >= 250:
                bright += 1

            if last_horizontal is not None:
                edge_sum += abs(intensity - last_horizontal)
                edge_count += 1

            last_horizontal = intensity

        if previous_row is not None:
            for current, previous in zip(row, previous_row):
                edge_sum += abs(current - previous)
                edge_count += 1

        previous_row = row

    n = len(intensities)

    return {
        "SampledPixels": n,
        "SampledIntensityMean": round(
            statistics.fmean(intensities), 5
        ),
        "SampledIntensityStd": round(
            statistics.pstdev(intensities), 5
        ),
        "SampledEdgeMagnitude": round(
            edge_sum / edge_count, 5
        ) if edge_count else 0,
        "SampledDarkPct": round(100 * dark / n, 5),
        "SampledBrightPct": round(100 * bright / n, 5),
        "SampledChannel0Mean": round(
            channel_sums[0] / n, 5
        ),
        "SampledChannel1Mean": round(
            channel_sums[1] / n, 5
        ),
        "SampledChannel2Mean": round(
            channel_sums[2] / n, 5
        ),
    }


def process(scenario, expected_frames):
    sources = sorted(
        (ROOT / "data" / "raw" / scenario).glob("*_sv_*.osi")
    )

    if len(sources) != 1:
        raise RuntimeError(
            f"{scenario}: expected one SensorView recording"
        )

    source = sources[0]
    rows = []
    previous_hash = None
    previous_timestamp = None

    with source.open("rb") as stream:
        frame = 0

        while True:
            header = stream.read(4)

            if not header:
                break

            if len(header) != 4:
                raise RuntimeError("Truncated OSI header")

            length = struct.unpack("<I", header)[0]

            if not 0 < length <= 100_000_000:
                raise RuntimeError("Invalid OSI payload size")

            payload = stream.read(length)

            if len(payload) != length:
                raise RuntimeError(
                    f"Truncated payload at frame {frame}"
                )

            sv = osi_sensorview_pb2.SensorView()
            sv.ParseFromString(payload)

            if (
                len(sv.camera_sensor_view) != 1
                or len(sv.lidar_sensor_view) != 1
                or len(sv.radar_sensor_view) != 1
            ):
                raise RuntimeError(
                    f"Missing sensor view: {scenario}, {frame}"
                )

            camera = sv.camera_sensor_view[0]
            config = camera.view_configuration

            width = int(
                config.number_of_pixels_horizontal
            )
            height = int(
                config.number_of_pixels_vertical
            )

            if width != 640 or height != 480:
                raise RuntimeError(
                    f"Unexpected Camera resolution at frame {frame}"
                )

            image = bytes(camera.image_data)
            digest = hashlib.sha256(image).digest()

            repeated = int(
                previous_hash == digest
            ) if previous_hash is not None else 0

            timestamp = (
                int(sv.timestamp.seconds) * 1_000_000_000
                + int(sv.timestamp.nanos)
            )

            if previous_timestamp is None:
                dt = ""
            else:
                dt = (
                    timestamp - previous_timestamp
                ) / 1_000_000

                if dt <= 0:
                    raise RuntimeError(
                        f"Nonmonotonic timestamp: {scenario}, {frame}"
                    )

            metrics = image_metrics(
                image, width, height
            )

            rows.append({
                "Scenario": scenario,
                "Recording": source.name,
                "Frame": frame,
                "Timestamp_ns": timestamp,
                "DT_ms": dt,
                "Width": width,
                "Height": height,
                "ImageBytes": len(image),
                "ImageRepeated": repeated,
                **metrics,
            })

            previous_hash = digest
            previous_timestamp = timestamp
            frame += 1

            if frame % 200 == 0:
                print(
                    f"{scenario}: {frame} frames",
                    flush=True
                )

    if len(rows) != expected_frames:
        raise RuntimeError(
            f"{scenario}: expected {expected_frames}, "
            f"found {len(rows)}"
        )

    return rows


def summarize(scenario, rows):
    def values(field):
        return [float(r[field]) for r in rows]

    intensity = values("SampledIntensityMean")
    dt_values = [
        float(r["DT_ms"])
        for r in rows
        if r["DT_ms"] != ""
    ]

    repeat = sum(
        int(r["ImageRepeated"]) for r in rows
    )

    return {
        "Scenario": scenario,
        "Frames": len(rows),
        "ImageBytesPerFrame": rows[0]["ImageBytes"],
        "RepeatedImages": repeat,
        "RepeatedImagePct": round(
            100 * repeat / len(rows), 4
        ),
        "MeanIntensity": round(
            statistics.fmean(intensity), 4
        ),
        "MedianIntensity": round(
            statistics.median(intensity), 4
        ),
        "P05Intensity": round(
            percentile(intensity, 0.05), 4
        ),
        "P95Intensity": round(
            percentile(intensity, 0.95), 4
        ),
        "MeanIntensityStd": round(
            statistics.fmean(
                values("SampledIntensityStd")
            ), 4
        ),
        "MeanEdgeMagnitude": round(
            statistics.fmean(
                values("SampledEdgeMagnitude")
            ), 4
        ),
        "MeanDarkPct": round(
            statistics.fmean(
                values("SampledDarkPct")
            ), 4
        ),
        "MeanBrightPct": round(
            statistics.fmean(
                values("SampledBrightPct")
            ), 4
        ),
        "MedianDT_ms": round(
            statistics.median(dt_values), 4
        ),
        "P95DT_ms": round(
            percentile(dt_values, 0.95), 4
        ),
    }


def main():
    for path in (FRAME_CSV, SUMMARY_CSV):
        if path.exists():
            raise RuntimeError(
                f"Output already exists: {path}"
            )

    all_rows = []
    summary_rows = []

    for scenario, count in SCENARIOS.items():
        print(
            f"\nProcessing {scenario}: expected {count} frames",
            flush=True
        )
        rows = process(scenario, count)
        all_rows.extend(rows)
        summary_rows.append(summarize(scenario, rows))

    if len(all_rows) != 2794:
        raise RuntimeError("Unexpected total Camera frames")

    # No outputs are committed until all four pass.
    for path, fields, records in [
        (FRAME_CSV, FRAME_FIELDS, all_rows),
        (SUMMARY_CSV, SUMMARY_FIELDS, summary_rows),
    ]:
        with path.open(
            "x", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=fields
            )
            writer.writeheader()
            writer.writerows(records)

    print("\n======================================")
    print("TASK 28.3D.3 — FULL CAMERA RESULTS")
    print("======================================")

    for r in summary_rows:
        print(f"\nScenario: {r['Scenario']}")
        print(f"Frames: {r['Frames']}")
        print(
            f"Sampled mean intensity: "
            f"{r['MeanIntensity']:.3f}"
        )
        print(
            f"Sampled intensity std: "
            f"{r['MeanIntensityStd']:.3f}"
        )
        print(
            f"Sampled edge magnitude: "
            f"{r['MeanEdgeMagnitude']:.3f}"
        )
        print(
            f"Repeated Camera images: "
            f"{r['RepeatedImages']}"
        )
        print(
            f"Median inter-frame interval: "
            f"{r['MedianDT_ms']:.3f} ms"
        )

    print(f"\nTotal Camera frames: {len(all_rows)}")
    print(f"Frame CSV: {FRAME_CSV}")
    print(f"Summary CSV: {SUMMARY_CSV}")

    print("STATUS: TASK 28.3D.3 SUCCESS")
    print(
        "NOTE: Sampled intensity and edge metrics "
        "are not object-detection accuracy."
    )
    print(
        "NOTE: Repeated image bytes do not by "
        "themselves establish sensor freshness."
    )


if __name__ == "__main__":
    main()
