#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
export nnUNet_raw=$WORK_ROOT/nnUNet_raw
export nnUNet_preprocessed=$WORK_ROOT/nnUNet_preprocessed
export nnUNet_results=$WORK_ROOT/nnUNet_results

mkdir -p "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"
cd "$REPO_DIR"

mapfile -t DATASET_JSONS < <(find /kaggle/input -path '*/Dataset598_ImageCAS_EDU100/dataset.json')
if [[ ${#DATASET_JSONS[@]} -ne 1 ]]; then
  echo "Expected exactly one attached Dataset501 dataset.json, found ${#DATASET_JSONS[@]}" >&2
  exit 1
fi
SOURCE_DATASET=$(dirname "${DATASET_JSONS[0]}")
TARGET_DATASET=$nnUNet_raw/Dataset598_ImageCAS_EDU100
if [[ ! -e "$TARGET_DATASET" ]]; then
  ln -s "$SOURCE_DATASET" "$TARGET_DATASET"
fi

nnUNetv2_plan_and_preprocess \
  -d 598 \
  --verify_dataset_integrity \
  -c 3d_fullres \
  -npfp 2 \
  -np 2

PREPROCESSED=$nnUNet_preprocessed/Dataset598_ImageCAS_EDU100
cp "$SOURCE_DATASET/metadata/splits_learning_curve.json" "$PREPROCESSED/splits_learning_curve.json"
cp "$SOURCE_DATASET/metadata/subset_manifest.csv" "$PREPROCESSED/subset_manifest.csv"

du -sh "$PREPROCESSED"
df -h "$WORK_ROOT"
