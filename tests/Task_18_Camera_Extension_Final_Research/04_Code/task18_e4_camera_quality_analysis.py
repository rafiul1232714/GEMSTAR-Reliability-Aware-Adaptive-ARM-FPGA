import csv
from pathlib import Path

import cv2
import numpy as np

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Camera_Extension_Final_Research"
)

IMAGES = BASE / "08_Extracted_Images"
DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"

DATA.mkdir(parents=True, exist_ok=True)
GRAPHS.mkdir(parents=True, exist_ok=True)

TARGET_SIZE = (640, 480)

def analyze_image(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)

    if image is None:
        raise RuntimeError(f"Cannot read {path}")

    h, w = image.shape[:2]

    # Standardize analysis resolution.
    if (w, h) != TARGET_SIZE:
        image = cv2.resize(
            image, TARGET_SIZE,
            interpolation=cv2.INTER_AREA
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness = float(laplacian.var())

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.mean(edges > 0) * 100)

    dark_pct = float(np.mean(gray <= 5) * 100)
    bright_pct = float(np.mean(gray >= 250) * 100)

    # Diagnostic metadata, not a reliability label.
    return {
        "OriginalWidth": w,
        "OriginalHeight": h,
        "AnalysisWidth": TARGET_SIZE[0],
        "AnalysisHeight": TARGET_SIZE[1],
        "Brightness": brightness,
        "Contrast": contrast,
        "LaplacianVariance": sharpness,
        "EdgeDensityPercent": edge_density,
        "NearBlackPercent": dark_pct,
        "NearWhitePercent": bright_pct,
    }

def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("\n=== TASK 18.E4 CAMERA QUALITY ANALYSIS ===")

    paths = sorted(IMAGES.rglob("*.png"))
    print("Images found:", len(paths))

    if not paths:
        raise RuntimeError("No extracted PNG files found.")

    rows = []

    for path in paths:
        measurements = analyze_image(path)

        row = {
            "Recording": path.parent.name,
            "ImageName": path.name,
            **measurements,
        }

        rows.append(row)

        print(
            f"{row['Recording']:30s} "
            f"| Brightness={row['Brightness']:7.2f} "
            f"| Contrast={row['Contrast']:7.2f} "
            f"| Sharpness={row['LaplacianVariance']:9.2f} "
            f"| Edges={row['EdgeDensityPercent']:6.2f}%"
        )

    out_csv = DATA / "task18_e4_camera_quality_metrics.csv"

    with out_csv.open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    # Per-recording descriptive summaries.
    scenarios = sorted(set(r["Recording"] for r in rows))
    summary_rows = []

    fields = [
        "Brightness", "Contrast",
        "LaplacianVariance",
        "EdgeDensityPercent",
        "NearBlackPercent",
        "NearWhitePercent",
    ]

    for scenario in scenarios:
        group = [
            r for r in rows
            if r["Recording"] == scenario
        ]

        summary = {
            "Recording": scenario,
            "Images": len(group),
        }

        for field in fields:
            summary[field + "Median"] = float(
                np.median([r[field] for r in group])
            )

        summary_rows.append(summary)

    summary_csv = (
        DATA / "task18_e4_camera_quality_scenario_summary.csv"
    )

    with summary_csv.open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(summary_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    # Four-panel research figure.
    fig, axes = plt.subplots(2, 2, figsize=(15, 9))

    metrics = [
        ("BrightnessMedian", "Brightness (0-255)"),
        ("ContrastMedian", "Grayscale contrast"),
        ("LaplacianVarianceMedian", "Sharpness proxy"),
        ("EdgeDensityPercentMedian", "Edge density (%)"),
    ]

    x = np.arange(len(summary_rows))
    names = [r["Recording"] for r in summary_rows]

    for ax, (key, title) in zip(axes.flat, metrics):
        values = [r[key] for r in summary_rows]

        ax.bar(x, values)
        ax.set_xticks(x)
        ax.set_xticklabels(
            names, rotation=25, ha="right", fontsize=8
        )
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.25)

    fig.suptitle(
        "GEMSTAR Camera Image Statistics — "
        "All images analyzed at 640 x 480"
    )
    fig.tight_layout()

    graph = (
        GRAPHS / "task18_e4_camera_quality_comparison.png"
    )

    fig.savefig(graph, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("\n=== RECORDING SUMMARY ===")

    for row in summary_rows:
        print(
            f"{row['Recording']:30s}"
            f" | brightness={row['BrightnessMedian']:.2f}"
            f" | contrast={row['ContrastMedian']:.2f}"
            f" | sharpness={row['LaplacianVarianceMedian']:.2f}"
            f" | edges={row['EdgeDensityPercentMedian']:.2f}%"
        )

    print("\n=== TASK 18.E4 COMPLETE ===")
    print("Total analyzed:", len(rows))
    print("Quality CSV saved:", out_csv.is_file())
    print("Scenario CSV saved:", summary_csv.is_file())
    print("Four-panel graph saved:", graph.is_file())
    print("Graph path:", graph)
    print("\nNOTE: These are image statistics, not")
    print("validated fog severity or detection reliability.")

if __name__ == "__main__":
    main()
