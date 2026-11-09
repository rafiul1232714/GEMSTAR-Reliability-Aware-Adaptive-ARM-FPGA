
from pathlib import Path
import csv
from collections import Counter

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_15_Final_Research"
CSV = BASE / "02_CSV_Data"
GRAPH = BASE / "01_Graphs" / "task15_sensor_coverage.png"
OUTPUT = BASE / "07_Research_Report" / "Task_15_Final_Research_Report.pdf"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def read_csv(name):
    path = CSV / name
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


manifest = read_csv("task15_dataset_manifest.csv")
coverage = read_csv("task15_sensor_status.csv")
scenarios = read_csv("task15_scenario_inventory.csv")
issues = read_csv("task15_open_issues.csv")
config_hashes = read_csv("task15_configuration_hashes.csv")

pair_path = (
    BASE / "05_Raw_Data_References"
    / "task15_recording_pair_evidence.csv"
)
with pair_path.open("r", newline="", encoding="utf-8-sig") as f:
    pairs = list(csv.DictReader(f))

unique_hashes = len({r["SHA256"] for r in manifest})
full = sum(r["Status"] == "FULL_3_SENSOR" for r in coverage)
missing = sum(r["Status"] == "MISSING_SENSOR" for r in coverage)
candidate_pairs = sum(r["Status"] == "CANDIDATE_PAIR" for r in pairs)

navy = colors.HexColor("#16324F")
blue = colors.HexColor("#2563A6")
light = colors.HexColor("#EFF4F9")
grey = colors.HexColor("#526272")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="ReportTitleCustom", parent=styles["Title"],
    fontSize=21, leading=26, textColor=navy, spaceAfter=18
))
styles.add(ParagraphStyle(
    name="SectionCustom", parent=styles["Heading2"],
    fontSize=13, leading=17, textColor=navy,
    spaceBefore=14, spaceAfter=8
))
styles.add(ParagraphStyle(
    name="BodyCustom", parent=styles["BodyText"],
    fontSize=9.5, leading=14, spaceAfter=8
))
styles.add(ParagraphStyle(
    name="SmallCustom", parent=styles["BodyText"],
    fontSize=7.3, leading=10, spaceAfter=3
))
styles.add(ParagraphStyle(
    name="CenterCustom", parent=styles["BodyText"],
    alignment=TA_CENTER, fontSize=10, leading=14
))


def p(text, style="BodyCustom"):
    return Paragraph(escape(str(text)), styles[style])


def section(title):
    story.append(p(title, "SectionCustom"))


def paragraph(text):
    story.append(p(text))


def table(headers, rows, widths=None):
    data = [[p(x, "SmallCustom") for x in headers]]
    for row in rows:
        data.append([p(x, "SmallCustom") for x in row])

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), light),
        ("TEXTCOLOR", (0, 0), (-1, 0), navy),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 11))


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=(595.28, 841.89),
    rightMargin=42,
    leftMargin=42,
    topMargin=52,
    bottomMargin=48,
)

story = []

# Cover
story.append(Spacer(1, 85))
story.append(p("GEMSTAR / ARM-FPGA RESEARCH", "CenterCustom"))
story.append(Spacer(1, 22))
story.append(p(
    "TASK 15 - FINAL RESEARCH REPORT",
    "ReportTitleCustom"
))
story.append(p(
    "Dataset Integrity, Sensor Coverage, Configuration Evidence "
    "and Reproducibility",
    "CenterCustom"
))
story.append(Spacer(1, 24))
story.append(p("Research phase: Scientific foundation", "CenterCustom"))
story.append(p(
    "Status: Archive evidence compiled; calibration and "
    "scenario provenance remain under investigation.",
    "CenterCustom"
))
story.append(Spacer(1, 35))

table(
    ["Metric", "Observed result"],
    [
        ["OSI file references", str(len(manifest))],
        ["Unique OSI SHA-256 hashes", str(unique_hashes)],
        ["Unique SensorView recordings", str(len(coverage))],
        ["Candidate GT/SV pairs", str(candidate_pairs)],
        ["Full three-sensor payload recordings", str(full)],
        ["Recordings missing sensor payloads", str(missing)],
        ["Open research issues", str(len(issues))],
    ],
    [280, 225]
)

story.append(PageBreak())

# Objective
section("1. Research objective")
paragraph(
    "Task 15 establishes a reproducible evidence archive for previous "
    "GEMSTAR experiments. It preserves file references and integrity "
    "hashes, inventories available scenarios, examines SensorView "
    "payload coverage, and documents unresolved limitations."
)
paragraph(
    "This task does not perform validated object-level sensor fusion, "
    "prove calibration correctness, or establish FPGA performance."
)

section("2. Experimental data inventory")
paragraph(
    f"The dataset manifest records {len(manifest)} OSI file references "
    f"with {unique_hashes} distinct SHA-256 hashes. "
    "Repeated hashes indicate identical file content."
)

section("3. GT / SensorView pairing")
paragraph(
    f"Filename and timestamp analysis produced {candidate_pairs} "
    "GT/SensorView candidate pairs. Matching recording identifiers "
    "are not conclusive evidence of synchronized sensor measurements. "
    "Internal timestamps will be audited in Task 17."
)
table(
    ["SV recording", "GT candidate", "Filename delta (s)"],
    [
        [
            r["SensorViewFile"].replace("20261027T", "").replace(
                "20261028T", ""
            )[:35],
            r["GroundTruthFile"].replace("20261027T", "").replace(
                "20261028T", ""
            )[:35],
            r["TimestampDifferenceSeconds"]
        ]
        for r in pairs
    ],
    [204, 204, 97]
)

story.append(PageBreak())
section("4. Sensor payload coverage")
paragraph(
    f"All {len(coverage)} unique SensorView recordings were parsed "
    "without reported parser errors. "
    f"{full} recordings had nonempty Camera image data, LiDAR "
    "reflection records and Radar reflection records in every parsed "
    f"SensorView message. The other {missing} recordings lacked at "
    "least one populated sensor stream."
)
paragraph(
    "Payload coverage is not equivalent to positive/valid returns, "
    "calibration accuracy, temporal synchronization or verified object "
    "associations."
)

if GRAPH.exists():
    iw, ih = ImageReader(str(GRAPH)).getSize()
    max_width, max_height = 505, 310
    scale = min(max_width / iw, max_height / ih)
    story.append(Image(
        str(GRAPH), width=iw * scale, height=ih * scale
    ))
    story.append(Spacer(1, 12))
else:
    paragraph("Sensor coverage graph unavailable at report generation.")

table(
    ["Recording ID", "Frames", "Camera", "LiDAR", "Radar"],
    [
        [
            r["Recording"].split("_X_")[-1].replace(".osi", "")[:20],
            r["Frames"], r["Camera"], r["LiDAR"], r["Radar"]
        ]
        for r in coverage
    ],
    [173, 68, 88, 88, 88]
)

story.append(PageBreak())
section("5. Scenario inventory")
paragraph(
    "Scenario folder names are treated as provisional evidence. "
    "Historical recording-specific weather parameters have not "
    "been conclusively reconstructed."
)
table(
    ["Folder", "GT", "SV", "Verification"],
    [
        [
            r["ScenarioFolder"],
            r["GTFiles"],
            r["SVFiles"],
            r["ScenarioVerified"]
        ]
        for r in scenarios
    ],
    [247, 55, 55, 148]
)

section("6. Configuration evidence")
paragraph(
    "Six configuration snapshots were archived and hashed. "
    "Camera and LiDAR mount parameters were identified; "
    "the Radar mounting convention needs further investigation. "
    "Logger inputs differed between inspected configuration versions."
)
table(
    ["Configuration file", "SHA-256 prefix"],
    [
        [r["FileName"], r["SHA256"][:16]]
        for r in config_hashes
    ],
    [345, 160]
)

paragraph(
    "A configuration snapshot shows what a file contains, not "
    "necessarily which settings were active when an earlier "
    "recording was generated."
)

story.append(PageBreak())
section("7. Open research issues")
table(
    ["ID", "Finding", "Next task"],
    [
        [r["IssueID"], r["Finding"], r["NextTask"]]
        for r in issues
    ],
    [70, 345, 90]
)

section("8. Interpretation and scientific limitations")
for text in [
    "The ten full-coverage recordings are candidates for subsequent "
    "three-sensor investigations, not yet validated fusion datasets.",
    "The nine incomplete recordings are retained as evidence of "
    "earlier development and logging configurations.",
    "The fog_mor20 and fog_mor50 dataset directories have no "
    "recordings in the inspected research archive.",
    "Radar geometry, historical configuration provenance, "
    "sensor synchronization and target association remain unresolved."
]:
    paragraph("- " + text)

section("9. Next research stages")
table(
    ["Task", "Next objective"],
    [
        ["16", "Literature matrix and testable research hypotheses"],
        ["17", "Sensor timestamps, coordinate systems and calibration"],
        ["18", "Camera features and multiframe observability"],
        ["19", "LiDAR filtering, geometry and quality"],
        ["20", "Radar measurement semantics and quality"],
        ["21", "Validated cross-sensor object association"],
    ],
    [65, 440]
)

section("10. Reproducibility package")
paragraph(
    "Associated research artifacts are stored in the "
    "Task_15_Final_Research folder: 01_Graphs, 02_CSV_Data, "
    "03_Configurations, 04_Code, 05_Raw_Data_References, "
    "06_Research_Findings and 07_Research_Report."
)
paragraph(
    "The original OSI files remain at their existing paths. "
    "References and SHA-256 hashes are preserved rather than "
    "duplicating multi-gigabyte recordings."
)


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.line(42, 36, 553, 36)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(grey)
    canvas.drawString(42, 24, "GEMSTAR | Task 15 Research Archive")
    canvas.drawRightString(553, 24, f"Page {doc.page}")
    canvas.restoreState()


doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)

print("=== TASK 15 PDF REPORT ===")
print("Report created:", OUTPUT)
print("File exists:", OUTPUT.exists())
print("File size KB:", round(OUTPUT.stat().st_size / 1024, 2))
print("Status: PDF generation successful")
