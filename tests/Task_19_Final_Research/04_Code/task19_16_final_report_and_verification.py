from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import json
import hashlib
import html
import re

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_19_Final_Research"
)

DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"
FINDINGS = BASE / "06_Research_Findings"
REPORTS = BASE / "07_Research_Report"

REPORTS.mkdir(parents=True, exist_ok=True)

PDF = REPORTS / "Task_19_Final_Illustrated_Research_Report.pdf"

METRICS = FINDINGS / "task19_15_verified_metrics.json"
MANIFEST = FINDINGS / "task19_15_artifact_manifest.csv"
MARKDOWN = FINDINGS / "task19_15_consolidated_findings.md"

assert METRICS.is_file(), "Missing Task 19.15 metrics."
assert MANIFEST.is_file(), "Missing Task 19.15 manifest."
assert MARKDOWN.is_file(), "Missing research findings."

with METRICS.open(encoding="utf-8") as f:
    metrics = json.load(f)

def loadcsv(filename):
    with (DATA / filename).open(
        encoding="utf-8-sig", newline=""
    ) as f:
        return list(csv.DictReader(f))

quant = loadcsv("task19_13_quantization_summary.csv")
quality = loadcsv("task19_11_preprocessing_quality_audit.csv")
monitor = loadcsv("task19_10p_observability_monitor_results.csv")
pipeline = loadcsv("task19_10t_full_monitor_pipeline_results.csv")
deadline = loadcsv("task19_12_deadline_scenario_summary.csv")

with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
    original_manifest = list(csv.DictReader(f))

print("\n=== TASK 19.16 FINAL RESEARCH REPORT ===")

print("Initial inventoried files:", len(original_manifest))

# -------------------------------------
# 1. Verify original manifest
# -------------------------------------

verification = []
missing = 0
changed = 0
verified = 0

for entry in original_manifest:

    relative = entry["RelativePath"]
    path = BASE / relative

    if not path.is_file():
        status = "MISSING"
        missing += 1
    else:
        digest = hashlib.sha256()

        with path.open("rb") as f:
            for block in iter(
                lambda: f.read(1024 * 1024), b""
            ):
                digest.update(block)

        same_hash = (
            digest.hexdigest().lower()
            == entry["SHA256"].lower()
        )

        same_size = (
            path.stat().st_size
            == int(entry["SizeBytes"])
        )

        if same_hash and same_size:
            status = "VERIFIED"
            verified += 1
        else:
            status = "CHANGED"
            changed += 1

    verification.append({
        "RelativePath": relative,
        "Status": status,
    })

verify_csv = FINDINGS / "task19_16_manifest_verification.csv"

with verify_csv.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=["RelativePath", "Status"]
    )
    writer.writeheader()
    writer.writerows(verification)

# -------------------------------------
# 2. PDF styling
# -------------------------------------

styles = getSampleStyleSheet()

navy = colors.HexColor("#17324D")
teal = colors.HexColor("#126B75")
grey = colors.HexColor("#536575")
light = colors.HexColor("#EEF3F7")

styles.add(ParagraphStyle(
    name="MainTitleCustom",
    fontName="Helvetica-Bold",
    fontSize=23,
    leading=29,
    textColor=navy,
    spaceAfter=18,
    alignment=TA_CENTER,
))

styles.add(ParagraphStyle(
    name="SectionCustom",
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=19,
    textColor=navy,
    spaceBefore=16,
    spaceAfter=9,
))

styles.add(ParagraphStyle(
    name="SubCustom",
    fontName="Helvetica-Bold",
    fontSize=10.5,
    leading=15,
    textColor=teal,
    spaceBefore=10,
    spaceAfter=6,
))

styles.add(ParagraphStyle(
    name="BodyCustom",
    fontName="Helvetica",
    fontSize=9.3,
    leading=14.5,
    spaceAfter=8,
))

styles.add(ParagraphStyle(
    name="SmallCustom",
    fontName="Helvetica",
    fontSize=8,
    leading=11.5,
    spaceAfter=6,
))

styles.add(ParagraphStyle(
    name="CaptionCustom",
    fontName="Helvetica-Oblique",
    fontSize=8,
    leading=11.5,
    textColor=grey,
    alignment=TA_CENTER,
    spaceBefore=7,
    spaceAfter=12,
))

def safe(value):
    text = str(value)
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\u00d7", "x")
    text = text.replace("\u2192", " -> ")
    text = text.replace("\u2265", ">=")
    text = text.replace("\u2264", "<=")
    text = text.replace("\u00b5", "u")
    return html.escape(text, quote=False)

def paragraph(text, style="BodyCustom"):
    return Paragraph(safe(text), styles[style])

def section(text):
    return paragraph(text, "SectionCustom")

def sub(text):
    return paragraph(text, "SubCustom")

def table_from_rows(headers, rows, widths=None):
    cells = [
        [paragraph(x, "SmallCustom") for x in headers]
    ]
    for row in rows:
        cells.append([
            paragraph(x, "SmallCustom") for x in row
        ])

    tbl = Table(
        cells,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), navy),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
            [colors.white, light]),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("LINEBELOW", (0,0), (-1,0),
            1, teal),
    ]))
    # Set header background directly for PDF-compatible
    # header contrast with Paragraph-based cells.
    cells[0] = [
        Paragraph(
            "<font color='white'><b>"
            + safe(x) + "</b></font>",
            styles["SmallCustom"]
        )
        for x in headers
    ]
    return tbl

def add_figure(story, image_path, caption):
    if not image_path.is_file():
        story.append(paragraph(
            "Figure unavailable: " + image_path.name,
            "SmallCustom"
        ))
        return False

    try:
        width_px, height_px = ImageReader(
            str(image_path)
        ).getSize()

        available_w = 490
        available_h = 495

        ratio = min(
            available_w / width_px,
            available_h / height_px
        )

        story.append(Image(
            str(image_path),
            width=width_px * ratio,
            height=height_px * ratio
        ))

        story.append(paragraph(
            caption, "CaptionCustom"
        ))
        return True

    except Exception as e:
        story.append(paragraph(
            "Could not embed figure "
            + image_path.name + ": " + str(e),
            "SmallCustom"
        ))
        return False

# -------------------------------------
# 3. PDF content
# -------------------------------------

story = []

story.append(Spacer(1, 65))
story.append(paragraph(
    "GEMSTAR - TASK 19",
    "MainTitleCustom"
))
story.append(paragraph(
    "LiDAR Processing, Sensor Observability, "
    "Adaptive Scheduling and ARM-FPGA Research",
    "MainTitleCustom"
))
story.append(Spacer(1, 18))
story.append(paragraph(
    "Final Illustrated Research Report",
    "SectionCustom"
))
story.append(paragraph(
    "Based on recorded MATLAB and Python experiments, "
    "not on assumed hardware results."
))
story.append(paragraph(
    "Report generated: "
    + datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )
))
story.append(paragraph(
    "Research archive: Task_19_Final_Research",
    "SmallCustom"
))
story.append(Spacer(1, 35))

story.append(paragraph(
    "Evidence: "
    + str(metrics["frames"])
    + " cross-recording frames; "
    + str(metrics["evaluated_frames"])
    + " evaluated frames; "
    + str(len(original_manifest))
    + " original inventoried artifacts."
))

story.append(PageBreak())

story.append(section("1. Executive Summary"))

story.append(paragraph(
    "Task 19 established a reproducible software "
    "baseline for GEMSTAR LiDAR preprocessing. "
    "It reconstructed OSI LiDAR reflections into "
    "3D coordinates, tested ROI and voxel reduction, "
    "compared ground-plane estimation methods, "
    "examined clustering limitations, built "
    "sensor-observability and scheduling prototypes, "
    "and measured execution-time distributions."
))

metric_rows = [
    ["Cross-recording observations",
     str(metrics["frames"])],
    ["Evaluated processing frames",
     str(metrics["evaluated_frames"])],
    ["Selected-policy diagnostic failures",
     str(metrics["selected_policy_failures"])],
    ["Median integrated speed ratio",
     f'{metrics["median_processed_speed_ratio"]:.3f}x'],
    ["Median observability-monitor latency",
     f'{metrics["median_monitor_ms"]:.5f} ms'],
    ["Full baseline P95",
     f'{metrics["baseline_p95_ms"]:.5f} ms'],
    ["Integrated policy P95",
     f'{metrics["policy_p95_ms"]:.5f} ms'],
    ["Illustrative deadline misses: full / policy",
     f'{metrics["baseline_deadline_misses"]} / '
     f'{metrics["policy_deadline_misses"]}'],
]

story.append(table_from_rows(
    ["Measurement", "Result"],
    metric_rows,
    [325, 165]
))

story.append(Spacer(1, 12))

story.append(paragraph(
    "Interpretation: The adaptive software policy "
    "often reduced latency, but three evaluated "
    "configurations failed the experimental "
    "reference-consistency criteria. "
    "Sensor-observability warnings did not "
    "identify every processing-quality failure."
))

story.append(section("2. Research Workflow"))

workflow = [
    ("19.1-19.3", "OSI reflection format, time-of-flight "
     "conversion, scan geometry, MATLAB XYZ visualization "
     "and internal geometry checks."),
    ("19.4-19.5", "ROI filtering, provisional ground-height "
     "filtering and voxel centroid downsampling."),
    ("19.6", "RANSAC ground estimation and comparison "
     "against simple ground-height classification."),
    ("19.7-19.8", "DBSCAN clustering, bounding boxes, "
     "simulator object IDs, ground-truth inspection "
     "and world alignment diagnostics."),
    ("19.9", "PC MATLAB preprocessing runtime and "
     "voxel-assisted RANSAC trade-offs."),
    ("19.10A-19.10J", "Multi-frame reconstruction, "
     "offline oracle, rule-based scheduler, "
     "held-out testing and failure audit."),
    ("19.10K-19.10Q", "Cross-recording validation, "
     "LiDAR observability, two-level policy analysis."),
    ("19.10R-19.10T", "Feature overhead, integrated "
     "software processing and complete monitor timing."),
    ("19.11-19.12", "Preprocessing consistency, "
     "deadline and tail-timing analysis."),
    ("19.13", "Frame-150 INT8 and INT16 "
     "coordinate quantization experiment."),
    ("19.14", "Proposed ARM-FPGA partition "
     "and measurement plan."),
    ("19.15-19.16", "Verified research consolidation, "
     "illustrated report and archive audit."),
]

story.append(table_from_rows(
    ["Research step", "Purpose / evidence"],
    workflow,
    [105, 385]
))

story.append(PageBreak())

story.append(section("3. LiDAR Reconstruction"))

story.append(paragraph(
    "GEMSTAR produced 251 by 21 LiDAR reflection "
    "grids, corresponding to 5,271 rays per scan. "
    "Range was reconstructed from the recorded "
    "round-trip time of flight using the simulator's "
    "air light-speed constant. The ray-grid indices "
    "were mapped to horizontal and vertical scan "
    "angles, yielding sensor-local XYZ coordinates."
))

story.append(paragraph(
    "The reconstructed frame-150 candidate cloud "
    "contained 2,044 valid points. The original "
    "20 m by +/-6 m ROI contained 1,922 points. "
    "Coordinate reconstruction was checked against "
    "the simulator source and its ray ordering, "
    "but independently verified object semantics "
    "were not established."
))

story.append(section("4. Geometric Preprocessing"))

story.append(paragraph(
    "Task 19 compared preliminary height-band "
    "ground filtering with an approximately "
    "horizontal RANSAC plane. It also studied "
    "0.10 m, 0.25 m and 0.50 m centroid voxel "
    "grids as mechanisms to reduce plane-fitting "
    "workload. The full-resolution RANSAC output "
    "is a consistency reference, not a verified "
    "ground-truth segmentation."
))

story.append(section("5. Clustering and Object IDs"))

story.append(paragraph(
    "Initial DBSCAN clustering found two clusters "
    "in the frame-150 RANSAC non-plane points. "
    "Their geometry and simulator object-ID analysis "
    "revealed predominantly planar or elongated "
    "returns, not independently validated vehicles. "
    "This is an important negative finding: "
    "clustering cannot be equated with successful "
    "obstacle detection without semantic validation."
))

story.append(section("6. Scheduler Evaluation"))

story.append(paragraph(
    "An initial ROI-count rule selected between "
    "full-resolution and 0.25 m voxel-assisted "
    "RANSAC. Its original eight-frame agreement "
    "with an offline diagnostic oracle did not "
    "generalize perfectly to held-out frames. "
    "The rule was therefore preserved as a fixed "
    "baseline for subsequent recordings."
))

story.append(paragraph(
    "Across 48 cross-recording observations, "
    "the integrated processing policy executed "
    "22 full-resolution paths, 25 voxel-assisted "
    "paths and one insufficient-data skip. "
    "Of 47 evaluated frames, three selected "
    "configurations failed the experimental "
    "processing-consistency criteria."
))

story.append(section("7. LiDAR Observability"))

state_rows = [
    [state, str(metrics["observability_states"].get(
        state, 0))]
    for state in [
        "OBSERVABLE", "REVIEW", "INSUFFICIENT"
    ]
]
story.append(table_from_rows(
    ["Diagnostic state", "Observations"],
    state_rows,
    [320, 170]
))

story.append(paragraph(
    "These states are provisional warning categories, "
    "not calibrated sensor-failure labels. "
    "Low return availability may arise from several "
    "causes. Monitoring return counts, range and "
    "spatial coverage does not by itself validate "
    "ground-segmentation accuracy."
))

story.append(section("8. Execution Time and Deadlines"))

story.append(paragraph(
    "The full monitor was benchmarked in MATLAB "
    "on a Windows PC. The recorded median monitor "
    "latency was "
    + f'{metrics["median_monitor_ms"]:.5f} ms. '
    "The overall processed-frame median baseline "
    "to integrated-policy latency ratio was "
    + f'{metrics["median_processed_speed_ratio"]:.3f}x.'
))

story.append(paragraph(
    "For an illustrative 3 ms computation budget, "
    "the recorded deadline violations changed "
    "from "
    + str(metrics["baseline_deadline_misses"])
    + " baseline samples to "
    + str(metrics["policy_deadline_misses"])
    + " policy samples. The respective overall "
    "P95 values were "
    + f'{metrics["baseline_p95_ms"]:.5f} ms and '
    + f'{metrics["policy_p95_ms"]:.5f} ms.'
))

story.append(paragraph(
    "These figures are not real-time guarantees. "
    "They exclude OSI decoding, data transfer, "
    "sensor synchronization, downstream fusion "
    "and hardware power measurements."
))

story.append(section("9. Quantization Assessment"))

qrows = []

for row in quant:
    bits = row["BitWidth"]
    rmse = float(row["PositionRMSEM"]) * 1000
    qrows.append([
        str(bits),
        f"{rmse:.3f}",
        str(row["ChangedGroundLabels"]),
        f'{float(row["StorageReductionVsDoublePercent"]):.1f}%'
    ])

story.append(table_from_rows(
    ["Bits", "XYZ RMSE (mm)", "Changed labels",
     "Raw XYZ saving"],
    qrows,
    [70, 130, 130, 160]
))

story.append(paragraph(
    "The single-frame coordinate-quantization "
    "experiment favored INT16 for numerical "
    "precision. The study used frame-specific "
    "calibration and floating-point plane "
    "evaluation; it does not constitute an "
    "integer-only FPGA implementation."
))

story.append(section("10. ARM-FPGA Architecture"))

story.append(paragraph(
    "The proposed initial hardware kernel performs "
    "fixed-point point-to-plane distance calculation, "
    "inlier threshold comparison and inlier counting. "
    "The ARM CPU retains data management, scheduling, "
    "RANSAC hypothesis generation and initial SVD "
    "plane refinement."
))

story.append(paragraph(
    "The next hardware study must implement and "
    "verify RTL, integrate suitable streaming/DMA "
    "interfaces, and measure actual board latency, "
    "resource utilization and energy per frame. "
    "These measurements were not completed in Task 19."
))

story.append(section("11. Critical Research Limitations"))

limitations = [
    "No independent semantic ground-truth "
    "accuracy for obstacle or road detection.",
    "Reference agreement may be high even "
    "when both algorithms are wrong.",
    "Only a small number of repeated PC timing "
    "samples were used.",
    "No measured FPGA LUT, FF, BRAM or DSP resources.",
    "No measured hardware power or energy savings.",
    "No full live camera-LiDAR-radar fusion.",
    "Quantization scales were assessed on one frame.",
    "Recordings may differ in more than weather.",
    "Low sensor return counts are not proof of failure.",
    "The current scheduling thresholds are exploratory.",
]

for item in limitations:
    story.append(paragraph("- " + item))

story.append(section("12. Recommended Next Research"))

for item in [
    "Validate quantization on multiple recordings "
    "with fixed, independently calibrated scales.",
    "Implement an RTL fixed-point distance/inlier kernel.",
    "Compare RTL and CPU results using identical inputs.",
    "Add ARM-FPGA data-transfer timing and buffering.",
    "Measure actual board power and energy per frame.",
    "Develop independent road/obstacle reference labels.",
    "Integrate camera and radar observability evidence.",
    "Evaluate the scheduler with deadlines and "
    "measured energy as explicit constraints.",
]:
    story.append(paragraph("- " + item))

# -------------------------------------
# 4. Include existing research figures
# -------------------------------------

story.append(PageBreak())
story.append(section(
    "13. Illustrated Experimental Evidence"
))
story.append(paragraph(
    "The following pages reproduce the saved "
    "research figures from the Task 19 archive. "
    "Figure captions identify their source files. "
    "They are experimental evidence and should "
    "be interpreted using the limitations above."
))

figures = sorted(
    p for p in GRAPHS.rglob("*.png")
    if p.name.lower().startswith("task19")
    or p.name.lower().startswith("task_19")
)

# Include all research graphs where possible.
figure_added = 0

for index, path in enumerate(figures, 1):

    story.append(PageBreak())

    story.append(section(
        f"Research Figure {index}"
    ))

    friendly = re.sub(
        r"^task19[_-]?[0-9a-z]*[_-]?",
        "", path.stem, flags=re.IGNORECASE
    ).replace("_", " ").strip()

    story.append(paragraph(
        friendly if friendly else path.stem,
        "SubCustom"
    ))

    if add_figure(
        story,
        path,
        "Original saved graph: "
        + str(path.relative_to(BASE))
    ):
        figure_added += 1

# -------------------------------------
# 5. Artifact appendix
# -------------------------------------

story.append(PageBreak())
story.append(section(
    "14. Reproducibility and Research Archive"
))

folder_counts = Counter()

for entry in original_manifest:
    path = Path(entry["RelativePath"])
    first = path.parts[0] if path.parts else "root"
    folder_counts[first] += 1

story.append(table_from_rows(
    ["Archive section", "Manifest files"],
    sorted(folder_counts.items()),
    [335, 155]
))

story.append(Spacer(1, 12))

story.append(paragraph(
    "Original manifest verified: "
    + str(verified) + " verified, "
    + str(missing) + " missing, "
    + str(changed) + " changed."
))

story.append(paragraph(
    "The original manifest is a point-in-time "
    "snapshot created in Task 19.15. Files generated "
    "after that snapshot, including this final PDF, "
    "are intentionally reported separately."
))

story.append(paragraph(
    "Full file hashes and verification statuses "
    "are saved in 06_Research_Findings. "
    "Source code and raw-data references remain "
    "in their existing archive folders."
))

# -------------------------------------
# 6. Build PDF
# -------------------------------------

def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(grey)
    canvas.drawString(
        45, 28, "GEMSTAR - Task 19 Research"
    )
    canvas.drawRightString(
        A4[0]-45, 28, f"Page {doc.page}"
    )
    canvas.restoreState()

doc = SimpleDocTemplate(
    str(PDF),
    pagesize=A4,
    rightMargin=52,
    leftMargin=52,
    topMargin=48,
    bottomMargin=50,
    title="GEMSTAR Task 19 Final Illustrated Research Report",
    author="GEMSTAR Research Project",
)

doc.build(
    story,
    onFirstPage=page_number,
    onLaterPages=page_number,
)

assert PDF.is_file(), "PDF generation failed."
assert PDF.stat().st_size > 10000, "PDF unexpectedly small."

with PDF.open("rb") as f:
    assert f.read(5) == b"%PDF-", "Invalid PDF header."

# Verify at least first pages using PDF page parser.
page_count = None

try:
    from pypdf import PdfReader
    reader = PdfReader(str(PDF))
    page_count = len(reader.pages)
except ImportError:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(PDF))
        page_count = len(reader.pages)
    except ImportError:
        pass

# -------------------------------------
# 7. Final verification report
# -------------------------------------

final = {
    "generated_utc": datetime.now(
        timezone.utc
    ).isoformat(),
    "task": "19.16",
    "initial_manifest_count": len(original_manifest),
    "verified_original_files": verified,
    "missing_original_files": missing,
    "changed_original_files": changed,
    "figures_found": len(figures),
    "figures_embedded": figure_added,
    "pdf_path": str(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "pdf_pages": page_count,
    "report_created": True,
    "hardware_implemented": False,
    "hardware_energy_measured": False,
    "archive_pass": missing == 0 and changed == 0,
}

final_json = FINDINGS / "task19_16_final_verification.json"

final_json.write_text(
    json.dumps(final, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 19.16 FINAL VERIFICATION ===")
print("Original artifacts:", len(original_manifest))
print("Verified:", verified)
print("Missing:", missing)
print("Modified:", changed)
print("Figures found:", len(figures))
print("Figures embedded:", figure_added)
print("PDF exists:", PDF.is_file())
print("PDF size (MB):", round(PDF.stat().st_size/1048576, 2))
print("PDF pages:", page_count if page_count else "Not checked")
print("Verification JSON:", final_json.is_file())
print("Archive verification PASS:", final["archive_pass"])
print("PDF location:", PDF)

if not final["archive_pass"]:
    print(
        "\nWARNING: Some original artifacts require inspection."
    )
else:
    print(
        "\nOriginal Task 19.15 evidence manifest verified."
    )

print("\nTask 19 final research report generated.")
print("Hardware implementation is separate future work.")
