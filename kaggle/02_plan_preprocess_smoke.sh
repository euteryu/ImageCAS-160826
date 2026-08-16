#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
export nnUNet_raw=$WORK_ROOT/nnUNet_raw
export nnUNet_preprocessed=$WORK_ROOT/nnUNet_preprocessed
export nnUNet_results=$WORK_ROOT/nnUNet_results

mkdir -p "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"
cd "$REPO_DIR"

nnUNetv2_plan_and_preprocess \
  -d 599 \
  --verify_dataset_integrity \
  -c 3d_fullres \
  -npfp 2 \
  -np 2

DATASET_DIR=$nnUNet_preprocessed/Dataset599_ImageCAS_SMOKE
cp artifacts/smoke_splits_final.json "$DATASET_DIR/splits_final.json"

python kaggle/02_report_plan.py
du -sh "$nnUNet_raw/Dataset599_ImageCAS_SMOKE"
du -sh "$DATASET_DIR"
df -h "$WORK_ROOT"

