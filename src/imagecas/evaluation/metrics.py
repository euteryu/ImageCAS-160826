from __future__ import annotations

import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize


CONNECTIVITY = np.ones((3, 3, 3), dtype=bool)


def _surface(mask: np.ndarray) -> np.ndarray:
    eroded = ndimage.binary_erosion(mask, structure=CONNECTIVITY, border_value=0)
    return mask & ~eroded


def _component_stats(mask: np.ndarray) -> tuple[int, float]:
    labels, count = ndimage.label(mask, structure=CONNECTIVITY)
    if count == 0:
        return 0, 0.0
    sizes = np.bincount(labels.ravel())[1:]
    return int(count), float(sizes.max() / sizes.sum())


def binary_metrics(
    prediction: np.ndarray,
    reference: np.ndarray,
    spacing: tuple[float, float, float],
    surface_tolerance_mm: float = 1.0,
) -> dict[str, float | int | None]:
    """Calculate overlap, physical-surface, and centerline/topology metrics."""
    pred = np.asarray(prediction, dtype=bool)
    ref = np.asarray(reference, dtype=bool)
    if pred.shape != ref.shape or pred.ndim != 3:
        raise ValueError("prediction and reference must have the same 3D shape")
    if len(spacing) != 3 or any(value <= 0 for value in spacing):
        raise ValueError("spacing must contain three positive values")

    pred_count = int(pred.sum())
    ref_count = int(ref.sum())
    intersection = int(np.logical_and(pred, ref).sum())
    union = pred_count + ref_count - intersection
    dice = 1.0 if pred_count + ref_count == 0 else 2 * intersection / (pred_count + ref_count)
    iou = 1.0 if union == 0 else intersection / union

    pred_components, pred_largest_fraction = _component_stats(pred)
    ref_components, ref_largest_fraction = _component_stats(ref)

    surface_dice: float | None = None
    hd95: float | None = None
    mean_surface_distance: float | None = None
    if pred_count and ref_count:
        pred_surface = _surface(pred)
        ref_surface = _surface(ref)
        distance_to_ref = ndimage.distance_transform_edt(~ref_surface, sampling=spacing)
        distance_to_pred = ndimage.distance_transform_edt(~pred_surface, sampling=spacing)
        pred_distances = distance_to_ref[pred_surface]
        ref_distances = distance_to_pred[ref_surface]
        all_distances = np.concatenate((pred_distances, ref_distances))
        surface_dice = float(
            (np.count_nonzero(pred_distances <= surface_tolerance_mm)
             + np.count_nonzero(ref_distances <= surface_tolerance_mm))
            / all_distances.size
        )
        hd95 = float(np.percentile(all_distances, 95))
        mean_surface_distance = float(all_distances.mean())

    cldice: float | None = None
    if pred_count and ref_count:
        pred_skeleton = skeletonize(pred)
        ref_skeleton = skeletonize(ref)
        pred_skeleton_count = int(pred_skeleton.sum())
        ref_skeleton_count = int(ref_skeleton.sum())
        if pred_skeleton_count and ref_skeleton_count:
            topology_precision = np.logical_and(pred_skeleton, ref).sum() / pred_skeleton_count
            topology_sensitivity = np.logical_and(ref_skeleton, pred).sum() / ref_skeleton_count
            denominator = topology_precision + topology_sensitivity
            cldice = float(
                0.0
                if denominator == 0
                else 2 * topology_precision * topology_sensitivity / denominator
            )

    return {
        "Dice": float(dice),
        "IoU": float(iou),
        "surface_Dice_1mm": surface_dice,
        "HD95_mm": hd95,
        "mean_surface_distance_mm": mean_surface_distance,
        "clDice": cldice,
        "predicted_components": pred_components,
        "reference_components": ref_components,
        "absolute_component_count_error": abs(pred_components - ref_components),
        "predicted_largest_component_fraction": pred_largest_fraction,
        "reference_largest_component_fraction": ref_largest_fraction,
        "predicted_foreground_voxels": pred_count,
        "reference_foreground_voxels": ref_count,
    }
