import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
T18 = ROOT / "tests" / "Task_18_Final_Research"
T29 = ROOT / "tests" / "Task_29_Final_Research"

DATA18 = T18 / "02_CSV_Data"
LABELS = T18 / "09_GroundTruth_Annotations"
DATA29 = T29 / "02_CSV_Data"

IOU_THRESHOLD = 0.50

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def save_csv(path, rows, fields):
    if path.exists():
        raise FileExistsError(f"Existing research preserved: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def iou(a, b):
    x1 = max(a["x1"], b["x1"])
    y1 = max(a["y1"], b["y1"])
    x2 = min(a["x2"], b["x2"])
    y2 = min(a["y2"], b["y2"])

    intersection = max(0, x2-x1) * max(0, y2-y1)

    area_a = max(0, a["x2"]-a["x1"]) * max(0, a["y2"]-a["y1"])
    area_b = max(0, b["x2"]-b["x1"]) * max(0, b["y2"]-b["y1"])

    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0

def normalize_prediction(row):
    return {
        "class": row["ClassName"].strip().lower(),
        "confidence": float(row["Confidence"]),
        "x1": float(row["X1"]),
        "y1": float(row["Y1"]),
        "x2": float(row["X2"]),
        "y2": float(row["Y2"])
    }

def normalize_reference(obj):
    return {
        "class": str(obj["class"]).strip().lower(),
        "x1": float(obj["x1"]),
        "y1": float(obj["y1"]),
        "x2": float(obj["x2"]),
        "y2": float(obj["y2"])
    }

def evaluate(refs, preds):
    candidates = []

    for pi, p in enumerate(preds):
        for ri, r in enumerate(refs):
            if p["class"] != r["class"]:
                continue

            score = iou(p, r)
            if score >= IOU_THRESHOLD:
                candidates.append(
                    (score, p["confidence"], pi, ri)
                )

    candidates.sort(reverse=True)

    matched_preds = set()
    matched_refs = set()

    for score, confidence, pi, ri in candidates:
        if pi in matched_preds or ri in matched_refs:
            continue
        matched_preds.add(pi)
        matched_refs.add(ri)

    tp = len(matched_preds)
    fp = len(preds) - tp
    fn = len(refs) - tp
    return tp, fp, fn

def main():
    manifest = read_csv(DATA18 / "task18_annotation_manifest.csv")
    frames = sorted({int(r["Frame"]) for r in manifest})

    sources = {
        "YOLO11n": DATA18 / "task18_yolo_detections.csv",
        "YOLO11s": DATA18 / "task18_yolo11s_detections.csv"
    }

    model_predictions = {}

    for name, path in sources.items():
        grouped = defaultdict(list)
        for row in read_csv(path):
            grouped[int(row["Frame"])].append(
                normalize_prediction(row)
            )
        model_predictions[name] = grouped

    frame_rows = []
    summary_rows = []

    for name, grouped in model_predictions.items():
        totals = {"TP": 0, "FP": 0, "FN": 0}

        for frame in frames:
            label_path = LABELS / f"task18_labels_frame_{frame:03d}.json"
            annotation = json.loads(label_path.read_text(encoding="utf-8-sig"))

            if not (
                annotation.get("reviewed") is True and
                annotation.get("annotation_source") == "MANUAL"
            ):
                raise RuntimeError(
                    f"Annotation not marked manually reviewed: {frame}"
                )

            refs = [
                normalize_reference(obj)
                for obj in annotation["objects"]
            ]

            preds = grouped.get(frame, [])
            tp, fp, fn = evaluate(refs, preds)

            for key, value in (("TP", tp), ("FP", fp), ("FN", fn)):
                totals[key] += value

            frame_rows.append({
                "Model": name,
                "Frame": frame,
                "ReferenceObjects": len(refs),
                "Predictions": len(preds),
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "IoUThreshold": IOU_THRESHOLD,
                "EvidenceStatus": "PROVISIONAL_MANUAL_JSON"
            })

        tp, fp, fn = totals["TP"], totals["FP"], totals["FN"]

        precision = tp / (tp+fp) if tp+fp else 0.0
        recall = tp / (tp+fn) if tp+fn else 0.0
        f1 = (
            2*precision*recall/(precision+recall)
            if precision+recall else 0.0
        )

        summary_rows.append({
            "Model": name,
            "Frames": len(frames),
            "ReferenceObjects": tp+fn,
            "Predictions": tp+fp,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "Precision": round(precision, 6),
            "Recall": round(recall, 6),
            "F1": round(f1, 6),
            "IoUThreshold": IOU_THRESHOLD,
            "EvidenceStatus": "PROVISIONAL_MANUAL_JSON"
        })

    frame_out = DATA29 / "task29_4C12D5E8B_frame_quality.csv"
    summary_out = DATA29 / "task29_4C12D5E8B_model_quality.csv"

    if frame_out.exists() or summary_out.exists():
        raise FileExistsError(
            "Existing results detected; nothing overwritten."
        )

    save_csv(
        frame_out,
        frame_rows,
        [
            "Model", "Frame", "ReferenceObjects",
            "Predictions", "TP", "FP", "FN",
            "IoUThreshold", "EvidenceStatus"
        ]
    )

    save_csv(
        summary_out,
        summary_rows,
        [
            "Model", "Frames", "ReferenceObjects",
            "Predictions", "TP", "FP", "FN",
            "Precision", "Recall", "F1",
            "IoUThreshold", "EvidenceStatus"
        ]
    )

    print("\n=== TASK 29.4C.12D.5E.8B: MODEL QUALITY ===")
    for row in summary_rows:
        print(
            f'{row["Model"]}: '
            f'TP={row["TP"]}, FP={row["FP"]}, FN={row["FN"]}, '
            f'Precision={row["Precision"]:.3f}, '
            f'Recall={row["Recall"]:.3f}, '
            f'F1={row["F1"]:.3f}'
        )

    print("Evidence: PROVISIONAL")
    print("Original Task 18 research modified: NO")
    print("TASK 29.4C.12D.5E.8B: COMPLETE")

if __name__ == "__main__":
    main()
