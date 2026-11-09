from pathlib import Path
import csv
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage

BASE = Path(r'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research')
OUT = BASE/'07_Research_Report'/'Task_18_Final_Research_Report_MATLAB_Extended.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='XTitle', parent=styles['Title'], fontSize=20, leading=24, textColor=colors.HexColor('#17365D'), spaceAfter=13))
styles.add(ParagraphStyle(name='XH', parent=styles['Heading2'], fontSize=12, leading=15, textColor=colors.HexColor('#17365D'), spaceBefore=13,spaceAfter=7))
styles.add(ParagraphStyle(name='XBody', parent=styles['BodyText'], fontSize=9,leading=13,spaceAfter=7))
styles.add(ParagraphStyle(name='XCaption', parent=styles['BodyText'],fontSize=8,leading=11,spaceAfter=9,textColor=colors.HexColor('#506070')))
styles.add(ParagraphStyle(name='XSmall',parent=styles['BodyText'],fontSize=7.6,leading=10.5))
story=[]
missing=[]

def p(s,style='XBody'): story.append(Paragraph(escape(str(s)),styles[style]))
def heading(s): p(s,'XH')
def fig(rel, caption, h=340):
    path=BASE/rel
    if not path.is_file():
        missing.append(rel); p('Missing figure: '+rel,'XCaption'); return
    with PILImage.open(path) as im: w0,h0=im.size
    factor=min(500/w0,h/h0)
    story.append(Image(str(path), width=w0*factor,height=h0*factor,hAlign='CENTER'))
    p(caption,'XCaption')
def readcsv(rel):
    f=BASE/rel
    if not f.is_file(): missing.append(rel); return []
    with f.open(encoding='utf-8-sig',newline='') as handle: return list(csv.DictReader(handle))
def val(r,k,default='—'):
    v=r.get(k,default)
    return str(v) if str(v).strip() else default

def tab(headers,rows,widths=None):
    data=[[Paragraph(escape(str(c)),styles['XSmall']) for c in headers]]
    data.extend([[Paragraph(escape(str(c)),styles['XSmall']) for c in row] for row in rows])
    t=Table(data,colWidths=widths or [505/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DFEAF6')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#BAC5D1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(t);story.append(Spacer(1,9))
def fnum(v):
    try:return f'{float(v):.4f}'
    except (ValueError,TypeError):return 'N/A'
def summary_csv(rel, fields, labels=None):
    rows=readcsv(rel)
    if not rows:return
    labels=labels or fields
    pairs=[]
    for row in rows:
        pairs.append([val(row,k) if k in ('Operation','Frame','Measurements') else fnum(row.get(k)) for k in fields])
    tab(labels,pairs)

p('TASK 18 — MATLAB EXTENDED RESEARCH REPORT','XTitle')
p('GEMSTAR Camera Perception | Python/OpenCV Reference + MATLAB Image Processing Toolbox + Integer/FPGА-Oriented Experiments')
p('This extended report retains the original Task 18 research evidence, and adds the completed MATLAB experiments 18.11–18.16. It does not replace or alter the original PDF.')
story.append(HRFlowable(width='100%',thickness=1,color=colors.HexColor('#A4BACF')))

heading('Executive summary')
p('Twelve 640 × 480 GEMSTAR Camera frames were extracted from a 466-message SensorView recording. The previous work established OpenCV preprocessing, MATLAB numerical validation, provisional YOLO11n/YOLO11s detection evaluation, and a 120-measurement repeated PC inference benchmark. The extension implements three MATLAB preprocessing stages on all selected frames, evaluates image statistics, measures MATLAB CPU operator time, and develops integer grayscale and Sobel reference algorithms. All reported quality metrics describe this selected dataset and are not an independently validated sensor-reliability score.')
heading('1. Original recorded-camera dataset and visual examples')
p('Source recording: 20261027T224313Z_sv_380_X_466_GEMSTAR.osi. Selected frame IDs: 0, 50, 100, 150, 200, 250, 300, 350, 400, 423, 424, 450. Camera payload interpreted as RGB, 640 × 480 × 3 (921,600 bytes), based on visual inspection. The original run has two previously identified frame-timing regimes.')
fig('01_Graphs/task18_selected_camera_contact_sheet.png','Original experiment: all twelve representative Camera frames.',h=390)
fig('01_Graphs/task18_camera_preprocessing_comparison.png','Original Python/OpenCV Camera processing pipeline.',h=310)
heading('2. Original YOLO detection and reference evaluation')
p('Two pretrained YOLO11 models were tested on PC CPU with imgsz=640, confidence=0.25, NMS IoU=0.7 and class-agnostic NMS. Reference annotations span just five provisional target objects across 12 selected frames. Detection confidence is not a calibrated reliability probability. Errors such as cars classified as unrelated categories motivate future cross-sensor checking.')
fig('01_Graphs/task18_yolo_detection_contact_sheet.png','Initial detection examples including visually observed classification errors.',h=380)
fig('01_Graphs/task18_manual_annotation_contact_sheet.png','Provisional manually annotated frames; annotations have not undergone independent review.',h=370)
tab(['Model','TP','FP','FN','Precision','Recall','F1'],[['YOLO11 Nano','1','5','4','16.67%','20.00%','18.18%'],['YOLO11 Small','3','7','2','30.00%','60.00%','40.00%']])
fig('01_Graphs/task18_matlab_detection_accuracy.png','Python/MATLAB independently verified controlled accuracy comparison.',h=260)
heading('3. Original repeated desktop CPU inference benchmark')
tab(['Model','Measurements','Median','Mean','P95','Std. dev.'],[['YOLO11 Nano','60','19.137 ms','19.392 ms','21.911 ms','1.497 ms'],['YOLO11 Small','60','44.512 ms','44.664 ms','47.356 ms','1.887 ms']])
p('The Small model median was approximately 2.33 times Nano. These values refer to PC CPU model inference, not total pipeline duration, FPGA execution, or board-level energy.')
fig('01_Graphs/task18_matlab_cpu_benchmark.png','Repeated CPU inference comparison, independently recalculated in MATLAB.',h=265)

heading('4. Task 18.11 — MATLAB toolbox-based Camera preprocessing')
p('MATLAB R2026b Image Processing Toolbox was installed and functionally checked using fspecial, imfilter and imshowpair. The production MATLAB script processed the twelve saved GEMSTAR RGB images with rgb2gray, a 5×5 Gaussian kernel (sigma 1) via imfilter with replicate boundaries, and imgradient Sobel magnitude. Thirty-six processed images were saved, three per frame.')
fig('01_Graphs/task18_matlab_full_camera_pipeline.png','Frame 150, MATLAB toolbox pipeline: RGB, grayscale, Gaussian and Sobel.',h=360)
summary_csv('02_CSV_Data/task18_matlab_full_preprocessing_metrics.csv',['Frame','MeanGray','MeanBlur','MeanEdge'])
heading('5. Task 18.12 — MATLAB versus Python/OpenCV (frame 0)')
p('Comparison is performed at the saved uint8 pixel level; small differences can arise from filter kernels, arithmetic rounding, Sobel scaling and border handling. Visual similarity does not imply bit-exact equality. The large maximum Sobel deviation merits attention even though average error is small.')
summary_csv('02_CSV_Data/task18_12_matlab_python_comparison.csv',['Operation','MAE','RMSE','MaxError','ExactMatchPercent'],['Operation','MAE','RMSE','Maximum error','Exact-match %'])
fig('01_Graphs/task18_12_matlab_python_comparison.png','Three-stage saved-output comparison, showing MATLAB, Python and absolute pixel differences.',h=430)
heading('6. Task 18.13 — Image-content metrics on 12 frames')
p('Measurements: grayscale brightness mean, global intensity standard deviation (contrast proxy), Shannon entropy, average Gaussian-induced pixel change and Sobel edge-pixel percentage at a fixed threshold of 40. These indicate scene-content variations. They do NOT independently identify fog severity or Camera sensor failure.')
fig('01_Graphs/task18_13_matlab_image_quality.png','Brightness, contrast proxy, grayscale entropy and Sobel edge density by selected frame.',h=370)
summary_csv('02_CSV_Data/task18_13_matlab_image_quality.csv',['Frame','Brightness','Contrast','ImageEntropy','GaussianMAE','EdgeDensity'])
heading('7. Task 18.14 — MATLAB preprocessing timing benchmark')
p('Each operation was measured ten times on each of twelve images after three warm-up executions. The 360 recorded MATLAB PC timing values exclude file reading and writing. They are not directly comparable to neural-network inference or ARM-FPGA timings as equivalent workloads.')
summary_csv('02_CSV_Data/task18_14_matlab_preprocessing_latency_summary.csv',['Operation','Measurements','MedianMs','MeanMs','P95Ms','StdDevMs'])
fig('01_Graphs/task18_14_matlab_preprocessing_latency.png','Measured desktop MATLAB CPU processing latencies; Sobel is the most expensive of the three operators in this implementation.',h=305)
heading('8. Task 18.15A — Integer grayscale for streaming hardware')
p('An integer weighted approximation uses Y = (77R + 150G + 29B + 128) >> 8. Input samples remain 8-bit, but accumulation uses uint32 to prevent overflow. This is a coefficient approximation to RGB grayscale; it is not identical to MATLAB rgb2gray. Distinct bit widths should be tested when converting this algorithm into HDL/HLS.')
rows=readcsv('02_CSV_Data/task18_15_integer_grayscale_accuracy.csv')
if rows:
    tab(['Frames','Mean MAE','Worst MAE','Worst max error','Mean exact match'],[[str(len(rows)),fnum(sum(float(r['MAE']) for r in rows)/len(rows)),fnum(max(float(r['MAE']) for r in rows)),fnum(max(float(r['MaxError']) for r in rows)),fnum(sum(float(r['ExactMatchPercent']) for r in rows)/len(rows))+'%']])
fig('01_Graphs/task18_15_integer_grayscale_comparison.png','Reference versus coefficient-quantized grayscale and absolute difference, frame 150.',h=275)
heading('9. Task 18.15B — Integer signed Sobel gradients')
p('Signed int32 arithmetic was used for Sobel Gx and Gy; this agrees exactly with a floating-point reference using the same coefficients, image, boundaries, and final hypot/round/clamp operation. Thus the gradients are integer but the final L2 magnitude is not yet integer-only. Standard 3×3 Sobel worst-case single-axis gradient is ±1020, so 11 signed bits suffice for each gradient before magnitude combination.')
rows=readcsv('02_CSV_Data/task18_15b_integer_sobel_accuracy.csv')
if rows:
    tab(['Frames','Mean MAE','Min exact match','Max |Gx|','Max |Gy|'],[[str(len(rows)),fnum(sum(float(r['MAE']) for r in rows)/len(rows)),fnum(min(float(r['ExactMatchPercent']) for r in rows))+'%',fnum(max(float(r['MaxAbsGx']) for r in rows)),fnum(max(float(r['MaxAbsGy']) for r in rows))]])
fig('01_Graphs/task18_15b_integer_sobel_comparison.png','Frame 150: smoothed Camera input, saved Sobel and signed-integer gradient implementation.',h=270)
heading('10. Task 18.16 — Fully integer L1 Sobel magnitude approximation')
p('The new magnitude approximation is min(255, |Gx|+|Gy|), replacing sqrt(Gx²+Gy²). The approximation changes output values, can amplify diagonal edges, and may saturate at 255 more often than L2. Pixel-level differences are measured directly against the L2 reference using the SAME integer Sobel gradients. Image similarity does not by itself demonstrate lower FPGA resource usage or energy savings.')
rows=readcsv('02_CSV_Data/task18_16_integer_sobel_approximation.csv')
if rows:
    def mean(k):return sum(float(r[k]) for r in rows)/len(rows)
    tab(['Frames','Mean MAE','Worst max error','Mean exact %','Mean sat. %'],[[str(len(rows)),fnum(mean('MAE')),fnum(max(float(r['MaxError']) for r in rows)),fnum(mean('ExactMatchPercent')),fnum(mean('ApproxSaturationPercent'))]])
    tab(['Frame','MAE','Max error','Exact %','Saturation %'],[[r.get('Frame',''),fnum(r.get('MAE')),fnum(r.get('MaxError')),fnum(r.get('ExactMatchPercent')),fnum(r.get('ApproxSaturationPercent'))] for r in rows])
fig('01_Graphs/task18_16_integer_sobel_approximation.png','Frame 150: exact L2 and integer L1 Sobel magnitude with absolute error image.',h=305)
heading('11. Reproducibility and important limitations')
for s in [
 'All model-accuracy claims are exploratory: only 12 selected frames and five provisional manual target-object annotations, with no independent reference-label review.',
 'MATLAB/OpenCV comparisons may depend on border padding, rounding, saved 8-bit saturation and gradient scaling; identical numerical output must be explicitly engineered if required.',
 'The MATLAB preprocessing latency benchmark uses tic/toc on a desktop and is affected by cache, JIT, processor load and implementation; it is not a comparison to OpenCV until both use matched test methodology.',
 'Integer grayscale and Sobel calculations are numerical reference experiments, not resource, power, timing or energy measurements on a synthesized FPGA.',
 'RGB input into pretrained YOLO remains distinct from the grayscale/Sobel branch; no detection improvement from preprocessing has been demonstrated.',
 'No claim of validated adaptive CPU-FPGA scheduling, energy savings or end-to-end real-time performance is supported by Task 18.'
]:p('• '+s)
heading('12. Task 18 research archive')
for folder in ['01_Graphs','02_CSV_Data','03_Configurations','04_Code','05_Raw_Data_References','06_Research_Findings','07_Research_Report','08_Extracted_Images','09_GroundTruth_Annotations']:
    loc=BASE/folder; count=sum(x.is_file() for x in loc.rglob('*')) if loc.exists() else 0
    p(f'{folder}: {count} local files.','XSmall')
p('Next work: preserve a deterministic hardware input-output test-vector format and, in subsequent tasks, profile corresponding operators on actual ARM/FPGA hardware with measured end-to-end timing, transfer overhead, resource utilization and energy.')
if missing:
    heading('Appendix: Missing optional or required files')
    for item in sorted(set(missing)):p(item,'XSmall')

def foot(canvas,doc):
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#556879'))
    canvas.drawRightString(A4[0]-42,25,f'Task 18 MATLAB Extended | {doc.page}')
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=40,title='Task 18 MATLAB Extended Research Report')
doc.build(story,onFirstPage=foot,onLaterPages=foot)
print('=== TASK 18.17 MATLAB EXTENDED FINAL REPORT ===')
print('PDF created:',OUT.is_file())
print('PDF size (bytes):',OUT.stat().st_size)
print('Missing input figures/files:',len(set(missing)))
for item in sorted(set(missing)):print(' MISSING:',item)
print('PDF path:',OUT)
