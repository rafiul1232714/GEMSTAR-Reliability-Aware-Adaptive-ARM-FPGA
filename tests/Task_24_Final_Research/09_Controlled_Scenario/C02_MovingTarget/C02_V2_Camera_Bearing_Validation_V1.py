import csv
import math
from pathlib import Path

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_24_Final_Research\09_Controlled_Scenario\C02_MovingTarget"
)
DIR = BASE / "C02_V2_EKF_Input_53Frames_V1"

FRAME = 530
TRACK_ID = 2

FX = 320.0
CX = 320.0
CAMERA_X_M = 0.7

MAX_POSITION_SEPARATION_M = 0.6
BEARING_SIGMA_FLOOR_RAD = 0.03
MAX_NORMALIZED_RESIDUAL = 3.0

def load(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

tracks = load(DIR / "lidar_temporal_tracks_v1.csv")
detections = load(
    BASE / "C02_V2_Frame0530_Deduplicated_Detections.csv"
)
associations = load(
    BASE / "C02_V2_ThreeSensor_Association_Frame0530_V1.csv"
)

matched_tracks = [
    r for r in tracks
    if int(r["frame"]) == FRAME
    and int(r["track_id"]) == TRACK_ID
]

if len(matched_tracks) != 1:
    raise RuntimeError("Expected exactly one Track 2 measurement")

track = matched_tracks[0]
x = float(track["x_m"])
y = float(track["y_m"])

valid_associations = [
    r for r in associations
    if int(r["frame"]) == FRAME
    and int(r["lidar_candidate_points"]) > 0
]

if len(valid_associations) != 1:
    raise RuntimeError("Expected one Camera-LiDAR candidate")

assoc = valid_associations[0]

separation = math.hypot(
    x - float(assoc["lidar_x_m"]),
    y - float(assoc["lidar_y_m"])
)

if separation > MAX_POSITION_SEPARATION_M:
    raise RuntimeError(
        "LiDAR track does not match Camera-LiDAR candidate"
    )

matching_boxes = [
    r for r in detections
    if r["OriginalClasses"] == assoc["original_classes"]
]

if len(matching_boxes) != 1:
    raise RuntimeError("Camera hypothesis is not unique")

box = matching_boxes[0]

x1 = float(box["X1"])
x2 = float(box["X2"])
y1 = float(box["Y1"])
y2 = float(box["Y2"])

if x2 <= x1 or y2 <= y1:
    raise RuntimeError("Invalid bounding box")

u = (x1 + x2) / 2
v = (y1 + y2) / 2

measured_bearing = math.atan2(u - CX, FX)

dx = x - CAMERA_X_M

if dx <= 0:
    raise RuntimeError("Target behind Camera")

predicted_bearing = math.atan2(-y, dx)

residual = math.atan2(
    math.sin(measured_bearing - predicted_bearing),
    math.cos(measured_bearing - predicted_bearing)
)

# This is an exploratory uncertainty estimate based on
# the half-width of the box, NOT calibrated detector noise.
box_half_width_rad = (
    math.atan2((x2-x1)/2, FX)
)

sigma = max(
    BEARING_SIGMA_FLOOR_RAD,
    box_half_width_rad
)

normalized = abs(residual) / sigma

status = (
    "BEARING_GEOMETRICALLY_COMPATIBLE_NOT_CALIBRATED"
    if normalized <= MAX_NORMALIZED_RESIDUAL
    else "BEARING_INCONSISTENT"
)

result = {
    "frame": FRAME,
    "track_id": TRACK_ID,
    "camera_original_classes": box["OriginalClasses"],
    "camera_confidence": box["Confidence"],
    "camera_center_u_px": u,
    "camera_center_v_px": v,
    "camera_box_width_px": x2 - x1,
    "track_x_m": x,
    "track_y_m": y,
    "track_candidate_separation_m": separation,
    "camera_bearing_rad": measured_bearing,
    "predicted_lidar_bearing_rad": predicted_bearing,
    "bearing_residual_rad": residual,
    "bearing_residual_deg": math.degrees(residual),
    "assumed_bearing_sigma_rad": sigma,
    "normalized_residual": normalized,
    "status": status,
    "ekf_update_authorized": "NO"
}

output = DIR / "camera_bearing_track2_frame530_v1.csv"

with output.open("x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(result))
    writer.writeheader()
    writer.writerow(result)

print("=== TASK 24.9.6A RESULTS ===")
print("FRAME=", FRAME)
print("TRACK_ID=", TRACK_ID)
print("CAMERA_CLASSES=", box["OriginalClasses"])
print("CAMERA_CONFIDENCE=", box["Confidence"])
print("TRACK_CANDIDATE_SEPARATION_M=", round(separation, 5))
print("CAMERA_CENTER_U_PX=", round(u, 5))
print("CAMERA_BEARING_DEG=", round(
    math.degrees(measured_bearing), 5
))
print("LIDAR_PREDICTED_BEARING_DEG=", round(
    math.degrees(predicted_bearing), 5
))
print("BEARING_RESIDUAL_DEG=", round(
    math.degrees(residual), 5
))
print("ASSUMED_SIGMA_DEG=", round(
    math.degrees(sigma), 5
))
print("NORMALIZED_RESIDUAL=", round(normalized, 5))
print("STATUS=", status)
print("OUTPUT_CSV=", output)
print("CAMERA_DEPTH_MEASUREMENT_USED=NO")
print("CAMERA_CALIBRATION_VALIDATED=NO")
print("EKF_UPDATE_PERFORMED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_09_06A_CAMERA_BEARING_COMPLETE")