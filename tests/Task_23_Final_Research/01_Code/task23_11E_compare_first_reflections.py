import sys
import struct
import math

from osi3.osi_sensorview_pb2 import SensorView

def read_first_frame(path):
    with open(path, "rb") as f:
        prefix = f.read(4)

        if len(prefix) != 4:
            raise RuntimeError("Missing OSI frame header")

        size = struct.unpack("<I", prefix)[0]
        data = f.read(size)

        if len(data) != size:
            raise RuntimeError("Incomplete OSI frame")

        sv = SensorView()
        sv.ParseFromString(data)

        if len(sv.lidar_sensor_view) != 1:
            raise RuntimeError("Expected one LiDAR view")

        return sv.lidar_sensor_view[0]

clear = read_first_frame(sys.argv[1])
fog = read_first_frame(sys.argv[2])

a = clear.reflection
b = fog.reflection

if len(a) != len(b):
    raise RuntimeError("Reflection slot count mismatch")

clear_positive = 0
fog_positive = 0
tof_same = 0
strength_same = 0
clear_positive_fog_zero = 0
fog_zero_strength = 0
fog_positive_tof = 0

for x, y in zip(a, b):

    if x.time_of_flight == y.time_of_flight:
        tof_same += 1

    if x.signal_strength == y.signal_strength:
        strength_same += 1

    xvalid = (
        math.isfinite(x.time_of_flight)
        and math.isfinite(x.signal_strength)
        and x.time_of_flight > 0
        and x.signal_strength > 0
    )

    yvalid = (
        math.isfinite(y.time_of_flight)
        and math.isfinite(y.signal_strength)
        and y.time_of_flight > 0
        and y.signal_strength > 0
    )

    clear_positive += xvalid
    fog_positive += yvalid

    if xvalid and y.signal_strength == 0:
        clear_positive_fog_zero += 1

    if y.signal_strength == 0:
        fog_zero_strength += 1

    if math.isfinite(y.time_of_flight) and y.time_of_flight > 0:
        fog_positive_tof += 1

print("TOTAL_REFLECTION_SLOTS={}".format(len(a)))
print("CLEAR_POSITIVE_RETURNS={}".format(clear_positive))
print("FOG_POSITIVE_RETURNS={}".format(fog_positive))

print("SAME_TIME_OF_FLIGHT_SLOTS={}".format(tof_same))
print("SAME_SIGNAL_STRENGTH_SLOTS={}".format(strength_same))

print("CLEAR_POSITIVE_TO_FOG_ZERO_STRENGTH={}".format(
    clear_positive_fog_zero
))

print("FOG_ZERO_SIGNAL_STRENGTH_SLOTS={}".format(
    fog_zero_strength
))

print("FOG_POSITIVE_TIME_OF_FLIGHT_SLOTS={}".format(
    fog_positive_tof
))

print("\nTASK23_11E_REFLECTION_COMPARISON_PASS")
