#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
export nnUNet_raw=$WORK_ROOT/nnUNet_raw
export nnUNet_preprocessed=$WORK_ROOT/nnUNet_preprocessed
export nnUNet_results=$WORK_ROOT/nnUNet_results
export CUDA_VISIBLE_DEVICES=0

cd "$REPO_DIR"
nnUNetv2_train 599 3d_fullres 0 -tr nnUNetTrainer_1epoch
python kaggle/03_report_training.py
du -sh "$nnUNet_results/Dataset599_ImageCAS_SMOKE"
df -h "$WORK_ROOT"

