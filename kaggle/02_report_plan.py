from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np


def main() -> None:
    dataset = Path(os.environ["nnUNet_preprocessed"]) / "Dataset599_ImageCAS_SMOKE"
    fingerprint = json.loads((dataset / "dataset_fingerprint.json").read_text(encoding="utf-8"))
    plans = json.loads((dataset / "nnUNetPlans.json").read_text(encoding="utf-8"))
    split = json.loads((dataset / "splits_final.json").read_text(encoding="utf-8"))
    configuration = plans["configurations"]["3d_fullres"]
    report = {
        "status": "PASS",
        "dataset": plans.get("dataset_name", "Dataset599_ImageCAS_SMOKE"),
        "configuration": "3d_fullres",
        "median_relative_size_after_cropping": fingerprint.get(
            "median_relative_size_after_cropping"
        ),
        "median_spacing": np.median(fingerprint["spacings"], axis=0).tolist(),
        "target_spacing": configuration.get("spacing"),
        "patch_size": configuration.get("patch_size"),
        "batch_size": configuration.get("batch_size"),
        "data_identifier": configuration.get("data_identifier"),
        "train_cases": len(split[0]["train"]),
        "validation_cases": len(split[0]["val"]),
        "split_installed": True,
    }
    print("SMOKE_PLAN_REPORT")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
