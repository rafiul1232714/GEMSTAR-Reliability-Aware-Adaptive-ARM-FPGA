from pathlib import Path
import csv
import html
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.utils import ImageReader

BASE = Path(r'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_17_Final_Research')
CSV = BASE / '02_CSV_Data'
GRAPHS = BASE / '01_Graphs'
OUTPUT = BASE / '07_Research_Report' / 'Task_17_Final_Research_Report.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

required = [
    CSV / 'task17_sensor_timestamps.csv',
    CSV / 'task17_groundtruth_timestamps.csv',
    CSV / 'task17_gt_sv_alignment.csv',
    CSV / 'task17_sensor_mounting_positions.csv',
    CSV / 'task17_timing_regime_summary.csv',
    CSV / 'task17_matlab_validation_results.csv',
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise FileNotFoundError('Missing input files:\n' + '\n'.join(missing))

def load(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

sv, gt = load(required[0]), load(required[1])
align, mounts = load(required[2]), load(required[3])
regimes, matlab = load(required[4]), load(required[5])

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ReportTitleX', parent=styles['Title'], fontSize=21, leading=27, textColor=colors.HexColor('#15334e'), spaceAfter=16))
styles.add(ParagraphStyle(name='SectionX', parent=styles['Heading2'], fontSize=12, leading=17, textColor=colors.HexColor('#17496d'), spaceBefore=14, spaceAfter=7))
styles.add(ParagraphStyle(name='BodyX', parent=styles['BodyText'], fontSize=9, leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name='CaptionX', parent=styles['BodyText'], fontSize=8, leading=11, textColor=colors.HexColor('#536472'), alignment=TA_CENTER, spaceAfter=12))
styles.add(ParagraphStyle(name='SmallX', parent=styles['BodyText'], fontSize=8, leading=11))

story = []
def P(text): story.append(Paragraph(html.escape(str(text)), styles['BodyX']))
def H(text): story.append(Paragraph(html.escape(str(text)), styles['SectionX']))
def tab(headers, rows, widths=None):
    data = [[Paragraph(html.escape(str(v)), styles['SmallX']) for v in headers]]
    data += [[Paragraph(html.escape(str(v)), styles['SmallX']) for v in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9f0f7')),
        ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#d3dfe9')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

def fig(filename, caption):
    p = GRAPHS / filename
    if not p.exists():
        P(f'Figure not available: {filename}. This figure was not embedded.')
        return
    image = ImageReader(str(p))
    w, h = image.getSize()
    maxw, maxh = 17.0 * cm, 10.7 * cm
    scale = min(maxw / w, maxh / h)
    story.append(Image(str(p), width=w*scale, height=h*scale))
    story.append(Paragraph(html.escape(caption), styles['CaptionX']))

def metric_map(rows):
    return {str(r['Metric']): r['Value'] for r in rows}

m = metric_map(matlab)
story.append(Spacer(1, 2*cm))
story.append(Paragraph('TASK 17 | FINAL RESEARCH REPORT', styles['ReportTitleX']))
P('GEMSTAR Camera-LiDAR-Radar Timestamp Synchronization, Sensor Mounting Geometry and Data Validity')
P('Project: Uncertainty-Constrained Energy-Aware ARM-FPGA Hardware-Software Co-Design for Tri-Sensor Perception')
P('Evidence: 20261027T224313Z GT/SV OSI recording (466 frames) | Dataset: fog_mor100 folder')
P('Status: Recorded-message alignment and mounting consistency established; acquisition-time equality and coordinate-axis conventions remain unverified.')
story.append(Spacer(1, .5*cm))
tab(['Critical result', 'Observed outcome'], [
    ['GroundTruth / SensorView message alignment', '466 / 466 identical timestamps; maximum difference 0 ms'],
    ['Mounting stability', 'All 3 sensor configurations unchanged across 466 frames'],
    ['Timing regime transition', 'Frame 424; 424 high-rate messages followed by 42 low-rate messages'],
    ['Independent calculation', 'MATLAB numerical calculations agree with Python'],
])

H('1. Research question and motivation')
P('Before camera-LiDAR-radar association, tracking, uncertainty estimation and hardware scheduling, are the recorded timestamps and sensor mounting configurations internally consistent? Incorrect alignment can appear as false object uncertainty or misleading processing deadlines.')
H('2. Dataset integrity and OSI inspection | Tasks 17.1-17.2')
P('Selected matching GT and SV files were compared against the Task 15 SHA-256 manifest. The dataset contained 466 OSI GroundTruth and 466 SensorView messages. The first SensorView contained one Camera, one LiDAR and one Radar entry, using the common SensorView timestamp; independent per-sensor capture timestamps were not established.')
P('First recorded SensorView timestamp: 0.016666799 s; last timestamp: 28.038191422 s. Filenames and manifest entries are preserved in 05_Raw_Data_References.')
H('3. Time extraction and reference alignment | Tasks 17.3-17.4')
P('Python read the length-prefixed OSI messages sequentially and saved frame indices, simulated timestamps, message intervals and sensor entry counts. Every GT message timestamp was compared with the SV message of the same frame index.')
tab(['Check', 'Result'], [
    ['SensorView frames', str(len(sv))],
    ['GroundTruth frames', str(len(gt))],
    ['Matching message timestamps', str(sum(str(x.get('ExactMatch', '')).strip().lower() == 'true' for x in align))],
    ['Maximum absolute SV-GT difference', '0 ms'],
    ['Median interval (all messages)', '32.9931 ms'],
    ['Long intervals (>2x overall median)', '42'],
])
fig('task17_gt_sv_alignment.png', 'Figure 1. GroundTruth vs SensorView recorded-message timestamp difference.')
fig('task17_sensor_timestamp_intervals.png', 'Figure 2. Interval variability across the selected OSI stream.')
H('4. Timing regime investigation | Task 17.8')
P('Exploratory gap analysis identified 42 long intervals, all beginning at frame 424. Recorded-message intervals changed from approximately 33 ms to approximately 333 ms. All three sensor entry types remained present in both regimes. The cause of the change was not determined; these intervals must not be interpreted as ARM or FPGA processing latency.')
tab(['Segment', 'Frames', 'Median interval', 'Approx. message rate'], [
    [r['Regime'], r['Frames'], f"{float(r['MedianIntervalMs']):.4f} ms", f"{float(r['ApproxRateHz']):.3f} Hz"]
    for r in regimes
])
fig('task17_timing_regime_transition.png', 'Figure 3. Distinct recorded-message timing regimes; vertical line indicates frame 424.')
H('5. Sensor mounting geometry | Tasks 17.5-17.6')
P('Positions extracted from OSI were stable throughout all 466 frames and numerically matched the inspected current DefaultGemstar.ini positions after cm-to-m conversion. Current configuration mounts all three sensors to SensorPlatform_1 with nominal zero Euler rotations.')
tab(['Sensor', 'X (m)', 'Y (m)', 'Z (m)'], [
    [r['Sensor'], f"{float(r['X_m']):.3f}", f"{float(r['Y_m']):.3f}", f"{float(r['Z_m']):.3f}"]
    for r in mounts
])
P('Inter-sensor origin distances: Camera-LiDAR 2.1024 m; Camera-Radar 1.5264 m; LiDAR-Radar 0.6083 m. Backups had different historic Radar positions and mounting assignments, so recording provenance must be distinguished from consistency with the current INI.')
P('Three 4x4 homogeneous pose matrices were constructed from reported position and roll/pitch/yaw. Rotation orthogonality, determinant, inverse and sensor-origin mapping checks passed. These are mathematical consistency checks, not independently verified physical projection accuracy.')
H('6. Independent MATLAB cross-validation | Task 17.7')
P('MATLAB independently imported the timestamp and mounting CSV files, reproduced 466 exact message timestamp matches, the 32.9931 ms median interval and 42 long intervals, calculated sensor-origin distances and reconstructed three 4x4 transformations.')
tab(['MATLAB metric', 'Value'], [[r['Metric'], r['Value']] for r in matlab])
fig('task17_matlab_timestamp_validation.png', 'Figure 4. MATLAB timestamp alignment and message-interval visualization.')
H('7. Source-code verification and open questions | Task 17.9')
P('CameraSensor.cpp references ToOSI::toMountingPosition; LiDAR and Radar implementations populate mounting_position. The brief search in the main Source directory inspected only two files and found no function definition. Therefore the OSI/Unreal coordinate-axis mapping, handedness and exact geometric interpretation remain unverified. That search result does not establish that the function is absent.')
H('8. Scientific limitations and interpretation')
for s in [
    'Identical GT/SV timestamps establish recorded-message alignment, not independent physical sensor acquisition synchrony.',
    'Sensor entry presence is not a full quality or payload-correctness test.',
    'The reason for the 30 Hz-to-3 Hz recorded-message interval change remains unresolved.',
    'Sensor-to-vehicle transformations assume the reported mounting convention is correct; a known-target projection check is still needed.',
    'The current INI agrees with the OSI content, but its exact historical version for this recording is not proven.',
]: P('- ' + s)
H('9. Implications for Tasks 18-50')
P('Tasks 18-20 will build camera image, LiDAR point-cloud and Radar preprocessing using these recording references. Tasks 21-23 must validate actual cross-sensor object projections and association against ground truth before relying on tracking uncertainty. Later hardware experiments must benchmark CPU/FPGA execution time and energy with independent timers and power instrumentation, not OSI simulated-time intervals. Separate the two recorded timing regimes during deadline experiments.')
H('10. Evidence archive and reproducibility')
for folder in ['01_Graphs', '02_CSV_Data', '03_Configurations', '04_Code', '05_Raw_Data_References', '06_Research_Findings', '07_Research_Report']:
    count = len([p for p in (BASE / folder).glob('*') if p.is_file()]) if (BASE/folder).exists() else 0
    P(f'{folder}: {count} files at report build time')
P('The original raw OSI recordings remain in the project data/raw folder; hashes and references are retained in the research archive.')


def footer(c, doc):
    c.saveState()
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#61768b'))
    c.drawString(2*cm, 1.2*cm, 'GEMSTAR | Task 17 Final Research')
    c.drawRightString(A4[0]-2*cm, 1.2*cm, f'Page {doc.page}')
    c.restoreState()

pdf = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.7*cm, bottomMargin=1.8*cm)
pdf.build(story, onFirstPage=footer, onLaterPages=footer)
try:
    from pypdf import PdfReader
    page_count = len(PdfReader(str(OUTPUT)).pages)
except ImportError:
    page_count = 'not counted (pypdf not installed)'
print('=== TASK 17.10C FINAL REPORT ===')
print('PDF created:', OUTPUT.exists())
print('Pages:', page_count)
print('Size (bytes):', OUTPUT.stat().st_size)
print('Path:', OUTPUT)
