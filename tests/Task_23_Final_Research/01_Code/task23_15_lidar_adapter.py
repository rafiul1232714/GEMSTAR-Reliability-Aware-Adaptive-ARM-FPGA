"""Task 23.15 LiDAR preprocessing adapter.

Reuses the validated LiDAR return-availability function without
executing historical experiment code.

This adapter does not perform LiDAR point reconstruction,
object detection, or independent reliability calibration.
"""

import ast
import math
from collections import namedtuple
from pathlib import Path

from task23_15_unified_preprocessing import (
    make_measurement,
    validate_timestamp_ns,
)


def load_lidar_processor():
    """Extract the original function without executing module-level code."""

    path = (
        Path(__file__).resolve().parent
        / "task23_11F_lidar_reliability.py"
    )

    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))

    matches = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "score_lidar_frame"
    ]

    if len(matches) != 1:
        raise RuntimeError("Expected one LiDAR scoring function")

    function_source = ast.get_source_segment(source, matches[0])

    if not function_source:
        raise RuntimeError("Unable to extract LiDAR function")

    ReliabilityResult = namedtuple(
        "ReliabilityResult",
        ["score", "status", "positive", "total"],
    )

    namespace = {
        "math": math,
        "ReliabilityResult": ReliabilityResult,
    }

    exec(
        compile(function_source, str(path), "exec"),
        namespace,
    )

    return namespace["score_lidar_frame"]


def process_lidar(lidar_view, timestamp_ns, previous_ns=None):
    """Produce a unified LiDAR measurement with availability metadata."""

    if not validate_timestamp_ns(timestamp_ns, previous_ns):
        return make_measurement(
            sensor="lidar",
            timestamp_ns=None,
            coordinate_frame="LIDAR_LOCAL",
            status="INVALID_TIMESTAMP",
        )

    scorer = load_lidar_processor()

    # Original scorer accepts timestamps in seconds.
    current_seconds = timestamp_ns / 1_000_000_000.0

    previous_seconds = (
        None if previous_ns is None
        else previous_ns / 1_000_000_000.0
    )

    result = scorer(
        lidar_view,
        current_seconds,
        previous_seconds,
    )

    quality = {
        "positive_return_ratio": result.score,
        "positive_returns": result.positive,
        "total_reflections": result.total,
    }

    return make_measurement(
        sensor="lidar",
        timestamp_ns=timestamp_ns,
        coordinate_frame="LIDAR_LOCAL",
        status=result.status,
        quality=quality,
        data=lidar_view,
    )


if __name__ == "__main__":
    print("TASK23_15B_04A_LIDAR_ADAPTER_IMPORT_PASS")
