from pathlib import Path
import csv
import json
import cv2

BASE = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_18_Final_Research")
IMAGES = BASE / "08_Extracted_Images" / "Selected_Frames"
LABELS = BASE / "09_GroundTruth_Annotations"
MANIFEST = BASE / "02_CSV_Data" / "task18_annotation_manifest.csv"

LABELS.mkdir(parents=True, exist_ok=True)

CLASSES = {
    ord("c"): "car",
    ord("t"): "truck",
    ord("b"): "bus",
    ord("p"): "person",
}

with MANIFEST.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

current_class = "car"
boxes = []
drawing = False
start_point = None
end_point = None

def mouse_callback(event, x, y, flags, userdata):
    global drawing, start_point, end_point, boxes

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_point = (x, y)
        end_point = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        end_point = (x, y)

    elif event == cv2.EVENT_LBUTTONUP and drawing:
        drawing = False
        end_point = (x, y)

        x1 = min(start_point[0], x)
        y1 = min(start_point[1], y)
        x2 = max(start_point[0], x)
        y2 = max(start_point[1], y)

        if x2 - x1 >= 4 and y2 - y1 >= 4:
            boxes.append({
                "class": current_class,
                "x1": x1, "y1": y1,
                "x2": x2, "y2": y2
            })

def save_labels(frame, image_file):
    output = LABELS / f"task18_labels_frame_{frame:03d}.json"

    data = {
        "frame": frame,
        "image": image_file,
        "annotation_source": "MANUAL",
        "reviewed": True,
        "objects": boxes
    }

    output.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    return output

window = "Task 18 - Manual Ground Truth Annotation"
cv2.namedWindow(window, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window, 1000, 750)
cv2.setMouseCallback(window, mouse_callback)

for row in rows:
    frame = int(row["Frame"])
    path = IMAGES / row["ImageFile"]
    output = LABELS / f"task18_labels_frame_{frame:03d}.json"

    if output.exists():
        print(f"Frame {frame}: already annotated - skipping")
        continue

    original = cv2.imread(str(path))

    if original is None:
        raise RuntimeError(f"Cannot read {path}")

    boxes = []
    current_class = "car"

    print(f"\nFrame {frame}: {path.name}")
    print("C=car T=truck B=bus P=person")
    print("Drag=box U=undo N=save+next Q=save+quit")

    while True:
        display = original.copy()

        for box in boxes:
            cv2.rectangle(
                display,
                (box["x1"], box["y1"]),
                (box["x2"], box["y2"]),
                (0, 255, 0), 2
            )

            cv2.putText(
                display, box["class"],
                (box["x1"], max(18, box["y1"]-6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (0, 255, 0), 2
            )

        if drawing and start_point and end_point:
            cv2.rectangle(
                display, start_point, end_point,
                (0, 255, 255), 1
            )

        cv2.putText(
            display,
            f"Frame {frame} | Selected: {current_class} | Boxes: {len(boxes)}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (0, 0, 0), 3
        )

        cv2.putText(
            display,
            f"Frame {frame} | Selected: {current_class} | Boxes: {len(boxes)}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (255, 255, 255), 1
        )

        cv2.imshow(window, display)

        key = cv2.waitKey(20) & 0xFF

        if key in CLASSES:
            current_class = CLASSES[key]

        elif key == ord("u") and boxes:
            boxes.pop()

        elif key == ord("n"):
            result = save_labels(frame, path.name)
            print(f"Saved: {result.name} | Objects: {len(boxes)}")
            break

        elif key == ord("q"):
            result = save_labels(frame, path.name)
            print(f"Saved: {result.name} | Objects: {len(boxes)}")
            print("Progress saved. Remaining images can be resumed.")
            cv2.destroyAllWindows()
            raise SystemExit(0)

cv2.destroyAllWindows()

print("\n=== TASK 18.7E ANNOTATION SESSION COMPLETE ===")
print("Saved annotation files:",
      len(list(LABELS.glob("task18_labels_frame_*.json"))))
