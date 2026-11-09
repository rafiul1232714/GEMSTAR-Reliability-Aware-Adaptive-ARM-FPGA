"""Zero-rotation sensor-local Unreal to vehicle-relative OSI transform.

Mount translation must already be expressed in OSI metres.
No world-pose transformation or measured extrinsic calibration is implied.
"""

import numpy as np

REFLECT_Y = np.array([1.0, -1.0, 1.0])


def to_vehicle_osi(points_ue, mount_translation_osi_m, mount_rpy_rad):
    """Transform an Nx3 array of points from sensor-local Unreal coordinates."""

    points = np.asarray(points_ue)
    translation = np.asarray(mount_translation_osi_m)
    orientation = np.asarray(mount_rpy_rad)

    for name, array in (
        ("points", points),
        ("translation", translation),
        ("orientation", orientation),
    ):
        if array.dtype.kind not in "iuf":
            raise ValueError(f"{name} must be numeric and nonboolean")

    points = points.astype(float)
    translation = translation.astype(float)
    orientation = orientation.astype(float)

    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points_ue must be an Nx3 array")

    if translation.shape != (3,) or orientation.shape != (3,):
        raise ValueError("Mount translation and orientation must be 3-vectors")

    if (
        not np.all(np.isfinite(points))
        or not np.all(np.isfinite(translation))
        or not np.all(np.isfinite(orientation))
    ):
        raise ValueError("Nonfinite coordinate or mounting input")

    if not np.allclose(orientation, 0.0, atol=1e-9, rtol=0):
        raise ValueError("Nonzero mounting rotation is unsupported")

    vehicle = points * REFLECT_Y + translation

    if not np.all(np.isfinite(vehicle)):
        raise ValueError("Nonfinite transformed coordinate")

    return vehicle


if __name__ == "__main__":
    print("TASK23_15B_06G_COORDINATE_MODULE_PASS")
