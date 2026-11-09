import csv
import json
import hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak,
    KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet, ParagraphStyle
)
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Camera_Extension_Final_Research"
)

DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"
IMAGES = BASE / "08_Extracted_Images"
FIXED = BASE / "09_Fixed_Point_Results"
CONFIG = BASE / "03_Configurations"
FINDINGS = BASE / "06_Research_Findings"
REPORTS = BASE / "07_Research_Report"

for folder in [
    DATA, GRAPHS, FINDINGS, REPORTS, CONFIG
]:
    folder.mkdir(parents=True, exist_ok=True)

PDF = REPORTS / (
    "Task_18_Camera_Extension_Final_Research_Report.pdf"
)

def read_csv(name):
    path = DATA / name
    assert path.is_file(), f"Missing file: {path}"
    with path.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))

def number(value):
    return float(value)

# Source data from completed experiments.
extraction = read_csv(
    "task18_e3_extracted_camera_frames.csv"
)
quality = read_csv(
    "task18_e4_camera_quality_scenario_summary.csv"
)
monitor = read_csv(
    "task18_e5_observability_summary.csv"
)
performance = read_csv(
    "task18_e6_camera_processing_summary.csv"
)
precision = read_csv(
    "task18_e7_fixed_point_results.csv"
)

module_file = DATA / "task18_e8_rtl_module_inventory.csv"
verification_file = (
    DATA / "task18_e8_camera_rtl_verification_plan.csv"
)
spec_file = CONFIG / "task18_e8_camera_fixed_point_spec.json"

assert module_file.is_file()
assert verification_file.is_file()
assert spec_file.is_file()

modules = read_csv(
    "task18_e8_rtl_module_inventory.csv"
)
verification_cases = read_csv(
    "task18_e8_camera_rtl_verification_plan.csv"
)

with spec_file.open(encoding="utf-8") as f:
    hardware_spec = json.load(f)

assert len(extraction) == 20
assert len(precision) == 20
assert len(modules) == 10
assert len(verification_cases) == 12

states = {
    r["Recording"]: r
    for r in monitor
}

extracted_images = sorted(IMAGES.rglob("*.png"))
assert len(extracted_images) >= 20

print("\n=== TASK 18.E9 FINAL CAMERA ARCHIVE ===")

# ------------------------------------
# 1. PDF styling
# ------------------------------------

styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name="CustomTitle",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=26,
    textColor=colors.HexColor("#17324D"),
    spaceAfter=20,
))

styles.add(ParagraphStyle(
    name="CustomHeading",
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=18,
    spaceBefore=14,
    spaceAfter=8,
    textColor=colors.HexColor("#17324D"),
))

styles.add(ParagraphStyle(
    name="CustomBody",
    fontName="Helvetica",
    fontSize=9,
    leading=14,
    spaceAfter=8,
))

styles.add(ParagraphStyle(
    name="CustomSmall",
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    spaceAfter=5,
))

def para(text, style="CustomBody"):
    return Paragraph(escape(str(text)), styles[style])

def heading(text):
    return para(text, "CustomHeading")

def report_table(headers, rows):
    data = [[
        Paragraph(
            "<b><font color='white'>"
            + escape(str(h))
            + "</font></b>",
            styles["CustomSmall"]
        )
        for h in headers
    ]]

    for row in rows:
        data.append([
            para(x, "CustomSmall") for x in row
        ])

    widths = [490 / len(headers)] * len(headers)

    result = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT"
    )

    result.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0),
         colors.HexColor("#17324D")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.white, colors.HexColor("#EEF3F7")]),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))

    return result

def insert_image(story, path, caption):
    if not path.is_file():
        story.append(para(
            "Unavailable figure: " + path.name
        ))
        return False

    try:
        w, h = ImageReader(str(path)).getSize()
        scale = min(490 / w, 410 / h)

        story.append(Image(
            str(path),
            width=w * scale,
            height=h * scale
        ))
        story.append(Spacer(1, 7))
        story.append(para(
            caption, "CustomSmall"
        ))
        return True

    except Exception as exc:
        story.append(para(
            f"Figure error: {path.name}: {exc}"
        ))
        return False

story = []

# ------------------------------------
# 2. Title and overview
# ------------------------------------

story.append(Spacer(1, 55))
story.append(para(
    "GEMSTAR - CAMERA RESEARCH EXTENSION",
    "CustomTitle"
))
story.append(para(
    "Task 18.E1 through Task 18.E9"
))
story.append(para(
    "Camera observability, image preprocessing, "
    "fixed-point Sobel arithmetic and FPGA preparation."
))
story.append(Spacer(1, 20))
story.append(para(
    "Status: Software research and hardware "
    "architecture preparation completed."
))
story.append(para(
    "Platform: Windows PC, GEMSTAR, "
    "Python and OpenCV."
))
story.append(para(
    "FPGA hardware measurements: Not performed."
))
story.append(para(
    "Generated: " +
    datetime.now(timezone.utc).isoformat()
))
story.append(PageBreak())

story.append(heading("1. Executive Summary"))
story.append(para(
    "This extension characterizes GEMSTAR camera "
    "recordings and establishes an initial "
    "hardware-oriented image-processing reference. "
    "Twenty frames from five recordings were extracted "
    "and evaluated using image-statistics monitoring, "
    "CPU preprocessing benchmarks and integer "
    "Sobel arithmetic experiments."
))

story.append(report_table(
    ["Experiment", "Verified output"],
    [
        ["E3 Camera extraction", "20 frames"],
        ["E5 Observability", "8 OBSERVABLE, 12 REVIEW"],
        ["E6 Timing", "2400 timed executions"],
        ["E7 INT16 Sobel", "100% exact software agreement"],
        ["E8 FPGA preparation",
         "10 planned RTL modules, 12 test cases"],
    ]
))

# ------------------------------------
# 3. Dataset
# ------------------------------------

story.append(heading("2. Dataset and Extraction"))
story.append(para(
    "Camera SensorView data was verified in five "
    "recordings. The task05_fog_test recording had "
    "no camera observations in the inspected sample."
))

recording_rows = []

for scenario in sorted(set(
    r["Recording"] for r in extraction
)):
    group = [
        r for r in extraction
        if r["Recording"] == scenario
    ]
    first = group[0]

    recording_rows.append([
        scenario,
        str(len(group)),
        f"{first['Width']} x {first['Height']}"
    ])

story.append(report_table(
    ["Recording", "Images", "Original resolution"],
    recording_rows
))

story.append(para(
    "The baseline_fog images were recorded at "
    "1920 x 1080, while the other extracted images "
    "were 640 x 480. For the initial comparative "
    "analysis, images were standardized to 640 x 480."
))
story.append(para(
    "Image-byte counts are consistent with three "
    "8-bit samples per pixel. RGB/BGR channel "
    "ordering has not been independently verified."
))

# ------------------------------------
# 4. Quality metrics
# ------------------------------------

story.append(heading("3. Image Quality Measurements"))

quality_rows = []

for r in quality:
    quality_rows.append([
        r["Recording"],
        f"{number(r['BrightnessMedian']):.2f}",
        f"{number(r['ContrastMedian']):.2f}",
        f"{number(r['LaplacianVarianceMedian']):.2f}",
        f"{number(r['EdgeDensityPercentMedian']):.2f}"
    ])

story.append(report_table(
    ["Recording", "Brightness", "Contrast",
     "Sharpness", "Edges %"],
    quality_rows
))

story.append(para(
    "The fog-labeled recordings generally showed "
    "lower contrast, sharpness or edge density "
    "than baseline_clear. However, changes may also "
    "reflect scene, rendering and resolution "
    "differences. This experiment does not establish "
    "a causal effect from fog alone."
))

# ------------------------------------
# 5. Observability
# ------------------------------------

story.append(heading("4. Camera Observability Monitor"))

monitor_rows = []

for r in monitor:
    monitor_rows.append([
        r["Recording"],
        r["Observable"],
        r["Review"],
        r["MedianWarningCount"],
    ])

story.append(report_table(
    ["Recording", "Observable", "Review", "Median warnings"],
    monitor_rows
))

story.append(para(
    "The monitor used brightness, contrast, "
    "Laplacian variance and edge density. "
    "Thresholds were derived from four "
    "baseline_clear frames and were not calibrated "
    "on independent labeled datasets."
))
story.append(para(
    "OBSERVABLE and REVIEW are provisional statistical "
    "states, not validated camera health or obstacle "
    "detection correctness labels."
))

# ------------------------------------
# 6. Performance
# ------------------------------------

story.append(heading("5. CPU Processing Performance"))

performance_rows = []

for r in performance:
    f1 = r["MedianEdgeMapF1VsFull"]
    performance_rows.append([
        r["Mode"],
        f"{number(r['MedianOfFrameMediansMs']):.4f}",
        f"{number(r['MedianFrameP95Ms']):.4f}",
        f"{number(f1):.4f}" if f1 else "N/A"
    ])

story.append(report_table(
    ["Mode", "Median ms", "Frame-P95 median ms", "Edge F1"],
    performance_rows
))

story.append(para(
    "Half-resolution Sobel reduced median execution "
    "time compared with full Sobel, but its "
    "thresholded output showed substantially less "
    "agreement with the full-resolution reference."
))
story.append(para(
    "All timings are Windows PC/OpenCV measurements. "
    "Image loading and initial resolution "
    "standardization were outside the timed region. "
    "The edge-map F1 is algorithm-to-algorithm "
    "agreement, not object detection accuracy."
))

# ------------------------------------
# 7. Fixed-point
# ------------------------------------

story.append(heading("6. Fixed-Point Sobel Research"))

i8 = sorted(
    number(r["INT8SaturatedAgreementPercent"])
    for r in precision
)

median_i8 = (i8[9] + i8[10]) / 2

clipped = sum(
    int(r["INT8ClippedGradientPixels"])
    for r in precision
)

story.append(report_table(
    ["Metric", "Result"],
    [
        ["Images evaluated", str(len(precision))],
        ["Minimum INT16 agreement", "100.000%"],
        ["Median saturated INT8 agreement",
         f"{median_i8:.3f}%"],
        ["Clipped-gradient pixel positions",
         str(clipped)],
        ["Maximum observed abs X gradient",
         str(max(int(r["MaxAbsGradientX"])
                 for r in precision))],
        ["Maximum observed abs Y gradient",
         str(max(int(r["MaxAbsGradientY"])
                 for r in precision))],
    ]
))

story.append(para(
    "Camera input pixels are unsigned 8-bit. "
    "A 3x3 Sobel gradient can theoretically span "
    "-1020 to +1020, requiring at least 11 signed "
    "bits. The INT8-saturation experiment was "
    "deliberately lossy and is not a recommended "
    "gradient representation."
))
story.append(para(
    "Exact integer-gradient agreement was validated "
    "in software. This does not verify an actual RTL "
    "datapath or its bit-exact rounding, timing, "
    "resource use or energy."
))

# ------------------------------------
# 8. Hardware architecture
# ------------------------------------

story.append(heading("7. Proposed Kria FPGA Architecture"))

story.append(para(
    "The initial accelerator will accept uint8 "
    "grayscale pixels, maintain two image row buffers, "
    "construct a 3x3 sliding window, compute signed "
    "Sobel gradients, combine their absolute "
    "magnitudes, and produce an 8-bit output stream."
))

story.append(report_table(
    ["Hardware property", "Planned specification"],
    [
        ["Input image", "640 x 480 grayscale"],
        ["Input pixel", "Unsigned 8-bit"],
        ["Gradient", "Signed 11-bit"],
        ["Combined magnitude", "Widened integer arithmetic"],
        ["Output", "Unsigned 8-bit"],
        ["Line storage", "At least 1280 bytes"],
        ["Interface", "Proposed AXI4-Stream"],
        ["RTL status", "Not implemented"],
    ]
))

story.append(para(
    "The 10 proposed RTL modules and 12 verification "
    "cases are saved in the archive. Task 23 will "
    "handle RTL implementation, synthesis, AXI/DMA "
    "integration, Kria deployment and hardware "
    "measurement."
))

# ------------------------------------
# 9. Limitations
# ------------------------------------

story.append(heading("8. Limitations and Future Work"))

for item in [
    "Only four selected camera frames per recording.",
    "No independent camera failure or object labels.",
    "No verified causal comparison of weather conditions.",
    "No validated RGB versus BGR image channel ordering.",
    "No ARM-only versus FPGA hardware comparison.",
    "No FPGA timing, resources or board energy measured.",
    "No hardware Sobel RTL implementation completed.",
    "Additional unseen frames and scenario-matched "
    "experiments are needed for robust evaluation.",
]:
    story.append(para("- " + item))

story.append(heading("9. Research Continuation"))
story.append(para(
    "Task 20 will characterize radar data. "
    "Task 21 will investigate synchronized sensor "
    "coordinates and timestamps. Task 22 will "
    "establish a fusion baseline, and Task 23 "
    "will implement selected accelerators on Kria."
))

# ------------------------------------
# 10. Existing figures
# ------------------------------------

story.append(PageBreak())
story.append(heading("10. Experimental Figures"))

figure_paths = [
    GRAPHS / "task18_e4_camera_quality_comparison.png",
    GRAPHS / "task18_e5_camera_observability.png",
    GRAPHS / "task18_e6_camera_processing_comparison.png",
    GRAPHS / "task18_e7_sobel_precision_comparison.png",
    GRAPHS / "task18_e8_camera_fpga_architecture.png",
]

embedded = 0

for path in figure_paths:
    story.append(PageBreak())
    story.append(heading(path.stem.replace("_", " ")))
    if insert_image(story, path, path.name):
        embedded += 1

# ------------------------------------
# 11. Example camera images
# ------------------------------------

story.append(PageBreak())
story.append(heading("11. Extracted GEMSTAR Images"))

for scenario in sorted(set(
    r["Recording"] for r in extraction
)):
    group = sorted(
        p for p in extracted_images
        if p.parent.name == scenario
    )

    if group:
        story.append(PageBreak())
        story.append(heading(scenario))
        if insert_image(
            story, group[0],
            f"Original extracted image: {group[0].name}"
        ):
            embedded += 1

# ------------------------------------
# 12. Render PDF
# ------------------------------------

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(
        50, 27, "GEMSTAR Camera Research Extension"
    )
    canvas.drawRightString(
        A4[0] - 50, 27, f"Page {doc.page}"
    )
    canvas.restoreState()

doc = SimpleDocTemplate(
    str(PDF),
    pagesize=A4,
    leftMargin=50,
    rightMargin=50,
    topMargin=45,
    bottomMargin=45,
    title="GEMSTAR Camera Extension Final Research",
)

doc.build(
    story,
    onFirstPage=footer,
    onLaterPages=footer
)

assert PDF.is_file()
assert PDF.stat().st_size > 10000

with PDF.open("rb") as f:
    assert f.read(5) == b"%PDF-"

# ------------------------------------
# 13. Artifact inventory
# ------------------------------------

manifest = []

# Avoid hashing the manifest and its own final report.
excluded_names = {
    "task18_e9_artifact_manifest.csv",
    "task18_e9_archive_verification.json",
}

for path in sorted(BASE.rglob("*")):
    if not path.is_file():
        continue
    if path.name in excluded_names:
        continue

    digest = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024), b""
        ):
            digest.update(block)

    manifest.append({
        "RelativePath": str(path.relative_to(BASE)),
        "SizeBytes": path.stat().st_size,
        "SHA256": digest.hexdigest()
    })

manifest_file = (
    FINDINGS / "task18_e9_artifact_manifest.csv"
)

with manifest_file.open(
    "w", encoding="utf-8", newline=""
) as f:
    writer = csv.DictWriter(
        f, fieldnames=list(manifest[0])
    )
    writer.writeheader()
    writer.writerows(manifest)

# ------------------------------------
# 14. Verification summary
# ------------------------------------

final = {
    "task": "18.E9",
    "report_created": PDF.is_file(),
    "pdf_path": str(PDF),
    "pdf_bytes": PDF.stat().st_size,
    "images_extracted": len(extracted_images),
    "quality_records": 20,
    "observability_records": 20,
    "fixed_point_records": len(precision),
    "rtl_modules_planned": len(modules),
    "rtl_verification_cases_planned":
        len(verification_cases),
    "illustrations_embedded": embedded,
    "artifacts_in_manifest": len(manifest),
    "rtl_implemented": False,
    "kria_measured": False,
    "complete": (
        PDF.is_file()
        and embedded == 10
        and len(extracted_images) >= 20
    ),
}

verification_path = (
    FINDINGS / "task18_e9_archive_verification.json"
)

verification_path.write_text(
    json.dumps(final, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 18.E9 FINAL VERIFICATION ===")
print("PDF created:", final["report_created"])
print("PDF size (MiB):",
      round(final["pdf_bytes"] / 1048576, 2))
print("Illustrations embedded:", embedded)
print("Extracted images:", len(extracted_images))
print("Artifacts inventoried:", len(manifest))
print("RTL implemented:", final["rtl_implemented"])
print("Hardware measured:", final["kria_measured"])
print("Archive completion:", final["complete"])
print("Verification JSON saved:",
      verification_path.is_file())
print("PDF location:", PDF)
