#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
export nnUNet_raw=$WORK_ROOT/nnUNet_raw
export nnUNet_preprocessed=$WORK_ROOT/nnUNet_preprocessed
export nnUNet_results=$WORK_ROOT/nnUNet_results
export CUDA_VISIBLE_DEVICES=0

mkdir -p "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"
cd "$REPO_DIR"
python -m pip install -q -e ".[nnunet]"
python kaggle/01_verify_stack.py
python kaggle/08_prepare_edu100_training.py
nnUNetv2_train 598 3d_fullres 2 -tr nnUNetTrainer_50epochs
python kaggle/09_report_edu100_training.py
du -sh "$nnUNet_results/Dataset598_ImageCAS_EDU100"
df -h "$WORK_ROOT"
