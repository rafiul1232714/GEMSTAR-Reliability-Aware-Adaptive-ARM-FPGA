
from pathlib import Path
from html import escape
import csv
import shutil
from datetime import datetime

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_13_Final_Research"

GRAPHS = TASK / "01_Graphs"
DATA = TASK / "02_CSV_Data"
CODE = TASK / "04_Code"
FINDINGS = TASK / "06_Research_Findings"

for folder in (GRAPHS, DATA, CODE, FINDINGS):
    folder.mkdir(parents=True, exist_ok=True)

print("\n===== TASK 13.8 - FINAL REPORT =====")

# Archive Task 13 Python and MATLAB scripts.
copied = 0

for pattern in ("task13*.py", "task13*.m"):
    for source in (ROOT / "src").glob(pattern):
        destination = CODE / source.name
        if not destination.exists():
            shutil.copy2(source, destination)
            copied += 1

# List existing archive directories, without renaming them.
folders = sorted(
    p for p in TASK.iterdir() if p.is_dir()
)

files = sorted(
    p for p in TASK.rglob("*") if p.is_file()
)

manifest = DATA / "task13_8_archive_manifest.csv"

with manifest.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["relative_path", "size_bytes"])

    for path in files:
        if path == manifest:
            continue
        writer.writerow([
            str(path.relative_to(TASK)),
            path.stat().st_size
        ])

# Select the most relevant figures, if available.
figure_specs = [
    ("Camera frame 150",
     "task13_5e_camera_frame150_rgb.png"),
    ("Camera-LiDAR-Radar overlay",
     "task13_5p_camera_lidar_radar_overlay.png"),
    ("Actor-coloured LiDAR overlay",
     "task13_5j_square_pixel_actors.png"),
    ("Filtered LiDAR reflections",
     "task13_5n_non_ground_candidates.png"),
    ("LiDAR reflections over time",
     "task13_7b_lidar_over_time.png"),
    ("Radar reflections over time",
     "task13_7b_radar_over_time.png"),
    ("Ground Truth target presence",
     "task13_7b_target_presence.png"),
]

def section(title, content):
    return (
        "<section><h2>" + escape(title) +
        "</h2>" + content + "</section>"
    )

def paragraph(text):
    return "<p>" + escape(text) + "</p>"

def table(headers, rows):
    result = "<table><thead><tr>"
    for header in headers:
        result += "<th>" + escape(str(header)) + "</th>"
    result += "</tr></thead><tbody>"

    for row in rows:
        result += "<tr>"
        for value in row:
            result += "<td>" + escape(str(value)) + "</td>"
        result += "</tr>"

    return result + "</tbody></table>"

parts = []

parts.append(section(
    "Executive summary",
    paragraph(
        "This study investigates synchronized Camera, LiDAR, "
        "and Radar observations from the GEMSTAR MOR100 scenario, "
        "with Ground Truth and coordinate-frame validation. "
        "It is a feasibility and calibration study, not a "
        "validated object-level fusion detector."
    )
))

parts.append(section(
    "Experimental setup",
    table(
        ["Parameter", "Recorded value"],
        [
            ("Scenario", "MOR100, fog"),
            ("Frames", "466"),
            ("Selected detailed frame", "150"),
            ("Frame 150 time", "4.902842395 s"),
            ("Camera", "640 x 480, RGB"),
            ("Camera mount", "(0.70, 0, 1.60) m"),
            ("LiDAR mount", "(2.60, 0, 0.70) m"),
            ("Radar mount", "(2.00, 0, 0.80) m"),
            ("LiDAR grid", "251 x 21 = 5271 rays"),
        ]
    )
))

parts.append(section(
    "Sensor availability and synchronization",
    table(
        ["Metric", "Result"],
        [
            ("Camera views", "466/466 frames"),
            ("LiDAR views", "466/466 frames"),
            ("Radar views", "466/466 frames"),
            ("LiDAR valid-return frames", "466"),
            ("Radar valid-return frames", "465"),
            ("LiDAR/Radar/GT timestamp alignment",
             "466/466 exported frames"),
            ("Target GT 76865 present", "376 frames"),
        ]
    )
))

parts.append(section(
    "Frame 150 LiDAR analysis",
    table(
        ["Actor diagnostic ID", "Returns", "Normal classification"],
        [
            ("83185", "1428", "Horizontal-like"),
            ("83265", "412", "Vertical-like"),
            ("83181", "200", "Horizontal-like"),
            ("83183", "4", "Horizontal-like"),
        ]
    ) +
    paragraph(
        "Actor 83185 is a strong flat-ground candidate. "
        "Its exact Unreal actor identity remains unconfirmed. "
        "The remaining 616 returns did not establish "
        "a confirmed association with GT target 76865."
    )
))

parts.append(section(
    "Origin and geometry calibration",
    paragraph(
        "Direct C++ diagnostics measured an actor-to-GT-bounds "
        "vertical offset of 0.82620 m in a separate run. "
        "A flat-surface reconstructed median Z of 0.825997 m "
        "became -0.000203 m after applying the correction. "
        "Cross-run XY and Z transfer remains provisional."
    ) +
    paragraph(
        "The LiDAR scan contains 5271 indexed records, "
        "including 3227 explicit misses and 2044 valid hits "
        "at frame 150. Unreal-to-OSI Y-axis inversion was "
        "consistent with the reconstructed ray directions."
    )
))

parts.append(section(
    "Radar-to-Ground-Truth assessment",
    table(
        ["Metric", "Exporter box A", "Comparison box B"],
        [
            ("Radar candidates", "31", "31"),
            ("Inside approximate box", "9", "0"),
            ("Within 0.5 m", "12", "5"),
            ("Within 1.0 m", "13", "8"),
            ("Minimum box distance", "0 m", "0.2799 m"),
        ]
    ) +
    paragraph(
        "Five Radar rays were within 0.5 m under both "
        "box assumptions. Their target identity is "
        "not confirmed, and repeated ranges should not "
        "be interpreted as independent detections."
    )
))

parts.append(section(
    "Final association assessment",
    table(
        ["Sensor", "Observation", "Target identity verified?"],
        [
            ("Camera", "Visible car in frame 150", "No"),
            ("LiDAR", "Projected and classified reflections", "No"),
            ("Radar", "Five near-box geometric candidates", "No"),
        ]
    )
))

figures = ""

for title, filename in figure_specs:
    if (GRAPHS / filename).exists():
        figures += (
            "<figure><img src='01_Graphs/" +
            escape(filename, quote=True) +
            "' alt='" + escape(title, quote=True) +
            "'><figcaption>" +
            escape(title) + "</figcaption></figure>"
        )

parts.append(section(
    "Experimental figures",
    figures or paragraph("No selected figures found.")
))

parts.append(section(
    "Limitations",
    "<ul>" + "".join(
        "<li>" + escape(item) + "</li>"
        for item in [
            "Camera-visible vehicle identity is not independently mapped.",
            "Actor-to-bounds offset was measured in a different run.",
            "Projected Radar/LiDAR overlap is not proof of target association.",
            "GT bounding dimensions have an exporter-semantics ambiguity.",
            "Complete camera intrinsic and runtime-pose calibration remains open.",
            "Precision and recall cannot be calculated from current labels.",
            "Energy and processing latency were not benchmarked.",
        ]
    ) + "</ul>"
))

parts.append(section(
    "Recommended next research work",
    paragraph(
        "Log exact per-frame sensor world transforms, "
        "map Unreal actor IDs to GT objects, validate "
        "3D-to-2D projection against independently identified "
        "landmarks, then implement and benchmark object-level "
        "Camera-LiDAR-Radar association over multiple scenarios."
    )
))

inventory = table(
    ["Archive directory", "Number of files"],
    [
        (folder.name,
         sum(1 for p in folder.rglob("*") if p.is_file()))
        for folder in folders
    ]
)

parts.append(section("Archive inventory", inventory))

style = """
<style>
body {
  font-family: Arial, sans-serif;
  max-width: 1050px;
  margin: 40px auto;
  padding: 0 25px;
  line-height: 1.65;
  color: #1b2938;
}
h1 { color: #102a43; font-size: 30px; }
h2 {
  color: #174b73;
  border-bottom: 1px solid #cbd5e1;
  padding-bottom: 8px;
}
section { margin: 30px 0; }
table { width: 100%; border-collapse: collapse; margin: 18px 0; }
th, td {
  border: 1px solid #cbd5e1;
  padding: 10px;
  text-align: left;
}
th { background: #eef3f8; }
figure { margin: 25px 0; }
img {
  display: block;
  max-width: 100%;
  max-height: 560px;
  object-fit: contain;
  border: 1px solid #cbd5e1;
}
figcaption { color: #526477; padding-top: 7px; }
footer { color: #64748b; margin-top: 45px; }
@media print {
  body { margin: 0; max-width: none; }
  figure { break-inside: avoid; }
}
</style>
"""

html = (
    "<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='utf-8'>"
    "<title>GEMSTAR Task 13 Research Report</title>"
    + style +
    "</head><body>"
    "<h1>GEMSTAR Task 13 — Multi-Sensor Research Report</h1>"
    "<p>Camera • LiDAR • Radar • Ground Truth • MATLAB</p>"
    "<p>Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M") +
    "</p>"
    + "\n".join(parts) +
    "<footer>Research findings must be interpreted with "
    "the documented calibration and association limitations."
    "</footer></body></html>"
)

report = TASK / "Task_13_Final_Research_Report.html"
report.write_text(html, encoding="utf-8")

print("Archived new source scripts:", copied)
print("Archive directories found:", len(folders))
for folder in folders:
    print(" ", folder.name)

print("\nReport:", report)
print("Manifest:", manifest)
print("\nTASK 13.8A COMPLETED")
