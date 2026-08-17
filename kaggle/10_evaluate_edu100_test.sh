#!/usr/bin/env bash
set -euo pipefail

WORK_ROOT=/kaggle/working
REPO_DIR=$WORK_ROOT/ImageCAS-160826
DATASET_NAME=Dataset598_ImageCAS_EDU100
export nnUNet_raw=$WORK_ROOT/nnUNet_raw
export nnUNet_preprocessed=$WORK_ROOT/nnUNet_preprocessed
export nnUNet_results=$WORK_ROOT/nnUNet_results
export CUDA_VISIBLE_DEVICES=0

mkdir -p "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"
cd "$REPO_DIR"
python -m pip install -q -e ".[excel,nnunet]"
python kaggle/01_verify_stack.py
python scripts/00_inspect_imagecas_inputs.py > "$WORK_ROOT/input_inspection.json"
python kaggle/10_prepare_edu100_test.py
nnUNetv2_predict \
  -i "$WORK_ROOT/edu100_test/imagesTs" \
  -o "$WORK_ROOT/edu100_test/predictions" \
  -d 598 -c 3d_fullres -f 2 \
  -tr nnUNetTrainer_50epochs \
  -chk checkpoint_best.pth
python kaggle/11_extract_edu100_test_references.py
python kaggle/12_evaluate_edu100_test.py
du -sh "$WORK_ROOT/edu100_test" "$nnUNet_results/$DATASET_NAME" 2>/dev/null || true
df -h "$WORK_ROOT"
