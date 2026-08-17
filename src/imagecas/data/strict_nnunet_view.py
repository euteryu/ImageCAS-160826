from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


EXPECTED_COUNTS = {"train": 64, "val": 16, "test": 20}


def read_and_validate_manifest(path: Path) -> pd.DataFrame:
    manifest = pd.read_csv(path)
    required = {"case_id", "role", "included_in_development_dataset"}
    if not required.issubset(manifest.columns):
        raise ValueError(f"manifest must contain columns: {sorted(required)}")
    if manifest.case_id.duplicated().any():
        raise ValueError("manifest contains duplicate case IDs")
    counts = manifest.groupby("role").size().to_dict()
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"unexpected manifest role counts: {counts}")
    included = manifest.included_in_development_dataset
    if included.dtype != bool:
        included = included.astype(str).str.lower().map({"true": True, "false": False})
    if included.isna().any():
        raise ValueError("included_in_development_dataset must contain only true/false")
    expected_included = manifest.role.isin(["train", "val"])
    if not included.equals(expected_included):
        raise ValueError("development inclusion flags do not match train/val roles")
    return manifest


def case_ids_for_mode(manifest: pd.DataFrame, mode: str) -> list[str]:
    if mode == "training":
        roles = ["train"]
    elif mode == "development":
        roles = ["train", "val"]
    else:
        raise ValueError(f"unknown view mode: {mode}")
    return manifest.loc[manifest.role.isin(roles), "case_id"].tolist()


def _clear_files(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.iterdir():
        if path.is_symlink() or path.is_file():
            path.unlink()
        else:
            raise RuntimeError(f"refusing to remove unexpected directory: {path}")


def build_view(source: Path, target: Path, manifest: pd.DataFrame, mode: str) -> dict:
    source = source.resolve()
    target = target.absolute()
    if source == target.resolve():
        raise ValueError("source and target datasets must be different")
    source_images = source / "imagesTr"
    source_labels = source / "labelsTr"
    if not source_images.is_dir() or not source_labels.is_dir():
        raise FileNotFoundError("source dataset must contain imagesTr and labelsTr")

    selected = case_ids_for_mode(manifest, mode)
    target.mkdir(parents=True, exist_ok=True)
    target_images = target / "imagesTr"
    target_labels = target / "labelsTr"
    _clear_files(target_images)
    _clear_files(target_labels)

    for case_id in selected:
        image = source_images / f"{case_id}_0000.nii.gz"
        label = source_labels / f"{case_id}.nii.gz"
        if not image.is_file() or not label.is_file():
            raise FileNotFoundError(f"missing source image or label for {case_id}")
        (target_images / image.name).symlink_to(image)
        (target_labels / label.name).symlink_to(label)

    dataset_json = json.loads((source / "dataset.json").read_text(encoding="utf-8"))
    dataset_json["numTraining"] = len(selected)
    (target / "dataset.json").write_text(
        json.dumps(dataset_json, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    test_ids = set(manifest.loc[manifest.role == "test", "case_id"])
    if test_ids.intersection(selected):
        raise RuntimeError("test isolation failure: test case entered the raw view")
    return {
        "status": "PASS",
        "mode": mode,
        "case_count": len(selected),
        "training_cases": int(
            (manifest.loc[manifest.case_id.isin(selected), "role"] == "train").sum()
        ),
        "validation_cases": int(
            (manifest.loc[manifest.case_id.isin(selected), "role"] == "val").sum()
        ),
        "test_cases": 0,
        "files_are_symlinks": True,
        "source_dataset": str(source),
        "target_dataset": str(target),
    }
