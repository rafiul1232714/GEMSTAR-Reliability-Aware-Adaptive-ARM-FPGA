"""Task 23.15 Radar preprocessing adapter.

Reuses the original Radar return-validation algorithm.
Does not execute historical experiments or reconstruct 3D points.
"""

import ast
import math
from pathlib import Path

from task23_15_unified_preprocessing import (
    make_measurement,
    validate_timestamp_ns,
)


def load_radar_processor():
    """Extract validated Radar function without importing experiment code."""

    path = (
        Path(__file__).resolve().parent
        / "task23_13C_01_radar_robustness_tests.py"
    )

    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))

    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "preprocess_radar_return"
    ]

    if len(functions) != 1:
        raise RuntimeError("Expected exactly one Radar processor")

    constants = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "C"
    ]

    if len(constants) != 1:
        raise RuntimeError("Radar speed-of-light constant not found")

    speed_of_light = ast.literal_eval(constants[0].value)

    if (
        isinstance(speed_of_light, bool)
        or not isinstance(speed_of_light, (int, float))
        or not math.isfinite(speed_of_light)
        or speed_of_light <= 0
    ):
        raise RuntimeError("Invalid Radar propagation constant")

    function_source = ast.get_source_segment(source, functions[0])

    if not function_source:
        raise RuntimeError("Radar processing function extraction failed")

    namespace = {
        "math": math,
        "C": speed_of_light,
    }

    exec(
        compile(function_source, str(path), "exec"),
        namespace,
    )

    return namespace["preprocess_radar_return"]


def process_radar_return(tof, strength, timestamp_ns):
    """Wrap one Radar reflection in the unified measurement format."""

    if not validate_timestamp_ns(timestamp_ns):
        return make_measurement(
            sensor="radar",
            timestamp_ns=None,
            coordinate_frame="RADAR_LOCAL",
            status="INVALID_TIMESTAMP",
        )

    processor = load_radar_processor()

    try:
        result = processor(tof, strength)
    except (ValueError, TypeError):
        return make_measurement(
            sensor="radar",
            timestamp_ns=timestamp_ns,
            coordinate_frame="RADAR_LOCAL",
            status="INVALID_MEASUREMENT",
        )

    return make_measurement(
        sensor="radar",
        timestamp_ns=timestamp_ns,
        coordinate_frame="RADAR_LOCAL",
        status=result["status"],
        quality={
            "signal_strength": result["signal_strength"],
        },
        data={
            "range_m": result["range_m"],
        },
    )


if __name__ == "__main__":
    print("TASK23_15B_05A_RADAR_ADAPTER_IMPORT_PASS")
