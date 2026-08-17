from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile

from imagecas.data.archives import extract_case_member, index_archives
from imagecas.data.discover import sha256_file
from imagecas.data.educational_subset import select_educational_subset
from imagecas.data.splits import read_split_table


DATASET_NAME = "Dataset598_ImageCAS_EDU100"
TRAINER_NAME = "nnUNetTrainer_50epochs__nnUNetPlans__3d_fullres"
WORKBOOK = Path("/kaggle/input/datasets/xiaoweixumedicalai/imagecas/imageCAS_data_split.xlsx")
ARCHIVE_ROOT = Path("/kaggle/working/imagecas_archive_links")
STAGE_ROOT = Path("/kaggle/working/edu100_test")


def find_trained_dataset(input_root: Path) -> tuple[Path, Path]:
    candidates = sorted(
        input_root.glob(
            f"**/{DATASET_NAME}/{TRAINER_NAME}/fold_2/checkpoint_best.pth"
        )
    )
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one attached Phase 3A checkpoint, found {candidates}")
    checkpoint = candidates[0]
    dataset_root = next(parent for parent in checkpoint.parents if parent.name == DATASET_NAME)
    return dataset_root, checkpoint


def main() -> None:
    manifest = select_educational_subset(read_split_table(WORKBOOK, split=1))
    test_ids = manifest.loc[manifest.role == "test", "case_id"].tolist()
    if len(test_ids) != 20 or manifest.loc[manifest.role == "test", "partition"].ne("test").any():
        raise ValueError("Educational test selection is not 20 official Split-1 test cases")

    result_source, checkpoint = find_trained_dataset(Path("/kaggle/input"))
    result_target = Path(os.environ["nnUNet_results"]) / DATASET_NAME
    result_target.parent.mkdir(parents=True, exist_ok=True)
    if result_target.exists() or result_target.is_symlink():
        raise FileExistsError(result_target)
    os.symlink(result_source, result_target, target_is_directory=True)

    images = STAGE_ROOT / "imagesTs"
    images.mkdir(parents=True, exist_ok=False)
    archive_index = index_archives(ARCHIVE_ROOT)
    records = []
    for position, case_id in enumerate(test_ids, start=1):
        case_number = int(case_id.removeprefix("case"))
        archive, entries = archive_index[case_number]
        target = images / f"{case_id}_0000.nii.gz"
        with tempfile.TemporaryDirectory(
            prefix=f"test_image_{case_id}_", dir="/kaggle/working"
        ) as tmp:
            source = extract_case_member(archive, entries, "img", Path(tmp))
            shutil.copy2(source, target)
        records.append(
            {
                "case_id": case_id,
                "official_partition": "test",
                "source_archive": archive.name,
                "image_entry": entries["img"],
                "image_sha256": sha256_file(target),
                "reference_extracted_before_inference": False,
            }
        )
        print(f"[{position}/20] staged test image {case_id}", flush=True)

    report = {
        "status": "PASS",
        "test_image_count": len(records),
        "test_reference_count": 0,
        "official_partition": "test",
        "selection_rule": "lowest_normalized_case_ids_within_official_partition",
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "model_is_read_only_symlink": True,
        "references_remain_unextracted": True,
        "cases": records,
    }
    STAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (STAGE_ROOT / "inference_input_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("EDU100_TEST_INFERENCE_INPUT_REPORT")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
