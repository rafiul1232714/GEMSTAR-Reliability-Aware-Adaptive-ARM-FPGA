import csv
import math
import sys
from pathlib import Path


def load_models(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 2:
        raise ValueError("Expected two model records")

    models = []

    for row in rows:
        model = {
            "name": row["Model"],
            "f1": float(row["F1"]),
            "p99_ms": float(row["P99Ms"]),
        }

        if not (
            0 <= model["f1"] <= 1
            and math.isfinite(model["f1"])
            and model["p99_ms"] > 0
            and math.isfinite(model["p99_ms"])
        ):
            raise ValueError("Invalid model metrics")

        models.append(model)

    if len({m["name"] for m in models}) != len(models):
        raise ValueError("Duplicate model names")

    return models


def select_model(
    models,
    queue_wait_ms,
    budget_ms=75.0,
    minimum_f1=0.50,
    health_mode="NORMAL_CANDIDATE"
):
    for value in (queue_wait_ms, budget_ms, minimum_f1):
        if not isinstance(value, (int, float)):
            raise ValueError("Invalid numeric input")
        if not math.isfinite(value):
            raise ValueError("Non-finite numeric input")

    if queue_wait_ms < 0 or budget_ms <= 0:
        raise ValueError("Invalid timing budget")

    if not 0 <= minimum_f1 <= 1:
        raise ValueError("Invalid F1 threshold")

    if health_mode not in (
        "NORMAL_CANDIDATE",
        "DEGRADED_CANDIDATE",
        "HOLD_OR_ALERT"
    ):
        raise ValueError("Unknown health mode")

    remaining = budget_ms - queue_wait_ms

    if health_mode == "HOLD_OR_ALERT":
        return {
            "model": None,
            "reason": "SAFETY_HOLD",
            "remaining_ms": remaining,
            "permission": "WITHHOLD_VALID_RESULT"
        }

    eligible = [
        m for m in models
        if m["f1"] >= minimum_f1
        and m["p99_ms"] <= remaining
    ]

    if not eligible:
        return {
            "model": None,
            "reason": "NO_QUALITY_AND_TIME_FEASIBLE_MODEL",
            "remaining_ms": remaining,
            "permission": "WITHHOLD_VALID_RESULT"
        }

    selected = min(eligible, key=lambda m: m["p99_ms"])

    return {
        "model": selected["name"],
        "reason": "QUALITY_AND_TIME_GATE_PASS",
        "remaining_ms": remaining,
        "permission": "PROVISIONAL_ONLY"
    }


def main():
    models = load_models(sys.argv[1])

    expected = {
        0: "YOLO11s",
        10: "YOLO11s",
        15: None,
        20: None,
        30: None,
    }

    print("=== QUEUE-AWARE QUALITY SELECTOR TESTS ===")

    for wait, expected_model in expected.items():
        result = select_model(models, wait)

        assert result["model"] == expected_model

        print(
            "WAIT_MS:", wait,
            "| MODEL:", result["model"],
            "| REASON:", result["reason"]
        )

    hold = select_model(
        models, 0,
        health_mode="HOLD_OR_ALERT"
    )
    assert hold["model"] is None
    assert hold["permission"] == "WITHHOLD_VALID_RESULT"

    strict = select_model(
        models, 0,
        minimum_f1=0.70
    )
    assert strict["model"] is None

    relaxed = select_model(
        models, 0,
        minimum_f1=0.20
    )
    assert relaxed["model"] == "YOLO11n"

    for invalid in (-1, float("nan"), float("inf")):
        try:
            select_model(models, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid queue wait accepted")

    print()
    print("QUEUE_TESTS: 5 PASS")
    print("HEALTH_HOLD: PASS")
    print("STRICT_QUALITY_THRESHOLD: PASS")
    print("RELAXED_QUALITY_THRESHOLD: PASS")
    print("INVALID_INPUT_GUARDS: PASS")
    print("PERMISSION: PROVISIONAL_ONLY OR WITHHOLD_VALID_RESULT")
    print("FULL_PIPELINE_VALIDATION: NOT PERFORMED")
    print("HARDWARE_ENERGY_MEASURED: NO")
    print("STATUS: TASK 29.5E.9L PASS")


if __name__ == "__main__":
    main()