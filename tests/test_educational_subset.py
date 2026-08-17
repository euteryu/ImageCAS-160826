import pandas as pd
import pytest

from imagecas.data.educational_subset import nested_training_splits, select_educational_subset


def make_split() -> pd.DataFrame:
    rows = []
    number = 1
    for partition, count in (("train", 70), ("val", 20), ("test", 30)):
        for _ in range(count):
            rows.append({"case_id": f"case{number:04d}", "partition": partition})
            number += 1
    return pd.DataFrame(rows).sample(frac=1, random_state=7).reset_index(drop=True)


def test_selection_has_fixed_counts_and_is_deterministic():
    split = make_split()
    first = select_educational_subset(split)
    second = select_educational_subset(split.sample(frac=1, random_state=11))
    assert first.case_id.tolist() == second.case_id.tolist()
    assert first.groupby("role").size().to_dict() == {"test": 20, "train": 64, "val": 16}


def test_test_cases_are_excluded_from_development():
    manifest = select_educational_subset(make_split())
    development = manifest.loc[manifest.included_in_development_dataset]
    assert len(development) == 80
    assert set(development.role) == {"train", "val"}
    assert not set(manifest.loc[manifest.role == "test", "case_id"]) & set(development.case_id)


def test_learning_curve_splits_are_nested_with_fixed_validation():
    manifest = select_educational_subset(make_split())
    splits = nested_training_splits(manifest)
    assert [len(item["train"]) for item in splits] == [16, 32, 64]
    assert all(len(item["val"]) == 16 for item in splits)
    assert set(splits[0]["train"]) < set(splits[1]["train"]) < set(splits[2]["train"])
    assert splits[0]["val"] == splits[1]["val"] == splits[2]["val"]


def test_selection_rejects_an_undersized_partition():
    split = make_split().loc[lambda frame: frame.partition != "test"].copy()
    with pytest.raises(ValueError, match="test cases"):
        select_educational_subset(split)
