"""Task 23.15: common sensor preprocessing metadata interface.

This module does not perform OSI decoding, sensor fusion, or
independent coordinate-frame calibration.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, Optional


VALID_SENSORS = frozenset(("camera", "lidar", "radar"))

VALID_STATUSES = frozenset((
    "VALID",
    "NO_RETURNS",
    "MISSING_FRAME",
    "EMPTY_FRAME",
    "MALFORMED_FRAME",
    "INVALID_TIMESTAMP",
    "INVALID_MEASUREMENT",
))

VALID_FRAMES = frozenset((
    "CAMERA_LOCAL",
    "LIDAR_LOCAL",
    "RADAR_LOCAL",
    "VEHICLE_OSI_METRES",
    "UNVERIFIED",
))


@dataclass(frozen=True)
class SensorMeasurement:
    sensor: str
    timestamp_ns: Optional[int]
    coordinate_frame: str
    status: str
    quality: Dict[str, Any] = field(default_factory=dict)
    data: Any = None

    def __post_init__(self):
        if self.sensor not in VALID_SENSORS:
            raise ValueError("Unknown sensor type")

        if self.status not in VALID_STATUSES:
            raise ValueError("Unknown processing status")

        if self.coordinate_frame not in VALID_FRAMES:
            raise ValueError("Unknown coordinate frame")

        if self.timestamp_ns is not None:
            if (
                isinstance(self.timestamp_ns, bool)
                or not isinstance(self.timestamp_ns, int)
                or self.timestamp_ns < 0
            ):
                raise ValueError("Invalid timestamp_ns")

        if not isinstance(self.quality, dict):
            raise TypeError("quality must be a dictionary")


def validate_timestamp_ns(timestamp_ns, previous_ns=None):
    """Validate nonnegative, strictly increasing integer timestamps."""
    if (
        isinstance(timestamp_ns, bool)
        or not isinstance(timestamp_ns, int)
        or timestamp_ns < 0
    ):
        return False

    if previous_ns is not None:
        if (
            isinstance(previous_ns, bool)
            or not isinstance(previous_ns, int)
            or previous_ns < 0
            or timestamp_ns <= previous_ns
        ):
            return False

    return True


def make_measurement(
    sensor,
    timestamp_ns,
    coordinate_frame,
    status,
    quality=None,
    data=None,
):
    """Create a validated common sensor-measurement container."""
    return SensorMeasurement(
        sensor=sensor,
        timestamp_ns=timestamp_ns,
        coordinate_frame=coordinate_frame,
        status=status,
        quality={} if quality is None else dict(quality),
        data=data,
    )


if __name__ == "__main__":
    print("TASK23_15B_01_UNIFIED_INTERFACE_MODULE_PASS")
