from pathlib import Path
from datetime import datetime
import csv
import hashlib
import statistics

task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")
raw = Path(r"E:\GEMSTAR_Project\gemstar\Output")

csv_path = task / "02_CSV_Data/task23_08_lidar_displacement_rays.csv"
graph_path = task / "03_Graphs/task23_08_lidar_displacement.svg"

baseline = raw / "20261103T190743Z_sv_380_X_573_GEMSTARLIDARCLEAR23.osi"
displaced = raw / "20261103T191205Z_sv_380_X_604_GEMSTARLIDARDISPLACED23.osi"

fog = raw / "20261103T190206Z_sv_380_X_336_GEMSTARLIDAR23.osi"

clear_ini = task / "04_Configurations/task23_08_lidar_clear_calibration.ini"
fog_ini = task / "04_Configurations/task23_08_lidar_only_calibration.ini"

manifest = task / "05_Raw_Data_References/task23_08_final_evidence_manifest.csv"
report = task / "07_Research_Report/task23_08_final_lidar_calibration_report.md"

required = [
    csv_path, graph_path, baseline, displaced,
    fog, clear_ini, fog_ini
]

for path in required:
    if not path.is_file():
        raise FileNotFoundError(f"Missing evidence: {path}")

with csv_path.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 5271:
    raise RuntimeError(
        f"Expected 5271 rays in CSV, found {len(rows)}"
    )

candidates = [
    r for r in rows
    if int(r["candidate_front_face"]) == 1
]

matched = [
    r for r in rows
    if int(r["geometry_match"]) == 1
]

if not candidates or not matched:
    raise RuntimeError("Missing candidate or matched rays")

if any(r not in candidates for r in matched):
    raise RuntimeError("Matched rays are not a subset of candidates")

percentage = 100 * len(matched) / len(candidates)

changes = [float(r["change_m"]) for r in matched]
errors = [abs(float(r["geometry_error_m"])) for r in matched]

median_change = statistics.median(changes)
median_error = statistics.median(errors)
max_error = max(errors)

status = (
    "PASS"
    if len(matched) >= 10 and percentage >= 70
    else "REQUIRES_INVESTIGATION"
)

if status != "PASS":
    raise RuntimeError("Displacement validation threshold not met")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

manifest.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)

evidence = [
    ("baseline_clear_sensorview", baseline),
    ("displaced_clear_sensorview", displaced),
    ("preliminary_fog_sensorview", fog),
    ("clear_configuration", clear_ini),
    ("fog_configuration", fog_ini),
    ("displacement_csv", csv_path),
    ("displacement_graph", graph_path),
]

with manifest.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["evidence_type", "absolute_path", "bytes", "sha256"])

    for kind, path in evidence:
        writer.writerow([
            kind,
            str(path),
            path.stat().st_size,
            sha256(path)
        ])

report.write_text(f"""# Task 23.8 — Final LiDAR Calibration Report

Generated: {datetime.now().isoformat(timespec="seconds")}

## 1. Research objective
Validate LiDAR range response to a controlled 2 m target displacement
in the isolated GEMSTAR simulation environment.

## 2. Experimental configuration
- Sensor: GEMSTAR SimpleLidar
- LiDAR origin: (1940, -2650, 250) cm
- Orientation: (0, 0, 0) degrees
- Horizontal rays: 251
- Vertical rays: 21
- Total rays per scan: 5271
- Configured range: 50 m
- Validation target: cube with 300 cm sides
- Baseline target center X: 2940 cm
- Displaced target center X: 3140 cm
- Baseline target front face X: 2790 cm
- Displaced target front face X: 2990 cm

## 3. Experimental datasets
- Preliminary fog recording: {fog.name}
- Clear baseline: {baseline.name}
- Clear displaced: {displaced.name}
- Ten frames per recording were used in displacement analysis.

## 4. Results
- Baseline geometric candidates: {len(candidates)}
- Matching rays: {len(matched)}
- Unmatched candidates: {len(candidates)-len(matched)}
- Matching proportion: {percentage:.2f}%
- Median matched range increase: {median_change:.6f} m
- Median absolute geometry error among matched rays: {median_error:.6f} m
- Maximum absolute geometry error among matched rays: {max_error:.6f} m
- Controlled displacement status: {status}

## 5. Interpretation
The matched LiDAR rays responded to the controlled target displacement
in a manner consistent with the expected simulated geometry.

The measured median path-length increase is approximately 2.014 m,
rather than exactly 2 m, because the rays intersect the front face
at different angles.

The baseline candidate selection used range proximity, rather than
independently verified object identity.

## 6. Limitations
- Not all candidate rays met the displacement criterion.
- Candidate rays can hit other surfaces or become occluded.
- Geometric matching was evaluated only on the selected ray subset.
- Near-zero error in that subset is not an independent accuracy metric.
- Recordings were made separately and are not synchronized.
- The clear/fog comparison showed no observed change in ranges or
  positive-range counts in the tested frames; intensity and weather
  degradation require separate investigation.
- This is simulated geometric validation, not physical LiDAR calibration.
- CPU/FPGA energy and processing latency were not measured here.

## 7. Reproducibility evidence
- Ray comparison CSV: {csv_path}
- Displacement graph: {graph_path}
- Source-file hash manifest: {manifest}
- Original validation map was restored after acquisition, according
  to the experiment's PowerShell verification output.

## 8. Conclusion
Task 23.8 controlled LiDAR geometric displacement validation: {status}.

Next task: Task 23.9 Camera calibration and validation.
""", encoding="utf-8")

print("\n=== TASK 23.8 — FINAL RESEARCH CONSOLIDATION ===")
print(f"Validation: {status}")
print(f"Total rays: {len(rows)}")
print(f"Baseline candidates: {len(candidates)}")
print(f"Matching rays: {len(matched)}")
print(f"Matching proportion: {percentage:.2f}%")
print(f"Median range increase: {median_change:.4f} m")
print(f"Median absolute matched error: {median_error:.6f} m")
print(f"Evidence manifest: {manifest}")
print(f"Final report: {report}")
print("Status: TASK_23_8_EVIDENCE_FINALIZED")
