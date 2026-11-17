import csv
import json
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK29 = ROOT / "tests" / "Task_29_Final_Research"

DATA = TASK29 / "02_CSV_Data"

MANIFEST = (
    ROOT / "tests" / "Task_28_Final_Research"
    / "02_CSV_Data" / "task28_3D4B2_camera_image_manifest.csv"
)

CORRECTIONS = (
    DATA / "task29_3D3C7_automatic_correction_candidates.csv"
)

OUT = (
    TASK29 / "01_Graphs"
    / "Camera_Candidate_Correction_Review"
)

SCENARIOS = [
    "baseline_clear",
    "baseline_fog_working_radar",
    "fog_mor100",
    "fog_postfix_validation",
]

COLORS = {
    "KEEP": (0, 180, 0),
    "RECLASS": (0, 180, 0),
    "REMOVE": (0, 0, 220),
    "PENDING": (0, 190, 255),
}

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def make_preview(item, proposals):
    image_path = Path(item["OutputPNG"])
    image = cv2.imread(str(image_path))

    if image is None or image.shape[:2] != (480, 640):
        raise RuntimeError(f"Invalid image: {image_path}")

    canvas = image.copy()

    for p in proposals:
        action = p["CandidateAction"]
        color = COLORS[action]

        x1 = int(round(float(p["X1"])))
        y1 = int(round(float(p["Y1"])))
        x2 = int(round(float(p["X2"])))
        y2 = int(round(float(p["Y2"])))

        x1 = max(0, min(639, x1))
        x2 = max(0, min(639, x2))
        y1 = max(0, min(479, y1))
        y2 = max(0, min(479, y2))

        cv2.rectangle(
            canvas, (x1, y1), (x2, y2), color, 2
        )

        if action == "RECLASS":
            label = (
                "PROPOSED " + p["CandidateClass"]
                + " (was " + p["OriginalClass"] + ")"
            )
        elif action == "KEEP":
            label = "PROPOSED " + p["CandidateClass"]
        elif action == "REMOVE":
            label = "EXCLUDE? " + p["OriginalClass"]
        else:
            label = "UNCERTAIN " + p["OriginalClass"]

        cv2.putText(
            canvas,
            label,
            (x1, max(18, y1 - 7)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.44,
            color,
            2,
            cv2.LINE_AA,
        )

    header = np.full((80, 640, 3), 245, dtype=np.uint8)

    cv2.putText(
        header,
        f"Frame {item['Frame']} | {len(proposals)} proposals",
        (12, 27),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65, (30, 30, 30), 2,
    )

    cv2.putText(
        header,
        "PROVISIONAL - NOT APPROVED GROUND TRUTH",
        (12, 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48, (0, 0, 180), 2,
    )

    return cv2.vconcat([header, canvas])

def main():
    print("=== TASK 29.3D.3C.9 ===", flush=True)

    images = read_csv(MANIFEST)
    proposals = read_csv(CORRECTIONS)

    assert len(images) == 20
    assert len(proposals) == 18

    if OUT.exists():
        raise FileExistsError(
            f"Output folder already exists; preserved: {OUT}"
        )

    grouped = defaultdict(list)

    for p in proposals:
        grouped[(p["Scenario"], int(p["Frame"]))].append(p)

    OUT.mkdir(parents=True, exist_ok=False)

    previews = 0
    sheets = 0

    for scenario in SCENARIOS:
        selected = sorted(
            [i for i in images if i["Scenario"] == scenario],
            key=lambda i: int(i["Frame"])
        )

        assert len(selected) == 5

        tiles = []

        for item in selected:
            frame = int(item["Frame"])

            preview = make_preview(
                item,
                grouped[(scenario, frame)]
            )

            name = (
                f"task29_3D3C9_{scenario}"
                f"_frame{frame:05d}.png"
            )

            path = OUT / name

            if not cv2.imwrite(str(path), preview):
                raise RuntimeError(f"Save failed: {path}")

            tiles.append(preview)
            previews += 1

        blank = np.full_like(tiles[0], 255)

        sheet = cv2.vconcat([
            cv2.hconcat(tiles[:3]),
            cv2.hconcat(tiles[3:] + [blank]),
        ])

        sheet_path = OUT / (
            f"task29_3D3C9_{scenario}_review_sheet.png"
        )

        if not cv2.imwrite(str(sheet_path), sheet):
            raise RuntimeError(f"Save failed: {sheet_path}")

        sheets += 1

        print("SAVED:", sheet_path.name, flush=True)

    assert previews == 20
    assert sheets == 4

    print("\n=== TASK 29.3D.3C.9 SUMMARY ===", flush=True)
    print("Images visualized:", previews, flush=True)
    print("Review contact sheets:", sheets, flush=True)
    print("Original predictions modified: 0", flush=True)
    print("Ground-truth annotations modified: 0", flush=True)
    print("Human validation complete: NO", flush=True)
    print("Output:", OUT, flush=True)
    print("\nTASK 29.3D.3C.9: PASS", flush=True)

if __name__ == "__main__":
    main()
