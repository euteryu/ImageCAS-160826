import numpy as np
import pytest

from imagecas.evaluation.metrics import binary_metrics


def test_identical_binary_masks_have_perfect_metrics():
    mask = np.zeros((12, 12, 12), dtype=bool)
    mask[2:10, 6, 6] = True
    result = binary_metrics(mask, mask, (0.5, 0.5, 1.0))
    assert result["Dice"] == 1.0
    assert result["IoU"] == 1.0
    assert result["surface_Dice_1mm"] == 1.0
    assert result["HD95_mm"] == 0.0
    assert result["mean_surface_distance_mm"] == 0.0
    assert result["clDice"] == 1.0
    assert result["absolute_component_count_error"] == 0


def test_disconnected_false_positive_is_reflected_in_overlap_and_topology():
    reference = np.zeros((15, 15, 15), dtype=bool)
    reference[2:10, 7, 7] = True
    prediction = reference.copy()
    prediction[12, 12, 12] = True
    result = binary_metrics(prediction, reference, (1.0, 1.0, 1.0))
    assert 0 < result["Dice"] < 1
    assert result["predicted_components"] == 2
    assert result["reference_components"] == 1
    assert result["absolute_component_count_error"] == 1
    assert result["predicted_largest_component_fraction"] == pytest.approx(8 / 9)


def test_empty_prediction_has_defined_overlap_and_unavailable_surface_metrics():
    prediction = np.zeros((5, 5, 5), dtype=bool)
    reference = prediction.copy()
    reference[2, 2, 2] = True
    result = binary_metrics(prediction, reference, (1.0, 1.0, 1.0))
    assert result["Dice"] == 0.0
    assert result["IoU"] == 0.0
    assert result["surface_Dice_1mm"] is None
    assert result["HD95_mm"] is None
    assert result["clDice"] is None


def test_metric_input_geometry_is_validated():
    with pytest.raises(ValueError, match="same 3D shape"):
        binary_metrics(np.zeros((2, 2)), np.zeros((2, 2)), (1.0, 1.0, 1.0))
