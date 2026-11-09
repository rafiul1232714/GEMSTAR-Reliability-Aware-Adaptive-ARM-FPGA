
# TASK 12.7 - COMPLETE RESEARCH ARCHIVE
# Collects existing Task 12 outputs and creates
# an illustrated, printable HTML research report.

from pathlib import Path
from datetime import datetime
from html import escape
import csv
import shutil

ROOT = Path("E:/GEMSTAR_Project/sensor-health-monitor")
PROJECT = Path("E:/GEMSTAR_Project/gemstar")
TASK = ROOT / "tests" / "Task_12_Final_Research"

GRAPHS = TASK / "01_Graphs"
DATA = TASK / "02_CSV_Data"
CONFIG = TASK / "03_Configurations"
CODE = TASK / "04_Code"
RAW = TASK / "05_Raw_Data_References"
FINDINGS = TASK / "06_Research_Findings"
REPORT = TASK / "07_Research_Report"

for folder in [GRAPHS, DATA, CONFIG, CODE, RAW, FINDINGS, REPORT]:
    folder.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1. ARCHIVE SOURCE SCRIPTS
# --------------------------------------------------

for source_dir, pattern in [
    (ROOT / "src", "task12*.py"),
    (ROOT / "matlab", "task12*.m"),
]:
    if source_dir.exists():
        for source in source_dir.glob(pattern):
            shutil.copy2(source, CODE / source.name)

# --------------------------------------------------
# 2. COPY RELEVANT CONFIGURATION
# --------------------------------------------------

config_source = PROJECT / "Simulation" / "DefaultGemstar.ini"

if config_source.exists():
    shutil.copy2(
        config_source,
        CONFIG / "DefaultGemstar_Task12_snapshot.ini"
    )

# --------------------------------------------------
# 3. COPY REFERENCED CAMERA IMAGES
# --------------------------------------------------

camera_source = (
    ROOT / "results" / "figures" / "fog_mor100_camera"
)

frames = [91, 101, 111, 121, 131, 141, 151, 431]

for frame in frames:
    source = camera_source / (
        f"mor100_frame_{frame:04d}_camera_0.ppm"
    )
    if source.exists():
        shutil.copy2(source, GRAPHS / source.name)

# --------------------------------------------------
# 4. ORIGINAL DATA REFERENCES
# --------------------------------------------------

references = [
    "TASK 12 - ORIGINAL DATA REFERENCES",
    "",
    "Scenario: GEMSTAR MOR100",
    "",
    "Ground Truth CSV:",
    str(ROOT / "tests" / "Task_11_Final_Research"
        / "02_CSV_Data" / "task11_groundtruth_objects.csv"),
    "",
    "LiDAR geometry CSV:",
    str(ROOT / "tests" / "Task_11_Final_Research"
        / "02_CSV_Data" / "task11_lidar_frame150_geometry.csv"),
    "",
    "Radar measurements CSV:",
    str(ROOT / "tests" / "Task_11_Final_Research"
        / "02_CSV_Data"
        / "task11_frame150_radar_cluster_association.csv"),
    "",
    "Raw recordings:",
]

raw_dir = ROOT / "data" / "raw" / "fog_mor100"
if raw_dir.exists():
    for file in sorted(raw_dir.glob("*.osi")):
        references.append(
            f"{file} ({file.stat().st_size:,} bytes)"
        )

(RAW / "task12_source_references.txt").write_text(
    "\n".join(references), encoding="utf-8"
)

# --------------------------------------------------
# 5. REPORT CHAPTERS
# --------------------------------------------------

chapters = [
    (
        "12.1 - Ground Truth Object Identification",
        "Identified the ego vehicle and nearby traffic vehicles "
        "in the MOR100 recording.",
        "Ego vehicle ID: 76895. Candidate white-car ID: 76865.",
        "The candidate correspondence required camera validation."
    ),
    (
        "12.2 - Ground Truth to Camera Projection",
        "Transformed the target position into a provisional "
        "ego-camera geometry and compared projected vehicle "
        "centers against the YOLO11s bounding box.",
        "The negative-Y projection fell within the detected "
        "car box with approximately 37.43 pixels of center error.",
        "The GT Z reference and camera extrinsics remain provisional."
    ),
    (
        "12.3 - LiDAR to Ground Truth Proximity",
        "Compared recorded LiDAR points with the target GT "
        "center for both lateral-axis hypotheses.",
        "279 and 389 points fell within the 2-metre search "
        "radius in the respective hypotheses.",
        "Nearby points were not verified as vehicle reflections."
    ),
    (
        "12.4 - Radar to Ground Truth Proximity",
        "Compared 31 recorded Radar returns against the "
        "same candidate vehicle position.",
        "Six and seven returns fell within a 2-metre "
        "GT-center search radius.",
        "Radar object identity and Doppler interpretation "
        "were not independently verified."
    ),
    (
        "12.5 - Cross-Sensor Evidence Assessment",
        "Combined Camera, LiDAR, Radar and GT proximity results "
        "into a reproducible evidence comparison.",
        "Camera-to-GT association was supported as a candidate. "
        "LiDAR/Radar object associations remained unverified.",
        "No confirmed object-level tri-sensor fusion was demonstrated."
    ),
    (
        "12.6A - Multi-Frame Availability",
        "Compared existing Camera image frames with Ground Truth "
        "vehicle presence.",
        "47 Camera images were available; 37 frames included "
        "both ego and target Ground Truth objects.",
        "GT presence alone does not indicate Camera visibility."
    ),
    (
        "12.6B - Camera Visibility Candidate Filtering",
        "Projected target GT centers using a provisional "
        "camera model.",
        "Eight frames had projected GT centers inside "
        "the image.",
        "Center-in-image is not a verified visibility label."
    ),
    (
        "12.6C - Multi-Frame YOLO11s Evaluation",
        "Ran YOLO11s on eight selected Camera frames.",
        "Seven frames contained vehicle predictions. Six "
        "contained provisional GT-center overlap.",
        "These counts are not validated detection recall."
    ),
    (
        "12.6D - Multi-Frame Performance Analysis",
        "Analyzed detection confidence, geometric alignment "
        "and CPU prediction time across the eight frames.",
        "Mean prediction wall time: 51.057 ms, with observed "
        "range 47.938-61.232 ms.",
        "Single-run timing does not establish hardware speedup "
        "or statistically robust latency performance."
    ),
]

# --------------------------------------------------
# 6. INVENTORY ALL ARCHIVED DATA
# --------------------------------------------------

inventory = []

for file in sorted(TASK.rglob("*")):
    if not file.is_file() or REPORT in file.parents:
        continue
    relative = file.relative_to(TASK)
    inventory.append((
        relative.as_posix(),
        file.stat().st_size
    ))

inventory_path = REPORT / "task12_file_inventory.csv"

with inventory_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["relative_path", "size_bytes"])
    writer.writerows(inventory)

# --------------------------------------------------
# 7. PREPARE FIGURE PREVIEWS
# --------------------------------------------------

image_files = sorted(
    file for file in GRAPHS.rglob("*")
    if file.is_file()
    and file.suffix.lower() in (".png", ".jpg", ".jpeg")
)

# Create browser-friendly previews for the PPM images.
from PIL import Image

for ppm in sorted(GRAPHS.glob("*.ppm")):
    preview = REPORT / (ppm.stem + "_preview.png")
    with Image.open(ppm) as image:
        image.convert("RGB").save(preview)
    image_files.append(preview)

# --------------------------------------------------
# 8. GENERATE ILLUSTRATED HTML REPORT
# --------------------------------------------------

chapter_html = ""

for title, method, result, limitation in chapters:
    chapter_html += f"""
    <section>
      <h2>{escape(title)}</h2>
      <h3>What we did</h3>
      <p>{escape(method)}</p>
      <h3>Findings</h3>
      <p>{escape(result)}</p>
      <h3>Limitations</h3>
      <p>{escape(limitation)}</p>
    </section>
    """

gallery_html = ""

for img in image_files:
    if REPORT in img.parents:
        relative = img.relative_to(REPORT)
    else:
        relative = Path("..") / img.relative_to(TASK)

    gallery_html += f"""
    <figure>
      <img src="{escape(relative.as_posix(), quote=True)}">
      <figcaption>{escape(img.stem)}</figcaption>
    </figure>
    """

inventory_html = "\n".join(
    f"<tr><td>{escape(path)}</td><td>{size:,}</td></tr>"
    for path, size in inventory
)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GEMSTAR Task 12 Research Report</title>
<style>
@page {{ size: A4; margin: 16mm; }}
body {{
  font-family: Arial, sans-serif;
  color: #17263a;
  max-width: 1050px;
  margin: 35px auto;
  line-height: 1.55;
}}
h1 {{ color: #173d63; }}
h2 {{
  color: #20517f;
  border-bottom: 1px solid #ccd9e6;
  padding-bottom: 6px;
}}
h3 {{ margin-bottom: 4px; }}
section {{ margin-bottom: 25px; }}
figure {{ margin: 25px 0; break-inside: avoid; }}
img {{
  max-width: 100%;
  max-height: 630px;
  object-fit: contain;
}}
figcaption {{ font-size: 12px; color: #555; }}
table {{ width: 100%; border-collapse: collapse; }}
td, th {{
  padding: 7px;
  border-bottom: 1px solid #ddd;
  text-align: left;
  overflow-wrap: anywhere;
}}
@media print {{
  section {{ break-inside: avoid; }}
}}
</style>
</head>
<body>

<h1>GEMSTAR - Task 12</h1>
<h2>Ground Truth-Based Multi-Sensor Association</h2>

<p><strong>Scenario:</strong> MOR100 Fog</p>
<p><strong>Generated:</strong> {datetime.now():%Y-%m-%d %H:%M}</p>

<h2>Executive Summary</h2>

<p>
Task 12 investigated whether camera detections, LiDAR
measurements and Radar returns could be associated
with a recorded Ground Truth vehicle.
Camera and Ground Truth correspondence was supported
under a provisional projection model, but verified
three-sensor object association was not established.
</p>

{chapter_html}

<h2>Experimental Figures and Camera Images</h2>
{gallery_html}

<h2>Complete Research File Inventory</h2>

<table>
<tr><th>File</th><th>Bytes</th></tr>
{inventory_html}
</table>

<h2>Final Research Conclusion</h2>
<p>
The experiment established a reusable multi-frame
Camera detection and geometric evidence baseline.
Further calibration, object-level correspondence
and independently validated annotations are needed
before claiming successful tri-sensor fusion.
</p>

</body>
</html>
"""

html_file = REPORT / "task12_illustrated_research_report.html"
html_file.write_text(html, encoding="utf-8")

# Also save a standalone text summary.
text_lines = ["TASK 12 - RESEARCH REPORT", ""]

for title, method, result, limitation in chapters:
    text_lines.extend([
        title,
        "Method: " + method,
        "Result: " + result,
        "Limitation: " + limitation,
        ""
    ])

(REPORT / "task12_research_summary.txt").write_text(
    "\n".join(text_lines), encoding="utf-8"
)

print("\n===== TASK 12 COMPLETE RESEARCH ARCHIVE =====")
print("Research files indexed:", len(inventory))
print("Research chapters:", len(chapters))
print("Images in report:", len(image_files))
print("HTML report:", html_file)
print("Inventory:", inventory_path)
print("TASK 12 ARCHIVE COMPLETED")
