import csv
import struct
from pathlib import Path
from google.protobuf.descriptor import FieldDescriptor
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")
RAW = ROOT / "data" / "raw"
BASE = ROOT / "tests" / "Task_18_Camera_Extension_Final_Research"
OUT = BASE / "02_CSV_Data" / "task18_e2_camera_payload_report.csv"

MAX_FRAMES = 30

def messages(path):
    with path.open("rb") as f:
        for index in range(MAX_FRAMES):
            header = f.read(4)
            if len(header) != 4:
                return

            size = struct.unpack("<I", header)[0]
            if not 0 < size < 100_000_000:
                raise ValueError("Invalid OSI message size")

            payload = f.read(size)
            if len(payload) != size:
                return

            msg = SensorView()
            msg.ParseFromString(payload)
            yield index, msg

def describe_fields(message, prefix="", depth=0):
    """Inspect populated protobuf fields without printing image bytes."""
    output = []

    if depth > 5:
        return output

    for descriptor, value in message.ListFields():
        name = prefix + descriptor.name

        if descriptor.is_repeated:
            output.append((name, "COUNT", len(value)))

            if value and descriptor.type == FieldDescriptor.TYPE_MESSAGE:
                output.extend(
                    describe_fields(
                        value[0],
                        name + "[0].",
                        depth + 1
                    )
                )
            continue

        if descriptor.type == FieldDescriptor.TYPE_BYTES:
            output.append((name, "BYTES", len(value)))

        elif descriptor.type == FieldDescriptor.TYPE_MESSAGE:
            output.append((name, "MESSAGE", value.ByteSize()))
            output.extend(
                describe_fields(
                    value, name + ".", depth + 1
                )
            )
        else:
            output.append((name, "VALUE", str(value)[:100]))

    return output

def main():
    print("\n=== TASK 18.E2 CAMERA PAYLOAD INSPECTION ===")

    files = sorted(RAW.rglob("*_sv_*.osi"))
    rows = []

    for path in files:
        camera_frames = 0
        populated = 0
        largest = 0
        interesting = set()
        first_fields = []

        try:
            for index, msg in messages(path):
                for camera in msg.camera_sensor_view:
                    camera_frames += 1
                    largest = max(largest, camera.ByteSize())

                    fields = describe_fields(camera)

                    if not first_fields:
                        first_fields = fields

                    for field, kind, value in fields:
                        if kind == "BYTES" and value > 0:
                            populated += 1

                        interesting.add(field)

            print("\nRecording:", path.parent.name)
            print("Camera views:", camera_frames)
            print("Largest camera message:", largest, "bytes")
            print("Nonempty byte fields observed:", populated)

            print("Fields in first camera view:")
            for name, kind, value in first_fields[:35]:
                print(" ", name, "|", kind, "|", value)

            rows.append({
                "Recording": path.parent.name,
                "File": path.name,
                "CameraViewsChecked": camera_frames,
                "LargestCameraMessageBytes": largest,
                "NonemptyByteFields": populated,
                "PopulatedFieldPaths": "; ".join(sorted(interesting)),
                "Status": "INSPECTED"
            })

        except Exception as exc:
            print("ERROR:", path.name, exc)
            rows.append({
                "Recording": path.parent.name,
                "File": path.name,
                "CameraViewsChecked": camera_frames,
                "LargestCameraMessageBytes": largest,
                "NonemptyByteFields": populated,
                "PopulatedFieldPaths": "",
                "Status": "ERROR: " + str(exc)[:120]
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== TASK 18.E2 COMPLETE ===")
    print("Recordings inspected:", len(rows))
    print("CSV saved:", OUT)

if __name__ == "__main__":
    main()
