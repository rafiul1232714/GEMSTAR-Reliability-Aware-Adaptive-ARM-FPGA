
from pathlib import Path
import struct
import csv

from osi3.osi_sensorview_pb2 import SensorView

# ==================================================
# TASK 5: GEMSTAR THREE-SENSOR VERIFICATION
# ==================================================

# Latest recording after C++ sensor-ID corrections
file_path = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

# Output directory for MATLAB analysis
results_folder = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)

results_folder.mkdir(parents=True, exist_ok=True)

csv_path = results_folder / "C02_NoVisualizer_V2_Sensor_Verification.csv"

# ==================================================
# CHECK INPUT FILE
# ==================================================

print("======================================")
print("GEMSTAR THREE-SENSOR VERIFICATION")
print("======================================")

if not file_path.is_file():
    raise FileNotFoundError(
        f"Recording not found: {file_path}"
    )

file_size_gb = file_path.stat().st_size / (1024 ** 3)

print("Recording:", file_path.name)
print(f"File size: {file_size_gb:.2f} GiB")
print()

# ==================================================
# INITIALIZE COUNTERS
# ==================================================

frames = 0

camera_frames = 0
lidar_frames = 0
radar_frames = 0

camera_data_frames = 0
lidar_data_frames = 0
radar_data_frames = 0

# ==================================================
# READ OSI RECORDING
# ==================================================

with file_path.open("rb") as file:

    while True:

        # Each message begins with a 4-byte length
        header = file.read(4)

        if not header:
            break

        if len(header) != 4:
            raise ValueError(
                "Incomplete OSI message header"
            )

        length = struct.unpack("<I", header)[0]

        if length == 0:
            raise ValueError(
                "Empty OSI message"
            )

        # Read one serialized SensorView message
        data = file.read(length)

        if len(data) != length:
            raise ValueError(
                "Incomplete OSI message payload"
            )

        sensor_view = SensorView()
        sensor_view.ParseFromString(data)

        frames += 1

        cameras = sensor_view.camera_sensor_view
        lidars = sensor_view.lidar_sensor_view
        radars = sensor_view.radar_sensor_view

        # Count messages containing each sensor
        camera_frames += bool(cameras)
        lidar_frames += bool(lidars)
        radar_frames += bool(radars)

        # Count messages with actual sensor payloads
        camera_data_frames += any(
            len(camera.image_data) > 0
            for camera in cameras
        )

        lidar_data_frames += any(
            len(lidar.reflection) > 0
            for lidar in lidars
        )

        radar_data_frames += any(
            len(radar.reflection) > 0
            for radar in radars
        )

        # Display first three messages
        if frames <= 3:
            print(f"Message {frames}")
            print("  Camera views:", len(cameras))
            print("  LiDAR views:", len(lidars))
            print("  Radar views:", len(radars))
            print()

        # Progress update every 25 messages
        if frames % 25 == 0:
            progress = (
                file.tell() / file_path.stat().st_size
            ) * 100

            print(
                f"Processed {frames} messages "
                f"({progress:.1f}% of file)"
            )

# ==================================================
# DISPLAY FINAL RESULTS
# ==================================================

print()
print("========== FINAL RESULTS ==========")

print("Total OSI messages:", frames)

print("\nFrames containing sensor views:")
print("Camera:", camera_frames)
print("LiDAR:", lidar_frames)
print("Radar:", radar_frames)

print("\nFrames containing sensor payloads:")
print("Camera images:", camera_data_frames)
print("LiDAR reflections:", lidar_data_frames)
print("Radar reflections:", radar_data_frames)

print("\n========== SENSOR STATUS ==========")

camera_ok = camera_data_frames > 0
lidar_ok = lidar_data_frames > 0
radar_ok = radar_data_frames > 0

print(
    "Camera:",
    "DATA FOUND" if camera_ok else "NO DATA"
)

print(
    "LiDAR:",
    "DATA FOUND" if lidar_ok else "NO DATA"
)

print(
    "Radar:",
    "DATA FOUND" if radar_ok else "NO DATA"
)

# ==================================================
# EXPORT SUMMARY TO CSV FOR MATLAB
# ==================================================

rows = [
    ["Total_Messages", frames],
    ["Camera_View_Frames", camera_frames],
    ["LiDAR_View_Frames", lidar_frames],
    ["Radar_View_Frames", radar_frames],
    ["Camera_Image_Frames", camera_data_frames],
    ["LiDAR_Reflection_Frames", lidar_data_frames],
    ["Radar_Reflection_Frames", radar_data_frames],
]

with csv_path.open(
    "w",
    newline="",
    encoding="utf-8"
) as csv_file:

    writer = csv.writer(csv_file)
    writer.writerow(["Metric", "Value"])
    writer.writerows(rows)

print()
print("Summary saved to:")
print(csv_path)

if camera_ok and lidar_ok and radar_ok:
    print("\nSUCCESS: All three sensor types contain data.")
else:
    print("\nCHECK: One or more sensor types have missing data.")

print("===================================")
