from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from imagecas.data.splits import read_split_table, reconcile_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("split_file", type=Path)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    manifest = pd.read_csv(args.manifest)
    split = read_split_table(args.split_file, args.split)
    report = reconcile_split(manifest, split)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    split.to_csv(args.output_dir / "split_manifest.csv", index=False)
    report.to_csv(args.output_dir / "split_reconciliation.csv", index=False)
    counts = split.partition.value_counts().to_dict()
    print(f"Partition counts: {counts}")
    problems = report[report.problem != ""]
    if len(problems):
        print(f"Reconciliation problems: {len(problems)}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()

