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
OUTPUTS = BASE / "09_Fixed_Point_Results"

for folder in (DATA, GRAPHS, OUTPUTS):
    folder.mkdir(parents=True, exist_ok=True)

def combine_gradients(gx, gy):
    ax = cv2.convertScaleAbs(gx)
    ay = cv2.convertScaleAbs(gy)
    return cv2.addWeighted(ax, 0.5, ay, 0.5, 0)

def analyze(path):
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Cannot decode {path}")

    if (image.shape[1], image.shape[0]) != (640, 480):
        image = cv2.resize(
            image, (640, 480),
            interpolation=cv2.INTER_AREA
        )

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gx16 = cv2.Sobel(
        gray, cv2.CV_16S, 1, 0,
        ksize=3, borderType=cv2.BORDER_DEFAULT
    )
    gy16 = cv2.Sobel(
        gray, cv2.CV_16S, 0, 1,
        ksize=3, borderType=cv2.BORDER_DEFAULT
    )

    reference = combine_gradients(gx16, gy16)

    # Independent explicit signed-integer convolution.
    padded = np.pad(gray.astype(np.int16), 1, mode="reflect")

    a = padded[:-2, :-2]
    b = padded[:-2, 1:-1]
    c = padded[:-2, 2:]
    d = padded[1:-1, :-2]
    f = padded[1:-1, 2:]
    g = padded[2:, :-2]
    h = padded[2:, 1:-1]
    i = padded[2:, 2:]

    manual_x = -a + c - 2*d + 2*f - g + i
    manual_y = -a - 2*b - c + g + 2*h + i

    # Bit-exact gradient verification before output formatting.
    exact_gradients = (
        np.array_equal(manual_x, gx16)
        and np.array_equal(manual_y, gy16)
    )

    if not exact_gradients:
        raise AssertionError(
            "Integer gradients disagree with OpenCV"
        )

    int16_output = combine_gradients(manual_x, manual_y)

    # Intentionally unsuitable 8-bit gradient saturation:
    # demonstrating lost information, not a proposed design.
    gx8 = np.clip(manual_x, -128, 127).astype(np.int8)
    gy8 = np.clip(manual_y, -128, 127).astype(np.int8)

    int8_output = combine_gradients(
        gx8.astype(np.int16),
        gy8.astype(np.int16)
    )

    exact_pixels = int(
        np.count_nonzero(int16_output == reference)
    )
    total_pixels = int(reference.size)

    int8_exact = int(
        np.count_nonzero(int8_output == reference)
    )

    gradient_clip_count = int(np.count_nonzero(
        (manual_x < -128) | (manual_x > 127)
        | (manual_y < -128) | (manual_y > 127)
    ))

    int8_mean_abs_error = float(np.mean(
        np.abs(
            int8_output.astype(np.int16)
            - reference.astype(np.int16)
        )
    ))

    return {
        "Recording": path.parent.name,
        "Image": path.name,
        "PixelCount": total_pixels,
        "MaxAbsGradientX": int(
            np.max(np.abs(manual_x.astype(np.int32)))
        ),
        "MaxAbsGradientY": int(
            np.max(np.abs(manual_y.astype(np.int32)))
        ),
        "INT16ExactAgreementPercent":
            100 * exact_pixels / total_pixels,
        "INT8SaturatedAgreementPercent":
            100 * int8_exact / total_pixels,
        "INT8ClippedGradientPixels":
            gradient_clip_count,
        "INT8MeanAbsOutputError":
            int8_mean_abs_error,
    }, reference, int8_output

def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    print("\n=== TASK 18.E7 FIXED-POINT SOBEL ===")

    paths = sorted(IMAGES.rglob("*.png"))
    if not paths:
        raise RuntimeError("No extracted camera images found")

    rows = []
    example = None

    for path in paths:
        row, reference, int8_output = analyze(path)
        rows.append(row)

        if example is None:
            example = (reference, int8_output)

        print(
            f"{row['Recording']:27s}"
            f" | INT16={row['INT16ExactAgreementPercent']:7.3f}%"
            f" | INT8={row['INT8SaturatedAgreementPercent']:7.3f}%"
            f" | Clipped={row['INT8ClippedGradientPixels']}"
        )

    result_path = DATA / "task18_e7_fixed_point_results.csv"

    with result_path.open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    # One visualization per recording: reference, unsuitable INT8,
    # and absolute difference.
    scenarios = sorted(set(r["Recording"] for r in rows))

    for scenario in scenarios:
        path = next(
            p for p in paths
            if p.parent.name == scenario
        )
        _, ref, i8 = analyze(path)

        difference = cv2.absdiff(ref, i8)

        panel = np.hstack([ref, i8, difference])

        cv2.imwrite(
            str(OUTPUTS / f"{scenario}_sobel_comparison.png"),
            panel
        )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    names = [r["Recording"] for r in rows]
    x = np.arange(len(rows))

    axes[0].bar(
        x, [r["INT8SaturatedAgreementPercent"] for r in rows]
    )
    axes[0].set_ylabel("Exact output agreement (%)")
    axes[0].set_title("Saturated INT8 vs full Sobel")
    axes[0].set_xlabel("Extracted image index")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(
        x, [r["INT8ClippedGradientPixels"] for r in rows]
    )
    axes[1].set_ylabel("Pixels with clipped gradient")
    axes[1].set_title("Loss of gradient dynamic range")
    axes[1].set_xlabel("Extracted image index")
    axes[1].grid(axis="y", alpha=0.25)

    fig.suptitle(
        "GEMSTAR - Sobel Fixed-Point Arithmetic Study"
    )
    fig.tight_layout()

    graph = (
        GRAPHS / "task18_e7_sobel_precision_comparison.png"
    )
    fig.savefig(graph, dpi=180)
    plt.close(fig)

    print("\n=== TASK 18.E7 SUMMARY ===")
    print("Images tested:", len(rows))

    print(
        "Minimum INT16 exact agreement:",
        min(r["INT16ExactAgreementPercent"] for r in rows),
        "%"
    )

    print(
        "Median INT8 exact agreement:",
        round(float(np.median([
            r["INT8SaturatedAgreementPercent"]
            for r in rows
        ])), 3),
        "%"
    )

    print(
        "Total clipped-gradient pixels:",
        sum(r["INT8ClippedGradientPixels"] for r in rows)
    )

    print(
        "Maximum observed absolute X gradient:",
        max(r["MaxAbsGradientX"] for r in rows)
    )

    print(
        "Maximum observed absolute Y gradient:",
        max(r["MaxAbsGradientY"] for r in rows)
    )

    print("\n=== TASK 18.E7 COMPLETE ===")
    print("Results CSV saved:", result_path.is_file())
    print("Graph saved:", graph.is_file())
    print("Comparison panels:", len(scenarios))
    print("Comparison folder:", OUTPUTS)

    print("\nLIMITATIONS:")
    print("This is bit-accuracy testing on a PC.")
    print("No RTL or FPGA was executed.")
    print("No hardware latency or energy measured.")
    print("INT8 saturation is a deliberately lossy baseline.")
    print("Input pixels are already unsigned 8-bit.")

if __name__ == "__main__":
    main()
