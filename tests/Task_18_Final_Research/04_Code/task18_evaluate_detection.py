from pathlib import Path
import csv
import json

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

LABELS = BASE / "09_GroundTruth_Annotations"
CSV_DIR = BASE / "02_CSV_Data"

SOURCES = {
    "YOLO11_Nano": CSV_DIR / "task18_yolo_detections.csv",
    "YOLO11_Small": CSV_DIR / "task18_yolo11s_detections.csv",
}

FRAMES = [0, 50, 100, 150, 200, 250, 300,
          350, 400, 423, 424, 450]

def iou(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    intersection = max(0, x2-x1) * max(0, y2-y1)

    area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])

    union = area_a + area_b - intersection

    return intersection / union if union > 0 else 0.0

def reference_boxes(frame):
    path = LABELS / f"task18_labels_frame_{frame:03d}.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("reviewed") is not True:
        raise ValueError(f"Frame {frame} not reviewed")

    return [
        {
            "class": obj["class"],
            "box": [
                float(obj[k])
                for k in ["x1", "y1", "x2", "y2"]
            ]
        }
        for obj in data["objects"]
    ]

def predictions_from_csv(path):
    result = {f: [] for f in FRAMES}

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            frame = int(row["Frame"])
            if frame not in result:
                continue

            result[frame].append({
                "class": row["ClassName"],
                "confidence": float(row["Confidence"]),
                "box": [
                    float(row[k])
                    for k in ["X1", "Y1", "X2", "Y2"]
                ]
            })
    return result

def evaluate(refs, predictions, class_aware=True):
    # Confidence-ordered greedy matching.
    used_refs = set()
    tp = 0
    fp = 0

    for pred in sorted(
        predictions,
        key=lambda x: x["confidence"],
        reverse=True
    ):
        candidates = []

        for idx, ref in enumerate(refs):
            if idx in used_refs:
                continue

            if class_aware and pred["class"] != ref["class"]:
                continue

            score = iou(pred["box"], ref["box"])

            if score >= 0.50:
                candidates.append((score, idx))

        if candidates:
            _, best_idx = max(candidates)
            used_refs.add(best_idx)
            tp += 1
        else:
            fp += 1

    return tp, fp, len(refs) - tp

rows = []

for model_name, source in SOURCES.items():
    predictions = predictions_from_csv(source)

    totals = {"tp": 0, "fp": 0, "fn": 0}
    localization_tp = 0

    for frame in FRAMES:
        refs = reference_boxes(frame)
        preds = predictions[frame]

        tp, fp, fn = evaluate(refs, preds, True)
        loc_tp, _, _ = evaluate(refs, preds, False)

        totals["tp"] += tp
        totals["fp"] += fp
        totals["fn"] += fn
        localization_tp += loc_tp

        rows.append({
            "Model": model_name,
            "Frame": frame,
            "ReferenceObjects": len(refs),
            "Predictions": len(preds),
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "LocalizationTP": loc_tp,
        })

    tp = totals["tp"]
    fp = totals["fp"]
    fn = totals["fn"]

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    print(f"\n=== {model_name} ===")
    print("True positives:", tp)
    print("False positives:", fp)
    print("False negatives:", fn)
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("Localization matches:", localization_tp)

output = CSV_DIR / "task18_detection_evaluation.csv"

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== TASK 18.7G COMPLETE ===")
print("Frames evaluated:", len(FRAMES))
print("Models evaluated:", len(SOURCES))
print("Evaluation CSV saved:", output.exists())
print("Output:", output)
