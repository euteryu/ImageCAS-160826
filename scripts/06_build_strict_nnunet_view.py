from __future__ import annotations

import argparse
import json
from pathlib import Path

from imagecas.data.strict_nnunet_view import build_view, read_and_validate_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a train-only or development nnU-Net view")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--mode", choices=["training", "development"], required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    manifest_path = args.source / "metadata" / "subset_manifest.csv"
    manifest = read_and_validate_manifest(manifest_path)
    report = build_view(args.source, args.target, manifest, args.mode)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
