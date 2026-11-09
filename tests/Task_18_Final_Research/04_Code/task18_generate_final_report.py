from pathlib import Path
import csv, json, math, textwrap
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage

BASE = Path(r'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research')
OUT = BASE / '07_Research_Report' / 'Task_18_Final_Research_Report.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='ReportTitle2', parent=styles['Title'], fontSize=20, leading=25, spaceAfter=18, textColor=colors.HexColor('#17365D')))
styles.add(ParagraphStyle(name='ReportHeading2', parent=styles['Heading2'], fontSize=12, leading=16, spaceBefore=14, spaceAfter=7, textColor=colors.HexColor('#17365D')))
styles.add(ParagraphStyle(name='ReportBody2', parent=styles['BodyText'], fontSize=9, leading=13, spaceAfter=7))
styles.add(ParagraphStyle(name='ReportCaption2', parent=styles['BodyText'], fontSize=8, leading=11, spaceAfter=10, textColor=colors.HexColor('#505965')))
styles.add(ParagraphStyle(name='ReportSmall2', parent=styles['BodyText'], fontSize=8, leading=11, spaceAfter=4))
story=[]
missing=[]

def p(text, style='ReportBody2'):
    story.append(Paragraph(escape(str(text)).replace('\n','<br/>'), styles[style]))

def heading(text):
    p(text,'ReportHeading2')

def table(headers, rows, widths=None):
    data=[[Paragraph(escape(str(x)),styles['ReportSmall2']) for x in headers]]
    data.extend([[Paragraph(escape(str(x)),styles['ReportSmall2']) for x in row] for row in rows])
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCE8F4')),
        ('GRID',(0,0),(-1,-1),.3,colors.HexColor('#BDC6D0')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(t); story.append(Spacer(1,9))

def figure(relative, caption, max_width=490, max_height=370):
    path=BASE/relative
    if not path.is_file():
        missing.append(str(relative)); p('Figure unavailable: '+str(relative),'ReportCaption2'); return
    with PILImage.open(path) as im:
        width,height=im.size
    scale=min(max_width/width,max_height/height)
    story.append(Image(str(path),width=width*scale,height=height*scale,hAlign='CENTER'))
    p(caption,'ReportCaption2')

def read_csv(rel):
    path=BASE/rel
    if not path.is_file(): missing.append(str(rel)); return []
    with path.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))

def stat(row,key,fmt='.3f'):
    try: return format(float(row[key]),fmt)
    except (KeyError,ValueError,TypeError): return 'N/A'

p('TASK 18 - FINAL RESEARCH REPORT','ReportTitle2')
p('GEMSTAR Camera Perception: OSI Decoding, Python/MATLAB Preprocessing, YOLO Detection, Annotation-Based Evaluation and Repeated CPU Benchmarking')
p('Research archive: Task_18_Final_Research | Status: software-stage evidence collected; performance conclusions preliminary')
story.append(HRFlowable(width='100%',thickness=1,color=colors.HexColor('#A4BACF')))

heading('Executive summary')
p('This report documents the 12-image exploratory camera experiment based on the 466-frame fog_mor100 GEMSTAR recording. It includes raw RGB decoding, grayscale/Gaussian/Sobel preprocessing, image and object-detection inspection, provisional manual annotations, class-aware IoU matching, independent MATLAB analysis, and repeated CPU-only inference benchmarks. These findings do not constitute an ARM-FPGA hardware or energy evaluation.')

heading('1. Reproducible dataset and Camera decoding (Tasks 18.1-18.2)')
p('Source: 20261027T224313Z_sv_380_X_466_GEMSTAR.osi. Selected frame indices: 0, 50, 100, 150, 200, 250, 300, 350, 400, 423, 424, 450. Image dimensions: 640 x 480, 3 bytes/pixel, 921,600 uncompressed image bytes. RGB ordering and orientation were judged visually; the precise OSI format-enumeration mapping still requires source-level confirmation.')
figure('08_Extracted_Images/task18_frame000_rgb_interpretation.png','Figure 1. First extracted Camera image, shown using the visually plausible RGB interpretation.',max_height=240)
figure('01_Graphs/task18_selected_camera_contact_sheet.png','Figure 2. Selected frames spanning the higher- and lower-rate recording segments.',max_height=480)

heading('2. Camera preprocessing (Tasks 18.3-18.4)')
p('The PC Python/OpenCV pipeline converts the image to grayscale, applies a 5x5 Gaussian blur with sigma 1, and produces Sobel gradient magnitude. A basic-MATLAB implementation reproduced the outputs with close numerical agreement on the first frame. The operations are potential FPGA mapping candidates, but object detection receives the original RGB image unless explicitly designed otherwise.')
table(['Stage','Python-MATLAB MAE (8-bit intensity)'],[['Grayscale','0.000146'],['Gaussian blur','0.017559'],['Sobel edges','0.122012']],[175,300])
figure('01_Graphs/task18_camera_preprocessing_comparison.png','Figure 3. Original Camera image and OpenCV processing stages.',max_height=310)
figure('01_Graphs/task18_matlab_preprocessing_comparison.png','Figure 4. MATLAB processing outputs on the same scene.',max_height=340)

heading('3. Selected-frame object detection (Tasks 18.5-18.6)')
p('The pretrained YOLO11 Nano and YOLO11 Small COCO-class detectors were applied to the selected images on a PC CPU (PyTorch CPU-only environment). Predictions include class, confidence score, and bounding-box coordinates. The original Nano run produced 9 predictions of which 6 were vehicle-class predictions. Errors included a passenger car labeled airplane and a nearby vehicle labeled airplane or toilet.')
figure('01_Graphs/task18_yolo_detection_contact_sheet.png','Figure 5. Initial YOLO11 Nano annotated frame overview, including classification failures.',max_height=450)

heading('4. Manual reference annotations and quality review (Task 18.7)')
p('Twelve images were manually reviewed and five target objects provisionally labeled: car at frames 100, 150, 300 and 350; truck at frame 450. The remaining frames were left without positive target annotations. Source images and annotation records were hashed and stored. Frame 150 box placement was corrected. Small distant items (especially frame 250), class distinctions, and the completeness of negative frames require independent review; therefore the metrics below must be treated as provisional.')
figure('01_Graphs/task18_manual_annotation_contact_sheet.png','Figure 6. Reviewed manual bounding boxes. These are provisional reference labels, not independently certified ground truth.',max_height=450)

heading('5. Controlled model comparison and IoU-based evaluation (Task 18.7)')
p('Both models were run on CPU with imgsz=640, confidence=0.25, IoU-NMS=0.70 and class-agnostic NMS enabled. Correct-class detections were matched one-to-one to reference boxes at IoU >= 0.50; unmatched predictions were false positives and unmatched references false negatives. The assessment is only on 12 selected images and five provisional reference objects.')
acc=read_csv('02_CSV_Data/task18_controlled_accuracy_results.csv')
if acc:
    table(['Model','TP','FP','FN','Precision','Recall','F1','Localization matches'],[[r.get('Model',''),r.get('TP',''),r.get('FP',''),r.get('FN',''),stat(r,'Precision','.2%'),stat(r,'Recall','.2%'),stat(r,'F1','.2%'),r.get('LocalizationMatches','')] for r in acc],[70,30,30,30,72,66,55,120])
else:
    table(['Model','TP','FP','FN','Precision','Recall','F1'],[['YOLO11 Nano','1','5','4','16.67%','20.00%','18.18%'],['YOLO11 Small','3','7','2','30.00%','60.00%','40.00%']])
figure('01_Graphs/task18_matlab_detection_accuracy.png','Figure 7. Independent MATLAB accuracy summary based on the controlled evaluation CSV.',max_height=295)
p('Both models had three class-independent localization matches, despite different correct-class match totals. This indicates that spatial localization and semantic classification must be analyzed separately in subsequent reliability studies.')

heading('6. Repeated PC CPU inference benchmark (Tasks 18.9A-18.9B)')
p('Each model was warmed up and evaluated five times per selected frame (60 measurements per model; 120 in total). Reported model inference timings exclude other pipeline components such as OSI decoding, inter-device transfer and end-to-end application overhead. These values are from the current PC, not an ARM SoC.')
bench=read_csv('02_CSV_Data/task18_repeated_cpu_summary.csv')
if bench:
    table(['Model','N','Median ms','Mean ms','P95 ms','Std dev ms'],[[r.get('Model',''),r.get('Measurements',''),stat(r,'MedianMs'),stat(r,'MeanMs'),stat(r,'P95Ms'),stat(r,'StdDevMs')] for r in bench],[105,40,85,85,85,85])
else:
    table(['Model','N','Median ms','Mean ms','P95 ms'],[['YOLO11 Nano','60','19.137','19.392','21.911'],['YOLO11 Small','60','44.512','44.664','47.356']])
figure('01_Graphs/task18_matlab_cpu_benchmark.png','Figure 8. MATLAB validation of repeated inference latency statistics.',max_height=320)
p('The observed median ratio is approximately 2.33 (Small/Nano). Larger model capacity improved preliminary detection F1 on this small sample but increased CPU inference latency. We cannot extrapolate the ratio to ARM, FPGA, or energy usage without direct measurements.')

heading('7. Research conclusions and thesis relevance')
for txt in [
    'Camera OSI images are accessible as reproducible numerical arrays and can be consumed by Python and MATLAB.',
    'Grayscale, Gaussian and Sobel are hardware-relevant streaming operators; their potential acceleration remains to be measured.',
    'Pretrained generic detectors can misclassify synthetic/partially visible vehicles; a higher confidence is not proof of calibrated reliability.',
    'The comparison illustrates a potential quality-latency trade-off suitable for future uncertainty-aware scheduling research, not a proven scheduler benefit.',
    'Future cross-sensor fusion must validate geometric association before using detection scores as reliable uncertainty estimates.'
]: p('- '+txt)

heading('8. Scientific limitations and planned follow-up')
for txt in [
    'Only 12 selected images, five provisional manually labeled reference objects, and a single recording scenario were evaluated.',
    'Annotation completeness and object classes are not independently verified; frame 250 deserves focused review.',
    'Precision, recall and F1 are small-sample descriptive figures; not a generalization or safety claim.',
    'Inference time is not complete processing time, real-time deadline performance, board energy, or power.',
    'No INT8 model, FPGA DPU, AXI DMA or ARM-FPGA implementation was evaluated in Task 18.',
    'Later tasks should validate multiple conditions, calibrate uncertainty, conduct hardware profiling, and quantify transfer and scheduling overhead.'
]: p('- '+txt)

heading('9. Research archive index')
for folder in ['01_Graphs','02_CSV_Data','03_Configurations','04_Code','05_Raw_Data_References','06_Research_Findings','07_Research_Report','08_Extracted_Images','09_GroundTruth_Annotations']:
    path=BASE/folder
    count=sum(1 for x in path.rglob('*') if x.is_file()) if path.exists() else 0
    p(f'{folder}: {count} files recorded in the local archive.', 'ReportSmall2')

heading('10. Source documentation')
finding=BASE/'06_Research_Findings'/'task18_final_research_findings.md'
if finding.exists():
    p('Detailed methods, values, limitations and next-task references are retained in 06_Research_Findings/task18_final_research_findings.md. Reproducible Python and MATLAB scripts, CSV outputs and annotated evidence remain in this Task 18 archive.')
else:
    missing.append('06_Research_Findings/task18_final_research_findings.md')

if missing:
    heading('Appendix - Missing optional or expected inputs')
    for m in sorted(set(missing)): p('- '+m,'ReportSmall2')

def page_number(canvas, doc):
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(colors.HexColor('#59697B'))
    canvas.drawRightString(A4[0]-42,25,f'Task 18 | Page {doc.page}')

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=45,bottomMargin=40,title='Task 18 Final Research Report',author='GEMSTAR Camera Perception Research')
doc.build(story,onFirstPage=page_number,onLaterPages=page_number)
print('=== TASK 18.10C FINAL REPORT ===')
print('PDF created:',OUT.is_file())
print('PDF size (bytes):',OUT.stat().st_size)
print('Missing input figures/files:',len(set(missing)))
for m in sorted(set(missing)): print(' MISSING:',m)
try:
    from pypdf import PdfReader
    print('Pages:',len(PdfReader(str(OUT)).pages))
except ImportError:
    print('Pages: not counted (pypdf not installed)')
print('Path:',OUT)
