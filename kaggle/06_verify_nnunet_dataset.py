from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run nnU-Net's official dataset integrity check")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--processes", type=int, default=2)
    args = parser.parse_args()

    from nnunetv2.experiment_planning.verify_dataset_integrity import verify_dataset_integrity

    verify_dataset_integrity(str(args.dataset), args.processes)
    print("NNUNET_DATASET_INTEGRITY: PASS")


if __name__ == "__main__":
    main()
