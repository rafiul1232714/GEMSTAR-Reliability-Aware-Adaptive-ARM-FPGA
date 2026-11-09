"""Task 23.15 Camera preprocessing adapter.

Reuses the validated Task 23.12 Camera preprocessing function.
Does not decode OSI, calibrate extrinsics, or perform fusion.
"""

from importlib import util
from pathlib import Path
import sys

from task23_15_unified_preprocessing import (
    make_measurement,
    validate_timestamp_ns,
)


def load_camera_processor():
    path = (
        Path(__file__).resolve().parent
        / "task23_12C_06_camera_cpu_preprocessing.py"
    )

    if not path.is_file():
        raise FileNotFoundError(path)

    spec = util.spec_from_file_location(
        "task23_12_camera_processor",
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError("Camera processor cannot be loaded")

    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module.preprocess_camera


def process_camera(image_bgr, timestamp_ns, roi=None):
    """Wrap validated Camera features in common sensor metadata."""

    if not validate_timestamp_ns(timestamp_ns):
        return make_measurement(
            sensor="camera",
            timestamp_ns=None,
            coordinate_frame="CAMERA_LOCAL",
            status="INVALID_TIMESTAMP",
            quality={},
        )

    if image_bgr is None:
        return make_measurement(
            sensor="camera",
            timestamp_ns=timestamp_ns,
            coordinate_frame="CAMERA_LOCAL",
            status="MISSING_FRAME",
            quality={},
        )

    preprocess_camera = load_camera_processor()

    try:
        result = preprocess_camera(image_bgr, roi=roi)
    except (TypeError, ValueError, AttributeError):
        return make_measurement(
            sensor="camera",
            timestamp_ns=timestamp_ns,
            coordinate_frame="CAMERA_LOCAL",
            status="INVALID_MEASUREMENT",
            quality={},
        )

    return make_measurement(
        sensor="camera",
        timestamp_ns=timestamp_ns,
        coordinate_frame="CAMERA_LOCAL",
        status=result["status"],
        quality=dict(result["features"]),
        data={
            "roi": result["roi"],
            "grayscale": result["grayscale"],
            "edges": result["edges"],
        },
    )


if __name__ == "__main__":
    print("TASK23_15B_03_CAMERA_ADAPTER_IMPORT_PASS")
