import cv2
import numpy as np


def preprocess_camera(image_bgr, roi=None):
    """
    Reusable CPU Camera preprocessing.

    Input:
        image_bgr: uint8 BGR image, H x W x 3
        roi: optional (x, y, width, height)

    Returns:
        Grayscale ROI, Canny edges, and quality features.
    """

    if not isinstance(image_bgr, np.ndarray):
        raise TypeError("Camera input must be a NumPy array")

    if (
        image_bgr.ndim != 3
        or image_bgr.shape[2] != 3
        or image_bgr.dtype != np.uint8
        or image_bgr.shape[0] == 0
        or image_bgr.shape[1] == 0
    ):
        raise ValueError("Expected nonempty uint8 BGR image")

    height, width = image_bgr.shape[:2]

    if roi is None:
        x, y, w, h = 0, 0, width, height
    else:
        if (
            len(roi) != 4
            or any(type(v) is not int for v in roi)
        ):
            raise ValueError("ROI must contain four integers")

        x, y, w, h = roi

        if (
            x < 0 or y < 0
            or w <= 0 or h <= 0
            or x + w > width
            or y + h > height
        ):
            raise ValueError("ROI outside image boundaries")

    region = image_bgr[y:y+h, x:x+w]

    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)

    edges = cv2.Canny(gray, 80, 160)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)

    features = {
        "mean_luminance": float(gray.mean()),
        "contrast_std": float(gray.std()),
        "edge_density": float(np.count_nonzero(edges) / edges.size),
        "laplacian_variance": float(laplacian.var()),
        "mean_saturation": float(hsv[:, :, 1].mean()),
    }

    return {
        "status": "VALID",
        "roi": (x, y, w, h),
        "grayscale": gray,
        "edges": edges,
        "features": features,
    }


if __name__ == "__main__":

    from pathlib import Path

    root = Path(
        r"E:\GEMSTAR_Project\sensor-health-monitor"
        r"\tests\Task_23_Final_Research"
        r"\08_Processed_Data\Camera_Weather_Comparison"
    )

    scenarios = {
        "CLEAR": "CLEAR_t0200ms.png",
        "FOG100": "FOG100_t0200ms.png",
        "FOG20": "FOG20_t0200ms.png",
    }

    for name, filename in scenarios.items():

        image = cv2.imread(str(root / filename))

        if image is None:
            raise RuntimeError(f"Cannot load image: {filename}")

        result = preprocess_camera(
            image,
            roi=(128, 96, 384, 288)
        )

        if result["status"] != "VALID":
            raise RuntimeError(f"{name}: preprocessing failed")

        print(
            f"{name}: STATUS={result['status']} "
            f"ROI={result['roi']} "
            f"EDGE_DENSITY={result['features']['edge_density']:.6f} "
            f"CONTRAST={result['features']['contrast_std']:.4f}"
        )

    print("TASK23_12C_06_CAMERA_CPU_PREPROCESSING_PASS")
