
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView
from osi3.osi_groundtruth_pb2 import GroundTruth

# ============================================
# TASK 11.1 - INSPECT GEMSTAR OSI MEASUREMENTS
# Camera + LiDAR + Radar + Ground Truth
# ============================================

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor")

RAW = ROOT / "data" / "raw" / "fog_mor100"

SV_FILE = (
    RAW / "20261027T224313Z_sv_380_X_466_GEMSTAR.osi"
)

GT_FILE = (
    RAW / "20261027T224313Z_gt_380_X_466_GEMSTAR.osi"
)

ARCHIVE = (
    ROOT / "tests" / "Task_11_Final_Research"
)

REPORT_DIR = ARCHIVE / "06_Research_Findings"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def read_osi(path, message_type):
    """Read length-prefixed protobuf messages."""

    with path.open("rb") as f:
        while True:
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                raise ValueError("Incomplete OSI header")

            size = int.from_bytes(header, "little")

            if size <= 0:
                raise ValueError(
                    f"Invalid message size: {size}"
                )

            payload = f.read(size)

            if len(payload) != size:
                raise ValueError("Incomplete OSI payload")

            message = message_type()
            message.ParseFromString(payload)
            yield message


def timestamp(message):
    return (
        message.timestamp.seconds
        + message.timestamp.nanos / 1e9
    )


def describe_message(message, indent="  "):
    """List protobuf fields without printing huge arrays."""

    for field, value in message.ListFields():

        name = field.name

        # Prevent printing all image bytes or reflections
        if name == "image_data":
            print(f"{indent}{name}: {len(value)} bytes")

        elif field.is_repeated:
            print(
                f"{indent}{name}: "
                f"{len(value)} entries"
            )

        else:
            text = str(value).replace("\n", " ")
            print(
                f"{indent}{name}: {text[:250]}"
            )


def inspect_sensorview():

    print("\n====================================")
    print("SENSORVIEW INSPECTION")
    print("====================================")

    for index, sv in enumerate(
        read_osi(SV_FILE, SensorView),
        start=1
    ):

        # Inspect only one representative later frame.
        # Frame 1 may contain initialization effects.
        if index != 101:
            continue

        print("Frame:", index)
        print("Timestamp:", timestamp(sv))

        print("\nCAMERA")
        print("Streams:", len(sv.camera_sensor_view))

        for i, camera in enumerate(sv.camera_sensor_view):
            print(f"\nCamera {i}")
            describe_message(camera)

            print("Camera configuration:")
            describe_message(camera.view_configuration, "    ")

        print("\nLIDAR")
        print("Streams:", len(sv.lidar_sensor_view))

        for i, lidar in enumerate(sv.lidar_sensor_view):
            print(f"\nLiDAR {i}")
            describe_message(lidar)

            print("LiDAR configuration:")
            describe_message(lidar.view_configuration, "    ")

            if len(lidar.reflection) > 0:
                print("First reflection:")
                describe_message(
                    lidar.reflection[0], "    "
                )

        print("\nRADAR")
        print("Streams:", len(sv.radar_sensor_view))

        for i, radar in enumerate(sv.radar_sensor_view):
            print(f"\nRadar {i}")
            describe_message(radar)

            print("Radar configuration:")
            describe_message(radar.view_configuration, "    ")

            if len(radar.reflection) > 0:
                print("First reflection:")
                describe_message(
                    radar.reflection[0], "    "
                )

        return

    raise RuntimeError(
        "Frame 101 not found in SensorView recording."
    )


def inspect_groundtruth():

    print("\n====================================")
    print("GROUND TRUTH INSPECTION")
    print("====================================")

    for index, gt in enumerate(
        read_osi(GT_FILE, GroundTruth),
        start=1
    ):

        if index != 101:
            continue

        print("Frame:", index)
        print("Timestamp:", timestamp(gt))

        print("Moving objects:", len(gt.moving_object))

        for i, obj in enumerate(gt.moving_object[:5]):

            print(f"\nObject {i}")

            describe_message(obj)

            if obj.HasField("base"):
                print("Object base:")
                describe_message(obj.base, "    ")

        return

    raise RuntimeError(
        "Frame 101 not found in Ground Truth recording."
    )


if __name__ == "__main__":

    if not SV_FILE.exists():
        raise FileNotFoundError(SV_FILE)

    if not GT_FILE.exists():
        raise FileNotFoundError(GT_FILE)

    inspect_sensorview()
    inspect_groundtruth()

    print("\nTASK 11.1 INSPECTION COMPLETE")
