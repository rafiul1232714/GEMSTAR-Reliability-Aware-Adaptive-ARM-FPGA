
# TASK 11 - COMPLETE RESEARCH ARCHIVE GENERATOR
# Creates an illustrated HTML report, Markdown report,
# file inventory, and preserves available Task 11 scripts.
# Does not modify original experiment data.

from pathlib import Path
from datetime import datetime
from html import escape
import csv
import shutil

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
PROJECT = Path(r"E:\GEMSTAR_Project\gemstar")
ARCHIVE = ROOT / "tests" / "Task_11_Final_Research"

GRAPHS = ARCHIVE / "01_Graphs"
DATA = ARCHIVE / "02_CSV_Data"
CONFIG = ARCHIVE / "03_Configurations"
CODE = ARCHIVE / "04_Code"
RAW_REFS = ARCHIVE / "05_Raw_Data_References"
FINDINGS = ARCHIVE / "06_Research_Findings"
REPORT = ARCHIVE / "07_Research_Report"

for folder in [
    GRAPHS, DATA, CONFIG, CODE,
    RAW_REFS, FINDINGS, REPORT
]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. PRESERVE ALL AVAILABLE TASK 11 SOURCE CODE
# ============================================================

copied = []

for source_dir, pattern in [
    (ROOT / "src", "task11*.py"),
    (ROOT / "matlab", "task11*.m"),
]:
    if source_dir.is_dir():
        for source in source_dir.glob(pattern):
            destination = CODE / source.name
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
                copied.append(source.name)

# Preserve the earlier camera extractor used in Task 11.
old_extractor = ROOT / "src" / "task09_extract_mor100_camera.py"

if old_extractor.is_file():
    shutil.copy2(old_extractor, CODE / old_extractor.name)

# Preserve current configuration as a reference snapshot.
ini = PROJECT / "Simulation" / "DefaultGemstar.ini"

if ini.is_file():
    shutil.copy2(
        ini, CONFIG / "DefaultGemstar_Task11_snapshot.ini"
    )


# ============================================================
# 2. RECORD RAW OSI SOURCES WITHOUT COPYING HUGE FILES
# ============================================================

raw_dir = ROOT / "data" / "raw" / "fog_mor100"

raw_files = (
    sorted(raw_dir.glob("*.osi"))
    if raw_dir.is_dir()
    else []
)

raw_text = [
    "TASK 11 RAW DATA REFERENCES",
    "",
    "Scenario: GEMSTAR MOR100",
    "Original files are referenced, not duplicated.",
    "",
]

for file in raw_files:
    raw_text.append(
        f"{file}\nSize: {file.stat().st_size:,} bytes\n"
    )

(RAW_REFS / "task11_original_osi_references.txt").write_text(
    "\n".join(raw_text),
    encoding="utf-8"
)


# ============================================================
# 3. RESEARCH CHAPTERS
# ============================================================

chapters = [
    (
        "11.1 - Sensor data and experiment identification",
        "Established the recorded GEMSTAR experiment, ego vehicle, "
        "SensorView messages, Ground Truth objects, and the relationship "
        "between recorded frame numbers and timestamps.",
        "Identified the MOR100 recording and established a common "
        "data source for Camera, LiDAR and Radar.",
        "Sensor identification alone does not prove calibration."
    ),
    (
        "11.2 - Common sensor-frame reconstruction",
        "Examined sensor mounting positions and orientations. "
        "Reconstructed LiDAR and Radar observations in a provisional "
        "ego-vehicle coordinate system.",
        "Produced coordinate-based measurement tables usable "
        "for MATLAB plotting and geometric diagnostics.",
        "Lateral-axis signs and the full coordinate transformation "
        "were not independently validated."
    ),
    (
        "11.3 - LiDAR point-cloud reconstruction",
        "Decoded LiDAR ranges and ray indices, reconstructed 3D "
        "positions, and inspected point-cloud distributions.",
        "Generated reusable LiDAR measurement CSVs and geometric "
        "visualizations.",
        "The underlying LiDAR return geometry requires calibration "
        "and simulator-surface interpretation."
    ),
    (
        "11.4 - Ground filtering and obstacle clustering",
        "Separated low ground-like returns from elevated candidates "
        "and applied geometric clustering to selected frames.",
        "Established a reproducible clustering workflow and "
        "identified candidate non-ground structures.",
        "A geometric cluster is not automatically a vehicle."
    ),
    (
        "11.5 - Ground Truth and LiDAR visibility investigation",
        "Investigated vehicle Ground Truth positions, forward-field "
        "candidates, LiDAR ray geometry, ray indices, scan layers "
        "and diagnostic simulator object IDs.",
        "Found that available raycast reflections could not reliably "
        "be identified with the predicted nearby vehicle.",
        "Simulator diagnostic surface IDs must not be confused "
        "with OSI Ground Truth vehicle IDs."
    ),
    (
        "11.6 - Independent LiDAR object clustering",
        "Performed a separate height-filtered clustering experiment "
        "on frame 150, without depending on a successful vehicle "
        "detection.",
        "A cluster of 190 points was obtained. Its measured "
        "dimensions were approximately 7.548 m by 0.992 m, "
        "with a vertical extent of 0.270 m.",
        "The long, low cluster is more consistent with roadside "
        "geometry than a verified complete vehicle."
    ),
    (
        "11.7 - Radar processing and LiDAR-Radar association",
        "Reconstructed Radar reflections and compared their "
        "distances with LiDAR points and the selected cluster.",
        "Frame 150 contained 31 valid Radar reflections. Nine "
        "were within 1 metre of the selected cluster in the "
        "provisional XY geometry.",
        "Spatial proximity is not sufficient evidence that "
        "both sensors detected the same physical object."
    ),
    (
        "11.8A-D - Camera extraction and synchronized dashboard",
        "Extracted the exact Camera image from OSI frame 150 "
        "and displayed Camera, LiDAR and Radar observations "
        "together in MATLAB.",
        "Successfully generated a synchronized three-sensor "
        "inspection dashboard. Camera timestamp: 4.902842 s.",
        "Simultaneous display does not establish object-level fusion."
    ),
    (
        "11.8E-F - YOLO vehicle detection",
        "Tested pretrained YOLO11n and YOLO11s models on the "
        "recorded Camera image and compared the classifications.",
        "YOLO11n missed the car and classified an object as an "
        "airplane. YOLO11s detected the white car with "
        "confidence 0.9306 and visually plausible bounding box "
        "(45.70,244.30)-(281.22,380.37). "
        "One YOLO11s CPU prediction took 70.419 ms.",
        "The additional person prediction was unverified. "
        "Single-image CPU timings are preliminary."
    ),
    (
        "11.8G-J - Camera calibration and 3D projection",
        "Read GEMSTAR Camera C++ code and sensor configuration. "
        "Used a provisional perspective camera model and "
        "projected LiDAR and Radar points onto the image.",
        "Confirmed 640x480 resolution and 90-degree horizontal "
        "capture FOV. Projection showed zero selected-cluster "
        "points in the car box for one lateral convention, "
        "versus 190 for the other.",
        "Choosing a coordinate sign because it increases "
        "overlap would be invalid calibration."
    ),
    (
        "11.8K - Cluster physical-geometry validation",
        "Compared the projected cluster with its actual "
        "3D shape, vertical distribution, and diagnostic ID.",
        "All 190 cluster points had reconstructed Z below "
        "0.5 m; measured Z ranged from 0.152 to 0.422 m. "
        "Diagnostic surface ID: 83265.",
        "Image-box overlap did not verify a common vehicle."
    ),
    (
        "11.9 - Validation and research archiving",
        "Audited the saved figures, CSVs, scripts and research "
        "findings, and documented successful and unsuccessful "
        "experiments.",
        "The previous focused audit confirmed 11 of 11 "
        "selected files were present.",
        "Full object-level Camera-LiDAR-Radar fusion remains "
        "unverified. Further Ground Truth calibration and "
        "multi-frame evaluation are required."
    ),
]


# ============================================================
# 4. DISCOVER ALL EXISTING EXPERIMENT FILES
# ============================================================

inventory = []

for file in sorted(ARCHIVE.rglob("*")):
    if not file.is_file():
        continue

    # Exclude generated report files to avoid stale/self entries.
    if REPORT in file.parents:
        continue

    relative = file.relative_to(ARCHIVE)

    inventory.append({
        "relative_path": str(relative),
        "category": relative.parts[0],
        "extension": file.suffix.lower(),
        "bytes": file.stat().st_size,
    })

inventory_csv = REPORT / "task11_complete_file_inventory.csv"

with inventory_csv.open(
    "w", newline="", encoding="utf-8"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "relative_path",
            "category",
            "extension",
            "bytes"
        ]
    )
    writer.writeheader()
    writer.writerows(inventory)


# ============================================================
# 5. GENERATE MARKDOWN RESEARCH REPORT
# ============================================================

markdown = [
    "# Task 11 - Complete Research Documentation",
    "",
    "**Project:** GEMSTAR Multi-Sensor Perception",
    "**Scenario:** MOR100 Fog",
    "**Reference frame:** 150",
    "**Camera timestamp:** 4.902842 s",
    f"**Report generated:** {datetime.now():%Y-%m-%d %H:%M}",
    "",
    "## Scope",
    "",
    "This report documents the Task 11 research baseline. "
    "It distinguishes verified results from provisional "
    "geometric interpretations.",
    "",
]

for title, method, result, limitation in chapters:
    markdown.extend([
        f"## Task {title}",
        "",
        f"**What we did:** {method}",
        "",
        f"**Results:** {result}",
        "",
        f"**Limitations:** {limitation}",
        "",
    ])

markdown.extend([
    "## Research conclusion",
    "",
    "The study established an end-to-end recorded-data "
    "inspection pipeline for Camera, LiDAR and Radar. "
    "A 2D car detection was visually confirmed, but "
    "the selected LiDAR and Radar measurements could "
    "not be reliably attributed to that vehicle.",
    "",
    "This is a valid and useful baseline result. "
    "Object-level fusion remains future work.",
    "",
    "## Complete file inventory",
    "",
])

for item in inventory:
    markdown.append(
        f"- `{item['relative_path']}` "
        f"({item['bytes']:,} bytes)"
    )

md_file = REPORT / "task11_complete_research_report.md"
md_file.write_text("\n".join(markdown), encoding="utf-8")


# ============================================================
# 6. BUILD ILLUSTRATED HTML REPORT
# ============================================================

def section(title, method, result, limitation):
    return f"""
    <section>
      <h2>{escape(title)}</h2>
      <h3>What we did</h3>
      <p>{escape(method)}</p>
      <h3>Results and findings</h3>
      <p>{escape(result)}</p>
      <h3>Limitations</h3>
      <p>{escape(limitation)}</p>
    </section>
    """

chapter_html = "\n".join(section(*c) for c in chapters)

# Include every available PNG/JPG image, grouped by folder.
image_files = [
    p for p in sorted(GRAPHS.rglob("*"))
    if p.is_file() and p.suffix.lower()
    in {".png", ".jpg", ".jpeg"}
]

# Convert original PPM images for the browser, when Pillow is available.
try:
    from PIL import Image

    for ppm in sorted(GRAPHS.rglob("*.ppm")):
        preview = REPORT / (ppm.stem + "_preview.png")
        with Image.open(ppm) as img:
            img.convert("RGB").save(preview)
        image_files.append(preview)

except ImportError:
    print("Pillow unavailable: PPM browser previews skipped.")

except Exception as exc:
    print("PPM preview conversion warning:", exc)

gallery_html = []

for image in image_files:
    relative = image.relative_to(REPORT) \
        if REPORT in image.parents \
        else Path("..") / image.relative_to(ARCHIVE)

    url = relative.as_posix()

    gallery_html.append(f"""
    <figure>
      <img src="{escape(url, quote=True)}"
           alt="{escape(image.name, quote=True)}">
      <figcaption>{escape(image.name)}</figcaption>
    </figure>
    """)

file_rows = "\n".join(
    "<tr>"
    f"<td>{escape(i['category'])}</td>"
    f"<td>{escape(i['relative_path'])}</td>"
    f"<td>{i['bytes']:,}</td>"
    "</tr>"
    for i in inventory
)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>GEMSTAR Task 11 Research Report</title>
<style>
@page {{ size: A4; margin: 17mm; }}
body {{
  font-family: Arial, sans-serif;
  color: #182739;
  max-width: 1050px;
  margin: 35px auto;
  line-height: 1.55;
}}
h1 {{ font-size: 30px; color: #16395b; }}
h2 {{
  color: #174a75;
  border-bottom: 2px solid #d7e4f1;
  padding-bottom: 8px;
  margin-top: 35px;
}}
h3 {{ font-size: 14px; margin-bottom: 3px; }}
section {{
  margin: 28px 0;
  break-inside: avoid;
}}
p {{ margin-top: 6px; }}
.subtitle {{ color: #61748a; }}
figure {{
  margin: 25px 0;
  break-inside: avoid;
}}
img {{
  max-width: 100%;
  max-height: 630px;
  object-fit: contain;
  border: 1px solid #d8e0e9;
}}
figcaption {{
  font-size: 12px;
  color: #57677c;
  overflow-wrap: anywhere;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}}
th, td {{
  border-bottom: 1px solid #d8e0e9;
  text-align: left;
  padding: 7px;
  overflow-wrap: anywhere;
}}
th {{ background: #eef3f9; }}
@media print {{
  body {{ margin: 0; max-width: none; }}
  figure, section {{ break-inside: avoid; }}
}}
</style>
</head>
<body>

<h1>GEMSTAR - Task 11</h1>
<h2>Complete Multi-Sensor Research Documentation</h2>

<p class="subtitle">
MOR100 Fog Scenario | Frame 150 | Camera / LiDAR / Radar
</p>

<p><strong>Report generated:</strong>
{datetime.now():%Y-%m-%d %H:%M}</p>

<h2>Executive summary</h2>
<p>
Task 11 established a recorded-data perception research baseline
using GEMSTAR OSI data, Python, MATLAB, and pretrained YOLO models.
Camera vehicle detection succeeded with YOLO11s.
LiDAR and Radar processing produced useful measurements,
but verified object-level tri-sensor fusion was not achieved.
</p>

{chapter_html}

<h2>Research figures and images</h2>
<p>
The following figures were discovered automatically in the
Task 11 archive. Images may include intermediate experiments,
diagnostics, and unsuccessful trials.
</p>

{''.join(gallery_html)}

<h2>Data and reproducibility inventory</h2>
<table>
<thead>
<tr><th>Folder</th><th>Relative path</th><th>Bytes</th></tr>
</thead>
<tbody>
{file_rows}
</tbody>
</table>

<h2>Final conclusion</h2>
<p>
A synchronized three-sensor processing workflow and visually
validated 2D Camera vehicle detection were demonstrated.
However, 2D overlap with the Camera bounding box did not
establish the identity of the corresponding 3D LiDAR
or Radar observations. This limitation is explicitly
retained as a research finding.
</p>

</body>
</html>
"""

html_file = REPORT / "task11_complete_illustrated_report.html"
html_file.write_text(html, encoding="utf-8")

print("\n===== TASK 11 ARCHIVE GENERATED =====")
print("Total indexed files:", len(inventory))
print("Copied Task 11 scripts:", len(copied))
print("Included images:", len(image_files))
print("Research chapters:", len(chapters))
print("\nMarkdown:", md_file)
print("HTML:", html_file)
print("File inventory:", inventory_csv)
print("\nOriginal OSI data was not duplicated.")
print("TASK 11 DOCUMENTATION COMPLETED")
