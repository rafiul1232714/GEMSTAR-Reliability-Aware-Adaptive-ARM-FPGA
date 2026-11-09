
# Task 13.4 - Verify recorded LiDAR scan configuration
# Read-only inspection. Does not modify original files.

from pathlib import Path
import sys
from collections import Counter

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

sys.path.insert(0, str(ROOT / "src"))

from task11_extract_measurements import read_osi, SV_FILE, SensorView

FRAME = 150

for frame, sv in enumerate(read_osi(SV_FILE, SensorView), 1):
    if frame != FRAME:
        continue

    print("===== TASK 13.4 - RECORDED LIDAR CONFIG =====")
    print("Frame:", frame)
    print("LiDAR views:", len(sv.lidar_sensor_view))

    for i, lidar in enumerate(sv.lidar_sensor_view):
        cfg = lidar.view_configuration

        nh = cfg.number_of_rays_horizontal
        nv = cfg.number_of_rays_vertical
        reflections = list(lidar.reflection)

        print(f"\nLiDAR view {i}")
        print("Horizontal rays:", nh)
        print("Vertical rays:", nv)
        print("Expected scan positions:", nh * nv)
        print("Stored reflection records:", len(reflections))
        print(
            "Horizontal FOV (radians):",
            cfg.field_of_view_horizontal
        )
        print(
            "Vertical FOV (radians):",
            cfg.field_of_view_vertical
        )

        no_hit_id = (1 << 64) - 1

        counts = Counter(
            "NO_HIT"
            if r.object_id.value == no_hit_id
            else "OTHER"
            for r in reflections
        )

        print("Explicit no-hit records:", counts["NO_HIT"])
        print("Other reflection records:", counts["OTHER"])

        print(
            "Grid size matches stored records:",
            nh * nv == len(reflections)
        )

        print("\nFirst 5 records:")
        for idx, r in enumerate(reflections[:5]):
            print(
                idx,
                "object_id=", r.object_id.value,
                "signal=", r.signal_strength,
                "time_of_flight=", r.time_of_flight
            )

    break
else:
    print(f"Frame {FRAME} not found in {SV_FILE}")
