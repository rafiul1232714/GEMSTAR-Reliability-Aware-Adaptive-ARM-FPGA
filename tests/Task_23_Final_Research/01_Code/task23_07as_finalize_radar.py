from pathlib import Path
import csv
import re
import hashlib
from datetime import datetime

root = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")

baseline = root / "05_Raw_Data_References/task23_07aq_instrumented_runtime.log"
displaced = root / "05_Raw_Data_References/task23_07ar_final_runtime.log"

csv_dir = root / "02_CSV_Data"
graph_dir = root / "03_Graphs"
findings_dir = root / "06_Research_Findings"
report_dir = root / "07_Research_Report"

for folder in (csv_dir, graph_dir, findings_dir, report_dir):
    folder.mkdir(parents=True, exist_ok=True)

for file in (baseline, displaced):
    if not file.is_file():
        raise FileNotFoundError(f"Required log missing: {file}")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

pattern = re.compile(
    r"RAY=(\d+).*?"
    r"BLOCKING=(\d+).*?"
    r"ACTOR=(\S+).*?"
    r"DIST_CM=([0-9.]+).*?"
    r"IMPACT=X=([-0-9.]+)\s+"
    r"Y=([-0-9.]+)\s+"
    r"Z=([-0-9.]+)"
)

def read_rays(path):
    result = {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    if not any("TASK23_RADAR_DIAGNOSTIC ORIGIN=" in x for x in lines):
        raise RuntimeError(f"Radar origin missing: {path.name}")

    for line in lines:
        if "TASK23_RADAR_DIAGNOSTIC RAY=" not in line:
            continue

        match = pattern.search(line)
        if not match:
            continue

        ray, blocking, actor, distance, x, y, z = match.groups()
        ray = int(ray)

        if ray not in result:
            result[ray] = {
                "blocking": int(blocking),
                "actor": actor,
                "distance": float(distance),
                "x": float(x),
                "y": float(y),
                "z": float(z)
            }

    for ray in (44, 45, 54, 55):
        if ray not in result:
            raise RuntimeError(f"Ray {ray} missing from {path.name}")

    return result

a = read_rays(baseline)
b = read_rays(displaced)

rows = []
for ray in (44, 45, 54, 55):
    first, second = a[ray], b[ray]

    rows.append({
        "ray": ray,
        "baseline_distance_cm": first["distance"],
        "displaced_distance_cm": second["distance"],
        "distance_change_cm": round(
            second["distance"] - first["distance"], 6
        ),
        "baseline_impact_x_cm": first["x"],
        "displaced_impact_x_cm": second["x"],
        "baseline_actor": first["actor"],
        "displaced_actor": second["actor"],
        "baseline_blocking": first["blocking"],
        "displaced_blocking": second["blocking"]
    })

passed = all(
    r["baseline_blocking"] == 1
    and r["displaced_blocking"] == 1
    and abs(r["baseline_impact_x_cm"] - 2790) < 1
    and abs(r["displaced_impact_x_cm"] - 2990) < 1
    and abs(r["distance_change_cm"] - 200.802) < 1
    for r in rows
)

if not passed:
    raise RuntimeError(
        "Observed displacement diagnostics failed validation. "
        "Evidence files not finalized."
    )

csv_file = csv_dir / "task23_07as_radar_displacement_final.csv"

with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

baseline_cm = rows[0]["baseline_distance_cm"]
displaced_cm = rows[0]["displaced_distance_cm"]
increase_cm = rows[0]["distance_change_cm"]

# Create a standalone SVG plot without external libraries.
maximum = 1200
width = 700
left = 175
scale = 440 / maximum

bars = [
    ("Original target", baseline_cm, 110, "#3478b9"),
    ("Target moved 2 m", displaced_cm, 200, "#21a17b")
]

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="700" height="310" viewBox="0 0 700 310">',
    '<rect width="700" height="310" fill="white"/>',
    '<text x="24" y="35" font-family="Arial" font-size="21" font-weight="bold">Radar range response</text>',
    '<text x="24" y="57" font-family="Arial" font-size="13" fill="#555">Instrumented GEMSTAR ray 44</text>'
]

for name, value, y, color in bars:
    bar_width = round(value * scale, 2)
    parts.append(
        f'<text x="24" y="{y+24}" font-family="Arial" font-size="14">{name}</text>'
    )
    parts.append(
        f'<rect x="{left}" y="{y}" width="{bar_width}" height="35" fill="{color}" rx="4"/>'
    )
    parts.append(
        f'<text x="{left+bar_width+10}" y="{y+24}" font-family="Arial" font-size="14">{value:.3f} cm</text>'
    )

parts.append(
    f'<text x="24" y="280" font-family="Arial" font-size="16">Measured increase: +{increase_cm:.3f} cm</text>'
)
parts.append('</svg>')

graph_file = graph_dir / "task23_07as_radar_displacement.svg"
graph_file.write_text("\n".join(parts), encoding="utf-8")

manifest = findings_dir / "task23_07as_evidence_hashes.csv"
with manifest.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["file", "sha256"])
    for path in (baseline, displaced, csv_file, graph_file):
        writer.writerow([str(path), sha256(path)])

report = report_dir / "task23_07as_radar_calibration_report.md"

report.write_text(f"""# Task 23.7AS — Radar Calibration and Displacement Validation

Generated: {datetime.now().isoformat(timespec="seconds")}

## Objective
Validate controlled geometric range response in the GEMSTAR
radar-only simulation before proceeding to multi-sensor processing.

## Setup
- Unreal Engine / GEMSTAR isolated research validation map
- Radar origin: (1940, -2650, 250) cm
- Radar orientation: (0, 0, 0) degrees
- Four central diagnostic rays: 44, 45, 54, 55
- Nominal calibration cube: 300 cm side length
- Initial cube center X: 2940 cm
- Displaced cube center X: 3140 cm

## Verified results
- Baseline ray 44: {baseline_cm:.3f} cm
- Displaced ray 44: {displaced_cm:.3f} cm
- Distance increase: {increase_cm:.3f} cm
- Baseline hit X: {rows[0]["baseline_impact_x_cm"]:.3f} cm
- Displaced hit X: {rows[0]["displaced_impact_x_cm"]:.3f} cm
- Four central rays satisfy the displacement checks
- Controlled displacement validation: PASS
- Map persistence independently verified during the experiment
- Original map and configuration were restored (per PowerShell output)

## Interpretation
The measured range change is consistent with a 200 cm shift
along world X. Because the rays are slightly angled, their
path-length increase is approximately 200.802 cm rather than
exactly 200 cm.

The initial unchanged-reading investigation was traced to
a map edit that had not persisted. Explicit map saving and an
independent reload fixed the experiment setup.

## Scientific limitations
- Validates a static, idealized simulation geometry
- Does not establish physical Radar sensor accuracy
- Does not measure real Radar noise, false detections or robustness
- Does not establish fog/traffic performance
- Does not measure CPU/FPGA energy or computational latency
- OSI range serialization needs separate end-to-end comparison
  if required for the thesis accuracy claim

## Research evidence
- Baseline log: {baseline}
- Displaced log: {displaced}
- Measurement CSV: {csv_file}
- Comparison graph: {graph_file}
- SHA-256 manifest: {manifest}

## Outcome
Task 23.7 controlled Radar displacement experiment: PASS.
Next planned sensor calibration: Task 23.8 LiDAR.
""", encoding="utf-8")

print("\n=== TASK 23.7AS — FINAL RADAR EVIDENCE ===")
print("Validation: PASS")
print(f"Baseline: {baseline_cm:.3f} cm")
print(f"Displaced: {displaced_cm:.3f} cm")
print(f"Increase: {increase_cm:.3f} cm")
print(f"Verified rays: {len(rows)}")
print(f"CSV: {csv_file}")
print(f"Graph: {graph_file}")
print(f"Hashes: {manifest}")
print(f"Report: {report}")
