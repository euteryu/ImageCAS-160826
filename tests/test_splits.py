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


def test_read_imagecas_v2_workbook(tmp_path):
    path = tmp_path / "imageCAS_data_split.xlsx"
    rows = pd.DataFrame([
        [None, "4-fold cross validation", None, None, None],
        ["FileName", "Split-1", "Split-2", "Split-3", "Split-4"],
        [1, "Training", "Training", "Validation", "Testing"],
        [2, "Validation", "Testing", "Training", "Training"],
        [3, "Testing", "Validation", "Testing", "Training"],
    ])
    with pd.ExcelWriter(path) as writer:
        rows.to_excel(writer, sheet_name="v2-latest", header=False, index=False)
    split = read_split_table(path, split=1)
    assert split.case_id.tolist() == ["case0001", "case0002", "case0003"]
    assert split.partition.tolist() == ["train", "val", "test"]
