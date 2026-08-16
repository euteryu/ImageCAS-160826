from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


def command_output(command: list[str]) -> str | None:
    try:
        return subprocess.run(command, check=False, capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Kaggle inputs and runtime information")
    parser.add_argument("--input-root", type=Path, default=Path("/kaggle/input"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    nifti = []
    workbooks = []
    datasets = []
    if args.input_root.exists():
        datasets = sorted(str(path) for path in args.input_root.iterdir() if path.is_dir())
        for path in args.input_root.rglob("*"):
            if not path.is_file():
                continue
            lower = path.name.lower()
            if lower.endswith((".nii", ".nii.gz")):
                nifti.append(str(path))
            elif lower.endswith((".xlsx", ".xls", ".csv")):
                workbooks.append(str(path))

    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "input_root": str(args.input_root),
        "attached_dataset_directories": datasets,
        "nifti_count": len(nifti),
        "nifti_examples": nifti[:20],
        "split_file_candidates": workbooks,
        "nvidia_smi": command_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]
        ),
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
