from pathlib import Path
import csv
import json
import hashlib
import statistics
import math

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
T26 = ROOT / "Task_26_Final_Research"
T27 = ROOT / "Task_27_Final_Research"

CAMERA = T26 / "02_CSV_Data" / "task26_4B_camera_cpu_summary.csv"
RADAR = T26 / "02_CSV_Data" / "task26_4G_radar_cpu_summary.csv"
YOLO = T26 / "02_CSV_Data" / "task26_4J_yolo_cpu_summary.csv"

MODEL = ROOT / "Task_18_Final_Research" / "03_Configurations" / "Models" / "yolo11s.pt"

OUT = T27 / "02_CSV_Data" / "task27_4C_sensor_compute_characterization.csv"
REPORT = T27 / "06_Research_Findings" / "task27_4C_sensor_compute_findings.txt"
MANIFEST = T27 / "06_Research_Findings" / "task27_4C_input_manifest.json"

def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest().upper()

def write_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def make_row(
    workload, scenario, mode, frame,
    items, payload, nominal_intermediate,
    model_bytes, median_ms, p99_ms, scope
):
    return {
        "workload": workload,
        "scenario": scenario,
        "mode": mode,
        "frame": frame,
        "processing_items": items,
        "nominal_processing_input_bytes": payload,
        "nominal_intermediate_buffer_sum_bytes": nominal_intermediate,
        "stored_model_file_bytes": model_bytes,
        "archived_cpu_median_ms": median_ms,
        "archived_cpu_p99_ms": p99_ms,
        "processing_scope": scope,
        "memory_traffic_measured": "NO",
        "energy_measured": "NO"
    }

def main():
    print("=== TASK 27.4C: CAMERA RADAR YOLO ANALYSIS ===")

    sources = [CAMERA, RADAR, YOLO, MODEL]
    for path in sources:
        if not path.is_file():
            raise FileNotFoundError(path)

    for path in (OUT, REPORT, MANIFEST):
        if path.exists():
            raise FileExistsError(
                f"Existing research output preserved: {path}"
            )

    camera = read_csv(CAMERA)
    radar = read_csv(RADAR)
    yolo = read_csv(YOLO)

    if (len(camera), len(radar), len(yolo)) != (6, 12, 5):
        raise RuntimeError("Archived benchmark group counts changed")

    rows = []
    camera_weather = set()
    camera_groups = set()

    # Camera preprocessing uses:
    # BGR 3 bytes/pixel
    # Grayscale 1 byte/pixel
    # HSV 3 bytes/pixel
    # Canny 1 byte/pixel
    # Laplacian float64 8 bytes/pixel
    #
    # The nominal sum is 16 bytes/pixel.
    # This is NOT peak RAM or DRAM traffic.

    for r in camera:
        weather = r["weather"]
        mode = r["mode"]
        pixels = int(r["processed_pixels"])

        if mode == "FULL":
            assert pixels == 640 * 480
        elif mode == "ROI":
            assert pixels == 384 * 288
        else:
            raise RuntimeError(f"Unknown Camera mode: {mode}")

        camera_weather.add(weather)
        camera_groups.add((weather, mode))

        rows.append(make_row(
            "Camera",
            weather,
            mode,
            "",
            pixels,
            pixels * 3,
            pixels * 16,
            0,
            float(r["median_ms"]),
            float(r["p99_ms"]),
            "Preprocessing only; cropped processing region"
        ))

    assert camera_weather == {"CLEAR", "FOG100", "FOG20"}
    assert len(camera_groups) == 6

    # Radar: benchmark processes valid-return batches.
    # Model two float64 values per return:
    # time-of-flight and signal strength.
    # This is nominal serialization, not actual storage.
    radar_returns = 0

    for r in radar:
        count = int(r["returns_processed"])
        radar_returns += count

        rows.append(make_row(
            "Radar",
            str(r["pair_id"]),
            "VALID_RETURN_BATCH",
            int(r["frame"]),
            count,
            count * 16,
            0,
            0,
            float(r["median_ms"]),
            float(r["p99_ms"]),
            "Valid Radar returns only; no association"
        ))

    # YOLO images are 640x480 BGR in the verified audit.
    # File size on disk is not runtime parameter memory.
    model_bytes = MODEL.stat().st_size

    for r in yolo:
        rows.append(make_row(
            "YOLO11s",
            "C02_CONTROLLED",
            "CPU_INFERENCE",
            int(r["frame"]),
            640 * 480,
            640 * 480 * 3,
            0,
            model_bytes,
            float(r["median_ms"]),
            float(r["p99_ms"]),
            "Predict: preprocessing + inference + postprocessing"
        ))

    if len(rows) != 23:
        raise RuntimeError("Expected 23 characterization rows")

    for r in rows:
        if not math.isfinite(r["archived_cpu_median_ms"]):
            raise RuntimeError("Invalid CPU timing")
        if r["archived_cpu_median_ms"] <= 0:
            raise RuntimeError("Nonpositive CPU timing")

    # Validate nominal Camera model against Task 27.2C.
    buffer_csv = T27 / "02_CSV_Data" / "task27_2C_camera_buffer_audit.csv"
    buffer_rows = {r["Mode"]: r for r in read_csv(buffer_csv)}

    for mode, pixels in (("FULL", 307200), ("ROI", 110592)):
        if int(buffer_rows[mode]["Nominal_Buffer_Sum_Bytes"]) != pixels * 16:
            raise RuntimeError("Task 27.2C buffer model mismatch")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    write_csv(OUT, rows)

    manifest = {
        "task": "27.4C",
        "input_files": [
            {
                "path": str(p),
                "sha256": sha256(p),
                "size_bytes": p.stat().st_size
            }
            for p in sources + [buffer_csv]
        ],
        "camera_groups": len(camera),
        "radar_groups": len(radar),
        "yolo_groups": len(yolo),
        "camera_nominal_buffer_bytes_per_pixel": 16,
        "radar_nominal_bytes_per_return": 16,
        "yolo_model_file_bytes": model_bytes,
        "timings_rerun": False,
        "real_memory_traffic_measured": False,
        "hardware_energy_measured": False
    }

    with MANIFEST.open("x", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    camera_medians = [float(r["median_ms"]) for r in camera]
    radar_medians = [float(r["median_ms"]) for r in radar]
    yolo_medians = [float(r["median_ms"]) for r in yolo]

    findings = [
        "GEMSTAR TASK 27.4C - WORKLOAD CHARACTERIZATION",
        "==============================================",
        f"Camera configurations: {len(camera)}",
        f"Radar batches: {len(radar)}",
        f"YOLO frames: {len(yolo)}",
        f"Total characterization rows: {len(rows)}",
        "",
        f"Camera median of group medians: {statistics.median(camera_medians):.6f} ms",
        f"Radar median of group medians: {statistics.median(radar_medians):.6f} ms",
        f"YOLO median of group medians: {statistics.median(yolo_medians):.6f} ms",
        f"Radar valid returns in distinct benchmark batches: {radar_returns}",
        f"Stored YOLO model size: {model_bytes} bytes",
        "",
        "CAMERA BUFFER MODEL:",
        "BGR + grayscale + HSV + Canny + float64 Laplacian.",
        "Calculated intermediate-size sum: 16 bytes per pixel.",
        "ROI and FULL are alternative processing modes.",
        "",
        "RADAR MODEL:",
        "Nominal 16 bytes per valid input return.",
        "No invalid returns or association included in timing.",
        "",
        "YOLO MODEL:",
        "The measured CPU predict time includes preprocessing,",
        "inference and postprocessing, but not model loading.",
        "Model file size is NOT runtime activation or weight RAM.",
        "",
        "LIMITATIONS:",
        "No DRAM traffic, cache misses, or DMA bandwidth measured.",
        "No operation count or arithmetic intensity validated.",
        "No real ARM-FPGA timing or energy measured.",
        "Sensor accuracy is not established by these timings.",
        "Different workloads have different timing boundaries.",
        "No hardware kernels selected yet."
    ]

    with REPORT.open("x", encoding="utf-8") as f:
        f.write("\n".join(findings) + "\n")

    print("CAMERA_CONFIGURATIONS:", len(camera))
    print("RADAR_BATCH_GROUPS:", len(radar))
    print("YOLO_FRAMES:", len(yolo))
    print("CHARACTERIZATION_ROWS:", len(rows))
    print("RADAR_BENCHMARK_VALID_RETURNS:", radar_returns)
    print("STORED_YOLO_MODEL_BYTES:", model_bytes)
    print("CAMERA_BUFFER_MODEL_VALIDATED: YES")
    print("ACTUAL_MEMORY_TRAFFIC_MEASURED: NO")
    print("HARDWARE_ENERGY_MEASURED: NO")
    print("OUTPUT_CSV:", OUT)
    print("OUTPUT_FINDINGS:", REPORT)
    print("OUTPUT_MANIFEST:", MANIFEST)
    print("TASK27_4C_SENSOR_WORKLOAD_CHARACTERIZATION_DONE")

if __name__ == "__main__":
    main()