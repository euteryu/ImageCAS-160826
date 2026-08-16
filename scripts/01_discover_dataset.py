from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from imagecas.data.discover import discover_dataset, manifest_hash, pairing_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/imagecas_split1.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--skip-hashes", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    files = discover_dataset(
        args.dataset_root,
        config["case_id"]["regex"],
        config["case_id"]["width"],
        compute_hashes=not args.skip_hashes,
    )
    manifest, problems = pairing_report(files)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files.to_csv(args.output_dir / "discovered_files.csv", index=False)
    manifest.to_csv(args.output_dir / "data_manifest.csv", index=False)
    problems.to_csv(args.output_dir / "pairing_problems.csv", index=False)
    print(f"NIfTI files: {len(files)}; paired cases: {len(manifest)}; problems: {len(problems)}")
    if len(manifest):
        print(f"Manifest SHA-256: {manifest_hash(manifest)}")
    expected = config.get("expected_cases")
    if expected is not None and len(manifest) != int(expected):
        print(f"Expected {expected} paired cases, found {len(manifest)}")
        raise SystemExit(2)
    if len(problems):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
