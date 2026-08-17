from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "kaggle" / "13_generate_edu100_visual_qc.py"
SPEC = importlib.util.spec_from_file_location("edu100_visual_qc", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
STAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGE)


def metric_rows() -> list[dict[str, float | str]]:
    rows = []
    for number in range(1, 21):
        rows.append(
            {
                "case_id": f"case{number:04d}",
                "Dice": 0.70 + number / 1000,
                "HD95_mm": 30.0 - number,
                "clDice": 0.80 + number / 1000,
                "absolute_component_count_error": float(number),
            }
        )
    return rows


def test_selection_contains_extremes_and_is_reproducible():
    first = STAGE.select_qc_cases(metric_rows())
    second = STAGE.select_qc_cases(metric_rows())
    assert first == second
    by_id = {row["case_id"]: row["reasons"] for row in first}
    assert "lowest_Dice" in by_id["case0001"]
    assert "highest_HD95_mm" in by_id["case0001"]
    assert "lowest_clDice" in by_id["case0001"]
    assert "highest_Dice_control" in by_id["case0020"]
    assert "highest_absolute_component_count_error" in by_id["case0020"]
    random_selection_count = sum(
        any(reason.startswith("seeded_random_") for reason in reasons)
        for reasons in by_id.values()
    )
    assert random_selection_count == 2


def test_read_metric_rows_requires_20_unique_cases(tmp_path: Path):
    path = tmp_path / "metrics.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "Dice"])
        writer.writeheader()
        writer.writerows({"case_id": f"case{number:04d}", "Dice": 0.5} for number in range(19))
    with pytest.raises(ValueError, match="20 unique"):
        STAGE.read_metric_rows(path)


def test_find_phase3b_output_requires_one_complete_attachment(tmp_path: Path):
    stage = tmp_path / "notebook" / "edu100_test"
    stage.mkdir(parents=True)
    (stage / "heldout_test_report.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="incomplete"):
        STAGE.find_phase3b_output(tmp_path)
