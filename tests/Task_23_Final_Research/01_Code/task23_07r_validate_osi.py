from pathlib import Path
import struct
import csv

root = Path(r"E:\GEMSTAR_Project\gemstar\Output")
task = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests\Task_23_Final_Research")

names = [
    "20261103T152603Z_sv_380_X_1534_GEMSTARADAR.osi",
    "20261103T152603Z_gt_380_X_1534_GEMSTARADAR.osi",
]

results = []

for name in names:
    path = root / name

    if not path.exists():
        results.append({
            "File": name,
            "Status": "MISSING",
            "Messages": 0,
            "FileBytes": 0,
            "ParsedBytes": 0
        })
        continue

    count = 0
    status = "VALID_LENGTH_PREFIX_STRUCTURE"

    with path.open("rb") as f:
        while True:
            header = f.read(4)

            if not header:
                break

            if len(header) != 4:
                status = "INCOMPLETE_HEADER"
                break

            size = struct.unpack("<I", header)[0]

            if size == 0 or size > 100_000_000:
                status = "INVALID_MESSAGE_SIZE"
                break

            payload = f.read(size)

            if len(payload) != size:
                status = "TRUNCATED_MESSAGE"
                break

            count += 1

        parsed_bytes = f.tell()

    results.append({
        "File": name,
        "Status": status,
        "Messages": count,
        "FileBytes": path.stat().st_size,
        "ParsedBytes": parsed_bytes
    })

output = task / "02_CSV_Data" / "task23_07r_osi_structure_validation.csv"
output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print("\n=== TASK 23.7R — OSI RECORDING VALIDATION ===")

for result in results:
    print("\nFile:", result["File"])
    print("Status:", result["Status"])
    print("Messages:", result["Messages"])
    print("File bytes:", result["FileBytes"])
    print("Parsed bytes:", result["ParsedBytes"])

print("\nCSV saved:", output)
