from __future__ import annotations

import csv
import json
from pathlib import Path

import nibabel as nib
import numpy as np

from imagecas.evaluation.metrics import binary_metrics


STAGE_ROOT = Path("/kaggle/working/edu100_test")
METRIC_KEYS = (
    "Dice",
    "IoU",
    "surface_Dice_1mm",
    "HD95_mm",
    "mean_surface_distance_mm",
    "clDice",
    "absolute_component_count_error",
    "predicted_largest_component_fraction",
    "reference_largest_component_fraction",
)


def main() -> None:
    input_report = json.loads(
        (STAGE_ROOT / "inference_input_report.json").read_text(encoding="utf-8")
    )
    reference_report = json.loads(
        (STAGE_ROOT / "reference_extraction_report.json").read_text(encoding="utf-8")
    )
    test_ids = [record["case_id"] for record in input_report["cases"]]
    rows = []
    geometry_pass = True
    binary_pass = True
    for position, case_id in enumerate(test_ids, start=1):
        prediction_image = nib.load(STAGE_ROOT / "predictions" / f"{case_id}.nii.gz")
        reference_image = nib.load(STAGE_ROOT / "references" / f"{case_id}.nii.gz")
        same_geometry = (
            prediction_image.shape == reference_image.shape
            and np.allclose(prediction_image.affine, reference_image.affine, atol=1e-5, rtol=0)
        )
        geometry_pass &= same_geometry
        prediction = np.asanyarray(prediction_image.dataobj)
        reference = np.asanyarray(reference_image.dataobj)
        pred_values = np.unique(prediction)
        ref_values = np.unique(reference)
        is_binary = set(pred_values.tolist()) <= {0, 1} and set(ref_values.tolist()) <= {0, 1}
        binary_pass &= is_binary
        if not same_geometry:
            raise ValueError(f"Prediction/reference physical geometry mismatch for {case_id}")
        if not is_binary:
            raise ValueError(
                f"Non-binary data for {case_id}: prediction={pred_values}, reference={ref_values}"
            )
        metrics = binary_metrics(
            prediction,
            reference,
            tuple(float(value) for value in reference_image.header.get_zooms()[:3]),
        )
        rows.append({"case_id": case_id, **metrics})
        print(f"[{position}/20] evaluated {case_id}: Dice={metrics['Dice']:.6f}", flush=True)

    with (STAGE_ROOT / "per_case_metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    aggregate = {}
    for key in METRIC_KEYS:
        values = [float(row[key]) for row in rows if row[key] is not None]
        aggregate[key] = {
            "mean": float(np.mean(values)) if values else None,
            "median": float(np.median(values)) if values else None,
            "evaluated_cases": len(values),
        }
    checks = {
        "official_test_cases": input_report["official_partition"] == "test",
        "checkpoint_best_used": "checkpoint_best.pth" in input_report["checkpoint"],
        "predictions_before_references": reference_report["prediction_gate_passed"],
        "prediction_count": len(rows) == 20,
        "reference_count": reference_report["reference_count"] == 20,
        "physical_geometry": geometry_pass,
        "binary_masks": binary_pass,
        "overlap_metrics": all(aggregate[key]["evaluated_cases"] == 20 for key in ("Dice", "IoU")),
        "surface_metrics": all(
            aggregate[key]["evaluated_cases"] == 20
            for key in ("surface_Dice_1mm", "HD95_mm", "mean_surface_distance_mm")
        ),
        "topology_metrics": aggregate["clDice"]["evaluated_cases"] == 20,
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "dataset": "Dataset598_ImageCAS_EDU100",
        "experiment": "64-train/16-validation/20-held-out-test educational baseline",
        "trainer": "nnUNetTrainer_50epochs",
        "configuration": "3d_fullres",
        "fold": 2,
        "checkpoint": "checkpoint_best.pth",
        "test_case_count": len(rows),
        "surface_tolerance_mm": 1.0,
        "checks": checks,
        "aggregate": aggregate,
        "checkpoint_sha256": input_report["checkpoint_sha256"],
        "interpretation": "Held-out EDU100 subset result; not the official ImageCAS benchmark.",
    }
    (STAGE_ROOT / "heldout_test_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print("EDU100_HELDOUT_TEST_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
