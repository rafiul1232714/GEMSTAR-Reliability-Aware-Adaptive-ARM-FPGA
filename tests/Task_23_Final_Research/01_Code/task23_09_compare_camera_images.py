from pathlib import Path
import struct
import zlib
import csv
import hashlib
from osi3 import osi_sensorview_pb2

task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")
root = Path(r"E:\GEMSTAR_Project\gemstar\Output")

baseline = root / "20261103T194105Z_sv_380_X_55_GEMSTARCAMERACLEAR23.osi"
displaced = root / "20261103T195644Z_sv_380_X_769_GEMSTARCAMERADISPLACED23.osi"

graphs = task / "03_Graphs"
csv_path = task / "02_CSV_Data/task23_09_camera_baseline_displaced.csv"
report = task / "06_Research_Findings/task23_09_camera_image_comparison.txt"

W, H = 640, 480
EXPECTED = W * H * 3

for path in (baseline, displaced):
    if not path.is_file():
        raise FileNotFoundError(path)

graphs.mkdir(parents=True, exist_ok=True)
csv_path.parent.mkdir(parents=True, exist_ok=True)

def read_camera_frame(path, target=3):
    with path.open("rb") as file:
        for frame in range(1, target + 1):
            header = file.read(4)

            if len(header) != 4:
                raise RuntimeError(
                    f"Missing frame {frame} in {path.name}"
                )

            size = struct.unpack("<I", header)[0]

            if not 0 < size < 20_000_000:
                raise RuntimeError(
                    f"Invalid OSI message length: {size}"
                )

            payload = file.read(size)

            if len(payload) != size:
                raise RuntimeError("Truncated OSI message")

            view = osi_sensorview_pb2.SensorView()
            view.ParseFromString(payload)

            if len(view.camera_sensor_view) != 1:
                raise RuntimeError(
                    f"Frame {frame}: expected one camera view"
                )

            image = view.camera_sensor_view[0].image_data

            if len(image) != EXPECTED:
                raise RuntimeError(
                    f"Frame {frame}: RGB size {len(image)} "
                    f"does not match expected {EXPECTED}"
                )

        return bytes(image)

def chunk(name, payload):
    body = name + payload
    return (
        struct.pack(">I", len(payload))
        + body
        + struct.pack(">I", zlib.crc32(body) & 0xffffffff)
    )

def save_png(path, rgb, width, height):
    row_size = width * 3

    scanlines = b"".join(
        b"\x00" + rgb[y*row_size:(y+1)*row_size]
        for y in range(height)
    )

    header = struct.pack(
        ">IIBBBBB", width, height, 8, 2, 0, 0, 0
    )

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(scanlines, 6))
        + chunk(b"IEND", b"")
    )

    path.write_bytes(data)

def diagnostic(rgb):
    # Sample every 16th pixel; do not infer cube segmentation.
    samples = [
        tuple(rgb[i:i+3])
        for i in range(0, len(rgb), 48)
    ]

    center_index = ((H // 2) * W + (W // 2)) * 3

    return {
        "unique_colors": len(set(samples)),
        "center_rgb": tuple(rgb[center_index:center_index+3]),
        "sha256": hashlib.sha256(rgb).hexdigest(),
    }

print("\n=== TASK 23.9J — CAMERA GEOMETRIC COMPARISON ===")

base_rgb = read_camera_frame(baseline)
move_rgb = read_camera_frame(displaced)

base_info = diagnostic(base_rgb)
move_info = diagnostic(move_rgb)

base_png = graphs / "task23_09_baseline_frame003.png"
move_png = graphs / "task23_09_displaced_frame003.png"
combined_png = graphs / "task23_09_baseline_vs_displaced.png"

save_png(base_png, base_rgb, W, H)
save_png(move_png, move_rgb, W, H)

# Combine corresponding rows horizontally.
stride = W * 3
combined = b"".join(
    base_rgb[y*stride:(y+1)*stride]
    + move_rgb[y*stride:(y+1)*stride]
    for y in range(H)
)

save_png(combined_png, combined, 2*W, H)

rows = [
    {
        "condition": "baseline",
        "cube_front_face_m": 8.5,
        "frame": 3,
        "width": W,
        "height": H,
        "image_bytes": len(base_rgb),
        "sampled_unique_colors": base_info["unique_colors"],
        "center_rgb": str(base_info["center_rgb"]),
        "rgb_sha256": base_info["sha256"],
    },
    {
        "condition": "displaced",
        "cube_front_face_m": 10.5,
        "frame": 3,
        "width": W,
        "height": H,
        "image_bytes": len(move_rgb),
        "sampled_unique_colors": move_info["unique_colors"],
        "center_rgb": str(move_info["center_rgb"]),
        "rgb_sha256": move_info["sha256"],
    },
]

with csv_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

status = (
    "CAMERA_RGB_COMPARISON_READY"
    if (
        base_info["unique_colors"] > 10
        and move_info["unique_colors"] > 10
        and base_info["sha256"] != move_info["sha256"]
    )
    else "CAMERA_IMAGE_CONTENT_REQUIRES_INVESTIGATION"
)

print("Baseline RGB bytes:", len(base_rgb))
print("Displaced RGB bytes:", len(move_rgb))
print("Baseline sampled colors:", base_info["unique_colors"])
print("Displaced sampled colors:", move_info["unique_colors"])
print("Baseline center RGB:", base_info["center_rgb"])
print("Displaced center RGB:", move_info["center_rgb"])
print("RGB images identical:", base_rgb == move_rgb)

print("\n=== EXPECTED GEOMETRY ===")
print("Baseline axial range: 8.50 m")
print("Displaced axial range: 10.50 m")
print("Expected apparent width ratio:", f"{8.5/10.5:.6f}")
print("Expected projected width reduction:", f"{100*(1-8.5/10.5):.2f}%")

report.write_text(
    "\n".join([
        "TASK 23.9 - CAMERA BASELINE VS DISPLACED",
        f"Status: {status}",
        "Frame used: 3 from each recording",
        "Resolution per image: 640x480",
        f"Baseline RGB SHA256: {base_info['sha256']}",
        f"Displaced RGB SHA256: {move_info['sha256']}",
        "Expected width ratio: 0.809524",
        "The target bounding boxes have not yet been measured.",
        "Weather-mode consistency requires separate verification.",
        f"Combined image: {combined_png}",
        f"CSV: {csv_path}",
    ]) + "\n",
    encoding="utf-8"
)

print("\n=== SAVED EVIDENCE ===")
print("Baseline image:", base_png)
print("Displaced image:", move_png)
print("Comparison image:", combined_png)
print("CSV:", csv_path)
print("Report:", report)

print("\nStatus:", status)
