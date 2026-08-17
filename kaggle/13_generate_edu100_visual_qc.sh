#!/usr/bin/env bash
set -euo pipefail

cd /kaggle/working/ImageCAS-160826
python -m pip install -e .
python kaggle/13_generate_edu100_visual_qc.py
du -sh /kaggle/working/edu100_visual_qc
