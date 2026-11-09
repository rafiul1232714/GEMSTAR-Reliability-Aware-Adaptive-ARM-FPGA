import sys
import math
import struct

from osi3.osi_sensorview_pb2 import SensorView

C = 299792458.0

with open(sys.argv[1], "rb") as f:
    prefix = f.read(4)
    size = struct.unpack("<I", prefix)[0]
    payload = f.read(size)

    if len(payload) != size:
        raise RuntimeError("Incomplete first OSI frame")

sv = SensorView()
sv.ParseFromString(payload)

if len(sv.lidar_sensor_view) != 1:
    raise RuntimeError("Expected one LiDAR view")

distances = []

for r in sv.lidar_sensor_view[0].reflection:
    if (
        math.isfinite(r.time_of_flight)
        and math.isfinite(r.signal_strength)
        and r.time_of_flight > 0
        and r.signal_strength > 0
    ):
        distance = C * r.time_of_flight / 2.0
        distances.append(distance)

if not distances:
    raise RuntimeError("No valid Clear returns")

distances.sort()

low_cutoff = 0.30286536 * 20.0
high_cutoff = 0.34634364 * 20.0

print("CLEAR_POSITIVE_RETURNS={}".format(len(distances)))
print("MIN_CLEAR_DISTANCE_M={:.6f}".format(distances[0]))
print("MEDIAN_CLEAR_DISTANCE_M={:.6f}".format(
    distances[len(distances) // 2]
))
print("MAX_CLEAR_DISTANCE_M={:.6f}".format(distances[-1]))

print("LOW_REFLECTIVITY_CUTOFF_M={:.6f}".format(low_cutoff))
print("HIGH_REFLECTIVITY_CUTOFF_M={:.6f}".format(high_cutoff))

print("RETURNS_WITHIN_LOW_CUTOFF={}".format(
    sum(d <= low_cutoff for d in distances)
))

print("RETURNS_WITHIN_HIGH_CUTOFF={}".format(
    sum(d <= high_cutoff for d in distances)
))

print("RETURNS_BEYOND_HIGH_CUTOFF={}".format(
    sum(d > high_cutoff for d in distances)
))

print("TASK23_11E_DISTANCE_THRESHOLD_ANALYSIS_PASS")
