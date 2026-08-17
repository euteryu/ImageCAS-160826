#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
export nnUNet_raw=$WORK_ROOT/nnUNet_raw
export nnUNet_preprocessed=$WORK_ROOT/nnUNet_preprocessed
export nnUNet_results=$WORK_ROOT/nnUNet_results

mkdir -p "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"
cd "$REPO_DIR"
python -m pip install -q -e ".[excel,nnunet]"

mapfile -t DATASET_JSONS < <(find /kaggle/input -path '*/Dataset598_ImageCAS_EDU100/dataset.json')
if [[ ${#DATASET_JSONS[@]} -ne 1 ]]; then
  echo "Expected exactly one attached Dataset598 dataset.json, found ${#DATASET_JSONS[@]}" >&2
  exit 1
fi
SOURCE_DATASET=$(dirname "${DATASET_JSONS[0]}")
TARGET_DATASET=$nnUNet_raw/Dataset598_ImageCAS_EDU100
TRAIN_REPORT=$WORK_ROOT/edu100_training_view_report.json
DEVELOPMENT_REPORT=$WORK_ROOT/edu100_development_view_report.json

# First expose all 80 development cases solely for input-integrity checking.
python scripts/06_build_strict_nnunet_view.py \
  "$SOURCE_DATASET" "$TARGET_DATASET" --mode development --report "$DEVELOPMENT_REPORT"
python kaggle/06_verify_nnunet_dataset.py "$TARGET_DATASET" --processes 2

# Fit fingerprint and plans using only the fixed 64-case training pool.
python scripts/06_build_strict_nnunet_view.py \
  "$SOURCE_DATASET" "$TARGET_DATASET" --mode training --report "$TRAIN_REPORT"
nnUNetv2_extract_fingerprint -d 598 --verify_dataset_integrity -np 2
nnUNetv2_plan_experiment -d 598

# Freeze the training-derived plan, restore validation inputs, and preprocess all 80.
python scripts/06_build_strict_nnunet_view.py \
  "$SOURCE_DATASET" "$TARGET_DATASET" --mode development --report "$DEVELOPMENT_REPORT"
nnUNetv2_preprocess -d 598 -c 3d_fullres -np 2

PREPROCESSED=$nnUNet_preprocessed/Dataset598_ImageCAS_EDU100
cp "$SOURCE_DATASET/metadata/splits_learning_curve.json" "$PREPROCESSED/splits_learning_curve.json"
cp "$SOURCE_DATASET/metadata/subset_manifest.csv" "$PREPROCESSED/subset_manifest.csv"
cp "$TRAIN_REPORT" "$PREPROCESSED/training_fingerprint_view_report.json"
cp "$DEVELOPMENT_REPORT" "$PREPROCESSED/development_preprocess_view_report.json"

python kaggle/07_report_edu100_preprocessing.py
du -sh "$PREPROCESSED"
df -h "$WORK_ROOT"
