import csv
import time
import statistics
from pathlib import Path

import cv2
import numpy as np

BASE = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_18_Camera_Extension_Final_Research"
)

IMAGE_DIR = BASE / "08_Extracted_Images"
DATA = BASE / "02_CSV_Data"
GRAPHS = BASE / "01_Graphs"

DATA.mkdir(parents=True, exist_ok=True)
GRAPHS.mkdir(parents=True, exist_ok=True)

cv2.setNumThreads(1)

RUNS = 30
WARMUPS = 5
FULL_SIZE = (640, 480)
HALF_SIZE = (320, 240)

def sobel(gray):
    gx = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_16S, 0, 1, ksize=3)
    magnitude = cv2.addWeighted(
        cv2.convertScaleAbs(gx), 0.5,
        cv2.convertScaleAbs(gy), 0.5, 0
    )
    return magnitude

def run_mode(image, mode):
    if mode == "GRAYSCALE":
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if mode == "SOBEL_FULL":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return sobel(gray)

    if mode == "GAUSSIAN_SOBEL":
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
        return sobel(blurred)

    if mode == "SOBEL_HALF":
        reduced = cv2.resize(
            image, HALF_SIZE,
            interpolation=cv2.INTER_AREA
        )
        gray = cv2.cvtColor(reduced, cv2.COLOR_BGR2GRAY)
        edges = sobel(gray)
        return cv2.resize(
            edges, FULL_SIZE,
            interpolation=cv2.INTER_LINEAR
        )

    raise ValueError("Unknown mode: " + mode)

def percentile_nearest(values, percentage):
    sorted_values = sorted(values)
    index = max(
        0,
        int(np.ceil(percentage / 100 * len(values))) - 1
    )
    return sorted_values[index]

def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("\n=== TASK 18.E6 CAMERA BENCHMARK ===")

    files = sorted(IMAGE_DIR.rglob("*.png"))

    modes = [
        "GRAYSCALE",
        "SOBEL_FULL",
        "GAUSSIAN_SOBEL",
        "SOBEL_HALF",
    ]

    results = []
    timing_samples = []

    for path in files:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None:
            continue

        # Normalize resolution before timing.
        if (image.shape[1], image.shape[0]) != FULL_SIZE:
            image = cv2.resize(
                image, FULL_SIZE,
                interpolation=cv2.INTER_AREA
            )

        reference = run_mode(image, "SOBEL_FULL")
        reference_edges = reference >= 40

        for mode in modes:
            for _ in range(WARMUPS):
                run_mode(image, mode)

            samples = []
            output = None

            for repeat in range(RUNS):
                t0 = time.perf_counter_ns()
                output = run_mode(image, mode)
                elapsed_ms = (
                    time.perf_counter_ns() - t0
                ) / 1_000_000

                samples.append(elapsed_ms)

                timing_samples.append({
                    "Recording": path.parent.name,
                    "ImageName": path.name,
                    "Mode": mode,
                    "Run": repeat + 1,
                    "LatencyMs": elapsed_ms,
                })

            row = {
                "Recording": path.parent.name,
                "ImageName": path.name,
                "Mode": mode,
                "MedianMs": statistics.median(samples),
                "P95Ms": percentile_nearest(samples, 95),
                "MaxMs": max(samples),
                "StdMs": statistics.stdev(samples),
                "Runs": RUNS,
            }

            # Diagnostic edge-map comparison only.
            # It is NOT validated object detection accuracy.
            if mode != "GRAYSCALE":
                candidate_edges = output >= 40

                intersection = np.count_nonzero(
                    reference_edges & candidate_edges
                )

                denominator = (
                    np.count_nonzero(reference_edges) +
                    np.count_nonzero(candidate_edges)
                )

                edge_f1 = (
                    2 * intersection / denominator
                    if denominator else 1.0
                )

                row["EdgeMapF1VsFull"] = edge_f1
            else:
                row["EdgeMapF1VsFull"] = ""

            results.append(row)

        print(
            f"{path.parent.name:30s} | "
            f"{path.name} | 4 modes completed"
        )

    if not results:
        raise RuntimeError("No images were benchmarked.")

    result_file = (
        DATA / "task18_e6_camera_processing_results.csv"
    )
    samples_file = (
        DATA / "task18_e6_camera_timing_samples.csv"
    )
    summary_file = (
        DATA / "task18_e6_camera_processing_summary.csv"
    )

    def save_csv(path, rows):
        with path.open(
            "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=list(rows[0].keys())
            )
            writer.writeheader()
            writer.writerows(rows)

    save_csv(result_file, results)
    save_csv(samples_file, timing_samples)

    summary = []

    for mode in modes:
        group = [r for r in results if r["Mode"] == mode]

        edge_scores = [
            float(r["EdgeMapF1VsFull"])
            for r in group
            if r["EdgeMapF1VsFull"] != ""
        ]

        row = {
            "Mode": mode,
            "Images": len(group),
            "MedianOfFrameMediansMs": statistics.median(
                r["MedianMs"] for r in group
            ),
            "MedianFrameP95Ms": statistics.median(
                r["P95Ms"] for r in group
            ),
            "WorstObservedMs": max(
                r["MaxMs"] for r in group
            ),
            "MedianEdgeMapF1VsFull": (
                statistics.median(edge_scores)
                if edge_scores else ""
            ),
        }
        summary.append(row)

    save_csv(summary_file, summary)

    fig, axes = plt.subplots(
        1, 2, figsize=(13, 5)
    )

    names = [r["Mode"] for r in summary]
    values = [
        r["MedianOfFrameMediansMs"]
        for r in summary
    ]

    axes[0].bar(names, values)
    axes[0].set_title("PC preprocessing latency")
    axes[0].set_ylabel("Median processing time (ms)")
    axes[0].tick_params(axis="x", rotation=25)
    axes[0].grid(axis="y", alpha=0.3)

    edge_names = [
        r["Mode"] for r in summary
        if r["MedianEdgeMapF1VsFull"] != ""
    ]
    edge_values = [
        r["MedianEdgeMapF1VsFull"]
        for r in summary
        if r["MedianEdgeMapF1VsFull"] != ""
    ]

    axes[1].bar(edge_names, edge_values)
    axes[1].set_title("Edge agreement with full Sobel")
    axes[1].set_ylabel("Binary edge-map F1")
    axes[1].set_ylim(0, 1.05)
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].grid(axis="y", alpha=0.3)

    fig.suptitle(
        "GEMSTAR Camera: Workload and Edge-Map Trade-offs"
    )
    fig.tight_layout()

    graph = (
        GRAPHS / "task18_e6_camera_processing_comparison.png"
    )
    fig.savefig(graph, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("\n=== TASK 18.E6 SUMMARY ===")

    for row in summary:
        f1 = row["MedianEdgeMapF1VsFull"]
        f1_text = (
            f"{f1:.4f}"
            if isinstance(f1, float) else "N/A"
        )

        print(
            f"{row['Mode']:16s}"
            f" | Median={row['MedianOfFrameMediansMs']:.4f} ms"
            f" | P95 median={row['MedianFrameP95Ms']:.4f} ms"
            f" | Edge F1={f1_text}"
        )

    print("\n=== TASK 18.E6 COMPLETE ===")
    print("Images:", len(files))
    print("Processing modes:", len(modes))
    print("Timing repetitions per image/mode:", RUNS)
    print("Timing samples:", len(timing_samples))
    print("Results saved:", result_file.is_file())
    print("Samples saved:", samples_file.is_file())
    print("Summary saved:", summary_file.is_file())
    print("Graph saved:", graph.is_file())
    print("Graph:", graph)

    print("\nLIMITATIONS:")
    print("PC OpenCV timing, not ARM/FPGA timing.")
    print("Image file I/O and initial resize excluded.")
    print("Sobel reference is an algorithm comparison,")
    print("not ground-truth feature or obstacle accuracy.")
    print("All runs use images standardized to 640x480.")

if __name__ == "__main__":
    main()
