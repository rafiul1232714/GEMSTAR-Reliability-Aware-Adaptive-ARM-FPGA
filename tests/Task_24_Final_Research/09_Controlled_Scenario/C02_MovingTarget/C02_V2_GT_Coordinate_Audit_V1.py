import csv
import struct
import sys
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth

gt_path = Path(sys.argv[1])
track_path = Path(sys.argv[2])

selected = {0, 245, 530, 816, 938}

tracks = {}

with track_path.open(
    newline="",
    encoding="utf-8-sig"
) as f:
    for row in csv.DictReader(f):
        if int(row["track_id"]) == 2:
            tracks[int(row["frame"])] = row

count = 0
selected_found = set()

with gt_path.open("rb") as f:
    while True:

        header = f.read(4)

        if not header:
            break

        if len(header) != 4:
            raise RuntimeError("Incomplete Ground Truth header")

        size = struct.unpack("<I", header)[0]

        if size <= 0 or size > 100_000_000:
            raise RuntimeError(
                f"Invalid Ground Truth message size at frame {count}: {size}"
            )

        if count not in selected:
            f.seek(size, 1)
            count += 1
            continue

        payload = f.read(size)

        if len(payload) != size:
            raise RuntimeError("Incomplete Ground Truth payload")

        gt = GroundTruth()
        gt.ParseFromString(payload)

        selected_found.add(count)

        t = (
            gt.timestamp.seconds
            + gt.timestamp.nanos * 1e-9
        )

        print()
        print("FRAME=", count)
        print("GT_TIME_S=", round(t, 9))
        print("GT_MOVING_OBJECTS=", len(gt.moving_object))

        if count in tracks:

            r = tracks[count]

            print(
                "ESTIMATED_TRACK2_XY_M=",
                (r["x_m"], r["y_m"])
            )

            print("TRACK2_TIME_S=", r["time_s"])

            difference = abs(
                t - float(r["time_s"])
            )

            print(
                "TIMESTAMP_DIFFERENCE_S=",
                round(difference, 9)
            )

        else:
            print("TRACK2_AT_FRAME=NOT_AVAILABLE")

        print("FIRST_GROUND_TRUTH_OBJECTS:")

        for i, obj in enumerate(gt.moving_object[:12]):

            p = obj.base.position
            v = obj.base.velocity

            print(
                f"  INDEX={i} "
                f"ID={obj.id.value} "
                f"POSITION=({p.x:.3f},{p.y:.3f},{p.z:.3f}) "
                f"VELOCITY=({v.x:.3f},{v.y:.3f},{v.z:.3f})"
            )

        count += 1

if count != 2122:
    raise RuntimeError(
        f"Expected 2122 GT frames, found {count}"
    )

if selected_found != selected:
    raise RuntimeError(
        f"Missing selected frames: {selected - selected_found}"
    )

print()
print("TOTAL_GT_FRAMES=", count)
print("SELECTED_FRAMES_INSPECTED=", len(selected_found))
print("EXPECTED_GT_FRAMES=2122")
print("OBJECT_IDS_USED_FOR_TRACKING=NO")
print("GROUND_TRUTH_USED_FOR_EVALUATION_PREPARATION_ONLY=YES")
print("ERROR_METRICS_COMPUTED=NO")
print("ORIGINAL_FILES_MODIFIED=NO")
print("TASK24_10_01_GT_AUDIT_COMPLETE")