from pathlib import Path
import csv, hashlib, json, struct

TESTS = Path(r'E:\GEMSTAR_Project\sensor-health-monitor\tests')
# Explicit Windows paths are built from the mounted E: drive, as in existing Task 26 scripts.
T23 = TESTS / 'Task_23_Final_Research'
T24 = TESTS / 'Task_24_Final_Research'
T26 = TESTS / 'Task_26_Final_Research'
T27 = TESTS / 'Task_27_Final_Research'
WEATHER = T23 / '08_Processed_Data' / 'Camera_Weather_Comparison'
YOLO_IMAGES = T24 / '09_Controlled_Scenario' / 'C02_MovingTarget' / 'Camera_NoVisualizer_V2_2122'
MODEL = TESTS / 'Task_18_Final_Research' / '03_Configurations' / 'Models' / 'yolo11s.pt'
WEATHER_FILES = [('CLEAR', 'CLEAR_t0200ms.png'), ('FOG100','FOG100_t0200ms.png'),('FOG20','FOG20_t0200ms.png')]
YOLO_FILES = [(0,'clean_camera_01_frame00000.png'),(530,'clean_camera_02_frame00530.png'),(1060,'clean_camera_03_frame01060.png'),(1591,'clean_camera_04_frame01591.png'),(2121,'clean_camera_05_frame02121.png')]
OUT = T27 / '02_CSV_Data' / 'task27_2B_camera_yolo_input_volume.csv'
REPORT = T27 / '06_Research_Findings' / 'task27_2B_camera_yolo_input_volume_report.json'

def sha256(p):
    d = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            d.update(b)
    return d.hexdigest().upper()

def png_dims(p):
    with p.open('rb') as f:
        h = f.read(29)
    if len(h) < 29 or h[:8] != b'\x89PNG\r\n\x1a\n' or h[12:16] != b'IHDR':
        raise ValueError(f'Not a supported PNG: {p}')
    w, hgt = struct.unpack('>II', h[16:24])
    if w < 1 or hgt < 1:
        raise ValueError(f'Invalid PNG dimensions: {p}')
    return w, hgt

def get_report(p):
    if not p.is_file():
        raise FileNotFoundError(f'Missing archived benchmark report: {p}')
    return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    print('=== TASK 27.2B: CAMERA AND YOLO INPUT VOLUME AUDIT ===')
    if OUT.exists() or REPORT.exists():
        raise FileExistsError('Previous Task 27.2B output preserved; no overwrite')
    camera_report = get_report(T26 / '06_Research_Findings' / 'task26_4B_camera_cpu_report.json')
    yolo_report = get_report(T26 / '06_Research_Findings' / 'task26_4J_yolo_cpu_report.json')
    archived_camera = {Path(r['path']).name: r for r in camera_report['image_manifest']}
    archived_yolo = {k: v.upper() for k, v in yolo_report['image_hashes'].items()}
    rows = []
    hashes_ok = 0
    for weather, name in WEATHER_FILES:
        p = WEATHER / name
        if not p.is_file(): raise FileNotFoundError(p)
        width, height = png_dims(p)
        digest = sha256(p)
        ref = archived_camera.get(name)
        if ref is None: raise RuntimeError(f'Missing archived camera manifest: {name}')
        if digest != ref['sha256'].upper() or width != int(ref['width']) or height != int(ref['height']):
            raise RuntimeError(f'Archived camera input mismatch: {name}')
        hashes_ok += 1
        for mode, pixels in [('FULL', width * height), ('ROI', 384 * 288)]:
            if mode == 'ROI' and (width < 384 or height < 288): continue
            rows.append(dict(workload='camera_preprocessing',case=weather,frame='',filename=name,mode=mode,
                width=width,height=height,processed_pixels=pixels,uncompressed_bgr_input_bytes=pixels*3,
                grayscale_output_bytes=pixels,edges_output_bytes=pixels,
                on_disk_png_bytes=p.stat().st_size,sha256=digest,
                buffer_note='Nominal uint8 array sizes; excludes HSV, Laplacian, temporaries and copies'))
        print(f'CAMERA {weather}: {width}x{height}; FULL_BGR_BYTES={width*height*3}; ROI_BGR_BYTES={384*288*3}; SHA256=PASS')
    for frame, name in YOLO_FILES:
        p = YOLO_IMAGES / name
        if not p.is_file(): raise FileNotFoundError(p)
        width, height = png_dims(p)
        digest = sha256(p)
        if archived_yolo.get(name) != digest: raise RuntimeError(f'Archived YOLO input mismatch: {name}')
        hashes_ok += 1
        rows.append(dict(workload='yolo11s_input',case='',frame=frame,filename=name,mode='IMAGE',
            width=width,height=height,processed_pixels=width*height,uncompressed_bgr_input_bytes=width*height*3,
            grayscale_output_bytes='',edges_output_bytes='',on_disk_png_bytes=p.stat().st_size,sha256=digest,
            buffer_note='Original uint8 BGR image; imgsz=640 is an inference setting, not proof of a 640x640 tensor shape'))
        print(f'YOLO FRAME {frame}: {width}x{height}; INPUT_BGR_BYTES={width*height*3}; SHA256=PASS')
    if not MODEL.is_file(): raise FileNotFoundError(MODEL)
    model_hash = sha256(MODEL)
    if model_hash != yolo_report['model_sha256'].upper():
        raise RuntimeError('YOLO model differs from frozen Task 26 benchmark')
    print(f'MODEL_FILE_BYTES: {MODEL.stat().st_size}')
    print('MODEL_SHA256: PASS')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader();writer.writerows(rows)
    report=dict(task='27.2B',status='PASS',camera_images=3,camera_modes=sum(r['workload']=='camera_preprocessing' for r in rows),
        yolo_images=5,source_images_hash_matched=hashes_ok,model_file_bytes=MODEL.stat().st_size,
        model_sha256=model_hash,model_configured_imgsz=640,source_rows=len(rows),
        measurement='Nominal data volume only; not measured memory traffic, operations, peak RAM, bandwidth, FPGA transfer or energy',
        output_csv=str(OUT))
    with REPORT.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(f'CAMERA_CONFIGURATIONS: {report["camera_modes"]}')
    print('YOLO_IMAGES: 5')
    print(f'ARCHIVED_SOURCE_IMAGE_HASHES_MATCHED: {hashes_ok}')
    print(f'OUTPUT_ROWS: {len(rows)}')
    print('MODEL_HASH_VERIFIED: YES')
    print('OUTPUT:',OUT)
    print('TASK27_2B_CAMERA_YOLO_VOLUME_AUDIT_DONE')

if __name__=='__main__':main()
