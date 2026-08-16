from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

from imagecas.data.splits import read_split_table


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the official ImageCAS split workbook")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--split", type=int, default=1)
    parser.add_argument("--config", type=Path, default=Path("configs/imagecas_split1.yaml"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/split_manifest.csv"))
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    split = read_split_table(args.workbook, args.split, config["case_id"]["width"])
    expected_ids = {f"case{value:04d}" for value in range(1, config["expected_cases"] + 1)}
    actual_ids = set(split.case_id)
    counts = split.partition.value_counts().to_dict()
    expected_counts = config["expected_counts"]
    problems = []
    if counts != expected_counts:
        problems.append(f"partition counts differ: {counts} != {expected_counts}")
    missing = sorted(expected_ids - actual_ids)
    unexpected = sorted(actual_ids - expected_ids)
    if missing:
        problems.append(f"missing IDs: {missing[:20]}")
    if unexpected:
        problems.append(f"unexpected IDs: {unexpected[:20]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    split.to_csv(args.output, index=False, lineterminator="\n")
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    report = {
        "sheet": "v2-latest",
        "official_split": args.split,
        "case_count": len(split),
        "partition_counts": counts,
        "first_case_id": split.case_id.iloc[0],
        "last_case_id": split.case_id.iloc[-1],
        "manifest_sha256": digest,
        "problems": problems,
        "status": "PASS" if not problems else "FAIL",
    }
    print(json.dumps(report, indent=2))
    if problems:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
