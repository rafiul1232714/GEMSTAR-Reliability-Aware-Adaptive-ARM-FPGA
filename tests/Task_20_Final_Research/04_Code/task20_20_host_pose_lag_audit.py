import csv
import json
import math
import struct
from pathlib import Path
from statistics import median

from osi3.osi_groundtruth_pb2 import GroundTruth
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

LIMIT = 100
OFFSETS = (-2, -1, 0, 1, 2)

def read_file(path, cls):
    result = []
    with path.open("rb") as f:
        for index in range(LIMIT):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise ValueError("Incomplete header")
            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid size")
            payload = f.read(size)
            if len(payload) != size:
                raise ValueError("Truncated payload")
            msg = cls()
            msg.ParseFromString(payload)
            result.append(msg)
    return result

def xyz(obj):
    p = obj.base.position
    return (float(p.x), float(p.y), float(p.z))

def distance(a, b):
    return math.sqrt(sum(
        (x-y)**2 for x, y in zip(a, b)
    ))

rows = []
summary = []
status_counts = {}

print("\n=== TASK 20.20 HOST POSE LAG AUDIT ===")
print("Offset: GT frame index minus SensorView frame index")

for folder in sorted(RAW.iterdir()):
    if not folder.is_dir():
        continue

    gt_paths = list(folder.glob("*_gt_*.osi"))
    sv_paths = list(folder.glob("*_sv_*.osi"))

    if len(gt_paths) != 1 or len(sv_paths) != 1:
        continue

    gt_frames = read_file(gt_paths[0], GroundTruth)
    sv_frames = read_file(sv_paths[0], SensorView)

    for offset in OFFSETS:
        xy_errors = []
        xyz_errors = []
        z_errors = []
        duplicates = 0
        inconsistent = 0
        matched_frames = 0

        for i, sv in enumerate(sv_frames):
            j = i + offset

            if not (0 <= j < len(gt_frames)):
                continue

            if not sv.HasField("global_ground_truth"):
                continue

            ngt = sv.global_ground_truth
            if not ngt.HasField("host_vehicle_id"):
                continue

            host_id = int(ngt.host_vehicle_id.value)

            hosts = [
                o for o in ngt.moving_object
                if int(o.id.value) == host_id
            ]

            gt_hosts = [
                o for o in gt_frames[j].moving_object
                if int(o.id.value) == host_id
            ]

            if not hosts or len(gt_hosts) != 1:
                continue

            nested_positions = [xyz(o) for o in hosts]
            duplicates += max(0, len(hosts) - 1)

            if any(
                distance(p, nested_positions[0]) > 1e-6
                for p in nested_positions[1:]
            ):
                inconsistent += 1
                continue

            a = nested_positions[0]
            b = xyz(gt_hosts[0])

            xy = math.hypot(a[0]-b[0], a[1]-b[1])
            dz = abs(a[2]-b[2])
            total = distance(a, b)

            xy_errors.append(xy)
            z_errors.append(dz)
            xyz_errors.append(total)
            matched_frames += 1

            rows.append({
                "Recording": folder.name,
                "SVFrame": i,
                "GTFrame": j,
                "GTMinusSVFrameOffset": offset,
                "HostID": host_id,
                "DuplicateHostEntries": len(hosts),
                "NestedX": a[0],
                "NestedY": a[1],
                "NestedZ": a[2],
                "GTX": b[0],
                "GTY": b[1],
                "GTZ": b[2],
                "XYErrorM": xy,
                "ZAbsErrorM": dz,
                "XYZErrorM": total,
            })

        result = {
            "Recording": folder.name,
            "GTMinusSVFrameOffset": offset,
            "MatchedFrames": matched_frames,
            "ExtraNestedDuplicateEntries": duplicates,
            "InconsistentDuplicateFrames": inconsistent,
            "MedianXYErrorM": (
                median(xy_errors) if xy_errors else None
            ),
            "MedianZAbsErrorM": (
                median(z_errors) if z_errors else None
            ),
            "MedianXYZErrorM": (
                median(xyz_errors) if xyz_errors else None
            ),
        }
        summary.append(result)

        if matched_frames:
            print(
                f"{folder.name:28s}"
                f" | Offset={offset:+d}"
                f" | Frames={matched_frames:3d}"
                f" | ExtraDuplicates={duplicates:3d}"
                f" | XY={median(xy_errors):.4f}m"
                f" | Z={median(z_errors):.4f}m"
                f" | XYZ={median(xyz_errors):.4f}m"
            )

def write_csv(path, values):
    if not values:
        return
    with path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f, fieldnames=list(values[0])
        )
        w.writeheader()
        w.writerows(values)

details_path = DATA / "task20_20_host_pose_lag_details.csv"
summary_path = DATA / "task20_20_host_pose_lag_summary.csv"
report_path = FINDINGS / "task20_20_host_pose_lag_audit.json"

write_csv(details_path, rows)
write_csv(summary_path, summary)

report_path.write_text(
    json.dumps({
        "Task": "20.20",
        "OffsetConvention": "GT index minus SV index",
        "Comparisons": summary,
        "Interpretation": (
            "Frame-offset comparison is diagnostic only; "
            "it does not prove synchronization or accuracy."
        ),
        "ValidatedRadarAccuracy": False,
        "MeasuredEnergy": False
    }, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.20 COMPLETE ===")
print("Comparisons:", len(rows))
print("Details CSV saved:", details_path.is_file())
print("Summary CSV saved:", summary_path.is_file())
print("Report saved:", report_path.is_file())
print("Radar accuracy validated:", False)
print("Energy measured:", False)
