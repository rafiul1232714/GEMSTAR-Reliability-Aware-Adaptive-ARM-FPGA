from pathlib import Path
import csv
import hashlib
import statistics
from datetime import datetime

task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")
raw = Path(r"E:\GEMSTAR_Project\gemstar\Output")

measurements = task / "02_CSV_Data/task23_09_camera_auto_measurements.csv"
comparison = task / "03_Graphs/task23_09_auto_detected_cubes.png"
configuration = task / "04_Configurations/task23_09_camera_clear_calibration.ini"

baseline = raw / "20261103T194105Z_sv_380_X_55_GEMSTARCAMERACLEAR23.osi"
displaced = raw / "20261103T195644Z_sv_380_X_769_GEMSTARCAMERADISPLACED23.osi"

manifest = task / "05_Raw_Data_References/task23_09_final_camera_manifest.csv"
report = task / "07_Research_Report/task23_09_final_camera_calibration_report.md"

evidence = [
    ("baseline_osi", baseline),
    ("displaced_osi", displaced),
    ("camera_configuration", configuration),
    ("automatic_measurements", measurements),
    ("annotated_comparison", comparison),
    ("baseline_png", task / "03_Graphs/task23_09_baseline_frame003.png"),
    ("displaced_png", task / "03_Graphs/task23_09_displaced_frame003.png"),
    ("capture_report", task / "06_Research_Findings/task23_09_retry_result.txt"),
]

for _, path in evidence:
    if not path.is_file():
        raise FileNotFoundError(path)

with measurements.open(newline="", encoding="utf-8") as f:
    data = {r["condition"]: r for r in csv.DictReader(f)}

if set(data) != {"baseline", "displaced"}:
    raise RuntimeError("Expected baseline and displaced measurements")

w0 = float(data["baseline"]["width_px"])
w1 = float(data["displaced"]["width_px"])

ratio = w1 / w0
expected = 8.5 / 10.5
reduction = 100 * (1-ratio)
expected_reduction = 100 * (1-expected)
ratio_error = abs(ratio-expected)

# Screening threshold for this simulated experiment.
passed = (
    w1 < w0
    and ratio_error <= 0.03
)

if not passed:
    raise RuntimeError("Camera geometry requires investigation")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

manifest.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)

with manifest.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["type", "absolute_path", "bytes", "sha256"])
    for kind, path in evidence:
        writer.writerow([
            kind, str(path), path.stat().st_size, digest(path)
        ])

report.write_text(f"""# Task 23.9 — Camera Calibration Research Report

Generated: {datetime.now().isoformat(timespec="seconds")}

## Objective
Validate RGB camera recording and the simulated perspective
response to a controlled 2 m target displacement.

## Setup
- Simulator: GEMSTAR / Unreal Engine
- Resolution: 640 x 480
- Image payload: raw RGB, 921600 bytes per frame
- Camera position: (1940, -2650, 250) cm
- Horizontal field of view: 90 degrees
- Cube side length: 300 cm
- Baseline target front-face distance: 8.50 m
- Displaced target front-face distance: 10.50 m

## Recorded measurements
- Baseline front-face width: {w0:.0f} pixels
- Displaced front-face width: {w1:.0f} pixels
- Measured width ratio: {ratio:.6f}
- Ideal pinhole ratio: {expected:.6f}
- Measured width reduction: {reduction:.2f}%
- Expected width reduction: {expected_reduction:.2f}%
- Absolute ratio deviation: {ratio_error:.6f}

## Validation
Result: PASS — controlled simulated perspective consistency.

The automatic rectangles were visually checked against the
calibration target. This test uses a screening tolerance of
0.03 absolute width ratio, not an independently established
camera-accuracy specification.

## Important limitations
- The apparent cube edges are identified using image gradients.
- Only a limited sample of captured frames was compared.
- Pixel boundaries and antialiasing introduce measurement uncertainty.
- Weather-mode consistency is NOT validated: a previous runtime
  log showed Fog despite the calibration INI requesting Clear.
- This experiment does not establish physical camera calibration.
- No CPU/FPGA energy or latency measurements were performed.
- Original map restoration was confirmed in the recording logs.

## Evidence
- Measurements CSV: {measurements}
- Annotated image: {comparison}
- Evidence manifest: {manifest}
- Baseline OSI: {baseline}
- Displaced OSI: {displaced}

## Conclusion
Task 23.9 RGB payload and controlled geometric response: PASS.
Weather-effect behavior remains a documented follow-up.

Next: review remaining Task 23 research requirements before
Task 24 camera-LiDAR-radar association and fusion.
""", encoding="utf-8")

print("=== TASK 23.9 — FINAL CAMERA RESEARCH ===")
print(f"Baseline cube width: {w0:.0f} px")
print(f"Displaced cube width: {w1:.0f} px")
print(f"Measured reduction: {reduction:.2f}%")
print(f"Expected reduction: {expected_reduction:.2f}%")
print(f"Absolute width-ratio deviation: {ratio_error:.6f}")
print("Geometric validation: PASS")
print("Weather validation: UNRESOLVED")
print(f"Manifest: {manifest}")
print(f"Research report: {report}")
print("Status: TASK_23_9_GEOMETRIC_EVIDENCE_FINALIZED")
