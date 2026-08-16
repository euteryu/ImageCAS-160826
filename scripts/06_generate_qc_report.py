from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from imagecas.qc.overlays import create_montage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("case_ids", nargs="*")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/qc/montages"))
    args = parser.parse_args()
    manifest = pd.read_csv(args.manifest).set_index("case_id")
    selected = args.case_ids or manifest.index.tolist()
    for case_id in selected:
        row = manifest.loc[case_id]
        create_montage(case_id, row.image_path, row.mask_path, args.output_dir / f"{case_id}.png")
    print(f"Created {len(selected)} montage(s) in {args.output_dir}")


if __name__ == "__main__":
    main()

