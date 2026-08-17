from __future__ import annotations

import pandas as pd


ROLE_COUNTS = {"train": 64, "val": 16, "test": 20}


def select_educational_subset(
    split: pd.DataFrame,
    counts: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Select a deterministic, partition-preserving educational subset."""
    requested = ROLE_COUNTS if counts is None else counts
    if set(requested) != {"train", "val", "test"}:
        raise ValueError("counts must contain exactly train, val, and test")
    if any(not isinstance(value, int) or value < 1 for value in requested.values()):
        raise ValueError("all requested counts must be positive integers")
    required_columns = {"case_id", "partition"}
    if not required_columns.issubset(split.columns):
        raise ValueError(f"split must contain columns: {sorted(required_columns)}")
    if split.case_id.duplicated().any():
        raise ValueError("split contains duplicate case IDs")

    selections = []
    for role in ("train", "val", "test"):
        pool = split.loc[split.partition == role].sort_values("case_id")
        count = requested[role]
        if len(pool) < count:
            raise ValueError(f"requested {count} {role} cases but only {len(pool)} are available")
        selected = pool.head(count).copy()
        selected["role"] = role
        selected["subset_position"] = range(1, count + 1)
        selected["included_in_development_dataset"] = role != "test"
        selections.append(selected)

    result = pd.concat(selections, ignore_index=True)
    result["selection_rule"] = "lowest_normalized_case_ids_within_official_partition"
    return result


def nested_training_splits(manifest: pd.DataFrame) -> list[dict[str, list[str]]]:
    """Return fixed validation splits for nested 16-, 32-, and 64-case runs."""
    train_ids = manifest.loc[manifest.role == "train", "case_id"].tolist()
    val_ids = manifest.loc[manifest.role == "val", "case_id"].tolist()
    if len(train_ids) != 64 or len(val_ids) != 16:
        raise ValueError("nested learning splits require exactly 64 train and 16 validation cases")
    return [{"train": train_ids[:size], "val": val_ids} for size in (16, 32, 64)]
