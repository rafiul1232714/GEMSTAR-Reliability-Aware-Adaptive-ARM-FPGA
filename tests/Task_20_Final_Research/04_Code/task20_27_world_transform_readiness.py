import csv
import json
import struct
from pathlib import Path

from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

def frames(path, limit=100):
    with path.open("rb") as f:
        for frame in range(limit):
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Invalid header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size < 100_000_000:
                raise ValueError("Invalid message length")

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Truncated message")

            msg = SensorView()
            msg.ParseFromString(payload)

            yield frame, msg

def populated(msg, field):
    return field in {
        f.name for f, _ in msg.ListFields()
    }

rows = []

print("\n=== TASK 20.27 TRANSFORM READINESS ===")

for path in sorted(RAW.rglob("*_sv_*.osi")):
    scenario = path.parent.name

    total = 0
    with_pose = 0
    with_mount = 0
    with_reflections = 0
    ready = 0

    for frame, sv in frames(path):
        total += 1

        pose = False
        mount = False
        reflections = False

        if populated(sv, "global_ground_truth"):
            gt = sv.global_ground_truth

            if populated(gt, "host_vehicle_id"):
                host = int(gt.host_vehicle_id.value)

                candidates = [
                    obj for obj in gt.moving_object
                    if int(obj.id.value) == host
                    and populated(obj.base, "position")
                    and populated(obj.base, "orientation")
                ]

                pose = bool(candidates)

        for view in sv.radar_sensor_view:
            if not populated(view, "view_configuration"):
                continue

            cfg = view.view_configuration

            if populated(cfg, "mounting_position"):
                mounting = cfg.mounting_position

                if (
                    populated(mounting, "position")
                    and populated(mounting, "orientation")
                ):
                    mount = True

            if len(view.reflection) > 0:
                reflections = True

        with_pose += int(pose)
        with_mount += int(mount)
        with_reflections += int(reflections)

        is_ready = pose and mount and reflections
        ready += int(is_ready)

        rows.append({
            "Recording": scenario,
            "Frame": frame,
            "HasHostPose": int(pose),
            "HasRadarMount": int(mount),
            "HasReflections": int(reflections),
            "AllInputsAvailable": int(is_ready)
        })

    print(
        f"{scenario:28s}"
        f" | Frames={total:3d}"
        f" | Pose={with_pose:3d}"
        f" | Mount={with_mount:3d}"
        f" | Reflections={with_reflections:3d}"
        f" | Ready={ready:3d}"
    )

csv_file = DATA / "task20_27_transform_readiness.csv"
json_file = FINDINGS / "task20_27_transform_readiness.json"

if rows:
    with csv_file.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

summary = {
    "Task": "20.27",
    "FramesChecked": len(rows),
    "FramesWithAllInputs": sum(
        r["AllInputsAvailable"] for r in rows
    ),
    "InputsChecked": [
        "Nested host pose",
        "Radar mounting position and orientation",
        "Radar reflection entries"
    ],
    "FrameTimingUncertaintyResolved": False,
    "RadarWorldCoordinatesValidated": False,
    "RadarAccuracyValidated": False,
    "HardwareEnergyMeasured": False
}

json_file.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.27 COMPLETE ===")
print("Frames checked:", summary["FramesChecked"])
print(
    "Frames with all inputs:",
    summary["FramesWithAllInputs"]
)
print("CSV saved:", csv_file.is_file())
print("JSON saved:", json_file.is_file())
print("Radar accuracy validated:", False)
