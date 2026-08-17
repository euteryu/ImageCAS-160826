from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np


INPUT_ROOT = Path("/kaggle/input")
OUTPUT_ROOT = Path("/kaggle/working/edu100_visual_qc")
RANDOM_SEED = 598
RANDOM_CASE_COUNT = 2


def find_phase3b_output(input_root: Path) -> Path:
    reports = sorted(input_root.glob("**/edu100_test/heldout_test_report.json"))
    if len(reports) != 1:
        raise RuntimeError(
            "Expected exactly one attached notebook 1.4 Version 2 held-out report, "
            f"found {len(reports)}: {reports}"
        )
    stage_root = reports[0].parent
    required = [
        stage_root / "per_case_metrics.csv",
        stage_root / "imagesTs",
        stage_root / "predictions",
        stage_root / "references",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Attached Phase 3B output is incomplete: {missing}")
    return stage_root


def read_metric_rows(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        raw_rows = list(csv.DictReader(stream))
    rows: list[dict[str, float | str]] = []
    for raw in raw_rows:
        case_id = raw.get("case_id", "")
        if not case_id:
            raise ValueError("Metric row has no case_id")
        rows.append(
            {
                key: value if key == "case_id" else float(value)
                for key, value in raw.items()
            }
        )
    if len(rows) != 20 or len({str(row["case_id"]) for row in rows}) != 20:
        raise ValueError("Expected metrics for exactly 20 unique held-out cases")
    return rows


def select_qc_cases(
    rows: list[dict[str, float | str]],
    random_seed: int = RANDOM_SEED,
    random_case_count: int = RANDOM_CASE_COUNT,
) -> list[dict[str, object]]:
    criteria = (
        ("lowest_Dice", "Dice", min),
        ("highest_HD95_mm", "HD95_mm", max),
        ("lowest_clDice", "clDice", min),
        (
            "highest_absolute_component_count_error",
            "absolute_component_count_error",
            max,
        ),
        ("highest_Dice_control", "Dice", max),
    )
    reasons: dict[str, list[str]] = {}
    row_by_id = {str(row["case_id"]): row for row in rows}
    for reason, key, chooser in criteria:
        selected = chooser(rows, key=lambda row: (float(row[key]), str(row["case_id"])))
        reasons.setdefault(str(selected["case_id"]), []).append(reason)

    remaining = sorted(set(row_by_id) - set(reasons))
    rng = np.random.default_rng(random_seed)
    sample_size = min(random_case_count, len(remaining))
    for case_id in sorted(rng.choice(remaining, size=sample_size, replace=False).tolist()):
        reasons.setdefault(case_id, []).append(f"seeded_random_{random_seed}")

    return [
        {
            "case_id": case_id,
            "reasons": reasons[case_id],
            "metrics": row_by_id[case_id],
        }
        for case_id in sorted(reasons)
    ]


def _boundary(mask: np.ndarray) -> np.ndarray:
    from scipy.ndimage import binary_erosion

    return mask & ~binary_erosion(mask)


def _slice_index(reference: np.ndarray, prediction: np.ndarray, axis: int) -> int:
    union = reference | prediction
    other_axes = tuple(index for index in range(3) if index != axis)
    areas = union.sum(axis=other_axes)
    return int(np.argmax(areas)) if areas.any() else union.shape[axis] // 2


def create_comparison_montage(
    case_id: str,
    image_path: Path,
    prediction_path: Path,
    reference_path: Path,
    output_path: Path,
    reasons: list[str],
    metrics: dict[str, float | str],
) -> None:
    image_nifti = nib.load(image_path)
    prediction_nifti = nib.load(prediction_path)
    reference_nifti = nib.load(reference_path)
    if not (
        image_nifti.shape == prediction_nifti.shape == reference_nifti.shape
        and np.allclose(image_nifti.affine, prediction_nifti.affine, atol=1e-5, rtol=0)
        and np.allclose(image_nifti.affine, reference_nifti.affine, atol=1e-5, rtol=0)
    ):
        raise ValueError(f"Physical geometry mismatch while rendering {case_id}")

    image = np.asarray(image_nifti.dataobj, dtype=np.float32)
    prediction = np.asarray(prediction_nifti.dataobj) != 0
    reference = np.asarray(reference_nifti.dataobj) != 0
    finite = image[np.isfinite(image)]
    if not finite.size:
        raise ValueError(f"CT contains no finite voxels for {case_id}")
    low, high = np.percentile(finite, [1, 99])
    views = ((0, "sagittal"), (1, "coronal"), (2, "axial"))
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    for column, (axis, label) in enumerate(views):
        index = _slice_index(reference, prediction, axis)
        ct_slice = np.rot90(np.take(image, index, axis=axis))
        ref_slice = np.rot90(np.take(reference, index, axis=axis))
        pred_slice = np.rot90(np.take(prediction, index, axis=axis))
        axes[column].imshow(ct_slice, cmap="gray", vmin=low, vmax=high)
        if ref_slice.any():
            axes[column].contour(
                _boundary(ref_slice), levels=[0.5], colors=["#ff3b30"], linewidths=0.8
            )
        if pred_slice.any():
            axes[column].contour(
                _boundary(pred_slice), levels=[0.5], colors=["#00d5ff"], linewidths=0.8
            )
        axes[column].set_title(f"{label}, slice {index}")
        axes[column].axis("off")
    fig.suptitle(
        f"{case_id} | reference=red, prediction=cyan | "
        f"Dice={float(metrics['Dice']):.3f}, HD95={float(metrics['HD95_mm']):.1f} mm\n"
        + ", ".join(reasons),
        fontsize=10,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    source_root = find_phase3b_output(INPUT_ROOT)
    heldout_report = json.loads(
        (source_root / "heldout_test_report.json").read_text(encoding="utf-8")
    )
    if heldout_report.get("status") != "PASS" or heldout_report.get("test_case_count") != 20:
        raise RuntimeError("Attached held-out report is not the accepted 20-case PASS result")

    rows = read_metric_rows(source_root / "per_case_metrics.csv")
    selections = select_qc_cases(rows)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=False)
    montage_root = OUTPUT_ROOT / "montages"
    rendered = []
    for position, selection in enumerate(selections, start=1):
        case_id = str(selection["case_id"])
        image_path = source_root / "imagesTs" / f"{case_id}_0000.nii.gz"
        prediction_path = source_root / "predictions" / f"{case_id}.nii.gz"
        reference_path = source_root / "references" / f"{case_id}.nii.gz"
        for path in (image_path, prediction_path, reference_path):
            if not path.is_file():
                raise FileNotFoundError(path)
        output_path = montage_root / f"{case_id}.png"
        create_comparison_montage(
            case_id,
            image_path,
            prediction_path,
            reference_path,
            output_path,
            list(selection["reasons"]),
            dict(selection["metrics"]),
        )
        rendered.append({**selection, "montage": str(output_path.relative_to(OUTPUT_ROOT))})
        print(f"[{position}/{len(selections)}] rendered {case_id}", flush=True)

    report = {
        "status": "PASS",
        "source_experiment": heldout_report["experiment"],
        "source_checkpoint_sha256": heldout_report["checkpoint_sha256"],
        "selection_policy": {
            "metric_extremes": [
                "lowest Dice",
                "highest HD95_mm",
                "lowest clDice",
                "highest absolute component count error",
                "highest Dice control",
            ],
            "random_seed": RANDOM_SEED,
            "random_case_count": RANDOM_CASE_COUNT,
            "duplicate_metric_extremes_are_merged": True,
        },
        "selected_case_count": len(rendered),
        "cases": rendered,
        "interpretation": (
            "Patient-derived visual-QC artifacts for the held-out EDU100 subset; "
            "review only, not a basis for model or checkpoint tuning."
        ),
    }
    (OUTPUT_ROOT / "visual_qc_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("EDU100_VISUAL_QC_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
