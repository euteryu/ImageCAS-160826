from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from scipy import ndimage


def _json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _bbox(mask: np.ndarray) -> list[list[int]] | None:
    points = np.argwhere(mask)
    if not len(points):
        return None
    return [[int(v) for v in points.min(axis=0)], [int(v) for v in points.max(axis=0)]]


def audit_case(
    case_id: str,
    image_path: str | Path,
    mask_path: str | Path,
    affine_atol: float = 1e-5,
    spacing_atol_mm: float = 1e-5,
) -> dict:
    image_nii = nib.load(str(image_path))
    mask_nii = nib.load(str(mask_path))
    image = np.asarray(image_nii.dataobj)
    mask = np.asarray(mask_nii.dataobj)
    image_spacing = np.asarray(image_nii.header.get_zooms()[:3], dtype=float)
    mask_spacing = np.asarray(mask_nii.header.get_zooms()[:3], dtype=float)
    finite = image[np.isfinite(image)]
    foreground = mask != 0
    labels, component_count = ndimage.label(foreground, structure=ndimage.generate_binary_structure(3, 3))
    component_sizes = np.bincount(labels.ravel())[1:]
    component_sizes = sorted((int(v) for v in component_sizes), reverse=True)
    values = np.unique(mask)
    affine_matches = bool(np.allclose(image_nii.affine, mask_nii.affine, atol=affine_atol, rtol=0))
    spacing_matches = bool(np.allclose(image_spacing, mask_spacing, atol=spacing_atol_mm, rtol=0))
    shape_matches = image.shape == mask.shape
    orientation_image = "".join(nib.aff2axcodes(image_nii.affine))
    orientation_mask = "".join(nib.aff2axcodes(mask_nii.affine))
    voxel_volume = float(np.prod(mask_spacing))
    warning_codes = []
    if not shape_matches:
        warning_codes.append("SHAPE_MISMATCH")
    if not spacing_matches:
        warning_codes.append("SPACING_MISMATCH")
    if not affine_matches:
        warning_codes.append("AFFINE_MISMATCH")
    if not np.all(np.isfinite(image)):
        warning_codes.append("NONFINITE_IMAGE")
    if len(values) > 2 or not set(values.tolist()).issubset({0, 1}):
        warning_codes.append("NONBINARY_MASK")
    if not foreground.any():
        warning_codes.append("EMPTY_MASK")
    percentiles = np.percentile(finite, [1, 50, 99]) if len(finite) else [np.nan] * 3
    return {
        "case_id": case_id,
        "image_path": str(Path(image_path).resolve()),
        "mask_path": str(Path(mask_path).resolve()),
        "image_shape_x": image.shape[0],
        "image_shape_y": image.shape[1],
        "image_shape_z": image.shape[2],
        "mask_shape_x": mask.shape[0],
        "mask_shape_y": mask.shape[1],
        "mask_shape_z": mask.shape[2],
        "spacing_x_mm": image_spacing[0],
        "spacing_y_mm": image_spacing[1],
        "spacing_z_mm": image_spacing[2],
        "image_orientation": orientation_image,
        "mask_orientation": orientation_mask,
        "image_affine": _json(image_nii.affine.tolist()),
        "mask_affine": _json(mask_nii.affine.tolist()),
        "image_dtype": str(image.dtype),
        "mask_dtype": str(mask.dtype),
        "image_min": float(np.min(finite)) if len(finite) else np.nan,
        "image_p01": float(percentiles[0]),
        "image_p50": float(percentiles[1]),
        "image_p99": float(percentiles[2]),
        "image_max": float(np.max(finite)) if len(finite) else np.nan,
        "mask_unique_values": _json(values.tolist()),
        "foreground_voxels": int(foreground.sum()),
        "foreground_fraction": float(foreground.mean()),
        "foreground_volume_mm3": float(foreground.sum() * voxel_volume),
        "bounding_box": _json(_bbox(foreground)),
        "connected_component_count": int(component_count),
        "largest_component_sizes": _json(component_sizes[:10]),
        "shape_matches": shape_matches,
        "spacing_matches": spacing_matches,
        "affine_matches": affine_matches,
        "warning_codes": ";".join(warning_codes),
    }


def audit_dataset(manifest: pd.DataFrame, **kwargs) -> pd.DataFrame:
    rows = [audit_case(row.case_id, row.image_path, row.mask_path, **kwargs) for row in manifest.itertuples()]
    return pd.DataFrame(rows).sort_values("case_id").reset_index(drop=True)

