#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
WORKBOOK=/kaggle/input/datasets/xiaoweixumedicalai/imagecas/imageCAS_data_split.xlsx
export nnUNet_raw=$WORK_ROOT/nnUNet_raw

cd "$REPO_DIR"
python -m pip install -q -e ".[excel,nnunet]"
python scripts/00_inspect_imagecas_inputs.py > "$WORK_ROOT/input_inspection.json"
python scripts/05_build_educational_dataset.py "$WORKBOOK"

du -sh "$nnUNet_raw/Dataset598_ImageCAS_EDU100"
df -h "$WORK_ROOT"
