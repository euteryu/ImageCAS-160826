import pandas as pd

from imagecas.data.splits import read_split_table, reconcile_split


def test_read_long_split_csv(tmp_path):
    path = tmp_path / "split.csv"
    pd.DataFrame({"case_id": [1, 2, 3], "partition": ["Training", "Validation", "Testing"]}).to_csv(path, index=False)
    split = read_split_table(path)
    assert split.partition.tolist() == ["train", "val", "test"]
    assert split.case_id.tolist() == ["case0001", "case0002", "case0003"]


def test_reconciliation_is_explicit():
    manifest = pd.DataFrame({"case_id": ["case0001", "case0002"]})
    split = pd.DataFrame({"case_id": ["case0002", "case0003"]})
    report = reconcile_split(manifest, split).set_index("case_id")
    assert report.loc["case0001", "problem"] == "missing_from_split"
    assert report.loc["case0003", "problem"] == "missing_from_dataset"

