"""Task 22 final report generator. Run with the project's Python venv.
Usage: python task22_10b_build_research_report.py --task-dir E:\\...\\Task_22_Final_Research
Needs reportlab: python -m pip install reportlab
"""
import argparse
import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable)

NAVY=colors.HexColor('#173153'); BLUE=colors.HexColor('#2370A1'); PALE=colors.HexColor('#EDF4F9'); GREY=colors.HexColor('#586678'); LINE=colors.HexColor('#D7E3ED')
PAGE_WIDTH, PAGE_HEIGHT=A4


def read_csv(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))


def num(x, default=0):
    try: return float(x)
    except (TypeError, ValueError): return default


def build(task):
    task=Path(task).resolve()
    reportdir=task/'07_Research_Report'; reportdir.mkdir(parents=True, exist_ok=True)
    target=reportdir/'Task_22_Final_Research_Report.pdf'
    csvdir=task/'02_CSV_Data'; graphdir=task/'03_Graphs'; benchmark=task/'09_Benchmark_Results'
    pairs=read_csv(csvdir/'task22_04b_deduplicated_pair_summary.csv')
    coverage=read_csv(csvdir/'task22_06_recording_comparison.csv')
    validation=read_csv(csvdir/'task22_07_validation_summary.csv')
    candidates=read_csv(task/'08_Processed_Data'/'task22_08_dataset_summary.csv')
    timing=read_csv(benchmark/'task22_09_benchmark_summary.csv')
    repro=read_csv(benchmark/'task22_09_reproducibility.csv')
    inventory=read_csv(csvdir/'task22_01_recording_inventory.csv')
    if not coverage or not validation or not candidates or not timing:
        raise RuntimeError('Essential Task 22 CSV evidence missing. Confirm Task 22.6–22.9 outputs are present.')

    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle22',fontName='Helvetica-Bold',fontSize=17,leading=22,textColor=NAVY,spaceAfter=10))
    styles.add(ParagraphStyle(name='ReportSub22',fontName='Helvetica',fontSize=9.2,leading=14,textColor=GREY,spaceAfter=11))
    styles.add(ParagraphStyle(name='Section22',fontName='Helvetica-Bold',fontSize=11.5,leading=15,textColor=NAVY,spaceBefore=13,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle(name='Body22',fontName='Helvetica',fontSize=9,leading=13,spaceAfter=7))
    styles.add(ParagraphStyle(name='Bullet22',parent=styles['Body22'],leftIndent=13,firstLineIndent=-9,spaceAfter=4))
    styles.add(ParagraphStyle(name='Figure22',fontName='Helvetica-Oblique',fontSize=8,leading=11,textColor=GREY,alignment=TA_CENTER,spaceBefore=4,spaceAfter=9))
    styles.add(ParagraphStyle(name='TableCell22',fontName='Helvetica',fontSize=7.5,leading=10))
    styles.add(ParagraphStyle(name='TableHeader22',fontName='Helvetica-Bold',fontSize=7.5,leading=10,textColor=colors.white))
    styles.add(ParagraphStyle(name='Small22',fontName='Helvetica',fontSize=7.8,leading=11,spaceAfter=5))
    flow=[]; available_w=PAGE_WIDTH-39*mm
    def P(s,sty='Body22'): flow.append(Paragraph(s,styles[sty]))
    def H(s): P(s,'Section22')
    def bullet(s): P('&#8226; '+s,'Bullet22')
    def tbl(headers,rows,widths=None):
        if not rows: return
        data=[[Paragraph(escape(str(v)),styles['TableHeader22']) for v in headers]]
        data += [[Paragraph(escape(str(v)),styles['TableCell22']) for v in row] for row in rows]
        if widths is None: widths=[available_w/len(headers)]*len(headers)
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.25,LINE)]))
        flow.append(t); flow.append(Spacer(1,6*mm))
    figures=[]
    def fig(name,caption):
        path=graphdir/name
        if not path.exists():
            bullet('Figure unavailable in source folder: <b>'+escape(name)+'</b>.')
            return
        try:
            from PIL import Image as PILImage
            with PILImage.open(path) as im: iw,ih=im.size
        except ImportError:
            from reportlab.lib.utils import ImageReader
            iw,ih=ImageReader(str(path)).getSize()
        maxw=available_w; maxh=110*mm
        scale=min(maxw/iw,maxh/ih)
        im=Image(str(path),width=iw*scale,height=ih*scale)
        flow.append(KeepTogether([im,Paragraph(escape(caption),styles['Figure22'])]))
        figures.append(name)
    def newpage(): flow.append(PageBreak())

    total_frames=sum(int(num(r.get('Frames'))) for r in coverage)
    total_candidates=sum(int(num(r.get('FusionCandidateFrames'))) for r in candidates)
    method={r['Method']:r for r in timing}
    py_ms=num(method.get('Python_loop',{}).get('MedianTimeMs'))
    np_ms=num(method.get('NumPy_vectorized',{}).get('MedianTimeMs'))
    ratio=py_ms/np_ms if np_ms else float('nan')

    P('TASK 22 | FINAL RESEARCH REPORT','ReportTitle22')
    P('Reusable GEMSTAR Multi-Recording OSI Processing, Integrity Validation, MATLAB/Python Standardization and CPU Reproducibility','ReportSub22')
    P('<b>Project:</b> Reliability-constrained energy-efficient Camera–LiDAR–Radar processing for ARM–FPGA hardware/software co-design.')
    P('<b>Scope:</b> Four deduplicated SensorView/GroundTruth recording pairs, first 100 messages per pair. No physical target-board power measurements.')
    tbl(['Critical research result','Observed outcome'],[
        ('Unique recording pairs',str(len(coverage))),
        ('Frames analyzed',str(total_frames)),
        ('Preliminary tri-sensor candidate frames',str(total_candidates)),
        ('MATLAB/Python candidate disagreements','0'),
        ('Reproducibility','3 of 3 reads reproduced the same candidate identities'),
        ('Python / NumPy median per-pass timing',f'{py_ms:.6f} ms / {np_ms:.6f} ms')], [62*mm,available_w-62*mm])
    H('1. Research question and motivation')
    P('Can archived GEMSTAR SensorView and GroundTruth recordings be processed using one reusable, source-traceable software workflow, with repeatable quality decisions and a MATLAB-compatible interface, before introducing fusion algorithms and hardware accelerators? Task 22 tests this data-engineering foundation rather than perception accuracy or electrical energy savings.')
    H('2. Workspace and source inventory | Task 22.1')
    P('Created the single Task_22_Final_Research workspace with separate directories for code, CSV results, graphs, configuration evidence, raw-data references, findings, reports, standardized exports and benchmark results. Original OSI files were referenced, not modified. The discovery inventory classifies filenames and source folders; those labels do not validate sensor payloads or scenario conditions.')
    if inventory: P(f'The preserved source inventory contains {len(inventory)} listed OSI file paths at the time of the inventory step.')
    H('3. Generic OSI message reader | Task 22.2')
    P('Implemented a configurable Python reader for length-prefixed OSI protobuf messages, with a four-byte little-endian length header, a message-size guard, structured error handling and user-selectable message limits. Initial smoke testing decoded three SensorView and three GroundTruth messages. These were independently selected small files, not a verified matching pair; the selected SensorView samples had no Camera, LiDAR or Radar entries.')
    H('4. Tri-sensor presence and paired timestamps | Task 22.3')
    P('Applied the reader to the corrected 50 m recording identified by suffix 806 and its matching GroundTruth file. In the first 100 messages, Camera.image_data, LiDAR.reflection and Radar.reflection fields were populated, with 100 of 100 matching SensorView/GroundTruth message timestamps. Presence is not evidence of image decode correctness or physical sensor capture-time synchrony.')

    newpage()
    H('5. Pair identification, duplicate audit and source provenance | Tasks 22.4, 22.4B, 22.5–22.5C')
    P('The inventory contained 19 matching filename pairs. Five pair entries were selected for limited inspection; all five passed message alignment in their first 100 frames. SHA-256 comparison subsequently established that two entries for recording 542, stored in different directories, were byte-identical on both SensorView and GroundTruth sides. One duplicate analysis entry was excluded, leaving four unique tested recordings without deleting original files.')
    tbl(['Recording suffix','Camera/LiDAR/Radar entry frames','Message timestamp matches'],[
        ('806','100 / 100 / 100','100/100'),('794','100 / 100 / 100','100/100'),('466','100 / 100 / 100','100/100'),('542','0 / 0 / 100','100/100')
    ],[38*mm,70*mm,available_w-108*mm])
    P('Task 22.5 categorized the folders of 794, 466 and 542 as fog-related <b>hints</b>, and 806 as unspecified output. No current-runtime SUMO map, weather value or traffic condition was independently confirmed. Task 22.5B scanned 23 candidate reference files and identified 43 potential references: 14 for 794, 15 for 466, 14 for 542, and none for 806. Task 22.5C reviewed 31 excerpt candidates; the matches primarily document archive identity, pairing and coverage, not verified runtime settings.')
    P('<b>Scientific implication:</b> comparisons here must be indexed by recording identity rather than described as a measured clear-vs-fog or low-vs-high-traffic experiment.')
    H('6. Multi-recording quantitative inspection | Task 22.6')
    P('The same reader analyzed the first 100 frames for each of the four unique pairs, exporting 400 per-frame rows, one recording summary and two plots. Payload presence and timestamp interval estimates were reported separately. Recorded-message interval is a simulated/logged timing property; it is not software compute latency.')
    tbl(['Recording','Camera','LiDAR','Positive radar','Median interval'],[
        (str(r['PairID']),str(r['CameraImageDataFrames']),str(r['LiDARReflectionFrames']),str(r['PositiveRadarFrames']),f"{num(r['MedianMessageIntervalMs']):.4f} ms") for r in coverage
    ],[30*mm,27*mm,27*mm,37*mm,available_w-121*mm])
    fig('task22_06_sensor_coverage.png','Figure 1. Per-recording sensor payload presence in the first 100 messages.')
    fig('task22_06_message_timing.png','Figure 2. Median recorded-message intervals; not CPU/FPGA processing times.')

    newpage()
    H('7. Structural integrity and radar payload rules | Task 22.7')
    P('The validation step independently rechecked frame identifiers, recorded-message timestamps, Camera image data, LiDAR reflection entries and Radar reflection slots. A positive Radar return was defined only as a slot with both time_of_flight and signal_strength greater than zero. This is an operational prefilter, not a validated target-detection metric.')
    tbl(['Recording','Radar slots','Positive returns','Result'],[
        (str(r['PairID']),str(r['TotalRadarReflectionSlots']),str(r['PositiveRadarReturnSlots']),r['Status'].replace('_',' ')) for r in validation
    ],[32*mm,32*mm,35*mm,available_w-99*mm])
    P('All four sampled recordings passed structural checks. Three received preliminary data-check passes. Recording 542 had 100 radar-entry frames and 10,000 reflection slots but no returns satisfying the two-positive-field test; Camera and LiDAR data were missing. This recording is retained as an incomplete-input regression case, not treated as valid three-sensor fusion evidence.')
    P('Recording 806 contained 5,696 positive returns across 100 sampled frames. Task 21 excluded startup frame 0, reducing the relevant corrected-range analysis to 5,614 returns. These are different inclusion rules, not conflicting findings.')
    H('8. Standardized export | Task 22.8A')
    P('Merged frame-level metrics, quality flags and deduplicated recording references into a uniform table for Python and MATLAB. Eligibility required matched message timestamps, structural checks, nonempty Camera image data, LiDAR reflections, positive Radar returns and a non-startup frame. The all-frames export retains incomplete recordings so missing-data handling can be tested.')
    tbl(['Recording','Frames examined','Preliminary candidates','Excluded'],[
        (str(r['PairID']),str(r['FramesExported']),str(r['FusionCandidateFrames']),str(int(num(r['FramesExported'])-num(r['FusionCandidateFrames'])))) for r in candidates
    ],[35*mm,37*mm,50*mm,available_w-122*mm])
    P(f'Total: {total_candidates} preliminary candidate rows from {total_frames} examined rows, with the remaining rows preserved and flagged. The export contains per-frame metadata, not decoded sensor arrays. The term “candidate” must not be interpreted as calibrated sensor-fusion readiness.')
    H('9. Independent MATLAB cross-validation | Task 22.8B')
    P('MATLAB R2026b independently imported all 400 rows and the 297 preselected candidate rows, recomputed the Boolean eligibility conditions, then compared the candidate (recording, frame) keys. It found <b>zero frame-level disagreements</b> and exact candidate-identity agreement, yielding 99 candidate frames for each of recordings 806, 794 and 466 and none for 542. A MATLAB MAT workspace, verification CSV, findings file and three figures were saved.')
    fig('task22_08b_matlab_sensor_coverage.png','Figure 3. Independent MATLAB sensor-availability chart.')
    fig('task22_08b_candidate_comparison.png','Figure 4. MATLAB candidate versus excluded frame counts.')
    fig('task22_08b_frame_eligibility.png','Figure 5. Frame-index eligibility across recording pairs.')

    newpage()
    H('10. Reproducibility and CPU filtering benchmark | Task 22.9')
    P('Three independent CSV rereads reproduced the same 297 candidate keys and candidate-set hash. Pure Python and NumPy vectorized eligibility functions agreed exactly. After warm-up, each implementation was measured in five trials with 1,000 executions per trial, excluding data loading and file I/O.')
    tbl(['Implementation','Median ms/pass','Minimum','Maximum'],[
        (r['Method'],f"{num(r['MedianTimeMs']):.6f}",f"{num(r['MinTimeMs']):.6f}",f"{num(r['MaxTimeMs']):.6f}") for r in timing
    ],[53*mm,37*mm,34*mm,available_w-124*mm])
    P(f'For the sampled 400-row eligibility calculation, NumPy was approximately {ratio:.2f} times faster than the plain Python loop by median execution time. This ranking is specific to the implementation, dataset size and host environment. It does not measure image processing, point-cloud filtering, fusion latency or electrical energy.')
    fig('task22_09_cpu_benchmark.png','Figure 6. Python loop versus NumPy median filter execution time.')
    fig('task22_09_benchmark_trials.png','Figure 7. Execution-time variability across five trials.')
    H('11. Scientific interpretation and limitations')
    bullet('Verified: four distinct tested file pairs, 400 sampled frame records, message-timestamp agreement, source-referenced payload-availability flags and deterministic software candidate selection.')
    bullet('Not verified: exact recording-time map/weather/traffic settings, independently acquired sensor timestamps, decoded image quality, LiDAR spatial geometry or Radar-to-GroundTruth association.')
    bullet('The frame-zero exclusion is a conservative experimental policy; it does not prove every startup frame in every recording is invalid.')
    bullet('The candidate filter is a light-weight metadata decision, not an actual multi-sensor perception/fusion kernel.')
    bullet('No ARM-target benchmarking, FPGA acceleration, power consumption or joule-per-valid-frame measurements were made.')
    H('12. Implications for Tasks 23–50')
    P('The standardized dataset, reproducibility evidence and failure case can now support stronger dataset quality gates, cross-sensor calibration checks and subsequent fusion design. Later ARM–FPGA studies must use actual decoded workloads, validated task-quality metrics, explicit transfer overhead, measured board power and deadline checks. The objective remains energy minimization subject to correctness and safety constraints.')

    newpage()
    H('13. Evidence archive and reproducibility')
    folder_rows=[]
    for name in ['01_Code','02_CSV_Data','03_Graphs','04_Configurations','05_Raw_Data_References','06_Research_Findings','07_Research_Report','08_Processed_Data','09_Benchmark_Results']:
        folder=task/name
        folder_rows.append((name,str(sum(x.is_file() for x in folder.rglob('*'))) if folder.exists() else 'MISSING'))
    tbl(['Task 22 research directory','Files at report build'],folder_rows,[95*mm,available_w-95*mm])
    P('Core reproducibility references: task22_04b_deduplicated_pair_summary.csv; task22_06_frame_metrics.csv; task22_07_validation_summary.csv; task22_08_all_frames.csv; task22_08_fusion_ready_candidates.csv; task22_08b_standardized_dataset.mat; task22_09_reproducibility.csv; task22_09_benchmark_trials.csv; task22_09_benchmark_summary.csv.')
    P('The original OSI recordings remain in their own source directories. The report documents tested subsets, not a full inspection of all frames in all available recordings. Data tables, full source scripts, configuration candidates and original figure PNGs are retained alongside this PDF in the single Task 22 research folder.')
    P(f'<b>Figures embedded:</b> {len(figures)} of 7 expected PNG graphs.')

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE); canvas.line(19.5*mm,15.2*mm,PAGE_WIDTH-19.5*mm,15.2*mm)
        canvas.setFont('Helvetica',7.8); canvas.setFillColor(GREY)
        canvas.drawString(19.5*mm,11.2*mm,'GEMSTAR | Task 22 Final Research')
        canvas.drawRightString(PAGE_WIDTH-19.5*mm,11.2*mm,f'Page {doc.page}')
        canvas.restoreState()
    doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=19.5*mm,rightMargin=19.5*mm,topMargin=18*mm,bottomMargin=21*mm,metadata={'title':'Task 22 Final Research Report','author':'GEMSTAR research workflow'})
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    if not target.exists() or target.stat().st_size<10000: raise RuntimeError('PDF was not generated correctly')
    print('\n=== TASK 22.10B PDF REPORT ===')
    print('Report:',target)
    print('Size (KB):',round(target.stat().st_size/1024,1))
    print('Original figures embedded:',len(figures))
    print('PDF saved:',target.is_file())
    print('=== TASK 22.10B COMPLETE ===')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--task-dir',default=r'E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_22_Final_Research')
    args=parser.parse_args()
    build(args.task_dir)
