from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> None:
    result_root = Path(os.environ["nnUNet_results"]) / "Dataset599_ImageCAS_SMOKE"
    trainers = list(result_root.glob("nnUNetTrainer_1epoch__nnUNetPlans__3d_fullres"))
    if len(trainers) != 1:
        raise RuntimeError(f"Expected one smoke trainer folder, found {trainers}")
    fold = trainers[0] / "fold_0"
    required = [fold / "checkpoint_final.pth", fold / "checkpoint_best.pth"]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    validation = fold / "validation"
    predictions = sorted(validation.glob("case*.nii.gz"))
    summary_path = validation / "summary.json"
    if missing:
        raise RuntimeError(f"Missing checkpoint files: {missing}")
    if len(predictions) != 4:
        raise RuntimeError(f"Expected four validation predictions, found {len(predictions)}")
    if not summary_path.is_file():
        raise RuntimeError(f"Missing validation summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = {
        "status": "PASS",
        "trainer": "nnUNetTrainer_1epoch",
        "configuration": "3d_fullres",
        "fold": 0,
        "checkpoint_final_mb": round(required[0].stat().st_size / 1024**2, 2),
        "checkpoint_best_mb": round(required[1].stat().st_size / 1024**2, 2),
        "validation_prediction_count": len(predictions),
        "validation_cases": [path.name.removesuffix(".nii.gz") for path in predictions],
        "foreground_mean": summary.get("foreground_mean"),
    }
    print("SMOKE_TRAIN_REPORT")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

