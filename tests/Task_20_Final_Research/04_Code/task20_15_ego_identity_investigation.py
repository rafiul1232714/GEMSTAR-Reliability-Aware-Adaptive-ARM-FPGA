import json
import struct
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
BASE = ROOT / "tests" / "Task_20_Final_Research"
RAW = ROOT / "data" / "raw"
OUT = BASE / "06_Research_Findings"
OUT.mkdir(parents=True, exist_ok=True)

def first_message(path, cls):
    with path.open("rb") as f:
        header = f.read(4)
        if len(header) != 4:
            raise RuntimeError("Missing OSI header")
        size = struct.unpack("<I", header)[0]
        if not 0 < size < 100_000_000:
            raise RuntimeError("Invalid OSI message size")
        payload = f.read(size)
        if len(payload) != size:
            raise RuntimeError("Truncated OSI payload")
    msg = cls()
    msg.ParseFromString(payload)
    return msg

def safe_text(msg, limit=3000):
    return str(msg)[:limit]

scenario = "baseline_clear"
folder = RAW / scenario

gt_paths = sorted(folder.glob("*_gt_*.osi"))
sv_paths = sorted(folder.glob("*_sv_*.osi"))

if len(gt_paths) != 1 or len(sv_paths) != 1:
    raise RuntimeError(
        f"Expected one GT and one SV file; "
        f"got GT={len(gt_paths)} SV={len(sv_paths)}"
    )

gt = first_message(gt_paths[0], GroundTruth)
sv = first_message(sv_paths[0], SensorView)

report = {
    "Recording": scenario,
    "GroundTruthDescriptorFields": [
        field.name for field in gt.DESCRIPTOR.fields
    ],
    "GroundTruthPopulatedFields": [
        field.name for field, _ in gt.ListFields()
    ],
    "SensorViewDescriptorFields": [
        field.name for field in sv.DESCRIPTOR.fields
    ],
    "SensorViewPopulatedFields": [
        field.name for field, _ in sv.ListFields()
    ],
    "HostOrEgoCandidates": {},
    "FirstFrameMovingObjects": [],
    "FirstFrameStationaryExamples": [],
    "EgoIdentityVerified": False,
}

for title, msg in [("GT", gt), ("SV", sv)]:
    for field, value in msg.ListFields():
        if any(word in field.name.lower()
               for word in ("host", "ego", "vehicle_id")):
            report["HostOrEgoCandidates"][
                title + "." + field.name
            ] = safe_text(value)

for obj in gt.moving_object:
    base = obj.base
    report["FirstFrameMovingObjects"].append({
        "ID": str(obj.id.value),
        "Position": [
            base.position.x,
            base.position.y,
            base.position.z
        ],
        "Dimensions": [
            base.dimension.length,
            base.dimension.width,
            base.dimension.height
        ],
        "OrientationYaw": base.orientation.yaw,
        "Velocity": [
            base.velocity.x,
            base.velocity.y,
            base.velocity.z
        ],
        "ObjectType": str(obj.type),
        "ModelReference": str(obj.model_reference),
        "PopulatedFields": [
            f.name for f, _ in obj.ListFields()
        ],
    })

for obj in list(gt.stationary_object)[:5]:
    report["FirstFrameStationaryExamples"].append({
        "ID": str(obj.id.value),
        "Position": [
            obj.base.position.x,
            obj.base.position.y,
            obj.base.position.z
        ],
        "Dimensions": [
            obj.base.dimension.length,
            obj.base.dimension.width,
            obj.base.dimension.height
        ],
    })

path = OUT / "task20_15_ego_identity_investigation.json"
path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)

print("\n=== TASK 20.15 EGO IDENTITY INVESTIGATION ===")
print("GT descriptor fields:")
print(report["GroundTruthDescriptorFields"])
print("\nGT populated fields:")
print(report["GroundTruthPopulatedFields"])
print("\nSV descriptor fields:")
print(report["SensorViewDescriptorFields"])
print("\nSV populated fields:")
print(report["SensorViewPopulatedFields"])
print("\nHost/ego candidate metadata:")
print(json.dumps(
    report["HostOrEgoCandidates"], indent=2
))
print("\nFirst-frame moving objects:")
for obj in report["FirstFrameMovingObjects"]:
    print(json.dumps(obj, indent=2))

print("\n=== TASK 20.15 COMPLETE ===")
print("Moving objects inspected:",
      len(report["FirstFrameMovingObjects"]))
print("Report saved:", path.is_file())
print("Report:", path)
print("Ego identity verified:", False)
