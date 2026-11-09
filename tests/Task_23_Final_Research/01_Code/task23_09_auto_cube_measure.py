from pathlib import Path
import csv
import numpy as np
import cv2

task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")
graphs = task / "03_Graphs"

baseline = graphs / "task23_09_baseline_frame003.png"
displaced = graphs / "task23_09_displaced_frame003.png"

csv_file = task / "02_CSV_Data/task23_09_camera_auto_measurements.csv"
report = task / "06_Research_Findings/task23_09_camera_auto_geometry.txt"
output_image = graphs / "task23_09_auto_detected_cubes.png"

for p in [baseline, displaced]:
    if not p.is_file():
        raise FileNotFoundError(p)

def find_cube(path, condition):
    img = cv2.imread(str(path))
    if img is None:
        raise RuntimeError(f"Cannot decode {path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Known target region from the camera's central geometry.
    # Restrict search to avoid dark side walls and shadows.
    x1, x2 = 245, 395
    y1, y2 = 160, 310

    roi = gray[y1:y2, x1:x2]

    # Extract image gradients to locate rectangular face boundaries.
    edges_x = np.abs(
        np.diff(roi.astype(np.float32), axis=1)
    ).mean(axis=0)

    edges_y = np.abs(
        np.diff(roi.astype(np.float32), axis=0)
    ).mean(axis=1)

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    def peak_in_range(scores, start, stop):
        start = max(0, start)
        stop = min(len(scores), stop)
        if stop <= start:
            raise RuntimeError("Invalid search region")
        return start + int(np.argmax(scores[start:stop]))

    # Search expected left/right cube edges.
    left = x1 + peak_in_range(edges_x, 10, 75)
    right = x1 + peak_in_range(edges_x, 80, 145)

    # Search expected top/bottom cube edges.
    top = y1 + peak_in_range(edges_y, 10, 75)
    bottom = y1 + peak_in_range(edges_y, 80, 145)

    width = right - left
    height = bottom - top

    cv2.rectangle(
        img, (left, top), (right, bottom),
        (0, 255, 0), 2
    )

    cv2.putText(
        img,
        f"{condition}: {width}px",
        (left, max(25, top - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (0, 255, 0), 2
    )

    return {
        "image": img,
        "condition": condition,
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
        "width_px": width,
        "height_px": height,
    }

print("\n=== TASK 23.9K — AUTOMATIC CUBE DETECTION ===")

a = find_cube(baseline, "baseline")
b = find_cube(displaced, "displaced")

if a["width_px"] <= 0 or b["width_px"] <= 0:
    raise RuntimeError("Invalid detected cube width")

ratio = b["width_px"] / a["width_px"]
expected = 8.5 / 10.5
reduction = 100 * (1 - ratio)

print(f"Baseline width: {a['width_px']} px")
print(f"Displaced width: {b['width_px']} px")
print(f"Measured ratio: {ratio:.6f}")
print(f"Expected ratio: {expected:.6f}")
print(f"Measured reduction: {reduction:.2f}%")

combined = np.hstack([a["image"], b["image"]])
cv2.imwrite(str(output_image), combined)

csv_file.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)

with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "condition", "left", "right", "top",
        "bottom", "width_px", "height_px"
    ])
    for r in (a, b):
        writer.writerow([
            r["condition"],
            r["left"], r["right"],
            r["top"], r["bottom"],
            r["width_px"], r["height_px"]
        ])

# Automatic edge detection is provisional until
# the annotated rectangles are checked.
status = (
    "CAMERA_AUTO_GEOMETRY_CANDIDATE"
    if b["width_px"] < a["width_px"]
    and abs(ratio - expected) <= 0.10
    else "CAMERA_AUTO_DETECTION_REQUIRES_REVIEW"
)

lines = [
    "=== TASK 23.9 - AUTOMATIC CAMERA GEOMETRY ===",
    f"Baseline cube width: {a['width_px']} px",
    f"Displaced cube width: {b['width_px']} px",
    f"Measured width ratio: {ratio:.6f}",
    f"Expected width ratio: {expected:.6f}",
    f"Measured reduction: {reduction:.2f}%",
    f"Status: {status}",
    "Note: Bounding boxes are algorithmic candidates.",
    "Visual confirmation of cube boundaries is still required.",
    f"Image: {output_image}",
    f"CSV: {csv_file}",
]

report.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("\n=== FINAL RESULT ===")
print("\n".join(lines))
