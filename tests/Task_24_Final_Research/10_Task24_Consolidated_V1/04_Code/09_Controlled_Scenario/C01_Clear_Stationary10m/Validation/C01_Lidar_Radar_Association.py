import os
import csv
import math
import struct
from osi3 import osi_sensorview_pb2

C = 299792458.0
MIN_RADAR_RETURNS = 3
SPATIAL_GATE_M = 1.5
TIME_TOLERANCE_S = 0.001

with open(os.environ["C01_LIDAR_CSV"],
          newline="", encoding="utf-8-sig") as f:
    lidar_rows = list(csv.DictReader(f))

if len(lidar_rows) != 31:
    raise RuntimeError("Expected 31 LiDAR tracking samples")

results = []
frame = 0

with open(os.environ["C01_SV"], "rb") as f:

    for lidar in lidar_rows:
        requested_t = float(lidar["timestamp_s"])

        while True:
            header = f.read(4)

            if len(header) != 4:
                raise RuntimeError("SensorView ended unexpectedly")

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid OSI message size")

            payload = f.read(size)

            if len(payload) != size:
                raise RuntimeError("Truncated OSI message")

            frame += 1
            msg = osi_sensorview_pb2.SensorView()
            msg.ParseFromString(payload)

            t = msg.timestamp.seconds + msg.timestamp.nanos/1e9

            if t + 1e-7 >= requested_t:
                break

        time_offset = abs(t-requested_t)

        if time_offset > TIME_TOLERANCE_S:
            raise RuntimeError(
                "LiDAR/Radar timestamp mismatch: "
                + str(time_offset)
            )

        if len(msg.radar_sensor_view) != 1:
            raise RuntimeError("Expected one Radar sensor")

        radar = msg.radar_sensor_view[0]
        mount = radar.view_configuration.mounting_position.position

        radar_points = []

        for r in radar.reflection:
            tof = float(r.time_of_flight)
            yaw = float(r.source_horizontal_angle)
            pitch = float(r.source_vertical_angle)

            if not all(math.isfinite(v)
                       for v in (tof, yaw, pitch)):
                continue

            if tof <= 0:
                continue

            distance = C*tof/2

            if not math.isfinite(distance) or distance <= 0.1:
                continue

            x = (float(mount.x)
                 + distance*math.cos(pitch)*math.cos(yaw))
            y = (float(mount.y)
                 - distance*math.cos(pitch)*math.sin(yaw))
            z = float(mount.z) + distance*math.sin(pitch)

            if (4 <= x <= 15
                and abs(y) <= 2.5
                and 0.4 <= z <= 2.5):
                radar_points.append((x,y,z))

        lidar_pos = (
            float(lidar["centroid_x_m"]),
            float(lidar["centroid_y_m"]),
            float(lidar["centroid_z_m"])
        )

        radar_pos = None
        separation = None
        status = "INSUFFICIENT_RADAR_RETURNS"

        if len(radar_points) >= MIN_RADAR_RETURNS:
            radar_pos = tuple(
                sum(p[k] for p in radar_points)/len(radar_points)
                for k in range(3)
            )

            separation = math.dist(lidar_pos, radar_pos)

            status = (
                "MATCHED"
                if separation <= SPATIAL_GATE_M
                else "SPATIAL_GATE_FAILED"
            )

        results.append({
            "timestamp_s": t,
            "lidar_track_id": lidar["track_id"],
            "lidar_x_m": lidar_pos[0],
            "lidar_y_m": lidar_pos[1],
            "lidar_z_m": lidar_pos[2],
            "radar_candidate_count": len(radar_points),
            "radar_x_m": radar_pos[0] if radar_pos else "",
            "radar_y_m": radar_pos[1] if radar_pos else "",
            "radar_z_m": radar_pos[2] if radar_pos else "",
            "centroid_separation_m": (
                separation if separation is not None else ""
            ),
            "association_status": status
        })

with open(os.environ["C01_RADAR_CSV"], "x",
          newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

matched = [
    r for r in results
    if r["association_status"] == "MATCHED"
]

print("TIMESTAMPS_CHECKED=",len(results))
print("MATCHED_TIMESTAMPS=",len(matched))
print("UNMATCHED_TIMESTAMPS=",len(results)-len(matched))
print("MIN_RADAR_RETURNS=",MIN_RADAR_RETURNS)
print("SPATIAL_GATE_M=",SPATIAL_GATE_M)
print("TIME_TOLERANCE_S=",TIME_TOLERANCE_S)

print("\n=== ASSOCIATION SAMPLES ===")

for r in results[::5]:
    print(
        "TIME_S=",round(r["timestamp_s"],6),
        "RADAR_POINTS=",r["radar_candidate_count"],
        "SEPARATION_M=",
        round(r["centroid_separation_m"],4)
        if r["centroid_separation_m"] != "" else "N/A",
        "STATUS=",r["association_status"]
    )

if matched:
    distances = [
        r["centroid_separation_m"] for r in matched
    ]

    print("\n=== MATCHED MEASUREMENTS ===")
    print("MEAN_SEPARATION_M=",
          round(sum(distances)/len(distances),5))
    print("MAX_SEPARATION_M=",
          round(max(distances),5))

print("\n=== SCIENTIFIC STATUS ===")
print("ASSOCIATION_TYPE=LIDAR_ASSISTED_RADAR_SPATIAL")
print("RADAR_INDEPENDENT_OBJECT_TRACK=NOT_IMPLEMENTED")
print("RADAR_DOPPLER_VALIDATED=NO")
print("CAMERA_ASSOCIATION=NOT_IMPLEMENTED")
print("THREE_SENSOR_EKF=NOT_IMPLEMENTED")
print("GROUND_TRUTH_USED=NO")
print("ORIGINAL_OSI_FILES_MODIFIED=NO")
print("OUTPUT_CSV=",os.environ["C01_RADAR_CSV"])
print("TASK24_05_LIDAR_RADAR_ASSOCIATION_COMPLETE")
