from pathlib import Path

import pandas as pd
import pytest

from imagecas.data.discover import infer_role, normalize_case_id, pairing_report


def test_normalize_case_id_uses_last_numeric_match():
    assert normalize_case_id(Path("patient_17_image_0000.nii.gz"), r"(\d+)") == "case0017"


def test_pairing_report_rejects_duplicate_images():
    files = pd.DataFrame([
        {"case_id": "case0001", "role": "image", "path": "a.nii.gz", "sha256": "a"},
        {"case_id": "case0001", "role": "image", "path": "b.nii.gz", "sha256": "b"},
        {"case_id": "case0001", "role": "mask", "path": "m.nii.gz", "sha256": "m"},
    ])
    manifest, problems = pairing_report(files)
    assert manifest.empty
    assert problems.iloc[0].problem == "duplicate_image_or_mask"


def test_normalize_case_id_raises_for_unknown_name():
    with pytest.raises(ValueError):
        normalize_case_id(Path("scan.nii.gz"), r"(\d+)")


def test_infer_role_uses_parent_directory():
    assert infer_role(Path("dataset/labelsTr/case0001.nii.gz")) == "mask"
    assert infer_role(Path("dataset/imagesTr/case0001_0000.nii.gz")) == "image"
