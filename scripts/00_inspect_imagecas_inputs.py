from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd


def find_dataset_root(input_root: Path) -> Path:
    matches = sorted(input_root.rglob("imageCAS_data_split.xlsx"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one imageCAS_data_split.xlsx, found {len(matches)}: {matches}")
    return matches[0].parent


def link_archive_group(dataset_root: Path, stem: str, link_root: Path) -> Path:
    link_root.mkdir(parents=True, exist_ok=True)
    members = sorted(dataset_root.glob(f"{stem}.z[0-9][0-9]"))
    head = dataset_root / f"{stem}.change2zip"
    if not head.exists() or not members:
        raise RuntimeError(f"Incomplete multipart archive group: {stem}")
    for source in members:
        target = link_root / source.name
        if not target.exists():
            target.symlink_to(source)
    zip_link = link_root / f"{stem}.zip"
    if not zip_link.exists():
        zip_link.symlink_to(head)
    return zip_link


def list_archive(archive: Path) -> dict:
    seven_zip = shutil.which("7z") or shutil.which("7zz")
    if not seven_zip:
        raise RuntimeError("7z/7zz is unavailable in this Kaggle image")
    process = subprocess.run(
        [seven_zip, "l", "-slt", str(archive)], capture_output=True, text=True, check=False
    )
    if process.returncode != 0:
        raise RuntimeError(f"7z could not read {archive.name}:\n{process.stdout}\n{process.stderr}")
    paths = [line[7:] for line in process.stdout.splitlines() if line.startswith("Path = ")]
    file_paths = [path for path in paths if re.search(r"\.nii(?:\.gz)?$", path, re.IGNORECASE)]
    return {
        "archive": archive.name,
        "nifti_entry_count": len(file_paths),
        "nifti_entry_examples": file_paths[:12],
    }


def inspect_workbook(path: Path) -> dict:
    workbook = pd.ExcelFile(path)
    sheets = {}
    for sheet in workbook.sheet_names:
        preview = pd.read_excel(path, sheet_name=sheet, nrows=5)
        sheets[str(sheet)] = {
            "columns": [str(column) for column in preview.columns],
            "preview": preview.where(preview.notna(), None).to_dict(orient="records"),
        }
    return {"path": str(path), "sheets": sheets}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument(
        "--link-root", type=Path, default=Path("/kaggle/working/imagecas_archive_links")
    )
    args = parser.parse_args()
    dataset_root = find_dataset_root(args.input_root)
    stems = ["1-200", "201-400", "401-600", "601-800", "801-1000"]
    archive_reports = []
    for stem in stems:
        archive = link_archive_group(dataset_root, stem, args.link_root)
        archive_reports.append(list_archive(archive))
    report = {
        "dataset_root": str(dataset_root),
        "archive_links_use_bytes": sum(path.lstat().st_size for path in args.link_root.iterdir()),
        "archives": archive_reports,
        "split_workbook": inspect_workbook(dataset_root / "imageCAS_data_split.xlsx"),
    }
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
