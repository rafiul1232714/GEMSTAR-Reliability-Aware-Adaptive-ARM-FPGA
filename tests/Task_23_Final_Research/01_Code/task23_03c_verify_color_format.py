import csv
import sys
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_23_Final_Research"

sys.path.insert(
    0,
    str(ROOT / "tests" / "Task_22_Final_Research" / "01_Code")
)

from task22_02_reusable_osi_reader import (
    iter_osi_messages, SensorView
)

manifest = TASK / "05_Raw_Data_References" / "task23_01_source_manifest.csv"
output = TASK / "02_CSV_Data" / "task23_03c_verified_camera_format.csv"

with manifest.open(newline="", encoding="utf-8-sig") as f:
    pairs = [r for r in csv.DictReader(f) if r["PairID"] in {"1", "2", "3"}]

print("\n=== TASK 23.3C CAMERA FORMAT VERIFICATION ===")

rows = []
all_pass = True

for pair in pairs:
    for frame, msg, size in iter_osi_messages(
        Path(pair["SensorViewPath"]), SensorView, 26
    ):
        if frame != 25:
            continue

        camera = msg.camera_sensor_view[0]
        cfg = camera.view_configuration

        format_field = cfg.DESCRIPTOR.fields_by_name["channel_format"]
        enum_descriptor = format_field.enum_type

        values = list(cfg.channel_format)
        names = [
            enum_descriptor.values_by_number[v].name
            if v in enum_descriptor.values_by_number
            else f"UNKNOWN_{v}"
            for v in values
        ]

        expected = (
            cfg.number_of_pixels_horizontal
            * cfg.number_of_pixels_vertical * 3
        )

        valid = (
            names == ["CHANNEL_FORMAT_RGB_U8_LIN"]
            and cfg.pixel_order == 0
            and len(camera.image_data) == expected
        )

        all_pass = all_pass and valid

        row = {
            "PairID": pair["PairID"],
            "Frame": frame,
            "ChannelFormatValues": str(values),
            "ChannelFormatNames": ";".join(names),
            "PixelOrder": cfg.pixel_order,
            "Width": cfg.number_of_pixels_horizontal,
            "Height": cfg.number_of_pixels_vertical,
            "ImageBytes": len(camera.image_data),
            "ExpectedRGBBytes": expected,
            "RGBFormatVerified": valid
        }
        rows.append(row)

        print(f"\nPair {pair['PairID']} | Frame {frame}")
        print("Channel format:", values, names)
        print("Pixel order:", cfg.pixel_order)
        print("Image bytes:", len(camera.image_data))
        print("Expected RGB bytes:", expected)
        print("RGB format verified:", valid)

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 23.3C FINAL VERIFICATION ===")
print("Recording pairs checked:", len(rows))
print("All formats verified:", all_pass)
print("CSV saved:", output.is_file())
print("\n=== TASK 23.3C COMPLETE ===")
