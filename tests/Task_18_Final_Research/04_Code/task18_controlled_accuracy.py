from pathlib import Path
import csv
import json

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Final_Research"
)

CSV_DIR = BASE / "02_CSV_Data"
LABEL_DIR = BASE / "09_GroundTruth_Annotations"

PREDICTIONS = CSV_DIR / "task18_controlled_predictions.csv"
MANIFEST = CSV_DIR / "task18_annotation_manifest.csv"

OUTPUT = CSV_DIR / "task18_controlled_accuracy_results.csv"
DETAILS = CSV_DIR / "task18_controlled_accuracy_by_frame.csv"

IOU_THRESHOLD = 0.50

def iou(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    intersection = max(0, x2-x1) * max(0, y2-y1)

    area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])

    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0

def match_objects(refs, preds, check_class=True):
    used = set()
    tp = 0

    for pred in sorted(
        preds,
        key=lambda x: x["confidence"],
        reverse=True
    ):
        candidates = []

        for index, ref in enumerate(refs):
            if index in used:
                continue

            if check_class and pred["class"] != ref["class"]:
                continue

            overlap = iou(pred["box"], ref["box"])

            if overlap >= IOU_THRESHOLD:
                candidates.append((overlap, index))

        if candidates:
            _, best = max(candidates)
            used.add(best)
            tp += 1

    return tp, len(preds) - tp, len(refs) - tp

with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
    frames = [int(r["Frame"]) for r in csv.DictReader(f)]

with PREDICTIONS.open("r", encoding="utf-8-sig", newline="") as f:
    prediction_rows = list(csv.DictReader(f))

reference = {}

for frame in frames:
    path = LABEL_DIR / f"task18_labels_frame_{frame:03d}.json"

    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("reviewed") is not True:
        raise RuntimeError(f"Frame {frame} not reviewed")

    reference[frame] = [
        {
            "class": obj["class"],
            "box": [
                float(obj[k])
                for k in ("x1", "y1", "x2", "y2")
            ]
        }
        for obj in data["objects"]
    ]

details = []
summary = []

for model in ["yolo11n", "yolo11s"]:
    tp_total = fp_total = fn_total = 0
    loc_total = 0

    for frame in frames:
        refs = reference[frame]

        preds = [
            {
                "class": r["ClassName"],
                "confidence": float(r["Confidence"]),
                "box": [
                    float(r[k])
                    for k in ("X1", "Y1", "X2", "Y2")
                ]
            }
            for r in prediction_rows
            if r["Model"] == model and int(r["Frame"]) == frame
        ]

        tp, fp, fn = match_objects(refs, preds, True)
        loc, _, _ = match_objects(refs, preds, False)

        tp_total += tp
        fp_total += fp
        fn_total += fn
        loc_total += loc

        details.append({
            "Model": model,
            "Frame": frame,
            "ReferenceObjects": len(refs),
            "Predictions": len(preds),
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "LocalizationMatches": loc
        })

    precision = (
        tp_total / (tp_total + fp_total)
        if tp_total + fp_total else 0
    )

    recall = (
        tp_total / (tp_total + fn_total)
        if tp_total + fn_total else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    summary.append({
        "Model": model,
        "TP": tp_total,
        "FP": fp_total,
        "FN": fn_total,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "LocalizationMatches": loc_total
    })

def save_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

save_csv(OUTPUT, summary)
save_csv(DETAILS, details)

print("\n=== TASK 18.7L CONTROLLED ACCURACY ===")

for r in summary:
    print(f"\nModel: {r['Model']}")
    print("TP:", r["TP"])
    print("FP:", r["FP"])
    print("FN:", r["FN"])
    print("Precision:", round(r["Precision"] * 100, 2), "%")
    print("Recall:", round(r["Recall"] * 100, 2), "%")
    print("F1:", round(r["F1"] * 100, 2), "%")
    print("Localization matches:", r["LocalizationMatches"])

print("\nSummary CSV saved:", OUTPUT.exists())
print("Per-frame CSV saved:", DETAILS.exists())
