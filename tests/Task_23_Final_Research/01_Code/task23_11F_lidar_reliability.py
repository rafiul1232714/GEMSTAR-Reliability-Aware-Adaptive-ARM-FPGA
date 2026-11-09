"""LiDAR measurement-availability scoring for Task 23.11.F."""

from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class ReliabilityResult:
    availability_score: Optional[float]
    status: str
    positive_returns: int
    total_reflections: int


def score_lidar_frame(
    lidar_view,
    timestamp,
    previous_timestamp=None,
):
    """Score positive LiDAR return availability, not detection accuracy."""

    def result(score, status, positive=0, total=0):
        return ReliabilityResult(score, status, positive, total)

    if lidar_view is None:
        return result(None, "MISSING_FRAME")

    reflections = getattr(lidar_view, "reflection", None)

    if reflections is None:
        return result(None, "MALFORMED_FRAME")

    try:
        total = len(reflections)
    except (TypeError, ValueError, OverflowError):
        return result(None, "MALFORMED_FRAME")

    try:
        current_time = float(timestamp)
    except (TypeError, ValueError, OverflowError):
        return result(None, "INVALID_TIMESTAMP", total=total)

    if not math.isfinite(current_time) or current_time < 0:
        return result(None, "INVALID_TIMESTAMP", total=total)

    if previous_timestamp is not None:
        try:
            previous_time = float(previous_timestamp)
        except (TypeError, ValueError, OverflowError):
            return result(None, "INVALID_TIMESTAMP", total=total)

        if (
            not math.isfinite(previous_time)
            or previous_time < 0
            or current_time <= previous_time
        ):
            return result(None, "INVALID_TIMESTAMP", total=total)

    if total == 0:
        return result(None, "EMPTY_FRAME")

    positive = 0

    try:
        for reflection in reflections:
            tof = reflection.time_of_flight
            strength = reflection.signal_strength

            if (
                math.isfinite(tof)
                and tof > 0
                and math.isfinite(strength)
                and strength > 0
            ):
                positive += 1

    except (AttributeError, TypeError, ValueError, OverflowError):
        return result(None, "MALFORMED_FRAME", total=total)

    score = positive / total
    status = "VALID" if positive > 0 else "NO_RETURNS"

    return result(score, status, positive, total)
