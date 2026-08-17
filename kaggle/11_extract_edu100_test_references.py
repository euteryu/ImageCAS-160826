from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile

from imagecas.data.archives import extract_case_member, index_archives
from imagecas.data.discover import sha256_file


STAGE_ROOT = Path("/kaggle/working/edu100_test")
ARCHIVE_ROOT = Path("/kaggle/working/imagecas_archive_links")


def main() -> None:
    input_report = json.loads(
        (STAGE_ROOT / "inference_input_report.json").read_text(encoding="utf-8")
    )
    test_ids = [record["case_id"] for record in input_report["cases"]]
    predictions = STAGE_ROOT / "predictions"
    prediction_ids = {
        path.name.removesuffix(".nii.gz") for path in predictions.glob("case*.nii.gz")
    }
    if prediction_ids != set(test_ids):
        raise RuntimeError(
            "References cannot be extracted until all test predictions exist: "
            f"missing={sorted(set(test_ids) - prediction_ids)}, "
            f"unexpected={sorted(prediction_ids - set(test_ids))}"
        )

    references = STAGE_ROOT / "references"
    references.mkdir(parents=True, exist_ok=False)
    archive_index = index_archives(ARCHIVE_ROOT)
    records = []
    for position, case_id in enumerate(test_ids, start=1):
        case_number = int(case_id.removeprefix("case"))
        archive, entries = archive_index[case_number]
        target = references / f"{case_id}.nii.gz"
        with tempfile.TemporaryDirectory(
            prefix=f"test_reference_{case_id}_", dir="/kaggle/working"
        ) as tmp:
            source = extract_case_member(archive, entries, "label", Path(tmp))
            shutil.copy2(source, target)
        records.append(
            {
                "case_id": case_id,
                "label_entry": entries["label"],
                "label_sha256": sha256_file(target),
            }
        )
        print(f"[{position}/20] opened test reference {case_id}", flush=True)

    report = {
        "status": "PASS",
        "prediction_gate_passed": True,
        "prediction_count_before_reference_extraction": len(prediction_ids),
        "reference_count": len(records),
        "cases": records,
    }
    (STAGE_ROOT / "reference_extraction_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("EDU100_TEST_REFERENCE_EXTRACTION_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
