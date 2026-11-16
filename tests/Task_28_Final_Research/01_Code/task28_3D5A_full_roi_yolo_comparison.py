import csv
import hashlib
import math
import statistics
import time
from collections import defaultdict
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests/Task_28_Final_Research"
DATA = TASK / "02_CSV_Data"
PLOTS = TASK / "04_Plots/Camera_YOLO_Comparison"
FINDINGS = TASK / "06_Research_Findings"

MANIFEST = DATA / "task28_3D4B2_camera_image_manifest.csv"

MODEL = (
    ROOT / "tests/Task_18_Final_Research"
    / "03_Configurations/Models/yolo11s.pt"
)

EXPECTED_HASH = (
    "85A76FE86DD8AFE384648546B56A7A78580C7CB7B404FC595F97969322D502D5"
)

TIMING = DATA / "task28_3D5A_full_roi_timing.csv"
FRAMES = DATA / "task28_3D5A_full_roi_frame_comparison.csv"
SUMMARY = DATA / "task28_3D5A_full_roi_scenario_summary.csv"
REPORT = FINDINGS / "task28_3D5A_full_roi_findings.txt"

ROI_X, ROI_Y = 128, 96
ROI_W, ROI_H = 384, 288

REPEATS = 5
WARMUPS = 2
CONF = 0.15
IMGSZ = 640
IOU_THRESHOLD = 0.5

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_mor100",
    "fog_postfix_validation"
]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1048576), b""):
            h.update(part)
    return h.hexdigest().upper()


def infer(model, image):
    result = model.predict(
        source=image,
        imgsz=IMGSZ,
        conf=CONF,
        device="cpu",
        verbose=False,
        save=False
    )
    if len(result) != 1:
        raise RuntimeError("Expected one result")
    return result[0]


def boxes(result, dx=0, dy=0):
    output = []
    for b in result.boxes:
        coords = [float(x) for x in b.xyxy[0].tolist()]
        output.append({
            "class": int(b.cls[0].item()),
            "conf": float(b.conf[0].item()),
            "xyxy": [
                coords[0] + dx,
                coords[1] + dy,
                coords[2] + dx,
                coords[3] + dy
            ]
        })
    return output


def iou(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    intersection = (
        max(0.0, x2-x1) * max(0.0, y2-y1)
    )

    area_a = max(0.0, a[2]-a[0]) * max(0.0, a[3]-a[1])
    area_b = max(0.0, b[2]-b[0]) * max(0.0, b[3]-b[1])

    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def inside_roi(box):
    x1, y1, x2, y2 = box
    return (
        x1 >= ROI_X and y1 >= ROI_Y
        and x2 <= ROI_X + ROI_W
        and y2 <= ROI_Y + ROI_H
    )


def matched_count(full, roi):
    # One-to-one greedy matching with same class and IoU >= 0.5.
    pairs = []

    for i, a in enumerate(full):
        for j, b in enumerate(roi):
            if a["class"] == b["class"]:
                overlap = iou(a["xyxy"], b["xyxy"])
                if overlap >= IOU_THRESHOLD:
                    pairs.append((overlap, i, j))

    pairs.sort(reverse=True)
    used_full = set()
    used_roi = set()

    for overlap, i, j in pairs:
        if i not in used_full and j not in used_roi:
            used_full.add(i)
            used_roi.add(j)

    return len(used_full)


def percentile(values, p):
    s = sorted(values)
    pos = (len(s)-1)*p
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi]-s[lo])*(pos-lo)


def main():
    outputs = [TIMING, FRAMES, SUMMARY, REPORT]
    if any(p.exists() for p in outputs):
        raise RuntimeError("Output exists; preserving prior work")

    if not MANIFEST.is_file():
        raise RuntimeError("Camera image manifest missing")

    if not MODEL.is_file() or sha256(MODEL) != EXPECTED_HASH:
        raise RuntimeError("Original Task 26 YOLO weights not verified")

    with MANIFEST.open("r", newline="", encoding="utf-8-sig") as f:
        manifest = list(csv.DictReader(f))

    if len(manifest) != 20:
        raise RuntimeError("Expected exactly 20 source images")

    torch.set_num_threads(4)
    cv2.setNumThreads(1)

    model = YOLO(str(MODEL))

    timings = []
    frame_rows = []

    for index, entry in enumerate(manifest, 1):
        scenario = entry["Scenario"]
        frame = int(entry["Frame"])
        path = Path(entry["OutputPNG"])

        if scenario not in SCENARIOS or not path.is_file():
            raise RuntimeError("Invalid manifest entry")

        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None or image.shape[:2] != (480, 640):
            raise RuntimeError(f"Invalid image: {path}")

        # Verify the input matches the source OSI image bytes
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if (
            hashlib.sha256(rgb.tobytes()).hexdigest().lower()
            != entry["ImageSHA256"].lower()
        ):
            raise RuntimeError(f"Input hash mismatch: {path}")

        roi_image = image[
            ROI_Y:ROI_Y+ROI_H,
            ROI_X:ROI_X+ROI_W
        ].copy()

        mode_images = [
            ("FULL", image),
            ("ROI", roi_image)
        ]

        results_by_mode = {}
        median_by_mode = {}

        # Alternate first mode across images to limit order bias.
        if index % 2 == 0:
            mode_images.reverse()

        for mode, source_image in mode_images:
            for _ in range(WARMUPS):
                infer(model, source_image)

            times = []
            counts = []
            result = None

            for repeat in range(1, REPEATS+1):
                start = time.perf_counter_ns()
                result = infer(model, source_image)
                elapsed = (time.perf_counter_ns()-start)/1e6

                times.append(elapsed)
                counts.append(len(result.boxes))

                timings.append({
                    "Scenario": scenario,
                    "Frame": frame,
                    "Mode": mode,
                    "Repeat": repeat,
                    "Elapsed_ms": round(elapsed, 6),
                    "Detections": len(result.boxes),
                })

            if len(set(counts)) != 1:
                print(
                    f"WARNING: variable detections "
                    f"{scenario}/{frame}/{mode}"
                )

            offset_x = ROI_X if mode == "ROI" else 0
            offset_y = ROI_Y if mode == "ROI" else 0

            results_by_mode[mode] = boxes(
                result, offset_x, offset_y
            )
            median_by_mode[mode] = statistics.median(times)

        full = results_by_mode["FULL"]
        roi = results_by_mode["ROI"]

        full_inside = [
            box for box in full
            if inside_roi(box["xyxy"])
        ]

        matched = matched_count(full_inside, roi)

        frame_rows.append({
            "Scenario": scenario,
            "Frame": frame,
            "FullDetections": len(full),
            "FullBoxesFullyInsideROI": len(full_inside),
            "ROIDetections": len(roi),
            "MatchedFullInsideROI": matched,
            "FullMedian_ms": round(median_by_mode["FULL"], 5),
            "ROIMedian_ms": round(median_by_mode["ROI"], 5),
            "ROIDividedByFullLatency": round(
                median_by_mode["ROI"] /
                median_by_mode["FULL"], 5
            ),
        })

        print(
            f"[{index:02d}/20] {scenario} frame={frame} "
            f"FULL={len(full)} ROI={len(roi)} "
            f"match={matched}/{len(full_inside)} "
            f"median(F/R)="
            f"{median_by_mode['FULL']:.2f}/"
            f"{median_by_mode['ROI']:.2f}ms",
            flush=True
        )

    summary_rows = []

    for scenario in SCENARIOS:
        rows = [
            r for r in frame_rows
            if r["Scenario"] == scenario
        ]

        if len(rows) != 5:
            raise RuntimeError(f"Unexpected scenario count: {scenario}")

        full_count = sum(r["FullDetections"] for r in rows)
        inside_count = sum(
            r["FullBoxesFullyInsideROI"] for r in rows
        )
        roi_count = sum(r["ROIDetections"] for r in rows)
        matched = sum(r["MatchedFullInsideROI"] for r in rows)

        summary_rows.append({
            "Scenario": scenario,
            "Images": len(rows),
            "FullDetections": full_count,
            "FullBoxesInsideROI": inside_count,
            "ROIDetections": roi_count,
            "MatchedFullInsideROI": matched,
            "MatchedOfInsidePct": (
                round(100*matched/inside_count, 3)
                if inside_count else ""
            ),
            "MeanFullMedian_ms": round(
                statistics.mean(r["FullMedian_ms"] for r in rows), 5
            ),
            "MeanROIMedian_ms": round(
                statistics.mean(r["ROIMedian_ms"] for r in rows), 5
            ),
        })

    for path, rows in [
        (TIMING, timings),
        (FRAMES, frame_rows),
        (SUMMARY, summary_rows)
    ]:
        with path.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    report_lines = [
        "TASK 28.3D.5A - FULL/ROI YOLO PAIRED PILOT",
        "==========================================",
        f"Model SHA256: {EXPECTED_HASH}",
        "Images: 20, four scenarios, five each",
        "ROI: centered x=128, y=96, width=384, height=288",
        "Full frame: 640x480",
        "YOLO imgsz: 640; confidence: 0.15; device: CPU",
        f"Warmups/mode/image: {WARMUPS}",
        f"Timed repeats/mode/image: {REPEATS}",
        "Comparison: same image, same YOLO weights and threshold",
        "ROI bounding boxes translated to full-frame coordinates",
        "Matching: same class, one-to-one, IoU >= 0.5",
        "",
        "LIMITATIONS",
        "FULL and ROI are different detector inputs.",
        "Matching measures consistency, not precision or recall.",
        "Fully-inside-ROI criterion excludes boundary crossings.",
        "YOLO resizes inputs; ROI is not guaranteed faster.",
        "Five images per scenario are not a matched weather study.",
        "No measured energy savings or independent accuracy labels.",
        "Workstation CPU timings are not KR260 timings.",
        "",
        "STATUS: TASK 28.3D.5A COMPLETE"
    ]

    REPORT.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8"
    )

    print("\n=== TASK 28.3D.5A FULL VS ROI RESULTS ===")

    for row in summary_rows:
        print(f"\nScenario: {row['Scenario']}")
        print(f"FULL boxes: {row['FullDetections']}")
        print(f"FULL boxes inside ROI: {row['FullBoxesInsideROI']}")
        print(f"ROI boxes: {row['ROIDetections']}")
        print(f"Matched inside-ROI boxes: {row['MatchedFullInsideROI']}")
        print(
            f"Mean FULL median latency: "
            f"{row['MeanFullMedian_ms']:.3f} ms"
        )
        print(
            f"Mean ROI median latency: "
            f"{row['MeanROIMedian_ms']:.3f} ms"
        )

    print(f"\nTimed CPU observations: {len(timings)}")
    print(f"Frame comparison CSV: {FRAMES}")
    print(f"Scenario summary CSV: {SUMMARY}")
    print(f"Research findings: {REPORT}")
    print("ACCURACY_VALIDATED: NO")
    print("ENERGY_MEASURED: NO")
    print("STATUS: TASK 28.3D.5A SUCCESS")


if __name__ == "__main__":
    main()
