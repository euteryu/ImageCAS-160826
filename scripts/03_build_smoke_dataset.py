from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from imagecas.data.archives import extract_case, index_archives
from imagecas.data.discover import sha256_file
from imagecas.data.splits import read_split_table


DATASET_NAME = "Dataset599_ImageCAS_SMOKE"


def write_json(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the non-scientific ImageCAS smoke dataset")
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--archive-root", type=Path, default=Path("/kaggle/working/imagecas_archive_links")
    )
    parser.add_argument("--nnunet-raw", type=Path, default=Path("/kaggle/working/nnUNet_raw"))
    parser.add_argument("--cases", type=int, default=20)
    parser.add_argument("--val-cases", type=int, default=4)
    args = parser.parse_args()
    if args.cases < 2 or not 0 < args.val_cases < args.cases:
        raise ValueError("Require at least two cases and 0 < val-cases < cases")

    split = read_split_table(args.workbook, split=1)
    selected = split.loc[split.partition == "train", "case_id"].head(args.cases).tolist()
    if len(selected) != args.cases:
        raise RuntimeError(f"Requested {args.cases} cases but selected {len(selected)}")
    archive_index = index_archives(args.archive_root)

    dataset = args.nnunet_raw / DATASET_NAME
    images_tr, labels_tr = dataset / "imagesTr", dataset / "labelsTr"
    images_tr.mkdir(parents=True, exist_ok=True)
    labels_tr.mkdir(parents=True, exist_ok=True)
    manifest = []
    for position, case_id in enumerate(selected, start=1):
        case_number = int(case_id.removeprefix("case"))
        archive, entries = archive_index[case_number]
        image_target = images_tr / f"{case_id}_0000.nii.gz"
        label_target = labels_tr / f"{case_id}.nii.gz"
        if not image_target.exists() or not label_target.exists():
            with tempfile.TemporaryDirectory(prefix=f"smoke_{case_id}_", dir="/kaggle/working") as tmp:
                image, label = extract_case(archive, entries, Path(tmp))
                shutil.copy2(image, image_target)
                shutil.copy2(label, label_target)
        manifest.append(
            {
                "case_id": case_id,
                "source_archive": archive.name,
                "image_entry": entries["img"],
                "label_entry": entries["label"],
                "image_sha256": sha256_file(image_target),
                "label_sha256": sha256_file(label_target),
            }
        )
        print(f"[{position}/{len(selected)}] {case_id}", flush=True)

    write_json(
        {
            "channel_names": {"0": "CT"},
            "labels": {"background": 0, "coronary": 1},
            "numTraining": len(selected),
            "file_ending": ".nii.gz",
            "name": "ImageCAS engineering smoke test - not for scientific reporting",
        },
        dataset / "dataset.json",
    )
    train_ids = selected[: -args.val_cases]
    val_ids = selected[-args.val_cases :]
    split_path = Path("artifacts/smoke_splits_final.json")
    write_json([{"train": train_ids, "val": val_ids}], split_path)
    write_json(manifest, Path("artifacts/smoke_manifest.json"))
    print(
        json.dumps(
            {
                "status": "PASS",
                "dataset": str(dataset),
                "training_cases": len(train_ids),
                "validation_cases": len(val_ids),
                "split_file_for_preprocessed_folder": str(split_path.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
