import argparse
import csv
import json
import struct
from pathlib import Path

from google.protobuf.message import DecodeError
from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

DEFAULT_ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_22_Final_Research"
)

MAX_MESSAGE_BYTES = 100 * 1024 * 1024


def iter_osi_messages(path, message_cls, limit):
    """Yield (frame index, decoded OSI message, byte size)."""

    with Path(path).open("rb") as f:
        frame = 0

        while frame < limit:
            header = f.read(4)

            if not header:
                return

            if len(header) != 4:
                raise ValueError(
                    f"Incomplete message header at frame {frame}"
                )

            size = struct.unpack("<I", header)[0]

            if size <= 0 or size > MAX_MESSAGE_BYTES:
                raise ValueError(
                    f"Invalid message size at frame {frame}: {size}"
                )

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError(
                    f"Truncated payload at frame {frame}: "
                    f"expected {size}, received {len(payload)}"
                )

            message = message_cls()

            try:
                message.ParseFromString(payload)
            except DecodeError as exc:
                raise ValueError(
                    f"Protobuf decoding failed at frame {frame}"
                ) from exc

            yield frame, message, size
            frame += 1


def timestamp_ns(message):
    ts = message.timestamp
    return int(ts.seconds) * 1_000_000_000 + int(ts.nanos)


def inspect_recording(path, kind, limit):
    cls = SensorView if kind == "SensorView" else GroundTruth
    records = []

    for frame, message, size in iter_osi_messages(
        path, cls, limit
    ):
        row = {
            "Filename": Path(path).name,
            "Type": kind,
            "Frame": frame,
            "TimestampNs": timestamp_ns(message),
            "MessageBytes": size,
            "CameraEntries": 0,
            "LiDAREntries": 0,
            "RadarEntries": 0,
            "MovingObjects": 0,
            "HostVehicleID": "",
            "SourcePath": str(Path(path).resolve())
        }

        if kind == "SensorView":
            row["CameraEntries"] = len(
                message.camera_sensor_view
            )
            row["LiDAREntries"] = len(
                message.lidar_sensor_view
            )
            row["RadarEntries"] = len(
                message.radar_sensor_view
            )
        else:
            row["MovingObjects"] = len(
                message.moving_object
            )
            row["HostVehicleID"] = int(
                message.host_vehicle_id.value
            )

        records.append(row)

    return records


def choose_inventory_files(inventory):
    selections = {}

    with inventory.open(
        "r", newline="", encoding="utf-8-sig"
    ) as f:
        rows = list(csv.DictReader(f))

    for kind in ("SensorView", "GroundTruth"):
        candidates = [
            row for row in rows
            if row.get("Type") == kind
            and Path(row.get("FullPath", "")).is_file()
        ]

        if not candidates:
            continue

        # Choose the smallest available recording,
        # minimizing work during this smoke test.
        candidates.sort(
            key=lambda row: Path(row["FullPath"]).stat().st_size
        )

        selections[kind] = Path(candidates[0]["FullPath"])

    return selections


def main():
    parser = argparse.ArgumentParser(
        description="Reusable GEMSTAR OSI stream reader"
    )

    parser.add_argument(
        "--task-dir",
        type=Path,
        default=DEFAULT_ROOT
    )

    parser.add_argument(
        "--sv",
        type=Path,
        default=None
    )

    parser.add_argument(
        "--gt",
        type=Path,
        default=None
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=3
    )

    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    task = args.task_dir
    inventory = (
        task / "02_CSV_Data" /
        "task22_01_recording_inventory.csv"
    )

    if not inventory.is_file():
        raise FileNotFoundError(
            f"Recording inventory missing: {inventory}"
        )

    selections = choose_inventory_files(inventory)

    if args.sv is not None:
        selections["SensorView"] = args.sv

    if args.gt is not None:
        selections["GroundTruth"] = args.gt

    csv_dir = task / "02_CSV_Data"
    finding_dir = task / "06_Research_Findings"

    csv_dir.mkdir(parents=True, exist_ok=True)
    finding_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    status = {}

    print("\n=== TASK 22.2 REUSABLE OSI READER ===")

    for kind in ("SensorView", "GroundTruth"):
        path = selections.get(kind)

        if path is None:
            print(f"{kind}: NO RECORDING FOUND")
            status[kind] = {
                "Success": False,
                "Reason": "No available input file"
            }
            continue

        print(f"\n{kind} file: {path.name}")

        try:
            records = inspect_recording(
                path, kind, args.limit
            )

            all_records.extend(records)

            status[kind] = {
                "Success": len(records) > 0,
                "InputFile": str(path),
                "MessagesRead": len(records)
            }

            print(f"Messages decoded: {len(records)}")

            for row in records:
                print(
                    f"Frame={row['Frame']} | "
                    f"TimestampNs={row['TimestampNs']} | "
                    f"Bytes={row['MessageBytes']} | "
                    f"Camera={row['CameraEntries']} | "
                    f"LiDAR={row['LiDAREntries']} | "
                    f"Radar={row['RadarEntries']} | "
                    f"GTObjects={row['MovingObjects']}"
                )

        except (OSError, ValueError, DecodeError) as exc:
            status[kind] = {
                "Success": False,
                "InputFile": str(path),
                "Error": str(exc)
            }

            print(f"ERROR: {exc}")

    csv_path = (
        csv_dir / "task22_02_osi_reader_validation.csv"
    )

    columns = [
        "Filename", "Type", "Frame",
        "TimestampNs", "MessageBytes",
        "CameraEntries", "LiDAREntries",
        "RadarEntries", "MovingObjects",
        "HostVehicleID", "SourcePath"
    ]

    with csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(all_records)

    json_path = (
        finding_dir / "task22_02_reader_validation.json"
    )

    json_path.write_text(
        json.dumps({
            "Task": "22.2",
            "MessageLimitPerFile": args.limit,
            "Status": status,
            "RecordsDecoded": len(all_records),
            "Limitations": [
                "Only a subset of messages was inspected",
                "No complete file-integrity scan performed",
                "Sensor entry presence does not prove payload validity",
                "Selected SV and GT files are not necessarily paired",
                "Timestamps were not compared between recordings",
                "No energy or detection-accuracy measurement"
            ]
        }, indent=2),
        encoding="utf-8"
    )

    print("\n=== TASK 22.2 FILE VERIFICATION ===")
    print("Records decoded:", len(all_records))
    print("CSV saved:", csv_path.is_file())
    print("JSON saved:", json_path.is_file())

    for kind in ("SensorView", "GroundTruth"):
        print(
            f"{kind} success:",
            status.get(kind, {}).get("Success", False)
        )

    print("\n=== TASK 22.2 COMPLETE ===")


if __name__ == "__main__":
    main()
