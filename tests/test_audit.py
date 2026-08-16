import nibabel as nib
import numpy as np

from imagecas.data.audit import audit_case


def test_audit_uses_physical_volume_and_components(tmp_path):
    affine = np.diag([0.5, 0.5, 1.0, 1.0])
    image = np.zeros((8, 8, 8), dtype=np.int16)
    mask = np.zeros_like(image, dtype=np.uint8)
    mask[1:3, 1:3, 1:3] = 1
    mask[6, 6, 6] = 1
    image_path, mask_path = tmp_path / "case1.nii.gz", tmp_path / "case1_mask.nii.gz"
    nib.save(nib.Nifti1Image(image, affine), image_path)
    nib.save(nib.Nifti1Image(mask, affine), mask_path)
    row = audit_case("case0001", image_path, mask_path)
    assert row["foreground_voxels"] == 9
    assert row["foreground_volume_mm3"] == 2.25
    assert row["connected_component_count"] == 2
    assert row["warning_codes"] == ""


def test_audit_flags_affine_and_nonbinary_mask(tmp_path):
    image = np.zeros((4, 4, 4), dtype=np.float32)
    mask = np.zeros_like(image, dtype=np.uint8)
    mask[1, 1, 1] = 2
    image_path, mask_path = tmp_path / "i.nii.gz", tmp_path / "m.nii.gz"
    nib.save(nib.Nifti1Image(image, np.eye(4)), image_path)
    changed = np.eye(4)
    changed[0, 3] = 2
    nib.save(nib.Nifti1Image(mask, changed), mask_path)
    warnings = audit_case("case0001", image_path, mask_path)["warning_codes"]
    assert "AFFINE_MISMATCH" in warnings
    assert "NONBINARY_MASK" in warnings

