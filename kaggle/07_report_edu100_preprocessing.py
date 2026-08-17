from __future__ import annotations

import json
import os
from pathlib import Path
import re


DATASET_NAME = "Dataset598_ImageCAS_EDU100"
CASE_PAYLOAD_RE = re.compile(r"^(case\d{4})(?:\.npz|\.npy)$")


def preprocessed_case_ids(data_folder: Path) -> set[str]:
    """Find cases in either packed (.npz) or unpacked (.npy) nnU-Net form."""
    case_ids: set[str] = set()
    for path in data_folder.iterdir():
        match = CASE_PAYLOAD_RE.fullmatch(path.name)
        if match is not None:
            case_ids.add(match.group(1))
    return case_ids


def main() -> None:
    dataset = Path(os.environ["nnUNet_preprocessed"]) / DATASET_NAME
    fingerprint = json.loads((dataset / "dataset_fingerprint.json").read_text(encoding="utf-8"))
    plans = json.loads((dataset / "nnUNetPlans.json").read_text(encoding="utf-8"))
    training_view = json.loads(
        (dataset / "training_fingerprint_view_report.json").read_text(encoding="utf-8")
    )
    development_view = json.loads(
        (dataset / "development_preprocess_view_report.json").read_text(encoding="utf-8")
    )
    configuration = plans["configurations"]["3d_fullres"]
    data_folder = dataset / configuration["data_identifier"]
    preprocessed_ids = preprocessed_case_ids(data_folder)
    preprocessed_cases = len(preprocessed_ids)
    fingerprint_cases = len(fingerprint["spacings"])
    checks = {
        "training_view_cases": training_view["case_count"] == 64,
        "fingerprint_cases": fingerprint_cases == 64,
        "development_view_cases": development_view["case_count"] == 80,
        "preprocessed_cases": preprocessed_cases == 80,
        "test_cases_in_views": training_view["test_cases"] == development_view["test_cases"] == 0,
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "dataset": DATASET_NAME,
        "configuration": "3d_fullres",
        "training_fingerprint_case_count": fingerprint_cases,
        "development_preprocessed_case_count": preprocessed_cases,
        "test_case_count": 0,
        "target_spacing": configuration["spacing"],
        "patch_size": configuration["patch_size"],
        "batch_size": configuration["batch_size"],
        "foreground_intensity_properties": plans[
            "foreground_intensity_properties_per_channel"
        ]["0"],
    }
    output = Path("/kaggle/working/edu100_preprocess_report.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("EDU100_PREPROCESS_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
