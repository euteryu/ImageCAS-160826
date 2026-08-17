import json

import pandas as pd
import pytest

from imagecas.data.strict_nnunet_view import (
    build_view,
    case_ids_for_mode,
    read_and_validate_manifest,
)


def manifest_frame() -> pd.DataFrame:
    rows = []
    number = 1
    for role, count in (("train", 64), ("val", 16), ("test", 20)):
        for _ in range(count):
            rows.append(
                {
                    "case_id": f"case{number:04d}",
                    "role": role,
                    "included_in_development_dataset": role != "test",
                }
            )
            number += 1
    return pd.DataFrame(rows)


def test_modes_keep_test_cases_out():
    manifest = manifest_frame()
    training = case_ids_for_mode(manifest, "training")
    development = case_ids_for_mode(manifest, "development")
    test = set(manifest.loc[manifest.role == "test", "case_id"])
    assert len(training) == 64
    assert len(development) == 80
    assert set(training) < set(development)
    assert not test.intersection(development)


def test_manifest_validation_rejects_incorrect_inclusion(tmp_path):
    manifest = manifest_frame()
    manifest.loc[manifest.role == "test", "included_in_development_dataset"] = True
    path = tmp_path / "manifest.csv"
    manifest.to_csv(path, index=False)
    with pytest.raises(ValueError, match="inclusion flags"):
        read_and_validate_manifest(path)


def test_build_view_uses_symlinks_and_updates_count(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "imagesTr").mkdir(parents=True)
    (source / "labelsTr").mkdir()
    (source / "dataset.json").write_text(
        json.dumps({"numTraining": 80, "file_ending": ".nii.gz"}), encoding="utf-8"
    )
    manifest = manifest_frame()
    for case_id in manifest.loc[manifest.role != "test", "case_id"]:
        (source / "imagesTr" / f"{case_id}_0000.nii.gz").touch()
        (source / "labelsTr" / f"{case_id}.nii.gz").touch()

    training_report = build_view(source, target, manifest, "training")
    assert training_report["case_count"] == 64
    assert len(list((target / "imagesTr").iterdir())) == 64
    assert all(path.is_symlink() for path in (target / "imagesTr").iterdir())
    assert json.loads((target / "dataset.json").read_text())["numTraining"] == 64

    development_report = build_view(source, target, manifest, "development")
    assert development_report["case_count"] == 80
    assert development_report["test_cases"] == 0
    assert json.loads((target / "dataset.json").read_text())["numTraining"] == 80
