import os
import csv
import math
import struct
from collections import deque
from osi3 import osi_sensorview_pb2

C = 299792458.0
SAMPLE_TIMES = [5.0 + i*0.5 for i in range(31)]
CLUSTER_RADIUS = 0.35
MIN_POINTS = 10
ASSOCIATION_GATE = 1.0

def extract_points(msg):
    lidar = msg.lidar_sensor_view[0]
    cfg = lidar.view_configuration

    nh = int(cfg.number_of_rays_horizontal)
    nv = int(cfg.number_of_rays_vertical)

    if nh < 2 or nv < 2 or len(lidar.reflection) != nh*nv:
        raise RuntimeError("Unexpected LiDAR grid")

    hfov = float(cfg.field_of_view_horizontal)
    vfov = float(cfg.field_of_view_vertical)
    mount = cfg.mounting_position.position

    points = []

    for i, r in enumerate(lidar.reflection):
        tof = float(r.time_of_flight)
        if not math.isfinite(tof) or tof <= 0:
            continue

        d = C * tof / 2
        if not math.isfinite(d) or d <= 0.1:
            continue

        hi = i % nh
        vi = i // nh

        yaw = -hfov/2 + hi*hfov/(nh-1)
        pitch = -vfov/2 + vi*vfov/(nv-1)

        x = d*math.cos(pitch)*math.cos(yaw) + float(mount.x)
        y = -d*math.cos(pitch)*math.sin(yaw) + float(mount.y)
        z = d*math.sin(pitch) + float(mount.z)

        if 4 <= x <= 15 and abs(y) <= 2.5 and 0.4 <= z <= 2.5:
            points.append((x, y, z))

    return points

def clusters_from_points(points):
    visited = set()
    clusters = []
    radius2 = CLUSTER_RADIUS**2

    for start in range(len(points)):
        if start in visited:
            continue

        visited.add(start)
        q = deque([start])
        group = []

        while q:
            i = q.popleft()
            group.append(points[i])
            x1, y1, z1 = points[i]

            for j, (x2, y2, z2) in enumerate(points):
                if j in visited:
                    continue

                d2 = (x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2

                if d2 <= radius2:
                    visited.add(j)
                    q.append(j)

        if len(group) >= MIN_POINTS:
            clusters.append(group)

    return clusters

def describe(group):
    xs = [p[0] for p in group]
    ys = [p[1] for p in group]
    zs = [p[2] for p in group]

    return {
        "centroid_x": sum(xs)/len(xs),
        "centroid_y": sum(ys)/len(ys),
        "centroid_z": sum(zs)/len(zs),
        "points": len(group),
        "size_x": max(xs)-min(xs),
        "size_y": max(ys)-min(ys),
        "size_z": max(zs)-min(zs)
    }

results = []
next_sample = 0
last_position = None
frame = 0
matched = 0
rejected = 0

with open(os.environ["C01_SV"], "rb") as f:
    while next_sample < len(SAMPLE_TIMES):
        header = f.read(4)

        if not header:
            raise RuntimeError("Recording ended before 20 seconds")

        if len(header) != 4:
            raise RuntimeError("Truncated OSI header")

        size = struct.unpack("<I", header)[0]
        if not 0 < size <= 100_000_000:
            raise RuntimeError("Invalid OSI message size")

        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Truncated OSI payload")

        frame += 1
        msg = osi_sensorview_pb2.SensorView()
        msg.ParseFromString(payload)

        t = msg.timestamp.seconds + msg.timestamp.nanos/1e9

        if t < SAMPLE_TIMES[next_sample]:
            continue

        points = extract_points(msg)
        candidates = [describe(c) for c in clusters_from_points(points)]

        selected = None
        association_distance = None

        if last_position is None:
            # Bootstrap using sensor-only candidate size.
            if candidates:
                selected = max(candidates, key=lambda c: c["points"])
        else:
            ranked = sorted(
                candidates,
                key=lambda c: math.dist(
                    last_position,
                    (c["centroid_x"], c["centroid_y"], c["centroid_z"])
                )
            )

            if ranked:
                best = ranked[0]
                association_distance = math.dist(
                    last_position,
                    (best["centroid_x"], best["centroid_y"], best["centroid_z"])
                )

                if association_distance <= ASSOCIATION_GATE:
                    selected = best

        if selected is not None:
            matched += 1
            last_position = (
                selected["centroid_x"],
                selected["centroid_y"],
                selected["centroid_z"]
            )
        else:
            rejected += 1

        results.append({
            "frame": frame,
            "timestamp_s": t,
            "track_id": "LIDAR_C01_1" if selected else "",
            "association_status": "MATCHED" if selected else "MISSING",
            "candidate_count": len(candidates),
            "point_count": selected["points"] if selected else "",
            "centroid_x_m": selected["centroid_x"] if selected else "",
            "centroid_y_m": selected["centroid_y"] if selected else "",
            "centroid_z_m": selected["centroid_z"] if selected else "",
            "size_x_m": selected["size_x"] if selected else "",
            "size_y_m": selected["size_y"] if selected else "",
            "size_z_m": selected["size_z"] if selected else "",
            "association_distance_m": (
                association_distance
                if association_distance is not None else ""
            )
        })

        next_sample += 1

if not results:
    raise RuntimeError("No measurements processed")

with open(os.environ["C01_TRACK_CSV"], "x", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

print("SAMPLES_REQUESTED=", len(SAMPLE_TIMES))
print("SAMPLES_PROCESSED=", len(results))
print("ASSOCIATED_SAMPLES=", matched)
print("MISSING_SAMPLES=", rejected)
print("TRACKING_METHOD=NEAREST_NEIGHBOR")
print("ASSOCIATION_GATE_M=", ASSOCIATION_GATE)
print("GROUND_TRUTH_USED=NO")
print("TRACK_CSV=", os.environ["C01_TRACK_CSV"])

print("\n=== FIRST FIVE MEASUREMENTS ===")
for row in results[:5]:
    print(
        "TIME=", round(row["timestamp_s"], 6),
        "TRACK=", row["track_id"],
        "POINTS=", row["point_count"],
        "X=", row["centroid_x_m"],
        "Y=", row["centroid_y_m"],
        "Z=", row["centroid_z_m"]
    )

print("\n=== STATUS ===")
print("EKF_IMPLEMENTED=NO")
print("SENSOR_ONLY_TEMPORAL_ASSOCIATION=COMPLETE")
print("ORIGINAL_OSI_FILES_MODIFIED=NO")
print("TASK24_05_TEMPORAL_ASSOCIATION_COMPLETE")
