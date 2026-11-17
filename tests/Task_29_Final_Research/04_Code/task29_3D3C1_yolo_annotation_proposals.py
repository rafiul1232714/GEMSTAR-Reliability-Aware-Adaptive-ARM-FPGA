import csv
import hashlib
import json
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK29 = ROOT / "tests" / "Task_29_Final_Research"

MANIFEST = (
    ROOT / "tests" / "Task_28_Final_Research"
    / "02_CSV_Data" / "task28_3D4B2_camera_image_manifest.csv"
)

MODEL_PATH = (
    ROOT / "tests" / "Task_18_Final_Research"
    / "03_Configurations" / "Models" / "yolo11s.pt"
)

PROPOSAL_DIR = (
    TASK29 / "03_Configurations"
    / "Camera_YOLO_Proposals"
)

GRAPH_DIR = (
    TASK29 / "01_Graphs"
    / "Camera_YOLO_Proposal_Review"
)

CSV_PATH = (
    TASK29 / "02_CSV_Data"
    / "task29_3D3C1_yolo_proposals.csv"
)

REPORT_PATH = (
    TASK29 / "06_Research_Findings"
    / "task29_3D3C1_proposal_report.json"
)

EXPECTED_HASH = (
    "85A76FE86DD8AFE384648546B56A7A78580C7CB7B404FC595F97969322D502D5"
)

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_mor100",
    "fog_postfix_validation",
]

# Lower threshold for review proposals only.
# Not an accuracy benchmark operating threshold.
CONF = 0.10
IMGSZ = 640
IOU = 0.70

# Main research object classes.
TARGET_CLASSES = {
    "car", "truck", "bus", "person",
    "bicycle", "motorcycle"
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def load_inputs():
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 20:
        raise RuntimeError("Expected 20 Camera images")

    pairs = [(r["Scenario"], int(r["Frame"])) for r in rows]

    if len(set(pairs)) != 20:
        raise RuntimeError("Duplicate scenario/frame entries")

    if set(r["Scenario"] for r in rows) != set(SCENARIOS):
        raise RuntimeError("Unexpected scenarios")

    for scenario in SCENARIOS:
        if sum(r["Scenario"] == scenario for r in rows) != 5:
            raise RuntimeError("Expected five images per scenario")

    return rows

def main():
    print("=== TASK 29.3D.3C.1: YOLO-ASSISTED ANNOTATION ===", flush=True)

    model_hash = sha256(MODEL_PATH)

    if model_hash != EXPECTED_HASH:
        raise RuntimeError("YOLO11s model SHA256 mismatch")

    manifest = load_inputs()

    # Preserve any previously generated research results.
    if CSV_PATH.exists() or REPORT_PATH.exists():
        raise FileExistsError(
            "Proposal output already exists; no overwrite performed"
        )

    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    torch.set_num_threads(4)
    cv2.setNumThreads(1)

    model = YOLO(str(MODEL_PATH))

    model.predict(
        source=cv2.imread(manifest[0]["OutputPNG"]),
        imgsz=IMGSZ,
        conf=CONF,
        device="cpu",
        verbose=False,
    )

    all_csv_rows = []
    reviewed_images = {}

    for scenario in SCENARIOS:
        reviewed_images[scenario] = []

        items = sorted(
            (r for r in manifest if r["Scenario"] == scenario),
            key=lambda r: int(r["Frame"])
        )

        for item in items:
            frame = int(item["Frame"])
            path = Path(item["OutputPNG"])

            if not path.is_file():
                raise FileNotFoundError(path)

            img = cv2.imread(str(path))

            if img is None or img.shape[:2] != (480, 640):
                raise RuntimeError("Invalid Camera image: " + str(path))

            # Verify pixel provenance against the original manifest.
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pixel_hash = hashlib.sha256(rgb.tobytes()).hexdigest()

            if pixel_hash.lower() != item["ImageSHA256"].lower():
                raise RuntimeError("Image pixel hash mismatch: " + str(path))

            result = model.predict(
                source=img,
                imgsz=IMGSZ,
                conf=CONF,
                iou=IOU,
                device="cpu",
                agnostic_nms=True,
                verbose=False,
                save=False,
            )[0]

            proposals = []
            display_img = img.copy()

            for box in result.boxes:
                class_id = int(box.cls[0].item())
                class_name = str(model.names[class_id])
                confidence = float(box.conf[0].item())
                x1, y1, x2, y2 = [
                    float(v) for v in box.xyxy[0].tolist()
                ]

                proposal = {
                    "class": class_name,
                    "class_id": class_id,
                    "confidence": confidence,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "target_class": class_name in TARGET_CLASSES,
                }
                proposals.append(proposal)

                all_csv_rows.append({
                    "Scenario": scenario,
                    "Frame": frame,
                    "Class": class_name,
                    "Confidence": round(confidence, 6),
                    "X1": round(x1, 2),
                    "Y1": round(y1, 2),
                    "X2": round(x2, 2),
                    "Y2": round(y2, 2),
                    "TargetClass": class_name in TARGET_CLASSES,
                })

                # Green = one of our target classes.
                # Orange = another predicted class; review separately.
                color = (
                    (0, 190, 0)
                    if class_name in TARGET_CLASSES
                    else (0, 140, 255)
                )

                cv2.rectangle(
                    display_img,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    color, 2
                )

                label = "{} {:.2f}".format(class_name, confidence)

                cv2.putText(
                    display_img,
                    label,
                    (max(0, int(x1)), max(18, int(y1) - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, color, 2, cv2.LINE_AA
                )

            proposal_path = PROPOSAL_DIR / (
                f"task29_proposal_{scenario}_frame{frame:05d}.json"
            )

            if proposal_path.exists():
                raise FileExistsError(proposal_path)

            proposal_record = {
                "task": "29.3D.3C.1",
                "scenario": scenario,
                "frame": frame,
                "source_image": str(path),
                "image_sha256": item["ImageSHA256"],
                "model": "yolo11s",
                "model_sha256": model_hash,
                "confidence_threshold": CONF,
                "inference_image_size": IMGSZ,
                "status": "UNREVIEWED_MODEL_PROPOSAL",
                "is_ground_truth": False,
                "proposals": proposals,
            }

            with proposal_path.open("x", encoding="utf-8") as f:
                json.dump(proposal_record, f, indent=2)

            # Single-image preview for easier detailed review.
            annotated_path = GRAPH_DIR / (
                f"task29_proposal_{scenario}_frame{frame:05d}.png"
            )

            if annotated_path.exists():
                raise FileExistsError(annotated_path)

            if not cv2.imwrite(str(annotated_path), display_img):
                raise RuntimeError("Failed to save preview")

            header = 42
            tile = cv2.copyMakeBorder(
                display_img, header, 0, 0, 0,
                cv2.BORDER_CONSTANT,
                value=(245, 245, 245)
            )

            cv2.putText(
                tile,
                f"Frame {frame} | {len(proposals)} proposals",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (25, 25, 25), 2, cv2.LINE_AA
            )

            reviewed_images[scenario].append(tile)

            print(
                f"{scenario} | Frame {frame} | "
                f"YOLO proposals: {len(proposals)}",
                flush=True
            )

    # Four scenario sheets, five images each.
    for scenario in SCENARIOS:
        tiles = reviewed_images[scenario]

        if len(tiles) != 5:
            raise RuntimeError("Contact sheet image count mismatch")

        empty = 255 * __import__("numpy").ones_like(tiles[0])

        upper = cv2.hconcat(tiles[:3])
        lower = cv2.hconcat(tiles[3:] + [empty])
        sheet = cv2.vconcat([upper, lower])

        sheet_path = GRAPH_DIR / (
            f"task29_3D3C1_{scenario}_proposals.png"
        )

        if sheet_path.exists():
            raise FileExistsError(sheet_path)

        if not cv2.imwrite(str(sheet_path), sheet):
            raise RuntimeError("Contact sheet write failure")

        print("SAVED CONTACT SHEET:", sheet_path.name, flush=True)

    fields = [
        "Scenario", "Frame", "Class", "Confidence",
        "X1", "Y1", "X2", "Y2", "TargetClass"
    ]

    with CSV_PATH.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_csv_rows)

    report = {
        "task": "29.3D.3C.1",
        "model": "yolo11s",
        "model_sha256": model_hash,
        "images_reviewed_by_model": 20,
        "scenarios": 4,
        "proposals": len(all_csv_rows),
        "threshold": CONF,
        "contact_sheets": 4,
        "manual_review_completed": False,
        "ground_truth_created": False,
        "note": "These are model-generated candidates, not independent annotations.",
    }

    with REPORT_PATH.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=== TASK 29.3D.3C.1 SUMMARY ===")
    print("Images processed: 20")
    print("Total YOLO suggestions:", len(all_csv_rows))
    print("Proposal JSON files: 20")
    print("Contact sheets generated: 4")
    print("Individual previews: 20")
    print("Ground-truth files modified: 0")
    print("Manual review required: YES")
    print("\nTASK 29.3D.3C.1: PASS", flush=True)


if __name__ == "__main__":
    main()
