from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import math

ROOT = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")
TASK = ROOT / "Task_27_Final_Research"
DATA = TASK / "02_CSV_Data"
PLOTS = TASK / "04_Plots"
FINDINGS = TASK / "06_Research_Findings"
REPORT_DIR = TASK / "07_Research_Report"

AUDIT = FINDINGS / "task27_7A_validation_audit.json"
REGISTER = DATA / "task27_7A_evidence_register.csv"

CPU = DATA / "task27_4A_cpu_workload_summary.csv"
LIDAR = DATA / "task27_3A_lidar_workload_metrics.csv"
MEMORY = DATA / "task27_3C_lidar_memory_model.csv"
KERNELS = DATA / "task27_6A_fpga_candidate_matrix.csv"
BREAK_EVEN = DATA / "task27_6B_break_even_summary.csv"
BREAK_CASES = DATA / "task27_6B_break_even_scenarios.csv"

FINAL_REPORT = REPORT_DIR / "task27_7B_final_research_report.md"
ARCHIVE_CSV = REPORT_DIR / "task27_7B_archive_sha256_manifest.csv"
VERIFICATION = REPORT_DIR / "task27_7B_final_verification.json"

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def load_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def csv_write_new(path, rows):
    with path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def main():
    print("=== TASK 27.7B: FINAL RESEARCH VERIFICATION ===")

    sources = [
        AUDIT, REGISTER, CPU, LIDAR, MEMORY,
        KERNELS, BREAK_EVEN, BREAK_CASES
    ]

    for path in sources:
        require(path.is_file(), f"Missing required input: {path}")

    for path in (FINAL_REPORT, ARCHIVE_CSV, VERIFICATION):
        require(not path.exists(), f"Existing output preserved: {path}")

    audit = load_json(AUDIT)
    register = load_csv(REGISTER)
    cpu = load_csv(CPU)
    lidar = load_csv(LIDAR)
    memory = load_csv(MEMORY)
    kernels = load_csv(KERNELS)
    break_even = load_csv(BREAK_EVEN)
    break_cases = load_csv(BREAK_CASES)

    require(audit.get("status") == "PASS",
            "Task 27.7A audit did not pass")

    require(audit.get("registered_datasets") == 20,
            "Expected 20 registered datasets")

    require(audit.get("source_hashes_verified") >= 15,
            "Expected at least 15 verified hashes")

    require(len(register) == 20,
            "Evidence register row count mismatch")

    for row in register:
        require(row["status"] == "PASS",
                f"Evidence check failed: {row['dataset']}")

        path = Path(row["file_path"])
        require(path.is_file(),
                f"Registered dataset missing: {path}")

        require(sha256(path) == row["sha256"].upper(),
                f"Registered dataset hash changed: {path.name}")

    require(len(cpu) == 6, "CPU workload count mismatch")
    require(len(lidar) == 53, "LiDAR frame count mismatch")
    require(len(memory) == 53, "Memory frame count mismatch")
    require(len(kernels) == 5, "Candidate count mismatch")
    require(len(break_even) == 12, "Break-even summary mismatch")
    require(len(break_cases) == 354, "Break-even cases mismatch")

    cpu_rows = sum(int(r["timing_rows"]) for r in cpu)
    require(cpu_rows == 6025, "CPU timing count mismatch")

    input_points = sum(int(r["input_points"]) for r in lidar)
    filtered_points = sum(int(r["filtered_points"]) for r in lidar)

    require(input_points == 172839, "LiDAR input mismatch")
    require(filtered_points == 16295, "LiDAR filtered mismatch")

    input_bytes = sum(
        int(r["nominal_input_xyz_bytes"]) for r in memory
    )
    output_bytes = sum(
        int(r["nominal_output_xyz_bytes"]) for r in memory
    )
    roundtrip_bytes = sum(
        int(r["model_roundtrip_payload_bytes"]) for r in memory
    )

    require(input_bytes == 2074068, "Input payload mismatch")
    require(output_bytes == 195540, "Output payload mismatch")
    require(roundtrip_bytes == input_bytes + output_bytes,
            "Round-trip payload mismatch")

    shortlisted = [
        r["kernel"] for r in kernels
        if r["decision"] == "PROVISIONAL_SHORTLIST"
    ]

    require(
        set(shortlisted) == {
            "LiDAR_filter", "Camera_preprocessing"
        },
        "Provisional shortlist mismatch"
    )

    require(all(
        r["energy_saving_demonstrated"] == "NO"
        for r in break_cases
    ), "Unsupported hardware energy claim")

    # Check all 24 MATLAB research figures.
    # Each should have PNG and editable FIG versions.
    figure_count = 0

    for number in range(1, 25):
        prefix = f"Task27_Fig{number:02d}_"
        pngs = list(PLOTS.glob(prefix + "*.png"))
        figs = list(PLOTS.glob(prefix + "*.fig"))

        require(
            len(pngs) == 1 and len(figs) == 1,
            f"Figure {number:02d} is missing or duplicated"
        )

        for path in pngs + figs:
            require(path.stat().st_size > 0,
                    f"Empty research figure: {path.name}")

        figure_count += 1

    # Recheck archived source hashes before finalizing.
    source_manifests = [
        FINDINGS / "task27_4A_cpu_input_manifest.json",
        FINDINGS / "task27_5A_source_manifest.json",
        FINDINGS / "task27_6A_fpga_candidate_manifest.json",
    ]

    verified_source_hashes = 0

    for manifest_path in source_manifests:
        require(manifest_path.is_file(),
                f"Missing source manifest: {manifest_path}")

        manifest = load_json(manifest_path)
        entries = manifest.get(
            "source_files", manifest.get("inputs", [])
        )

        checked_here = 0

        for entry in entries:
            path_text = (
                entry.get("path")
                or entry.get("file")
                or entry.get("source")
            )

            expected_hash = entry.get("sha256")

            if not path_text or not expected_hash:
                continue

            path = Path(path_text)
            require(path.is_file(),
                    f"Manifest source missing: {path}")

            require(sha256(path) == expected_hash.upper(),
                    f"Manifest hash mismatch: {path.name}")

            checked_here += 1

        require(checked_here > 0,
                f"No source hashes verified: {manifest_path.name}")

        verified_source_hashes += checked_here

    require(verified_source_hashes >= 15,
            "Insufficient source hash verification")

    # Verify archived median results.
    medians = {
        row["workload"]:
        float(row["median_of_group_medians_ms"])
        for row in cpu
    }

    require(
        math.isclose(medians["YOLO11s"],43.74605,abs_tol=1e-6),
        "YOLO CPU median mismatch"
    )

    require(
        math.isclose(medians["Camera"],1.81505,abs_tol=1e-6),
        "Camera CPU median mismatch"
    )

    reduction = 100 * (1 - filtered_points/input_points)

    # Build the scientific report only from validated values.
    report_lines = [
        "# GEMSTAR Task 27 — Final Research Report",
        "",
        "**Study:** Workload characterization, nominal memory",
        "modeling and preliminary ARM–FPGA candidate selection.",
        "",
        "**Status:** Software profiling and analytical modeling",
        "completed; final hardware and perception validation pending.",
        "",
        "## 1. Research objective",
        "",
        "Identify promising ARM–FPGA processing kernels while",
        "preserving perception quality and eventually minimizing",
        "measured system energy per valid perception result.",
        "",
        "## 2. Reproducible evidence",
        "",
        f"- Original CPU timing observations: {cpu_rows:,}",
        f"- Registered research datasets: {len(register)}",
        f"- Source hash checks repeated: {verified_source_hashes}",
        f"- MATLAB figures checked: {figure_count} PNG/FIG pairs",
        "",
        "## 3. CPU workload observations",
        "",
        "| Workload | Median of group medians (ms) |",
        "|---|---:|",
    ]

    for name in (
        "EKF", "Camera", "LiDAR", "Radar",
        "YOLO11s", "Partial_LiDAR_Radar"
    ):
        report_lines.append(
            f"| {name} | {medians[name]:.6f} |"
        )

    report_lines.extend([
        "",
        "Different benchmarks cover different data sizes and",
        "processing boundaries. EKF is a replay; Radar times",
        "cover batches; LiDAR stages were timed individually.",
        "These values are not equivalent end-to-end frame times.",
        "",
        "## 4. LiDAR structural and memory analysis",
        "",
        f"- Input points: {input_points:,}",
        f"- Retained after spatial filtering: {filtered_points:,}",
        f"- Point reduction: {reduction:.4f}%",
        f"- Nominal XYZ input bytes: {input_bytes:,}",
        f"- Nominal filtered XYZ output bytes: {output_bytes:,}",
        f"- Modeled two-way payload bytes: {roundtrip_bytes:,}",
        "",
        "Point reduction is not an energy saving and does not",
        "establish preservation of all relevant objects.",
        "Payload sizes assume compact float32 XYZ triples.",
        "",
        "## 5. Camera, Radar and YOLO analysis",
        "",
        "Camera uses BGR-to-grayscale/HSV conversion, Canny",
        "edges, and float64 Laplacian processing. Named buffer",
        "sizes are calculated, not observed DRAM traffic.",
        "",
        "Radar timing measures valid-return batches, excluding",
        "association and invalid returns.",
        "",
        "YOLO11s prediction is the largest measured standalone",
        "workload, but detection accuracy, layer-level resource",
        "costs and accelerator feasibility remain unvalidated.",
        "",
        "## 6. Provisional FPGA kernel shortlist",
        "",
    ])

    for item in shortlisted:
        report_lines.append(f"- **{item}**")

    report_lines.extend([
        "",
        "This is a provisional engineering shortlist, not",
        "a measured energy-optimal selection. YOLO remains",
        "a candidate for further layer-level study.",
        "",
        "## 7. Transfer and energy break-even",
        "",
        f"- Workload/model cases: {len(break_cases)}",
        f"- Parameter-sweep summary groups: {len(break_even)}",
        "- Transfer bandwidths are hypothetical.",
        "- FPGA compute and fixed overhead are hypothetical.",
        "- No real DMA, FPGA execution or power was measured.",
        "",
        "An energy comparison requires matched execution",
        "boundaries and measured total-system energy.",
        "A lower latency alone does not prove lower energy.",
        "",
        "## 8. Scientific limitations",
        "",
        "- No empirical hardware roofline established.",
        "- Exact operation counts and DRAM traffic unknown.",
        "- No measured ARM–FPGA latency or energy savings.",
        "- Full three-sensor perception quality unverified.",
        "- No end-to-end p99 deadline guarantee.",
        "- Rain and dense-traffic generalization unverified.",
        "- Camera ROI equivalence to FULL not established.",
        "- Development CPU timings cannot stand in for ARM.",
        "",
        "## 9. Requirements for the next tasks",
        "",
        "Task 28: validate numerical fidelity and hardware-",
        "compatible representations against matched inputs.",
        "",
        "Task 29: use quality and deadline constraints when",
        "designing the adaptive scheduling architecture.",
        "",
        "Hardware stages: measure transfers, actual execution",
        "time and complete board/system energy; compare with",
        "matched CPU baselines and valid perception outputs.",
        "",
        "## 10. Provenance",
        "",
        "Primary data: Task 26 CPU measurements and Task 27",
        "derived research CSVs. The evidence register and",
        "SHA-256 archive manifest accompany this report.",
        "",
        "The archive manifest covers files present at the",
        "time of finalization, including this report, but",
        "excludes the manifest itself and the final JSON.",
        "",
    ])

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with FINAL_REPORT.open("x", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    # Inventory the actual files, including the new report.
    # Exclude the inventory and verification JSON to
    # avoid self-referential checksums.
    archive_rows = []

    for path in sorted(TASK.rglob("*")):
        if not path.is_file():
            continue

        if path in (ARCHIVE_CSV, VERIFICATION):
            continue

        archive_rows.append({
            "relative_path": path.relative_to(TASK).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path)
        })

    require(len(archive_rows) > 40,
            "Archive unexpectedly small")

    csv_write_new(ARCHIVE_CSV, archive_rows)

    # Verify archived SHA-256 records immediately.
    for row in archive_rows:
        path = TASK / Path(row["relative_path"])
        require(sha256(path) == row["sha256"],
                f"Final archive checksum failed: {path}")

    verification = {
        "task": "27.7B",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "cpu_timing_observations": cpu_rows,
        "evidence_datasets": len(register),
        "verified_source_hash_checks": verified_source_hashes,
        "matlab_figure_pairs": figure_count,
        "archive_files_hashed": len(archive_rows),
        "archive_manifest_scope":
            "Files present at finalization; manifest and "
            "verification JSON excluded",
        "provisional_kernels": shortlisted,
        "hardware_energy_measured": False,
        "full_pipeline_quality_validated": False,
        "empirical_roofline_established": False,
        "final_hardware_selection_validated": False,
        "final_report": str(FINAL_REPORT),
        "archive_manifest": str(ARCHIVE_CSV)
    }

    with VERIFICATION.open("x", encoding="utf-8") as f:
        json.dump(verification, f, indent=2)

    print("EVIDENCE_DATASETS_VERIFIED:", len(register))
    print("SOURCE_HASH_CHECKS:", verified_source_hashes)
    print("MATLAB_FIGURE_PAIRS:", figure_count)
    print("ARCHIVE_FILES_HASHED:", len(archive_rows))
    print("CPU_TIMING_OBSERVATIONS:", cpu_rows)
    print("PROVISIONAL_FPGA_KERNELS:", len(shortlisted))
    print("HARDWARE_ENERGY_MEASURED: NO")
    print("FULL_PIPELINE_QUALITY_VALIDATED: NO")
    print("FINAL_REPORT:", FINAL_REPORT)
    print("ARCHIVE_MANIFEST:", ARCHIVE_CSV)
    print("FINAL_VERIFICATION:", VERIFICATION)
    print("TASK27_7B_FINAL_RESEARCH_VERIFICATION_DONE")

if __name__ == "__main__":
    main()