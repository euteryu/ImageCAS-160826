from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd


NIFTI_SUFFIXES = (".nii", ".nii.gz")
DEFAULT_MASK_TOKENS = ("mask", "label", "seg", "annotation", "gt")


@dataclass(frozen=True)
class DiscoveredFile:
    case_id: str
    role: str
    path: str
    size_bytes: int
    sha256: str


def is_nifti(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(NIFTI_SUFFIXES)


def normalize_case_id(path: Path, pattern: str, width: int = 4) -> str:
    """Extract a patient identifier while ignoring nnU-Net channel suffixes."""
    stem = path.name[:-7] if path.name.lower().endswith(".nii.gz") else path.stem
    stem = re.sub(r"_\d{4}$", "", stem)
    matches = re.findall(pattern, stem)
    if not matches:
        raise ValueError(f"Cannot extract case ID from {path.name!r}")
    value = matches[-1]
    if isinstance(value, tuple):
        value = next((part for part in value if part), "")
    return f"case{int(value):0{width}d}"


def infer_role(path: Path, mask_tokens: Sequence[str] = DEFAULT_MASK_TOKENS) -> str:
    components = [part.lower() for part in path.parts]
    name = path.name.lower()
    is_mask = any(
        token in name or any(token in component for component in components)
        for token in mask_tokens
    )
    return "mask" if is_mask else "image"


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_dataset(
    root: Path,
    case_pattern: str,
    case_width: int = 4,
    mask_tokens: Sequence[str] = DEFAULT_MASK_TOKENS,
    compute_hashes: bool = True,
) -> pd.DataFrame:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset root does not exist: {root}")
    rows: list[dict] = []
    for path in sorted((p for p in root.rglob("*") if p.is_file() and is_nifti(p))):
        row = DiscoveredFile(
            case_id=normalize_case_id(path, case_pattern, case_width),
            role=infer_role(path, mask_tokens),
            path=str(path),
            size_bytes=path.stat().st_size,
            sha256=sha256_file(path) if compute_hashes else "",
        )
        rows.append(asdict(row))
    return pd.DataFrame(rows, columns=["case_id", "role", "path", "size_bytes", "sha256"])


def pairing_report(files: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return one-row-per-case pairing manifest and all pairing problems."""
    if files.empty:
        cols = ["case_id", "image_path", "mask_path", "image_sha256", "mask_sha256"]
        return pd.DataFrame(columns=cols), pd.DataFrame(columns=["case_id", "problem", "paths"])
    manifests: list[dict] = []
    problems: list[dict] = []
    for case_id, group in files.groupby("case_id", sort=True):
        images = group[group.role == "image"]
        masks = group[group.role == "mask"]
        if len(images) != 1 or len(masks) != 1:
            if not len(images):
                problem = "orphan_mask"
            elif not len(masks):
                problem = "orphan_image"
            else:
                problem = "duplicate_image_or_mask"
            problems.append(
                {"case_id": case_id, "problem": problem, "paths": " | ".join(group.path)}
            )
            continue
        image, mask = images.iloc[0], masks.iloc[0]
        manifests.append(
            {
                "case_id": case_id,
                "image_path": image.path,
                "mask_path": mask.path,
                "image_sha256": image.sha256,
                "mask_sha256": mask.sha256,
            }
        )
    return pd.DataFrame(manifests), pd.DataFrame(problems)


def manifest_hash(records: pd.DataFrame, columns: Iterable[str] | None = None) -> str:
    subset = records[list(columns)] if columns else records
    payload = subset.sort_values(list(subset.columns)).to_csv(index=False, lineterminator="\n")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
