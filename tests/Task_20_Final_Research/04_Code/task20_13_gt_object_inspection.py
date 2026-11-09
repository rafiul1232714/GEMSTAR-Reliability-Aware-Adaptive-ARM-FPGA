import csv
import json
import struct
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"
DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

def read_gt(path, limit=100):
    with path.open("rb") as f:
        for index in range(limit):
            header = f.read(4)
            if not header:
                break
            if len(header) != 4:
                raise RuntimeError("Incomplete header")

            size = struct.unpack("<I", header)[0]
            if not (0 < size < 100_000_000):
                raise RuntimeError("Invalid size")

            payload = f.read(size)
            if len(payload) != size:
                raise RuntimeError("Truncated message")

            msg = GroundTruth()
            msg.ParseFromString(payload)
            yield index, msg

def identifier(obj):
    try:
        return str(obj.id.value)
    except Exception:
        return ""

def position(base):
    try:
        return (
            base.position.x,
            base.position.y,
            base.position.z
        )
    except Exception:
        return (None, None, None)

def object_row(scenario, frame, stamp_ns, kind, obj):
    base = obj.base
    xyz = position(base)

    return {
        "Recording": scenario,
        "FrameIndex": frame,
        "TimestampNs": stamp_ns,
        "Kind": kind,
        "ObjectID": identifier(obj),
        "X": xyz[0],
        "Y": xyz[1],
        "Z": xyz[2],
        "Length": base.dimension.length,
        "Width": base.dimension.width,
        "Height": base.dimension.height,
        "Yaw": base.orientation.yaw,
        "Pitch": base.orientation.pitch,
        "Roll": base.orientation.roll,
    }

def field_names(obj):
    return [field.name for field, _ in obj.ListFields()]

def main():
    print("\n=== TASK 20.13 GT OBJECT INSPECTION ===")

    files = sorted(RAW.rglob("*_gt_*.osi"))

    rows = []
    summaries = []
    examples = {}

    for path in files:
        scenario = path.parent.name
        moving_total = 0
        stationary_total = 0
        frames = 0
        ids = set()

        for frame, msg in read_gt(path):
            frames += 1
            ts = (
                msg.timestamp.seconds * 1_000_000_000
                + msg.timestamp.nanos
            )

            for kind, objects in (
                ("MOVING", msg.moving_object),
                ("STATIONARY", msg.stationary_object)
            ):
                for obj in objects:
                    row = object_row(
                        scenario, frame, ts, kind, obj
                    )
                    rows.append(row)
                    ids.add((kind, row["ObjectID"]))

                    if kind == "MOVING":
                        moving_total += 1
                    else:
                        stationary_total += 1

                    if scenario not in examples:
                        examples[scenario] = {
                            "Kind": kind,
                            "TopLevelFields": field_names(obj),
                            "BaseFields": field_names(obj.base),
                            "SampleObject": row,
                        }

        summary = {
            "Recording": scenario,
            "Frames": frames,
            "MovingObjectEntries": moving_total,
            "StationaryObjectEntries": stationary_total,
            "UniqueKindIDPairs": len(ids),
        }
        summaries.append(summary)

        print(
            f"{scenario:28s}"
            f" | Frames={frames:3d}"
            f" | Moving={moving_total:5d}"
            f" | Stationary={stationary_total:5d}"
            f" | Unique IDs={len(ids)}"
        )

        if scenario in examples:
            ex = examples[scenario]
            print("  Object fields:", ex["TopLevelFields"])
            print("  Base fields:", ex["BaseFields"])
            print("  Example:", ex["SampleObject"])

    if not rows:
        raise RuntimeError("No GT objects found in sampled frames")

    csv_file = DATA / "task20_13_gt_objects.csv"
    summary_file = DATA / "task20_13_gt_summary.csv"
    json_file = FINDINGS / "task20_13_gt_schema_samples.json"

    def save_csv(path, items):
        with path.open(
            "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=list(items[0])
            )
            writer.writeheader()
            writer.writerows(items)

    save_csv(csv_file, rows)
    save_csv(summary_file, summaries)

    json_file.write_text(
        json.dumps(examples, indent=2, default=str),
        encoding="utf-8"
    )

    print("\n=== TASK 20.13 COMPLETE ===")
    print("GT files:", len(files))
    print("Object rows:", len(rows))
    print("Object CSV saved:", csv_file.is_file())
    print("Summary CSV saved:", summary_file.is_file())
    print("Schema JSON saved:", json_file.is_file())

    print("\nLIMITATIONS:")
    print("Ground-truth object centres are not radar hits.")
    print("Radar-to-object association not yet established.")
    print("Coordinate and ego-pose alignment still needed.")
    print("No perception accuracy or energy measured.")

if __name__ == "__main__":
    main()
