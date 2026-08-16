#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=/kaggle/working/ImageCAS-160826
REPO_URL=https://github.com/euteryu/ImageCAS-160826.git
WORKBOOK=/kaggle/input/datasets/xiaoweixumedicalai/imagecas/imageCAS_data_split.xlsx

if [[ -d "$REPO_DIR/.git" ]]; then
  git -C "$REPO_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"
python -m pip install -q -e ".[excel,nnunet]"
python scripts/00_inspect_imagecas_inputs.py > /kaggle/working/input_inspection.json
python scripts/03_build_smoke_dataset.py "$WORKBOOK"
python kaggle/01_verify_stack.py
