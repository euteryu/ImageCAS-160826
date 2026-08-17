from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil


DATASET_NAME = "Dataset598_ImageCAS_EDU100"
CASE_DATA_RE = re.compile(r"^case\d{4}(?:\.npz|\.npy|\.b2nd)$")


def validate_splits(splits: list[dict[str, list[str]]]) -> None:
    if len(splits) != 3:
        raise ValueError(f"Expected three learning-curve splits, found {len(splits)}")
    expected_sizes = [16, 32, 64]
    validation = splits[0]["val"]
    for index, (split, size) in enumerate(zip(splits, expected_sizes, strict=True)):
        if set(split) != {"train", "val"}:
            raise ValueError(f"Split {index} has unexpected keys: {sorted(split)}")
        if len(split["train"]) != size or len(set(split["train"])) != size:
            raise ValueError(f"Split {index} does not contain {size} unique training cases")
        if len(split["val"]) != 16 or split["val"] != validation:
            raise ValueError(f"Split {index} does not reuse the fixed 16-case validation set")
        if set(split["train"]) & set(split["val"]):
            raise ValueError(f"Split {index} overlaps training and validation cases")
    if not set(splits[0]["train"]) < set(splits[1]["train"]) < set(splits[2]["train"]):
        raise ValueError("Training splits are not strictly nested 16 < 32 < 64")


def main() -> None:
    input_root = Path("/kaggle/input")
    candidates = sorted(input_root.glob(f"**/{DATASET_NAME}/nnUNetPlans.json"))
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one attached preprocessed Dataset598, found {candidates}")
    source = candidates[0].parent
    preprocessed_root = Path(os.environ["nnUNet_preprocessed"])
    target = preprocessed_root / DATASET_NAME
    target.mkdir(parents=True, exist_ok=False)

    training_report = json.loads(
        (source / "training_fingerprint_view_report.json").read_text(encoding="utf-8")
    )
    development_report = json.loads(
        (source / "development_preprocess_view_report.json").read_text(encoding="utf-8")
    )
    if training_report["case_count"] != 64 or training_report["test_cases"] != 0:
        raise ValueError("Training fingerprint view did not preserve the required 64/0 counts")
    if development_report["case_count"] != 80 or development_report["test_cases"] != 0:
        raise ValueError("Development view did not preserve the required 80/0 counts")

    splits = json.loads((source / "splits_learning_curve.json").read_text(encoding="utf-8"))
    validate_splits(splits)
    plans = json.loads((source / "nnUNetPlans.json").read_text(encoding="utf-8"))
    data_identifier = plans["configurations"]["3d_fullres"]["data_identifier"]
    data_source = source / data_identifier
    data_ids = {
        path.name[:8] for path in data_source.iterdir() if CASE_DATA_RE.fullmatch(path.name)
    }
    expected_ids = set(splits[2]["train"]) | set(splits[2]["val"])
    if data_ids != expected_ids:
        raise ValueError(
            f"Preprocessed case mismatch: missing={sorted(expected_ids - data_ids)}, "
            f"unexpected={sorted(data_ids - expected_ids)}"
        )

    for path in source.iterdir():
        if path.name in {data_identifier, "gt_segmentations", "splits_learning_curve.json"}:
            continue
        if path.is_file():
            shutil.copy2(path, target / path.name)
    os.symlink(data_source, target / data_identifier, target_is_directory=True)
    os.symlink(source / "gt_segmentations", target / "gt_segmentations", target_is_directory=True)
    (target / "splits_final.json").write_text(
        json.dumps(splits, indent=2) + "\n", encoding="utf-8"
    )

    report = {
        "status": "PASS",
        "source_dataset": str(source),
        "target_dataset": str(target),
        "preprocessed_cases": len(data_ids),
        "fold_training_cases": [len(split["train"]) for split in splits],
        "validation_cases_per_fold": [len(split["val"]) for split in splits],
        "test_cases": 0,
        "data_are_read_only_symlinks": True,
    }
    print("EDU100_TRAINING_VIEW_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
