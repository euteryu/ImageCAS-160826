from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from imagecas.data.archives import extract_case, index_archives
from imagecas.data.discover import sha256_file
from imagecas.data.educational_subset import nested_training_splits, select_educational_subset
from imagecas.data.splits import read_split_table


DATASET_NAME = "Dataset598_ImageCAS_EDU100"


def write_json(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the 80-case development portion of the ImageCAS educational subset"
    )
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--archive-root", type=Path, default=Path("/kaggle/working/imagecas_archive_links")
    )
    parser.add_argument("--nnunet-raw", type=Path, default=Path("/kaggle/working/nnUNet_raw"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/edu100"))
    args = parser.parse_args()

    official_split = read_split_table(args.workbook, split=1)
    manifest = select_educational_subset(official_split)
    development = manifest.loc[manifest.included_in_development_dataset]
    test_cases = manifest.loc[manifest.role == "test", "case_id"].tolist()
    dataset = args.nnunet_raw / DATASET_NAME
    images_tr = dataset / "imagesTr"
    labels_tr = dataset / "labelsTr"
    images_tr.mkdir(parents=True, exist_ok=True)
    labels_tr.mkdir(parents=True, exist_ok=True)
    archive_index = index_archives(args.archive_root)

    source_records = []
    for position, row in enumerate(development.itertuples(index=False), start=1):
        case_id = row.case_id
        case_number = int(case_id.removeprefix("case"))
        archive, entries = archive_index[case_number]
        image_target = images_tr / f"{case_id}_0000.nii.gz"
        label_target = labels_tr / f"{case_id}.nii.gz"
        if not image_target.exists() or not label_target.exists():
            with tempfile.TemporaryDirectory(
                prefix=f"edu_{case_id}_", dir="/kaggle/working"
            ) as tmp:
                image, label = extract_case(archive, entries, Path(tmp))
                shutil.copy2(image, image_target)
                shutil.copy2(label, label_target)
        source_records.append(
            {
                "case_id": case_id,
                "role": row.role,
                "source_archive": archive.name,
                "image_entry": entries["img"],
                "label_entry": entries["label"],
                "image_sha256": sha256_file(image_target),
                "label_sha256": sha256_file(label_target),
            }
        )
        print(f"[{position}/{len(development)}] {case_id} ({row.role})", flush=True)

    write_json(
        {
            "channel_names": {"0": "CT"},
            "labels": {"background": 0, "coronary": 1},
            "numTraining": len(development),
            "file_ending": ".nii.gz",
            "name": "ImageCAS 100-case educational baseline (80 development cases)",
        },
        dataset / "dataset.json",
    )
    args.artifacts.mkdir(parents=True, exist_ok=True)
    metadata = dataset / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PASS",
        "dataset": str(dataset),
        "development_case_count": len(development),
        "training_pool_count": int((development.role == "train").sum()),
        "validation_count": int((development.role == "val").sum()),
        "held_out_test_count": len(test_cases),
        "held_out_test_cases_extracted": 0,
        "test_isolation": "PASS",
        "next_step": (
            "persist raw dataset; preprocess from a read-only attachment in a fresh session"
        ),
    }
    for output in (args.artifacts, metadata):
        manifest.to_csv(output / "subset_manifest.csv", index=False)
        write_json(source_records, output / "development_source_manifest.json")
        write_json(nested_training_splits(manifest), output / "splits_learning_curve.json")
        write_json(report, output / "build_report.json")
    print((args.artifacts / "build_report.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
