import tkinter as tk
from pathlib import Path
import csv

task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")

image_file = task / "03_Graphs/task23_09_baseline_vs_displaced.png"
csv_file = task / "02_CSV_Data/task23_09_camera_cube_measurements.csv"
report_file = task / "06_Research_Findings/task23_09_camera_geometry_result.txt"
graph_file = task / "03_Graphs/task23_09_camera_width_comparison.svg"

if not image_file.is_file():
    raise FileNotFoundError(image_file)

root = tk.Tk()
root.title("Task 23.9 - Camera Cube Measurement")

image = tk.PhotoImage(file=str(image_file))
canvas = tk.Canvas(
    root, width=1280, height=480,
    highlightthickness=0
)
canvas.pack()

canvas.create_image(0, 0, image=image, anchor="nw")

message = tk.StringVar(
    value="Drag around LEFT cube front face, then RIGHT cube front face. Exclude shadows."
)

tk.Label(
    root, textvariable=message,
    font=("Arial", 11)
).pack(pady=8)

rectangles = {}
measurements = {}
start = None
active_side = None

def on_press(event):
    global start, active_side

    if not (0 <= event.x < 1280 and 0 <= event.y < 480):
        return

    active_side = "baseline" if event.x < 640 else "displaced"
    start = (event.x, event.y)

    if active_side in rectangles:
        canvas.delete(rectangles[active_side])

    color = "#00ff00" if active_side == "baseline" else "#ff3030"

    rectangles[active_side] = canvas.create_rectangle(
        event.x, event.y, event.x, event.y,
        outline=color, width=3
    )

def on_drag(event):
    if start is None or active_side is None:
        return

    boundary_min = 0 if active_side == "baseline" else 640
    boundary_max = 639 if active_side == "baseline" else 1279

    x = max(boundary_min, min(boundary_max, event.x))
    y = max(0, min(479, event.y))

    canvas.coords(
        rectangles[active_side],
        start[0], start[1], x, y
    )

def on_release(event):
    global start, active_side

    if start is None or active_side is None:
        return

    boundary_min = 0 if active_side == "baseline" else 640
    boundary_max = 639 if active_side == "baseline" else 1279

    x = max(boundary_min, min(boundary_max, event.x))
    y = max(0, min(479, event.y))

    x1, x2 = sorted((start[0], x))
    y1, y2 = sorted((start[1], y))

    width = x2 - x1
    height = y2 - y1

    if width < 10 or height < 10:
        message.set("Selection too small. Draw the rectangle again.")
        start = None
        active_side = None
        return

    measurements[active_side] = {
        "x_min": x1 - boundary_min,
        "x_max": x2 - boundary_min,
        "y_min": y1,
        "y_max": y2,
        "width_px": width,
        "height_px": height,
    }

    message.set(
        f"{active_side}: width={width} px, height={height} px. "
        "Select or adjust the other cube."
    )

    start = None
    active_side = None

def save_results():
    if len(measurements) != 2:
        message.set("Please select BOTH cube front faces first.")
        return

    baseline = measurements["baseline"]
    displaced = measurements["displaced"]

    width_base = baseline["width_px"]
    width_move = displaced["width_px"]

    ratio = width_move / width_base
    expected = 8.5 / 10.5
    reduction = (1 - ratio) * 100
    deviation = abs(ratio - expected)

    csv_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    graph_file.parent.mkdir(parents=True, exist_ok=True)

    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "condition", "distance_m", "x_min", "y_min",
            "x_max", "y_max", "width_px", "height_px"
        ])

        for condition, distance in [
            ("baseline", 8.5),
            ("displaced", 10.5),
        ]:
            box = measurements[condition]
            writer.writerow([
                condition, distance,
                box["x_min"], box["y_min"],
                box["x_max"], box["y_max"],
                box["width_px"], box["height_px"]
            ])

    status = (
        "CAMERA_WIDTH_GEOMETRY_CONSISTENT"
        if width_move < width_base and deviation <= 0.10
        else "CAMERA_WIDTH_REQUIRES_REVIEW"
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
width="700" height="300" viewBox="0 0 700 300">
<rect width="700" height="300" fill="white"/>
<text x="30" y="35" font-size="22" font-family="Arial">
Camera cube apparent width</text>
<text x="30" y="90" font-size="15" font-family="Arial">
Baseline (8.5 m)</text>
<rect x="195" y="65" width="{width_base*2.5}"
height="32" fill="#3578bc"/>
<text x="{205+width_base*2.5}" y="87"
font-size="15" font-family="Arial">{width_base} px</text>
<text x="30" y="165" font-size="15" font-family="Arial">
Displaced (10.5 m)</text>
<rect x="195" y="140" width="{width_move*2.5}"
height="32" fill="#239675"/>
<text x="{205+width_move*2.5}" y="162"
font-size="15" font-family="Arial">{width_move} px</text>
<text x="30" y="230" font-size="15" font-family="Arial">
Measured ratio: {ratio:.4f}</text>
<text x="30" y="255" font-size="15" font-family="Arial">
Expected ratio: {expected:.4f}</text>
<text x="30" y="280" font-size="13" font-family="Arial">
Manual bounding-box measurements</text>
</svg>'''

    graph_file.write_text(svg, encoding="utf-8")

    lines = [
        "=== TASK 23.9 - CAMERA GEOMETRIC VALIDATION ===",
        f"Baseline cube width: {width_base} px",
        f"Displaced cube width: {width_move} px",
        f"Baseline cube height: {baseline['height_px']} px",
        f"Displaced cube height: {displaced['height_px']} px",
        f"Measured width ratio: {ratio:.6f}",
        f"Expected width ratio: {expected:.6f}",
        f"Measured reduction: {reduction:.2f}%",
        f"Absolute ratio deviation: {deviation:.6f}",
        "Measurement type: manual front-face bounding boxes",
        "Tolerance: 0.10 absolute ratio (screening criterion)",
        "Weather consistency: not independently verified",
        f"Status: {status}",
        f"CSV: {csv_file}",
        f"Graph: {graph_file}",
    ]

    report_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print("\n".join(lines))
    root.destroy()

canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)

tk.Button(
    root,
    text="Save measurements",
    font=("Arial", 12, "bold"),
    command=save_results
).pack(pady=10)

root.mainloop()
