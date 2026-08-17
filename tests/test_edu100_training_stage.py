import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "kaggle" / "08_prepare_edu100_training.py"
SPEC = importlib.util.spec_from_file_location("edu100_training_stage", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
STAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STAGE)


def valid_splits():
    train = [f"case{number:04d}" for number in range(1, 65)]
    val = [f"case{number:04d}" for number in range(101, 117)]
    return [{"train": train[:size], "val": val.copy()} for size in (16, 32, 64)]


def test_validate_splits_accepts_nested_learning_curve():
    STAGE.validate_splits(valid_splits())


def test_validate_splits_rejects_changed_validation_set():
    splits = valid_splits()
    splits[1]["val"] = splits[1]["val"][:-1] + ["case0999"]
    with pytest.raises(ValueError, match="fixed 16-case validation"):
        STAGE.validate_splits(splits)


def test_validate_splits_rejects_training_validation_overlap():
    splits = valid_splits()
    splits[0]["val"][0] = splits[0]["train"][0]
    with pytest.raises(ValueError, match="overlaps"):
        STAGE.validate_splits(splits)
