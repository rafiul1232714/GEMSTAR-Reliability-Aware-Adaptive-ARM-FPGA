from pathlib import Path
import ast
import json
import hashlib

TESTS = Path(r"E:\GEMSTAR_Project\sensor-health-monitor\tests")

BASE = (
    TESTS / "Task_24_Final_Research"
    / "09_Controlled_Scenario"
    / "C02_MovingTarget"
)

TASK26 = TESTS / "Task_26_Final_Research"

SOURCES = [
    BASE / "C02_V2_Track2_Camera_EKF_V1.py",
    BASE / "C02_V2_Track2_EKF_Baseline_V1.py",
    BASE / "C02_V2_Radar_Track_Association_V1.py",
]

REPORT = (
    TASK26 / "06_Research_Findings"
    / "task26_5F_ekf_source_inspection.json"
)

WRITE_INDICATORS = [
    "to_csv",
    "to_json",
    "savefig",
    "savetxt",
    "save",
    "writerow",
    "writerows",
    "write_text",
    "write_bytes",
    "mkdir",
    "makedirs",
    "open",
    "fopen",
]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(
            lambda: stream.read(1024 * 1024), b""
        ):
            h.update(block)
    return h.hexdigest()

def source_segment(text, node, limit=220):
    segment = ast.get_source_segment(text, node) or ""
    segment = " ".join(segment.strip().split())
    return segment[:limit]

def inspect(path):
    if not path.is_file():
        raise FileNotFoundError(path)

    text = path.read_text(
        encoding="utf-8-sig", errors="replace"
    )

    tree = ast.parse(text, filename=str(path))

    imports = []
    functions = []
    top_level = []
    string_references = []
    write_candidates = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(
                alias.name for alias in node.names
            )

        elif isinstance(node, ast.ImportFrom):
            imports.append(
                f"from {node.module} import ..."
            )

        elif isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "arguments": [
                    arg.arg for arg in node.args.args
                ],
            })

        elif isinstance(node, ast.If):
            condition = source_segment(text, node.test)

            top_level.append({
                "kind": "if",
                "line": node.lineno,
                "preview": condition,
            })

        elif not isinstance(
            node, (
                ast.Import,
                ast.ImportFrom,
                ast.ClassDef,
                ast.Expr,
            )
        ):
            top_level.append({
                "kind": type(node).__name__,
                "line": node.lineno,
                "preview": source_segment(text, node),
            })

        elif isinstance(node, ast.Expr):
            # Module docstrings are safe, but other
            # expressions may execute on import.
            if not isinstance(
                node.value, ast.Constant
            ):
                top_level.append({
                    "kind": "expression",
                    "line": node.lineno,
                    "preview": source_segment(text, node),
                })

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                value = node.value
                low = value.lower()

                if any(
                    suffix in low for suffix in (
                        ".csv", ".json", ".png",
                        ".npy", ".npz", ".osi"
                    )
                ):
                    if value not in string_references:
                        string_references.append(value)

        if isinstance(node, ast.Call):
            call_name = source_segment(
                text, node.func, 160
            )

            lower = call_name.lower()

            if any(
                word in lower
                for word in WRITE_INDICATORS
            ):
                write_candidates.append({
                    "line": node.lineno,
                    "function": call_name,
                    "preview": source_segment(
                        text, node, 180
                    ),
                })

    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "imports": imports,
        "functions": functions,
        "top_level_operations": top_level[:100],
        "file_references": string_references[:100],
        "possible_file_operations":
            write_candidates[:100],
    }

def main():
    if REPORT.exists():
        raise FileExistsError(
            f"Existing report preserved: {REPORT}"
        )

    results = [inspect(path) for path in SOURCES]

    print("=== TASK 26.5F ORIGINAL EKF SOURCE INSPECTION ===")

    for result in results:
        print()
        print("SOURCE:", result["path"])
        print("SIZE_BYTES:", result["size_bytes"])
        print("SHA256:", result["sha256"])

        print("IMPORTS:", result["imports"])

        print("FUNCTIONS:")
        for function in result["functions"]:
            print(
                "  LINE=", function["line"],
                "NAME=", function["name"],
                "ARGS=", function["arguments"],
            )

        print(
            "TOP_LEVEL_OPERATION_COUNT:",
            len(result["top_level_operations"])
        )

        for item in result["top_level_operations"][:15]:
            print(
                "  TOP_LEVEL:",
                item["line"],
                item["kind"],
                item["preview"],
            )

        print("FILE_REFERENCES:")
        for ref in result["file_references"][:15]:
            print(" ", ref)

        print(
            "POSSIBLE_FILE_OPERATION_COUNT:",
            len(result["possible_file_operations"])
        )

        for item in result["possible_file_operations"][:15]:
            print(
                "  FILE_OPERATION:",
                item["line"],
                item["function"],
                item["preview"],
            )

    REPORT.parent.mkdir(
        parents=True, exist_ok=True
    )

    payload = {
        "task": "26.5F",
        "analysis_type": "Static source inspection only",
        "source_execution": False,
        "source_files_modified": False,
        "findings": results,
        "limitations": [
            "Static analysis does not prove runtime behavior.",
            "Possible write operations are candidates, not proof of writes.",
            "Nested function calls and dynamic paths need manual review.",
            "No EKF prediction or update was executed.",
            "No perception quality or energy was measured."
        ]
    }

    with REPORT.open(
        "x", encoding="utf-8"
    ) as stream:
        json.dump(payload, stream, indent=2)

    print()
    print("SOURCE_FILES_EXECUTED: NO")
    print("SOURCE_FILES_MODIFIED: NO")
    print("TASK26_5F_EKF_SOURCE_INSPECTION_PASS")
    print("REPORT:", REPORT)

if __name__ == "__main__":
    main()
