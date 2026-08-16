from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


PARTITION_ALIASES = {
    "train": "train", "training": "train",
    "val": "val", "valid": "val", "validation": "val",
    "test": "test", "testing": "test",
}


def normalize_partition(value: object) -> str:
    key = str(value).strip().lower()
    if key not in PARTITION_ALIASES:
        raise ValueError(f"Unknown partition value: {value!r}")
    return PARTITION_ALIASES[key]


def normalize_id(value: object, width: int = 4) -> str:
    matches = re.findall(r"\d+", str(value))
    if not matches:
        raise ValueError(f"Cannot extract case ID from {value!r}")
    return f"case{int(matches[-1]):0{width}d}"


def _read_imagecas_workbook(path: Path, split: int) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="v2-latest", header=None)
    header_rows = raw.index[raw.iloc[:, 0].astype(str).str.strip().str.lower() == "filename"]
    if len(header_rows) != 1:
        raise ValueError("Could not locate the FileName header in v2-latest")
    header_row = int(header_rows[0])
    headings = [str(value).strip() for value in raw.iloc[header_row]]
    frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = headings
    case_column = "FileName"
    partition_column = f"Split-{split}"
    if partition_column not in frame.columns:
        raise ValueError(f"Workbook does not contain {partition_column}")
    result = frame[[case_column, partition_column]].dropna().copy()
    result.columns = ["case_id", "partition"]
    return result


def read_split_table(path: Path, split: int = 1, case_width: int = 4) -> pd.DataFrame:
    """Read a CSV/XLSX in either long form or three-column train/val/test form."""
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        frame = _read_imagecas_workbook(path, split)
    else:
        raise ValueError(f"Unsupported split format: {path.suffix}")
    lower = {str(c).strip().lower(): c for c in frame.columns}
    if {"case_id", "partition"}.issubset(lower):
        result = frame[[lower["case_id"], lower["partition"]]].copy()
        result.columns = ["case_id", "partition"]
    else:
        chunks = []
        for name, canonical in PARTITION_ALIASES.items():
            if name in lower:
                chunk = frame[[lower[name]]].dropna().rename(columns={lower[name]: "case_id"})
                chunk["partition"] = canonical
                chunks.append(chunk)
        if not chunks:
            raise ValueError("Split file needs case_id/partition columns or train/val/test columns")
        result = pd.concat(chunks, ignore_index=True)
    result["case_id"] = result.case_id.map(lambda value: normalize_id(value, case_width))
    result["partition"] = result.partition.map(normalize_partition)
    result["official_split"] = split
    if result.case_id.duplicated().any():
        duplicates = sorted(result.loc[result.case_id.duplicated(False), "case_id"].unique())
        raise ValueError(f"Duplicate cases in split: {duplicates[:10]}")
    return result.sort_values("case_id").reset_index(drop=True)


def reconcile_split(manifest: pd.DataFrame, split: pd.DataFrame) -> pd.DataFrame:
    cases = set(manifest.case_id)
    split_cases = set(split.case_id)
    rows = []
    for case_id in sorted(cases | split_cases):
        in_dataset, in_split = case_id in cases, case_id in split_cases
        rows.append({
            "case_id": case_id,
            "in_dataset": in_dataset,
            "in_official_split": in_split,
            "problem": "" if in_dataset and in_split else ("missing_from_split" if in_dataset else "missing_from_dataset"),
        })
    return pd.DataFrame(rows)
