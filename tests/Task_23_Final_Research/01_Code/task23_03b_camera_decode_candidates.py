import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages,
    SensorView
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

GRAPH_DIR = TASK / "03_Graphs"
IMAGE_DIR = TASK / "08_Processed_Data" / "Camera_Previews"
CSV_DIR = TASK / "02_CSV_Data"
FINDINGS = TASK / "06_Research_Findings"

for directory in (
    GRAPH_DIR, IMAGE_DIR, CSV_DIR, FINDINGS
):
    directory.mkdir(parents=True, exist_ok=True)

FRAME = 25
PAIR_IDS = {"1", "2", "3"}

WIDTH = 640
HEIGHT = 480
CHANNELS = 3

EXPECTED_BYTES = WIDTH * HEIGHT * CHANNELS


def protobuf_fields(message, depth=0):
    """Return populated configuration fields safely."""
    if depth > 5:
        return {"limit": "Maximum nesting reached"}

    result = {}

    for descriptor, value in message.ListFields():
        name = descriptor.name

        if descriptor.is_repeated:
            result[name] = {
                "count": len(value)
            }
        elif descriptor.type == descriptor.TYPE_MESSAGE:
            result[name] = protobuf_fields(
                value, depth + 1
            )
        elif descriptor.type == descriptor.TYPE_BYTES:
            result[name] = {
                "byte_count": len(value)
            }
        else:
            result[name] = value

    return result


def read_camera(path, frame_number):
    for index, message, size in iter_osi_messages(
        path, SensorView, frame_number + 1
    ):
        if index != frame_number:
            continue

        if not message.camera_sensor_view:
            raise ValueError(
                f"No camera in frame {index}"
            )

        return message.camera_sensor_view[0]

    raise ValueError(
        f"Frame {frame_number} not found"
    )


def create_comparison(images, pair_id):
    # Images are resized only for comparison display.
    tile_w = 480
    tile_h = 360
    label_h = 35

    canvas = Image.new(
        "RGB",
        (tile_w * 3, tile_h + label_h),
        "white"
    )

    draw = ImageDraw.Draw(canvas)

    labels = [
        "640x480 RGB hypothesis",
        "640x480 BGR hypothesis",
        "1280x720 grayscale hypothesis"
    ]

    for i, (label, image) in enumerate(zip(labels, images)):
        preview = image.convert("RGB").resize(
            (tile_w, tile_h)
        )

        canvas.paste(
            preview, (i * tile_w, label_h)
        )

        draw.text(
            (i * tile_w + 10, 10),
            label,
            fill="black"
        )

    path = GRAPH_DIR / (
        f"task23_03b_pair{pair_id}_"
        "camera_layout_comparison.png"
    )

    canvas.save(path)
    return path


print("\n=== TASK 23.3B CAMERA DECODING TEST ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as handle:
    selected = [
        row for row in csv.DictReader(handle)
        if row["PairID"] in PAIR_IDS
    ]

results = []

for pair in selected:
    pair_id = pair["PairID"]
    source = Path(pair["SensorViewPath"])

    print(f"\n=== PAIR {pair_id} ===")

    camera = read_camera(source, FRAME)
    payload = camera.image_data

    configuration = protobuf_fields(
        camera.view_configuration
    )

    print("Image bytes:", len(payload))
    print(
        "Camera view configuration:",
        json.dumps(configuration, indent=2)
    )

    if len(payload) != EXPECTED_BYTES:
        print(
            "SKIPPED: payload size does not match "
            "the tested layouts"
        )
        continue

    array = np.frombuffer(
        payload, dtype=np.uint8
    )

    # Hypothesis A: contiguous RGB, row-major.
    rgb_array = array.reshape(
        HEIGHT, WIDTH, CHANNELS
    )

    rgb_img = Image.fromarray(
        rgb_array, mode="RGB"
    )

    # Hypothesis B: contiguous BGR, row-major.
    bgr_img = Image.fromarray(
        rgb_array[:, :, ::-1].copy(),
        mode="RGB"
    )

    # Hypothesis C: 1280x720 single channel.
    gray_array = array.reshape(720, 1280)

    gray_img = Image.fromarray(
        gray_array, mode="L"
    )

    images = [
        ("RGB_HYPOTHESIS", rgb_img),
        ("BGR_HYPOTHESIS", bgr_img),
        ("GRAY_HYPOTHESIS", gray_img)
    ]

    for name, img in images:
        output = IMAGE_DIR / (
            f"pair{pair_id}_frame25_{name}.png"
        )
        img.save(output)

        print("Saved:", output.name)

    comparison_path = create_comparison(
        [img for _, img in images], pair_id
    )

    print(
        "Comparison graph:",
        comparison_path.name
    )

    result = {
        "PairID": pair_id,
        "Frame": FRAME,
        "ImageBytes": len(payload),
        "AssumedRGBWidth": WIDTH,
        "AssumedRGBHeight": HEIGHT,
        "AssumedRGBChannels": CHANNELS,
        "CameraConfiguration": configuration,
        "ComparisonGraph": str(comparison_path),
        "DecodingStatus": "CANDIDATES_UNVERIFIED"
    }

    results.append(result)

csv_path = (
    CSV_DIR / "task23_03b_camera_decode_summary.csv"
)

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as handle:
    columns = [
        "PairID",
        "Frame",
        "ImageBytes",
        "AssumedRGBWidth",
        "AssumedRGBHeight",
        "AssumedRGBChannels",
        "DecodingStatus"
    ]

    writer = csv.DictWriter(
        handle, fieldnames=columns
    )
    writer.writeheader()

    for row in results:
        writer.writerow({
            key: row[key] for key in columns
        })

json_path = (
    FINDINGS / "task23_03b_camera_decode_findings.json"
)

json_path.write_text(
    json.dumps({
        "Task": "23.3B",
        "Results": results,
        "Limitations": [
            "Candidate layouts are not confirmed",
            "Color-channel order is unverified",
            "Byte count alone does not establish dimensions",
            "Pixel row stride and orientation unverified",
            "No image quality or detection accuracy measured"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 23.3B FINAL VERIFICATION ===")
print("Recording pairs tested:", len(selected))
print("Candidate comparisons created:", len(results))
print("Summary CSV saved:", csv_path.is_file())
print("Findings JSON saved:", json_path.is_file())

print("\n=== TASK 23.3B COMPLETE ===")
