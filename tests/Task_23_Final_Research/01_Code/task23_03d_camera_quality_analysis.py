import csv
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(0, str(
    ROOT / "tests" / "Task_22_Final_Research" / "01_Code"
))

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView
)

MANIFEST = (
    TASK / "05_Raw_Data_References" /
    "task23_01_source_manifest.csv"
)

CSV_DIR = TASK / "02_CSV_Data"
GRAPH_DIR = TASK / "03_Graphs"
FINDINGS = TASK / "06_Research_Findings"
IMAGE_DIR = (
    TASK / "08_Processed_Data" /
    "Camera_Validated_RGB"
)

for directory in (
    CSV_DIR, GRAPH_DIR, FINDINGS, IMAGE_DIR
):
    directory.mkdir(parents=True, exist_ok=True)

PAIR_IDS = {"1", "2", "3"}
FRAME_LIMIT = 100
SAVE_FRAMES = {1, 25, 99}

rows = []

print("\n=== TASK 23.3D CAMERA QUALITY ANALYSIS ===")

with MANIFEST.open(
    newline="", encoding="utf-8-sig"
) as f:
    pairs = [
        p for p in csv.DictReader(f)
        if p["PairID"] in PAIR_IDS
    ]

for pair in pairs:
    pair_id = pair["PairID"]
    path = Path(pair["SensorViewPath"])

    print(f"\n=== PAIR {pair_id} ===")
    print("Recording:", path.name)

    count = 0

    for frame, message, size in iter_osi_messages(
        path, SensorView, FRAME_LIMIT
    ):
        if not message.camera_sensor_view:
            raise ValueError(
                f"Pair {pair_id}, frame {frame}: no camera"
            )

        camera = message.camera_sensor_view[0]
        cfg = camera.view_configuration

        width = cfg.number_of_pixels_horizontal
        height = cfg.number_of_pixels_vertical

        expected_bytes = width * height * 3

        if (
            width != 640
            or height != 480
            or list(cfg.channel_format) != [6]
            or cfg.pixel_order != 0
            or len(camera.image_data) != expected_bytes
        ):
            raise ValueError(
                f"Unexpected camera format: "
                f"pair={pair_id}, frame={frame}"
            )

        rgb = np.frombuffer(
            camera.image_data,
            dtype=np.uint8
        ).reshape(height, width, 3)

        # ITU-R BT.709-style luma weighting applied
        # to encoded RGB values for comparative metrics.
        gray = (
            0.2126 * rgb[:, :, 0].astype(np.float32)
            + 0.7152 * rgb[:, :, 1].astype(np.float32)
            + 0.0722 * rgb[:, :, 2].astype(np.float32)
        )

        brightness = float(gray.mean())
        contrast = float(gray.std())

        dark_pct = float(
            np.mean(gray < 40) * 100.0
        )

        bright_pct = float(
            np.mean(gray > 215) * 100.0
        )

        # Downsampled spatial-gradient magnitude
        # as a simple image-detail proxy.
        small = gray[::4, ::4]

        dx = np.abs(
            np.diff(small, axis=1)
        ).mean()

        dy = np.abs(
            np.diff(small, axis=0)
        ).mean()

        edge_strength = float(
            (dx + dy) / 2.0
        )

        rows.append({
            "PairID": pair_id,
            "Frame": frame,
            "Width": width,
            "Height": height,
            "ImageBytes": len(camera.image_data),
            "BrightnessMean": brightness,
            "ContrastStd": contrast,
            "DarkPixelPct": dark_pct,
            "BrightPixelPct": bright_pct,
            "EdgeStrength": edge_strength,
        })

        if frame in SAVE_FRAMES:
            image_path = IMAGE_DIR / (
                f"pair{pair_id}_frame{frame:03d}_rgb.png"
            )

            Image.fromarray(
                rgb, mode="RGB"
            ).save(image_path)

        count += 1

    print("Frames analyzed:", count)

    if count != FRAME_LIMIT:
        raise RuntimeError(
            f"Pair {pair_id}: expected 100 frames, "
            f"found {count}"
        )

# --------------------------------------------------
# Save frame-level statistics
# --------------------------------------------------

csv_path = (
    CSV_DIR / "task23_03d_camera_frame_metrics.csv"
)

columns = [
    "PairID",
    "Frame",
    "Width",
    "Height",
    "ImageBytes",
    "BrightnessMean",
    "ContrastStd",
    "DarkPixelPct",
    "BrightPixelPct",
    "EdgeStrength",
]

with csv_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=columns
    )
    writer.writeheader()
    writer.writerows(rows)

# --------------------------------------------------
# Recording-level summary
# --------------------------------------------------

summary = []

metric_names = [
    "BrightnessMean",
    "ContrastStd",
    "DarkPixelPct",
    "BrightPixelPct",
    "EdgeStrength",
]

for pair in pairs:
    pair_id = pair["PairID"]

    selected = [
        r for r in rows
        if r["PairID"] == pair_id
    ]

    item = {
        "PairID": pair_id,
        "Frames": len(selected),
    }

    for name in metric_names:
        values = np.array(
            [r[name] for r in selected],
            dtype=float
        )

        item[name + "_Mean"] = float(
            np.mean(values)
        )

        item[name + "_Std"] = float(
            np.std(values)
        )

    summary.append(item)

summary_path = (
    CSV_DIR / "task23_03d_camera_recording_summary.csv"
)

with summary_path.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(summary[0].keys())
    )
    writer.writeheader()
    writer.writerows(summary)

# --------------------------------------------------
# Plot 1: Brightness
# --------------------------------------------------

plt.figure(figsize=(10, 5))

for pair in pairs:
    pair_id = pair["PairID"]

    selected = [
        r for r in rows
        if r["PairID"] == pair_id
    ]

    plt.plot(
        [r["Frame"] for r in selected],
        [r["BrightnessMean"] for r in selected],
        label=f"Pair {pair_id}",
        linewidth=1.5,
    )

plt.xlabel("Recorded frame index")
plt.ylabel("Mean intensity (0-255)")
plt.title("Task 23.3D - Camera Brightness")
plt.legend()
plt.grid(alpha=0.25)
plt.tight_layout()

brightness_path = (
    GRAPH_DIR / "task23_03d_camera_brightness.png"
)

plt.savefig(brightness_path, dpi=180)
plt.close()

# --------------------------------------------------
# Plot 2: Contrast and edge strength
# --------------------------------------------------

fig, axes = plt.subplots(
    2, 1, figsize=(10, 8),
    sharex=True
)

for pair in pairs:
    pair_id = pair["PairID"]
    selected = [
        r for r in rows
        if r["PairID"] == pair_id
    ]

    frame_indices = [
        r["Frame"] for r in selected
    ]

    axes[0].plot(
        frame_indices,
        [r["ContrastStd"] for r in selected],
        label=f"Pair {pair_id}"
    )

    axes[1].plot(
        frame_indices,
        [r["EdgeStrength"] for r in selected],
        label=f"Pair {pair_id}"
    )

axes[0].set_ylabel("Contrast (std)")
axes[0].set_title("Camera Contrast")
axes[1].set_ylabel("Mean spatial difference")
axes[1].set_xlabel("Recorded frame index")
axes[1].set_title("Camera Edge Strength")

for ax in axes:
    ax.grid(alpha=0.25)
    ax.legend()

fig.tight_layout()

detail_path = (
    GRAPH_DIR / "task23_03d_camera_contrast_edges.png"
)

fig.savefig(detail_path, dpi=180)
plt.close(fig)

# --------------------------------------------------
# Research findings
# --------------------------------------------------

findings_path = (
    FINDINGS / "task23_03d_camera_quality_findings.json"
)

findings_path.write_text(
    json.dumps({
        "Task": "23.3D",
        "Description": (
            "Validated RGB decoding and descriptive "
            "camera image statistics"
        ),
        "TotalFrames": len(rows),
        "RecordingSummary": summary,
        "Methodology": {
            "PixelFormat": "OSI RGB_U8_LIN",
            "Brightness": "Mean weighted RGB intensity",
            "Contrast": "Std of weighted RGB intensity",
            "DarkThreshold": 40,
            "BrightThreshold": 215,
            "EdgeStrength": (
                "Mean absolute neighboring difference "
                "in quarter-resolution grayscale"
            )
        },
        "Limitations": [
            "Metrics are descriptive image statistics",
            "No object detection accuracy measured",
            "No verified runtime weather labels",
            "No reference image quality scores",
            "No electrical energy measurement",
            "Frame index is not elapsed time"
        ]
    }, indent=2),
    encoding="utf-8"
)

print("\n=== RECORDING QUALITY SUMMARY ===")

for item in summary:
    print(
        f"Pair {item['PairID']} | "
        f"Frames={item['Frames']} | "
        f"Brightness={item['BrightnessMean_Mean']:.2f} | "
        f"Contrast={item['ContrastStd_Mean']:.2f} | "
        f"EdgeStrength={item['EdgeStrength_Mean']:.2f}"
    )

print("\n=== TASK 23.3D FINAL VERIFICATION ===")
print("Frames analyzed:", len(rows))
print("Frame CSV saved:", csv_path.is_file())
print("Summary CSV saved:", summary_path.is_file())
print("Brightness graph saved:", brightness_path.is_file())
print("Contrast/edge graph saved:", detail_path.is_file())
print("Research findings saved:", findings_path.is_file())

print("\n=== TASK 23.3D COMPLETE ===")
