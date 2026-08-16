#!/usr/bin/env bash
set -euo pipefail

BOOTSTRAP_URL=https://raw.githubusercontent.com/euteryu/ImageCAS-160826/main/kaggle/bootstrap_smoke.sh
BOOTSTRAP_FILE=/tmp/imagecas_bootstrap_smoke.sh
REPO_DIR=/kaggle/working/ImageCAS-160826

wget -qO "$BOOTSTRAP_FILE" "$BOOTSTRAP_URL"
bash "$BOOTSTRAP_FILE"
bash "$REPO_DIR/kaggle/02_plan_preprocess_smoke.sh"
bash "$REPO_DIR/kaggle/03_train_smoke.sh"

