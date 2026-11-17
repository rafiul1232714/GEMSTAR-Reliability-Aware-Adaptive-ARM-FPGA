import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
TASK = ROOT / "tests" / "Task_29_Final_Research"
DATA = TASK / "02_CSV_Data"

SOURCE = DATA / "task29_4C12D5C4C_master_ground_truth_review.csv"
REVIEWS = DATA / "task29_4C12D5C4D_human_frame_reviews.csv"
BOXES = DATA / "task29_4C12D5C4D_human_boxes.csv"

CLASSES = (
    "person", "car", "truck",
    "bus", "bicycle", "motorcycle"
)

REVIEW_FIELDS = [
    "Scenario", "Frame", "ImagePath",
    "Status", "ObjectCount", "ReviewMethod"
]

BOX_FIELDS = [
    "Scenario", "Frame", "Class",
    "X1", "Y1", "X2", "Y2",
    "AnnotationOrigin"
]

def load_csv(path):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_csv(path, fields, rows):
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(temp, path)

class Annotator:
    def __init__(self, root):
        self.root = root
        self.root.title("GEMSTAR - Independent Camera Annotation")

        self.images = load_csv(SOURCE)
        if len(self.images) != 20:
            raise RuntimeError("Expected 20 master review entries")

        self.reviews = load_csv(REVIEWS)
        self.boxes = load_csv(BOXES)

        self.index = 0
        self.start = None
        self.preview = None
        self.image = None

        self.label = tk.StringVar(value="person")
        self.status = tk.StringVar()

        header = ttk.Frame(root, padding=8)
        header.pack(fill="x")

        self.heading = ttk.Label(
            header, text="", font=("Arial", 12, "bold")
        )
        self.heading.pack(anchor="w")

        self.info = ttk.Label(header, text="")
        self.info.pack(anchor="w")

        ttk.Label(
            header,
            text="Draw rectangles around actual visible road users. "
                 "Do not copy YOLO proposals."
        ).pack(anchor="w")

        controls = ttk.Frame(root, padding=8)
        controls.pack(fill="x")

        ttk.Label(controls, text="Object class:").pack(side="left")

        ttk.Combobox(
            controls,
            textvariable=self.label,
            values=CLASSES,
            state="readonly",
            width=14
        ).pack(side="left", padx=8)

        ttk.Button(
            controls, text="Undo last box",
            command=self.undo
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Confirm objects",
            command=self.confirm_objects
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Confirm empty",
            command=self.confirm_empty
        ).pack(side="left", padx=4)

        ttk.Button(
            controls, text="Mark uncertain",
            command=self.mark_uncertain
        ).pack(side="left", padx=4)

        self.canvas = tk.Canvas(
            root,
            width=640,
            height=480,
            background="black"
        )
        self.canvas.pack(padx=10, pady=5)

        self.canvas.bind("<ButtonPress-1>", self.mouse_down)
        self.canvas.bind("<B1-Motion>", self.mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)

        self.details = ttk.Label(root, text="")
        self.details.pack(anchor="w", padx=10)

        bottom = ttk.Frame(root, padding=10)
        bottom.pack(fill="x")

        ttk.Button(
            bottom, text="Previous",
            command=self.previous
        ).pack(side="left", padx=5)

        ttk.Button(
            bottom, text="Next",
            command=self.next
        ).pack(side="left", padx=5)

        ttk.Label(
            bottom, textvariable=self.status
        ).pack(side="left", padx=12)

        self.show()

    def key(self):
        r = self.images[self.index]
        return (r["Scenario"], str(r["Frame"]))

    def current_review(self):
        key = self.key()
        return next(
            (
                r for r in self.reviews
                if (r["Scenario"], str(r["Frame"])) == key
            ),
            None
        )

    def current_boxes(self):
        key = self.key()
        return [
            b for b in self.boxes
            if (b["Scenario"], str(b["Frame"])) == key
        ]

    def clear_review(self):
        key = self.key()
        self.reviews = [
            r for r in self.reviews
            if (r["Scenario"], str(r["Frame"])) != key
        ]

    def show(self):
        r = self.images[self.index]
        path = Path(r["ImagePath"])
        if not path.is_file():
            raise RuntimeError("Missing image: " + str(path))

        self.image = tk.PhotoImage(file=str(path))

        if self.image.width() != 640 or self.image.height() != 480:
            raise RuntimeError("Expected 640 x 480 PNG")

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.image, anchor="nw")
        self.heading.config(
            text=f"Image {self.index+1}/20: "
                 f"{r['Scenario']} - Frame {r['Frame']}"
        )

        self.info.config(
            text="Priority score: " + str(r["PriorityScore"])
        )

        for b in self.current_boxes():
            self.draw_saved_box(b)

        review = self.current_review()
        current_status = (
            review["Status"] if review else "UNREVIEWED"
        )

        self.status.set("Status: " + current_status)
        self.details.config(
            text=f"Saved boxes in current frame: "
                 f"{len(self.current_boxes())}"
        )

    def draw_saved_box(self, b):
        coords = [
            float(b[x]) for x in ("X1", "Y1", "X2", "Y2")
        ]
        self.canvas.create_rectangle(
            *coords, outline="lime", width=2
        )
        self.canvas.create_text(
            coords[0], max(8, coords[1]-8),
            text=b["Class"], anchor="w", fill="yellow"
        )

    def mouse_down(self, event):
        self.start = (
            max(0, min(639, event.x)),
            max(0, min(479, event.y))
        )
        self.preview = None

    def mouse_move(self, event):
        if self.start is None:
            return

        if self.preview is not None:
            self.canvas.delete(self.preview)

        self.preview = self.canvas.create_rectangle(
            self.start[0], self.start[1],
            max(0, min(639, event.x)),
            max(0, min(479, event.y)),
            outline="yellow", width=2
        )

    def mouse_up(self, event):
        if self.start is None:
            return

        if self.preview is not None:
            self.canvas.delete(self.preview)
            self.preview = None

        x1 = min(self.start[0], max(0, min(639, event.x)))
        y1 = min(self.start[1], max(0, min(479, event.y)))
        x2 = max(self.start[0], max(0, min(639, event.x)))
        y2 = max(self.start[1], max(0, min(479, event.y)))

        self.start = None

        if x2-x1 < 3 or y2-y1 < 3:
            return

        scenario, frame = self.key()

        self.boxes.append({
            "Scenario": scenario,
            "Frame": frame,
            "Class": self.label.get(),
            "X1": x1, "Y1": y1,
            "X2": x2, "Y2": y2,
            "AnnotationOrigin": "HUMAN_DRAWN_PROVISIONAL"
        })

        self.clear_review()
        save_csv(BOXES, BOX_FIELDS, self.boxes)
        save_csv(REVIEWS, REVIEW_FIELDS, self.reviews)
        self.show()

    def undo(self):
        key = self.key()

        for i in range(len(self.boxes)-1, -1, -1):
            b = self.boxes[i]
            if (b["Scenario"], str(b["Frame"])) == key:
                self.boxes.pop(i)
                self.clear_review()
                save_csv(BOXES, BOX_FIELDS, self.boxes)
                save_csv(REVIEWS, REVIEW_FIELDS, self.reviews)
                self.show()
                return

    def record(self, status):
        scenario, frame = self.key()
        count = len(self.current_boxes())

        self.clear_review()
        self.reviews.append({
            "Scenario": scenario,
            "Frame": frame,
            "ImagePath": self.images[self.index]["ImagePath"],
            "Status": status,
            "ObjectCount": (
                str(count) if status != "UNCERTAIN" else ""
            ),
            "ReviewMethod": "INDEPENDENT_MANUAL_INSPECTION"
        })

        save_csv(BOXES, BOX_FIELDS, self.boxes)
        save_csv(REVIEWS, REVIEW_FIELDS, self.reviews)
        self.show()

    def confirm_objects(self):
        if not self.current_boxes():
            messagebox.showwarning(
                "No boxes",
                "Draw at least one object box first."
            )
            return
        self.record("HUMAN_REVIEWED_PROVISIONAL")

    def confirm_empty(self):
        if self.current_boxes():
            messagebox.showwarning(
                "Existing boxes",
                "Undo the boxes before marking empty."
            )
            return
        self.record("HUMAN_REVIEWED_EMPTY_PROVISIONAL")

    def mark_uncertain(self):
        self.record("UNCERTAIN")

    def next(self):
        if self.index < len(self.images)-1:
            self.index += 1
            self.show()

    def previous(self):
        if self.index > 0:
            self.index -= 1
            self.show()

if __name__ == "__main__":
    app = tk.Tk()
    Annotator(app)
    app.mainloop()
