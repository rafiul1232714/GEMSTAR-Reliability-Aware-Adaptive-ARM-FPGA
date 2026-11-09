import csv
import struct
from pathlib import Path

import cv2
import numpy as np
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_18_Camera_Extension_Final_Research"
OUT = BASE / "08_Extracted_Images"
CSV_OUT = BASE / "02_CSV_Data" / "task18_e3_extracted_camera_frames.csv"

# extract a few frames from each recording
TARGET_FRAMES = [0, 5, 10, 20]

def iter_messages(path):
    with path.open("rb") as f:
        frame_index = 0
        while True:
            header = f.read(4)
            if len(header) != 4:
                break

            size = struct.unpack("<I", header)[0]
            if not (0 < size < 100_000_000):
                raise ValueError(f"Invalid message size {size}")

            payload = f.read(size)
            if len(payload) != size:
                break

            msg = SensorView()
            msg.ParseFromString(payload)
            yield frame_index, msg
            frame_index += 1

def main():
    print("\n=== TASK 18.E3 CAMERA FRAME EXTRACTION ===")

    rows = []
    total_saved = 0

    files = sorted(RAW.rglob("*_sv_*.osi"))

    for path in files:
        scenario = path.parent.name
        scenario_out = OUT / scenario
        scenario_out.mkdir(parents=True, exist_ok=True)

        saved_here = 0
        print(f"\nRecording: {scenario}")

        for frame_index, msg in iter_messages(path):
            if frame_index not in TARGET_FRAMES:
                continue

            if len(msg.camera_sensor_view) == 0:
                continue

            cam = msg.camera_sensor_view[0]
            cfg = cam.view_configuration

            width = cfg.number_of_pixels_horizontal
            height = cfg.number_of_pixels_vertical
            raw = cam.image_data

            expected_rgb = width * height * 3
            expected_gray = width * height

            status = "UNKNOWN"
            save_path = ""

            if len(raw) == expected_rgb:
                array = np.frombuffer(raw, dtype=np.uint8).reshape((height, width, 3))

                # save RGB interpretation
                rgb_path = scenario_out / f"{scenario}_frame_{frame_index:03d}_rgb.png"
                cv2.imwrite(str(rgb_path), cv2.cvtColor(array, cv2.COLOR_RGB2BGR))
                save_path = str(rgb_path)
                status = "RGB_3CH_SAVED"
                total_saved += 1
                saved_here += 1

            elif len(raw) == expected_gray:
                array = np.frombuffer(raw, dtype=np.uint8).reshape((height, width))
                gray_path = scenario_out / f"{scenario}_frame_{frame_index:03d}_gray.png"
                cv2.imwrite(str(gray_path), array)
                save_path = str(gray_path)
                status = "GRAY_SAVED"
                total_saved += 1
                saved_here += 1

            else:
                status = f"UNEXPECTED_SIZE_{len(raw)}"

            print(
                f"Frame {frame_index:3d} | "
                f"CameraViews={len(msg.camera_sensor_view)} | "
                f"Resolution={width}x{height} | "
                f"Bytes={len(raw)} | {status}"
            )

            rows.append({
                "Recording": scenario,
                "File": path.name,
                "FrameIndex": frame_index,
                "CameraViews": len(msg.camera_sensor_view),
                "Width": width,
                "Height": height,
                "RawBytes": len(raw),
                "ExpectedRGBBytes": expected_rgb,
                "ExpectedGrayBytes": expected_gray,
                "Status": status,
                "SavedImage": save_path
            })

        print(f"Saved images from this recording: {saved_here}")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TASK 18.E3 COMPLETE ===")
    print("Total extracted images:", total_saved)
    print("CSV saved:", CSV_OUT)
    print("Image folder:", OUT)

if __name__ == "__main__":
    main()
