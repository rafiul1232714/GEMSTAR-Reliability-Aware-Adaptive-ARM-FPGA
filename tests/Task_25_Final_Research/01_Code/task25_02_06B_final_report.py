import csv
from pathlib import Path
from html import escape

ROOT = Path(
    r"E:\GEMSTAR_Project\sensor-health-monitor"
    r"\tests\Task_25_Final_Research"
)

CSV_DIR = ROOT / "02_CSV_Data"
PLOT_DIR = ROOT / "04_Plots"
REPORT_DIR = ROOT / "07_Research_Report"

HEALTH = CSV_DIR / "task25_20_c02_sensor_health_fullrate.csv"
FRESHNESS = CSV_DIR / "task25_12_c02_fullrate_freshness.csv"
VALIDATION = (
    ROOT / "06_Research_Findings"
    / "task25_21_sensor_health_validation.txt"
)

SENSORS = ["Camera", "LiDAR", "Radar"]
COLORS = {
    "Camera": "#2563eb",
    "LiDAR": "#059669",
    "Radar": "#d97706"
}

def load_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_svg(path, body, width, height):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'{body}</svg>'
    )
    path.write_text(svg, encoding="utf-8")

def main():
    data = load_csv(HEALTH)
    source = load_csv(FRESHNESS)

    if len(data) != 2122 or len(source) != 2122:
        raise RuntimeError("Expected 2122 rows in both CSVs")

    if not VALIDATION.is_file():
        raise RuntimeError("Missing validation evidence")

    if "TASK25_02_06A_PASS" not in VALIDATION.read_text(
        encoding="utf-8-sig"
    ):
        raise RuntimeError("Previous validation did not pass")

    counts = {}
    for sensor in SENSORS:
        statuses = [r[f"{sensor}_Status"] for r in data]
        counts[sensor] = {
            "new": statuses.count("NEW_PAYLOAD"),
            "repeat": statuses.count("REPEATED_PAYLOAD"),
            "first": statuses.count("FIRST_OBSERVATION"),
            "max_ms": max(
                float(r[f"{sensor}_UnchangedDuration_ms"])
                for r in data
            )
        }

        if sum(
            counts[sensor][x]
            for x in ("new", "repeat", "first")
        ) != 2122:
            raise RuntimeError(f"Invalid {sensor} counts")

    expected = {
        "Camera": (2121, 0),
        "LiDAR": (633, 1488),
        "Radar": (286, 1835)
    }

    for sensor, (new, repeat) in expected.items():
        if (
            counts[sensor]["new"] != new
            or counts[sensor]["repeat"] != repeat
        ):
            raise RuntimeError(
                f"Unexpected classification: {sensor}"
            )

    # Figure 1: status distribution.
    parts = [
        '<text x="65" y="52" font-family="Arial" '
        'font-size="25" font-weight="bold">'
        'C02 Sensor Payload Classification</text>',
        '<text x="65" y="81" font-family="Arial" '
        'font-size="14" fill="#555">'
        '2,121 consecutive-frame comparisons per sensor</text>'
    ]

    for index, sensor in enumerate(SENSORS):
        y = 130 + index * 100
        n = counts[sensor]["new"]
        r = counts[sensor]["repeat"]
        new_width = 680 * n / 2121
        rep_width = 680 * r / 2121

        parts.append(
            f'<text x="65" y="{y}" font-family="Arial" '
            f'font-size="17">{sensor}</text>'
        )
        parts.append(
            f'<rect x="65" y="{y+12}" width="{new_width:.3f}" '
            'height="35" fill="#059669"/>'
        )
        parts.append(
            f'<rect x="{65+new_width:.3f}" y="{y+12}" '
            f'width="{rep_width:.3f}" height="35" '
            'fill="#d97706"/>'
        )
        parts.append(
            f'<text x="65" y="{y+70}" font-family="Arial" '
            f'font-size="13" fill="#444">'
            f'Changed: {n} | Repeated: {r}</text>'
        )

    parts.extend([
        '<rect x="65" y="450" width="16" height="16" fill="#059669"/>',
        '<text x="89" y="463" font-family="Arial" font-size="14">'
        'Changed payload</text>',
        '<rect x="280" y="450" width="16" height="16" fill="#d97706"/>',
        '<text x="304" y="463" font-family="Arial" font-size="14">'
        'Repeated payload</text>'
    ])

    save_svg(
        PLOT_DIR / "task25_22_payload_status_summary.svg",
        "".join(parts), 850, 495
    )

    # Figure 2: full-rate repetition timeline.
    # Each frame contributes one small segment, preserving
    # all 2122 observations without downsampling.
    left = 135
    width = 900
    parts = [
        '<text x="65" y="48" font-family="Arial" '
        'font-size="24" font-weight="bold">'
        'C02 Full-Rate Sensor Payload Timeline</text>',
        '<text x="65" y="78" font-family="Arial" '
        'font-size="14" fill="#555">'
        'Orange = repeated compared with preceding frame</text>'
    ]

    for index, sensor in enumerate(SENSORS):
        y = 120 + 95 * index

        parts.append(
            f'<text x="35" y="{y+20}" font-family="Arial" '
            f'font-size="17">{sensor}</text>'
        )
        parts.append(
            f'<rect x="{left}" y="{y}" width="{width}" '
            'height="38" fill="#059669"/>'
        )

        for i in range(1, 2122):
            if data[i][f"{sensor}_Status"] == "REPEATED_PAYLOAD":
                x = left + width * i / 2122
                w = width / 2122 + 0.12
                parts.append(
                    f'<rect x="{x:.3f}" y="{y}" '
                    f'width="{w:.3f}" height="38" '
                    'fill="#d97706"/>'
                )

    for tick in (0, 10, 20, 30, 40, 50):
        # Relative elapsed time, not absolute timestamps.
        start_ns = int(data[0]["Timestamp_ns"])
        end_ns = int(data[-1]["Timestamp_ns"])
        elapsed = (end_ns - start_ns) / 1e9
        x = left + width * tick / elapsed

        parts.append(
            f'<line x1="{x:.2f}" y1="405" '
            f'x2="{x:.2f}" y2="416" stroke="#555"/>'
        )
        parts.append(
            f'<text x="{x-10:.2f}" y="437" '
            f'font-family="Arial" font-size="13">{tick}</text>'
        )

    parts.append(
        '<text x="450" y="476" font-family="Arial" '
        'font-size="15">Elapsed recording time (s)</text>'
    )

    save_svg(
        PLOT_DIR / "task25_23_sensor_freshness_timeline.svg",
        "".join(parts), 1100, 505
    )

    report = [
        "# Task 25.2 — Sensor Health and Freshness Research",
        "",
        "## 1. Dataset",
        "",
        "Scenario: C02 clean V2 moving-target experiment.",
        "SensorView recording: 2,122 frames.",
        "Sensors: Camera, LiDAR, Radar.",
        "",
        "## 2. Validated findings",
        "",
        "| Sensor | Changed | Repeated | Max unchanged (s) |",
        "|---|---:|---:|---:|"
    ]

    for sensor in SENSORS:
        c = counts[sensor]
        report.append(
            f'| {sensor} | {c["new"]} | {c["repeat"]} | '
            f'{c["max_ms"]/1000:.3f} |'
        )

    report.extend([
        "",
        "All counts exclude the first observation, for which",
        "there is no preceding frame to compare.",
        "",
        "The full-rate health table passed an independent",
        "frame-alignment, timestamp, status and duration check.",
        "",
        "Reflection-level boundary checks confirmed that",
        "LiDAR and Radar measurements themselves repeat",
        "during the investigated long unchanged intervals.",
        "",
        "## 3. Interpretation",
        "",
        "Exact payload repetition is observed, but the",
        "independent measurement acquisition time is unknown.",
        "An advancing SensorView timestamp does not prove",
        "that a new sensor acquisition occurred.",
        "",
        "Repeated measurements must not be treated as",
        "independent new observations by the fusion estimator.",
        "",
        "## 4. Configuration evidence",
        "",
        "The original and archived C02 V2 INI configurations",
        "have identical SHA256 hashes:",
        "",
        "1982F8C80901BB7C90EBB5B4808E999EEDE0FC41F98AB24B523C729948728290",
        "",
        "The preserved configuration includes all three",
        "sensor inputs and clear weather with weather effects",
        "disabled. Effective per-sensor acquisition rates",
        "and exact runtime provenance are not fully verified.",
        "",
        "## 5. Limitations",
        "",
        "- Repetition is not proof of a sensor hardware fault.",
        "- Independent sensor acquisition age is unknown.",
        "- Effective sensor update rates are not established.",
        "- Camera payload changes do not prove detection quality.",
        "- Sensor associations remain partly provisional.",
        "- No energy savings or hardware acceleration are",
        "  demonstrated by Task 25.2.",
        "- Full-rate payload checks do not mean the EKF was",
        "  evaluated on all 2,122 frames.",
        "",
        "## 6. Implications for Task 25.3",
        "",
        "Use controlled fault injection and matched comparisons.",
        "Track stale/repeated observations separately from",
        "intentional measurement dropout.",
        "Preserve quality constraints and record every",
        "accepted or rejected EKF update.",
        "",
        "## 7. Evidence",
        "",
        "- task25_12_c02_fullrate_freshness.csv",
        "- task25_13_repetition_runs.csv",
        "- task25_15_reflection_boundary_audit.csv",
        "- task25_19_c02_v2_config_hashes.csv",
        "- task25_20_c02_sensor_health_fullrate.csv",
        "- task25_21_sensor_health_validation.txt",
        "",
        "TASK25_02_06B_COMPLETE",
        ""
    ])

    report_path = (
        REPORT_DIR / "Task25_2_Sensor_Health_Final_Report.md"
    )
    report_path.write_text(
        "\n".join(report), encoding="utf-8"
    )

    for p in (
        PLOT_DIR / "task25_22_payload_status_summary.svg",
        PLOT_DIR / "task25_23_sensor_freshness_timeline.svg",
        report_path
    ):
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"Missing output: {p}")
        print("CREATED:", p)

    print("VALIDATED_FRAMES=2122")
    print("TASK25_02_06B_PASS")

if __name__ == "__main__":
    main()
