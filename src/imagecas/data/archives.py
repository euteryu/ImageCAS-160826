from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


ENTRY_PATTERN = re.compile(r"(?:^|/)(\d+)\.(img|label)\.nii\.gz$", re.IGNORECASE)


def seven_zip() -> str:
    executable = shutil.which("7z") or shutil.which("7zz")
    if not executable:
        raise RuntimeError("7z/7zz is unavailable")
    return executable


def archive_entries(archive: Path) -> dict[int, dict[str, str]]:
    process = subprocess.run(
        [seven_zip(), "l", "-slt", str(archive)], check=True, capture_output=True, text=True
    )
    cases: dict[int, dict[str, str]] = {}
    for line in process.stdout.splitlines():
        if not line.startswith("Path = "):
            continue
        entry = line[7:]
        match = ENTRY_PATTERN.search(entry)
        if match:
            case_number, role = int(match.group(1)), match.group(2).lower()
            cases.setdefault(case_number, {})[role] = entry
    incomplete = {case: roles for case, roles in cases.items() if set(roles) != {"img", "label"}}
    if incomplete:
        raise RuntimeError(f"Incomplete archive pairs: {incomplete}")
    return cases


def index_archives(archive_root: Path) -> dict[int, tuple[Path, dict[str, str]]]:
    archives = sorted(archive_root.glob("*.zip"))
    if len(archives) != 5:
        raise RuntimeError(f"Expected five linked archives, found {len(archives)}")
    index = {}
    for archive in archives:
        for case_number, entries in archive_entries(archive).items():
            if case_number in index:
                raise RuntimeError(f"Duplicate case across archives: {case_number}")
            index[case_number] = (archive, entries)
    return index


def extract_case(archive: Path, entries: dict[str, str], output_dir: Path) -> tuple[Path, Path]:
    process = subprocess.run(
        [
            seven_zip(), "x", "-y", f"-o{output_dir}", str(archive),
            entries["img"], entries["label"],
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Extraction failed:\n{process.stdout}\n{process.stderr}")
    image_matches = list(output_dir.rglob(Path(entries["img"]).name))
    mask_matches = list(output_dir.rglob(Path(entries["label"]).name))
    if len(image_matches) != 1 or len(mask_matches) != 1:
        raise RuntimeError(f"Unexpected extraction result for {entries}")
    return image_matches[0], mask_matches[0]

