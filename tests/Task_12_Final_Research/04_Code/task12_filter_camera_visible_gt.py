
# TASK 12.6B - CAMERA / GROUND TRUTH MULTI-FRAME FILTER
# GEMSTAR MOR100
# Geometric visibility candidate, NOT confirmed optical visibility.

from pathlib import Path
import csv
import math
import shutil

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")

TASK11 = ROOT / "tests" / "Task_11_Final_Research"
TASK12 = ROOT / "tests" / "Task_12_Final_Research"

DATA = TASK12 / "02_CSV_Data"
FINDINGS = TASK12 / "06_Research_Findings"
CODE = TASK12 / "04_Code"

for folder in [DATA, FINDINGS, CODE]:
    folder.mkdir(parents=True, exist_ok=True)

GT_FILE = TASK11 / "02_CSV_Data" / "task11_groundtruth_objects.csv"
FRAME_FILE = DATA / "task12_6_camera_gt_frame_availability.csv"

EGO_ID = 76895
TARGET_ID = 76865

WIDTH = 640
HEIGHT = 480

HFOV_DEG = 90.0
FX = WIDTH / (2.0 * math.tan(math.radians(HFOV_DEG / 2)))
FY = FX
CX = WIDTH / 2
CY = HEIGHT / 2

CAMERA_X = 0.70
CAMERA_Z = 1.60

assert GT_FILE.is_file(), GT_FILE
assert FRAME_FILE.is_file(), FRAME_FILE

# Load only the two vehicles needed.
gt_by_key = {}

with GT_FILE.open(newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        oid = int(row["object_id"])
        if oid in (EGO_ID, TARGET_ID):
            gt_by_key[(int(row["frame"]), oid)] = row

with FRAME_FILE.open(newline="", encoding="utf-8-sig") as f:
    available = list(csv.DictReader(f))

results = []

for item in available:
    frame = int(item["frame"])

    ego = gt_by_key.get((frame, EGO_ID))
    target = gt_by_key.get((frame, TARGET_ID))

    if ego is None or target is None:
        continue

    dx = float(target["x_m"]) - float(ego["x_m"])
    dy = float(target["y_m"]) - float(ego["y_m"])

    yaw = float(ego["yaw_rad"])

    forward = math.cos(yaw)*dx + math.sin(yaw)*dy
    lateral = -math.sin(yaw)*dx + math.cos(yaw)*dy

    # Same provisional Z convention as Task 12.2.
    relative_z = (
        float(target["z_m"]) - float(ego["z_m"])
    )

    camera_forward = forward - CAMERA_X

    if camera_forward > 0.05:
        u = CX - FX * lateral / camera_forward
        v = CY - FY * (relative_z - CAMERA_Z) / camera_forward
        in_image = (0 <= u < WIDTH and 0 <= v < HEIGHT)
    else:
        u = float("nan")
        v = float("nan")
        in_image = False

    bearing_deg = math.degrees(
        math.atan2(lateral, camera_forward)
    )

    results.append({
        "frame": frame,
        "time_s": item["time_s"],
        "forward_m": round(forward, 4),
        "lateral_m": round(lateral, 4),
        "gt_distance_m": round(math.hypot(dx,dy), 4),
        "bearing_deg": round(bearing_deg, 3),
        "projected_u_px": round(u, 2),
        "projected_v_px": round(v, 2),
        "center_in_image": int(in_image),
        "image_filename": item["image_filename"]
    })

OUT = DATA / "task12_6_camera_gt_visibility_candidates.csv"

columns = [
    "frame", "time_s",
    "forward_m", "lateral_m", "gt_distance_m",
    "bearing_deg", "projected_u_px", "projected_v_px",
    "center_in_image", "image_filename"
]

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(results)

candidates = [r for r in results if r["center_in_image"]]

report = [
    "TASK 12.6B - MULTI-FRAME GT CAMERA FILTER",
    f"Frames with both GT objects: {len(results)}",
    f"Frames with projected center in image: {len(candidates)}",
    "",
    "Projection uses the negative-Y convention from Task 12.2.",
    "Camera horizontal FOV: 90 degrees.",
    "Principal point assumed at image center.",
    "No occlusion or image-boundary box clipping test.",
    "GT center and vertical reference remain provisional.",
    "In-image center does not guarantee target visibility.",
    "",
    "Candidate frames:",
    ", ".join(str(r["frame"]) for r in candidates)
]

(FINDINGS / "task12_6_camera_visibility_findings.txt").write_text(
    "\n".join(report) + "\n",
    encoding="utf-8"
)

shutil.copy2(Path(__file__), CODE / Path(__file__).name)

print("\n===== TASK 12.6B RESULTS =====")
print("Frames with both GT objects:", len(results))
print("Projected centers inside image:", len(candidates))

print("\nFrame | Forward (m) | Lateral (m) | Bearing | Pixel U,V")

for row in candidates:
    print(
        f"{row['frame']:5} | "
        f"{row['forward_m']:11.2f} | "
        f"{row['lateral_m']:11.2f} | "
        f"{row['bearing_deg']:7.2f} | "
        f"{row['projected_u_px']:.1f}, "
        f"{row['projected_v_px']:.1f}"
    )

print("\nSaved CSV:", OUT)
print("TASK 12.6B COMPLETED")
