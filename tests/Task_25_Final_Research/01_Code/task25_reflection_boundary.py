import csv
import hashlib
import struct
from pathlib import Path
from osi3.osi_sensorview_pb2 import SensorView

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor\tests"
    r"\Task_25_Final_Research"
)

SOURCE = Path(
    r"E:\GEMSTAR_Project\gemstar\Output"
    r"\20261108T211139Z_sv_380_X_2122_GEMSTAR.osi"
)

OUTPUT = ROOT / "02_CSV_Data" / (
    "task25_15_reflection_boundary_audit.csv"
)

FRAMES = {
    2, 3, 188, 189, 190,
    1297, 1298, 1299, 1300,
    1467, 1468, 1469, 1470,
    1800, 1801, 2000, 2001, 2120, 2121
}

def reflection_hash(view):
    h = hashlib.sha256()

    for reflection in view.reflection:
        data = reflection.SerializeToString(
            deterministic=True
        )
        h.update(struct.pack("<I", len(data)))
        h.update(data)

    return h.hexdigest()

def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)

    results = []

    with SOURCE.open("rb") as stream:
        for frame in range(2122):
            header = stream.read(4)

            if len(header) != 4:
                raise RuntimeError("Incomplete OSI header")

            size = struct.unpack("<I", header)[0]

            if not 0 < size <= 100_000_000:
                raise RuntimeError("Invalid OSI payload size")

            if frame not in FRAMES:
                stream.seek(size, 1)
                continue

            payload = stream.read(size)

            if len(payload) != size:
                raise RuntimeError("Truncated OSI frame")

            sv = SensorView()
            sv.ParseFromString(payload)

            if (len(sv.lidar_sensor_view) != 1 or
                len(sv.radar_sensor_view) != 1):
                raise RuntimeError("Unexpected sensor count")

            for sensor, view in (
                ("LiDAR", sv.lidar_sensor_view[0]),
                ("Radar", sv.radar_sensor_view[0])
            ):
                valid = sum(
                    r.time_of_flight > 0
                    for r in view.reflection
                )

                nonzero_doppler = sum(
                    abs(r.doppler_shift) > 1e-9
                    for r in view.reflection
                )

                results.append({
                    "Frame": frame,
                    "Sensor": sensor,
                    "ReflectionCount": len(view.reflection),
                    "PositiveTOFCount": valid,
                    "NonzeroDopplerCount": nonzero_doppler,
                    "ReflectionSHA256": reflection_hash(view)
                })

        if stream.read(1):
            raise RuntimeError("Extra data after expected frames")

    if len(results) != 2 * len(FRAMES):
        raise RuntimeError("Incomplete reflection audit")

    with OUTPUT.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(results[0])
        )
        writer.writeheader()
        writer.writerows(results)

    print("REFLECTION_AUDIT_PASS")
    print("INSPECTED_FRAMES=", len(FRAMES))

    for sensor in ("LiDAR", "Radar"):
        rows = [
            r for r in results
            if r["Sensor"] == sensor
        ]
        print(
            sensor,
            "UNIQUE_REFLECTION_HASHES=",
            len(set(r["ReflectionSHA256"] for r in rows))
        )

        for r in rows:
            print(
                f'{sensor} FRAME={r["Frame"]} '
                f'VALID_TOF={r["PositiveTOFCount"]} '
                f'NONZERO_DOPPLER={r["NonzeroDopplerCount"]} '
                f'HASH={r["ReflectionSHA256"][:12]}'
            )

    print("SAVED=", OUTPUT)
    print("ORIGINAL_OSI_MODIFIED=NO")

if __name__ == "__main__":
    main()
