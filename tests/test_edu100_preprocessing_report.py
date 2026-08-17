import importlib.util
from pathlib import Path


REPORT_SCRIPT = Path(__file__).parents[1] / "kaggle" / "07_report_edu100_preprocessing.py"
SPEC = importlib.util.spec_from_file_location("edu100_preprocessing_report", REPORT_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def test_preprocessed_case_ids_accepts_packed_and_unpacked_cases(tmp_path):
    (tmp_path / "case0001.npz").touch()
    (tmp_path / "case0002.npy").touch()
    (tmp_path / "case0002_seg.npy").touch()
    (tmp_path / "case0003.b2nd").touch()
    (tmp_path / "case0003_seg.b2nd").touch()
    (tmp_path / "case0004.pkl").touch()

    assert REPORT.preprocessed_case_ids(tmp_path) == {"case0001", "case0002", "case0003"}


def test_preprocessed_case_ids_deduplicates_both_representations(tmp_path):
    (tmp_path / "case0001.npz").touch()
    (tmp_path / "case0001.npy").touch()

    assert REPORT.preprocessed_case_ids(tmp_path) == {"case0001"}
