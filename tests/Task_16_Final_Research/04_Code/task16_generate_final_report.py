
from pathlib import Path
from collections import Counter
import csv
from xml.sax.saxutils import escape

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_16_Final_Research"
)

DATA = BASE / "02_CSV_Data"
GAP = BASE / "05_Research_Gap"
GRAPHS = BASE / "01_Graphs"
OUTPUT = BASE / "07_Research_Report" / "Task_16_Final_Research_Report.pdf"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def load(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


papers = load(DATA / "task16_literature_database.csv")
matrix = load(DATA / "task16_research_comparison_matrix.csv")
competing = load(GAP / "task16_priority_competing_research.csv")
risks = load(GAP / "task16_novelty_risk_assessment.csv")
baselines = load(GAP / "task16_experimental_baselines.csv")
hypotheses = load(GAP / "task16_research_hypotheses.csv")
metrics = load(GAP / "task16_evaluation_metrics.csv")
operations = load(GAP / "task16_hardware_operation_selection.csv")
workflow = load(GAP / "task16_experimental_workflow.csv")
threeway = load(GAP / "task16_carma_dyuns_proposed_comparison.csv")
carma = load(GAP / "task16_carma_verified_evidence.csv")

NAVY = colors.HexColor("#19344D")
PALE = colors.HexColor("#EAF1F7")
GREY = colors.HexColor("#566475")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="MainTitle16", parent=styles["Title"],
    fontSize=20, leading=25, textColor=NAVY, spaceAfter=16
))
styles.add(ParagraphStyle(
    name="Heading16", parent=styles["Heading2"],
    fontSize=12, leading=16, textColor=NAVY,
    spaceBefore=13, spaceAfter=8
))
styles.add(ParagraphStyle(
    name="Body16", parent=styles["BodyText"],
    fontSize=9, leading=13, spaceAfter=7
))
styles.add(ParagraphStyle(
    name="Cell16", parent=styles["BodyText"],
    fontSize=7, leading=10, wordWrap="CJK"
))
styles.add(ParagraphStyle(
    name="Center16", parent=styles["BodyText"],
    fontSize=10, leading=15, alignment=TA_CENTER
))

story = []
PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 76


def para(text, style="Body16"):
    return Paragraph(escape(str(text)), styles[style])


def heading(text):
    story.append(para(text, "Heading16"))


def text(text):
    story.append(para(text))


def make_table(headers, rows, widths=None):
    data = [[para(h, "Cell16") for h in headers]]
    data.extend(
        [para(value, "Cell16") for value in row]
        for row in rows
    )
    if widths is None:
        widths = [CONTENT_W / len(headers)] * len(headers)

    tab = Table(
        data, colWidths=widths,
        repeatRows=1, hAlign="LEFT"
    )
    tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("GRID", (0, 0), (-1, -1), .35,
         colors.HexColor("#CAD4DF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tab)
    story.append(Spacer(1, 12))


def figure(name, caption, max_height=260):
    path = GRAPHS / name
    if not path.exists():
        text("Figure unavailable: " + name)
        return
    width, height = ImageReader(str(path)).getSize()
    scale = min(CONTENT_W / width, max_height / height)
    story.append(Image(
        str(path), width=width * scale,
        height=height * scale
    ))
    story.append(Spacer(1, 5))
    text(caption)


# COVER
story.append(Spacer(1, 95))
story.append(para("GEMSTAR / ARM-FPGA RESEARCH", "Center16"))
story.append(Spacer(1, 25))
story.append(para(
    "TASK 16 - FINAL RESEARCH REPORT", "MainTitle16"
))
story.append(para(
    "Literature Review, Research-Gap Analysis, "
    "Novelty Risk and Experimental Methodology",
    "Center16"
))
story.append(Spacer(1, 35))
story.append(para(
    "PRELIMINARY LITERATURE ASSESSMENT",
    "Center16"
))
story.append(Spacer(1, 25))

make_table(
    ["Research artifact", "Count"],
    [
        ["Literature publications", str(len(papers))],
        ["Comparison matrix entries", str(len(matrix))],
        ["Priority competing studies", str(len(competing))],
        ["Novelty-risk areas", str(len(risks))],
        ["Experimental baselines", str(len(baselines))],
        ["Research hypotheses", str(len(hypotheses))],
        ["Evaluation metrics", str(len(metrics))],
        ["Processing operations", str(len(operations))],
        ["Workflow stages", str(len(workflow))],
    ],
    [350, CONTENT_W - 350]
)

story.append(PageBreak())

heading("1. Research objective")
text(
    "Investigate whether sensor-derived reliability and tracking "
    "uncertainty can improve energy-aware ARM-FPGA processing "
    "decisions for Camera, LiDAR and Radar perception while "
    "satisfying timing and quality requirements."
)
text(
    "This report documents the research design, not experimental "
    "proof of novelty or hardware performance."
)

heading("2. Literature distribution")
figure(
    "task16_literature_categories.png",
    "Figure 1. Distribution of the 20 collected papers "
    "by research category."
)

heading("3. Literature inventory")
for paper in papers:
    story.append(para(
        paper["PaperID"] + " | " +
        paper["Title"] + " (" + paper["Year"] + ")"
    ))
    story.append(para(
        "Category: " + paper["Category"] +
        " | Venue: " + paper["Venue"],
        "Cell16"
    ))
    story.append(para(
        "Source: " + paper["URL"],
        "Cell16"
    ))
    story.append(para(
        "Review: " + paper["ReviewStatus"],
        "Cell16"
    ))
    story.append(Spacer(1, 7))

story.append(PageBreak())

heading("4. Literature comparison matrix")
text(
    "The following is a compact summary of the complete "
    "research comparison CSV. 'Not established' signifies "
    "insufficient reviewed evidence, not confirmed absence."
)
make_table(
    ["ID", "Category", "FPGA", "Uncertainty-based placement"],
    [
        [
            r["PaperID"],
            r["Category"],
            r["FPGA"],
            r["SensorUncertaintyScheduling"]
        ]
        for r in matrix
    ],
    [41, 173, 88, CONTENT_W - 302]
)

heading("5. Priority competing research")
make_table(
    ["ID", "Study / topic", "Priority"],
    [
        [r["ID"], r["Topic"], r["Priority"]]
        for r in competing
    ],
    [55, 340, CONTENT_W - 395]
)

heading("6. CARMA full-text findings")
make_table(
    ["Feature", "Finding", "Pages"],
    [
        [r["Feature"], r["Finding"], r["EvidencePage"]]
        for r in carma
    ],
    [142, 310, CONTENT_W - 452]
)

story.append(PageBreak())

heading("7. CARMA versus DyUnS versus proposed system")
make_table(
    ["Feature", "CARMA", "DyUnS", "Proposed"],
    [
        [
            r["Feature"], r["CARMA"], r["DyUnS"], r["Proposed"]
        ]
        for r in threeway
    ],
    [95, 135, 135, CONTENT_W - 365]
)
text(
    "The comparison represents our present reading of the "
    "published work. Claims about missing capabilities remain "
    "provisional until all relevant methods are reviewed."
)

heading("8. Novelty-risk assessment")
figure(
    "task16_novelty_risk.png",
    "Figure 2. Preliminary classification of seven "
    "candidate research areas.",
    max_height=220
)
make_table(
    ["ID", "Research area", "Risk"],
    [
        [r["ID"], r["ResearchArea"], r["NoveltyRisk"]]
        for r in risks
    ],
    [43, 358, CONTENT_W - 401]
)

heading("9. Candidate research gap")
text(
    "Existing literature separately demonstrates multimodal "
    "fusion, energy-aware FPGA adaptation, heterogeneous "
    "scheduling, uncertainty-aware task allocation and "
    "low-precision processing."
)
text(
    "The proposed investigation tests the additional value "
    "of sensor-derived reliability and tracking uncertainty "
    "for runtime assignment of selected perception operators "
    "to ARM or FPGA, accounting for data-transfer cost, "
    "energy and deadlines."
)
text(
    "This remains a candidate contribution. The literature "
    "review has not established exclusivity or novelty."
)

story.append(PageBreak())

heading("10. Experimental baselines")
make_table(
    ["ID", "Strategy", "Scheduling inputs"],
    [
        [r["ID"], r["Name"], r["SchedulingInputs"]]
        for r in baselines
    ],
    [38, 161, CONTENT_W - 199]
)

heading("11. Research hypotheses")
make_table(
    ["ID", "Hypothesis", "Comparison"],
    [
        [r["ID"], r["Hypothesis"], r["PrimaryComparison"]]
        for r in hypotheses
    ],
    [34, 370, CONTENT_W - 404]
)
text(
    "All hypotheses are untested. No expected percentage "
    "savings is represented as a measured result."
)

heading("12. Evaluation metrics")
make_table(
    ["ID", "Metric", "Unit"],
    [
        [r["MetricID"], r["Metric"], r["Unit"]]
        for r in metrics
    ],
    [45, 310, CONTENT_W - 355]
)

heading("13. Hardware operation selection")
make_table(
    ["ID", "Sensor", "Operation", "Priority"],
    [
        [r["ID"], r["Sensor"], r["Operation"], r["Priority"]]
        for r in operations
    ],
    [46, 65, 275, CONTENT_W - 386]
)

story.append(PageBreak())

heading("14. Experimental workflow")
make_table(
    ["Stage", "Description", "Phase"],
    [
        [r["Step"], r["Stage"], r["Phase"]]
        for r in workflow
    ],
    [50, 340, CONTENT_W - 390]
)
text(
    "PC-based stages prepare and validate algorithms. "
    "Physical ARM-FPGA experiments are required for "
    "hardware energy, transfer overhead and execution results."
)

heading("15. Scientific limitations")
for item in [
    "Many full-text reviews and bibliographic checks remain pending.",
    "The research gap is a hypothesis, not established novelty.",
    "No ARM-FPGA performance improvement has yet been demonstrated.",
    "Sensor and tracking uncertainty require calibration.",
    "GEMSTAR synchronization and coordinate systems require validation.",
    "Deadline and tracking-quality thresholds are not yet fixed.",
    "Physical hardware measurements are required for energy claims.",
]:
    text("- " + item)

heading("16. Reproducibility and next steps")
text(
    "The Task_16_Final_Research directory contains the literature "
    "CSV, comparison CSV, novelty-risk evidence, hypotheses, "
    "metrics, workflow, plotting code, generated figures and "
    "this PDF."
)
text(
    "Subsequent work must verify remaining publication metadata, "
    "read the most relevant full papers, validate sensor data "
    "and implement the selected algorithms before drawing "
    "experimental conclusions."
)


def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#C8D3DE"))
    canvas.line(38, 35, PAGE_W - 38, 35)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(38, 24, "GEMSTAR | Task 16 Research Report")
    canvas.drawRightString(
        PAGE_W - 38, 24, f"Page {document.page}"
    )
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=38,
    rightMargin=38,
    topMargin=48,
    bottomMargin=48,
)

doc.build(
    story,
    onFirstPage=footer,
    onLaterPages=footer
)

print("\n=== TASK 16 FINAL PDF ===")
print("PDF exists:", OUTPUT.exists())
print("PDF size KB:", round(OUTPUT.stat().st_size / 1024, 2))
print("Literature records included:", len(papers))
print("Competing studies included:", len(competing))
print("Graphs available:", sum([
    (GRAPHS / "task16_literature_categories.png").exists(),
    (GRAPHS / "task16_novelty_risk.png").exists()
]))
print("Saved:", OUTPUT)
