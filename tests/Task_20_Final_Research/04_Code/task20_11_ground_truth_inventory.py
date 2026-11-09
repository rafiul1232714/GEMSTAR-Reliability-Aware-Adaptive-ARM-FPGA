import csv
import json
import struct
from pathlib import Path

from osi3.osi_groundtruth_pb2 import GroundTruth
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_20_Final_Research"

DATA = BASE / "02_CSV_Data"
FINDINGS = BASE / "06_Research_Findings"

DATA.mkdir(parents=True, exist_ok=True)
FINDINGS.mkdir(parents=True, exist_ok=True)

def first_messages(path, message_type, limit=5):
    with path.open("rb") as f:
        for i in range(limit):
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]

            if not (0 < size < 100_000_000):
                raise ValueError("Invalid OSI size")

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Truncated OSI payload")

            msg = message_type()
            msg.ParseFromString(payload)
            yield i, msg

def timestamp_text(msg):
    if not hasattr(msg, "timestamp"):
        return ""

    stamp = msg.timestamp

    if not stamp.ListFields():
        return ""

    return str(stamp).replace("\n", " ").strip()

def object_count(msg, field_name):
    if hasattr(msg, field_name):
        return len(getattr(msg, field_name))
    return None

def inspect_file(path, message_type, kind):
    samples = []

    for frame, msg in first_messages(
        path, message_type, limit=5
    ):
        samples.append({
            "Frame": frame,
            "Timestamp": timestamp_text(msg),
            "MovingObjects": object_count(
                msg, "moving_object"
            ),
            "StationaryObjects": object_count(
                msg, "stationary_object"
            ),
            "RadarViews": object_count(
                msg, "radar_sensor_view"
            ),
            "PopulatedTopLevelFields": ",".join(
                field.name
                for field, _ in msg.ListFields()
            ),
        })

    row = {
        "Recording": path.parent.name,
        "Kind": kind,
        "Filename": path.name,
        "FullPath": str(path),
        "FileBytes": path.stat().st_size,
        "FramesSampled": len(samples),
        "FirstTimestamp": (
            samples[0]["Timestamp"] if samples else ""
        ),
        "FirstMovingObjects": (
            samples[0]["MovingObjects"] if samples else None
        ),
        "FirstStationaryObjects": (
            samples[0]["StationaryObjects"]
            if samples else None
        ),
        "FirstRadarViews": (
            samples[0]["RadarViews"]
            if samples else None
        ),
        "Status": "OK"
    }

    return row, samples

def main():
    print("\n=== TASK 20.11 GROUND TRUTH INVENTORY ===")

    gt_files = sorted(RAW.rglob("*_gt_*.osi"))
    sv_files = sorted(RAW.rglob("*_sv_*.osi"))

    print("GroundTruth files found:", len(gt_files))
    print("SensorView files found:", len(sv_files))

    inventory = []
    details = []
    errors = []

    for kind, files, message_type in [
        ("GROUND_TRUTH", gt_files, GroundTruth),
        ("SENSOR_VIEW", sv_files, SensorView)
    ]:
        for path in files:
            try:
                row, samples = inspect_file(
                    path, message_type, kind
                )

                inventory.append(row)

                for sample in samples:
                    details.append({
                        "Recording": path.parent.name,
                        "Kind": kind,
                        "Filename": path.name,
                        **sample
                    })

                print(
                    f"{kind:13s} "
                    f"| {path.parent.name:28s} "
                    f"| Frames={len(samples)} "
                    f"| Objects={row['FirstMovingObjects']} "
                    f"| Radar={row['FirstRadarViews']} "
                    f"| Timestamp={row['FirstTimestamp'][:45]}"
                )

            except Exception as exc:
                errors.append({
                    "File": str(path),
                    "Error": str(exc)
                })

                print(
                    "ERROR:", path.name, str(exc)
                )

    def save_csv(name, rows):
        path = DATA / name

        if rows:
            with path.open(
                "w", encoding="utf-8", newline=""
            ) as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(rows[0])
                )
                writer.writeheader()
                writer.writerows(rows)

        return path

    inventory_file = save_csv(
        "task20_11_ground_truth_inventory.csv",
        inventory
    )

    samples_file = save_csv(
        "task20_11_ground_truth_sample_metadata.csv",
        details
    )

    # This only checks file presence within a recording
    # folder. It does NOT prove timestamp synchronization.
    scenarios = sorted(set(
        p.parent.name
        for p in gt_files + sv_files
    ))

    pairs = []

    for scenario in scenarios:
        gt = [
            p for p in gt_files
            if p.parent.name == scenario
        ]
        sv = [
            p for p in sv_files
            if p.parent.name == scenario
        ]

        pairs.append({
            "Recording": scenario,
            "GroundTruthFiles": len(gt),
            "SensorViewFiles": len(sv),
            "BothKindsPresent": bool(gt and sv),
            "TimestampAlignmentVerified": False,
        })

    pair_file = save_csv(
        "task20_11_ground_truth_pair_candidates.csv",
        pairs
    )

    report = {
        "Task": "20.11",
        "GroundTruthFiles": len(gt_files),
        "SensorViewFiles": len(sv_files),
        "RecordingFolders": len(scenarios),
        "FoldersWithBothKinds": sum(
            x["BothKindsPresent"] for x in pairs
        ),
        "Errors": errors,
        "TimestampAlignmentVerified": False,
        "RadarToObjectAssociationVerified": False,
        "GroundTruthAccuracyMeasured": False,
        "EnergyMeasured": False
    }

    report_file = (
        FINDINGS /
        "task20_11_ground_truth_inventory.json"
    )

    report_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print("\n=== TASK 20.11 COMPLETE ===")
    print("GroundTruth files:", len(gt_files))
    print("SensorView files:", len(sv_files))
    print(
        "Folders containing both:",
        report["FoldersWithBothKinds"]
    )
    print("Parsing errors:", len(errors))
    print(
        "Inventory CSV saved:",
        inventory_file.is_file()
    )
    print(
        "Metadata CSV saved:",
        samples_file.is_file()
    )
    print(
        "Pair candidates saved:",
        pair_file.is_file()
    )
    print(
        "JSON report saved:",
        report_file.is_file()
    )

    print("\nIMPORTANT:")
    print("File presence does not establish synchronization.")
    print("GroundTruth labels and object associations")
    print("still require verification.")

if __name__ == "__main__":
    main()
