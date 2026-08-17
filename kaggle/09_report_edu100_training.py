from __future__ import annotations

import json
import os
from pathlib import Path


DATASET_NAME = "Dataset598_ImageCAS_EDU100"
TRAINER = "nnUNetTrainer_50epochs"


def main() -> None:
    result_root = Path(os.environ["nnUNet_results"]) / DATASET_NAME
    trainer_root = result_root / f"{TRAINER}__nnUNetPlans__3d_fullres"
    fold = trainer_root / "fold_0"
    split_path = Path(os.environ["nnUNet_preprocessed"]) / DATASET_NAME / "splits_final.json"
    split = json.loads(split_path.read_text(encoding="utf-8"))[0]
    required = [fold / "checkpoint_final.pth", fold / "checkpoint_best.pth"]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    validation = fold / "validation"
    predictions = sorted(validation.glob("case*.nii.gz"))
    summary_path = validation / "summary.json"
    checks = {
        "training_cases": len(split["train"]) == 16,
        "validation_cases": len(split["val"]) == 16,
        "checkpoints": not missing,
        "validation_predictions": len(predictions) == 16,
        "validation_summary": summary_path.is_file(),
    }
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "dataset": DATASET_NAME,
        "trainer": TRAINER,
        "configuration": "3d_fullres",
        "fold": 0,
        "epochs": 50,
        "training_case_count": len(split["train"]),
        "validation_case_count": len(split["val"]),
        "validation_prediction_count": len(predictions),
        "checkpoint_final_mb": round(required[0].stat().st_size / 1024**2, 2)
        if required[0].is_file()
        else None,
        "checkpoint_best_mb": round(required[1].stat().st_size / 1024**2, 2)
        if required[1].is_file()
        else None,
        "foreground_mean": summary.get("foreground_mean"),
    }
    output = Path("/kaggle/working/edu100_train16_report.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("EDU100_TRAIN16_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
