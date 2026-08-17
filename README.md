# ImageCAS segmentation

Reproducible, auditable preparation of ImageCAS for an nnU-Net v2 coronary-artery baseline.
The first milestone is dataset integrity and visual QC. No model training should start until that gate passes.

For reusable guidance on storage-bounded, unattended Kaggle projects, see the
[Kaggle Machine-Learning Playbook](docs/KAGGLE_ML_PLAYBOOK.md).
For the concrete meaning of ImageCAS spacing, CT normalization, and categorical
mask resampling, see [ImageCAS nnU-Net Preprocessing Explained](docs/IMAGECAS_NNUNET_PREPROCESSING.md).

## Current scope: IMG-CAS-001

The repository currently provides:

- recursive NIfTI discovery without assuming the Kaggle folder layout;
- normalized case IDs, SHA-256 file hashes, duplicate/orphan detection, and deterministic manifests;
- image/mask shape, spacing, orientation, affine, dtype, intensity, foreground, bounding-box, and connected-component audits;
- official split import and exact dataset/split reconciliation;
- axial, coronal, and sagittal CT/reference-boundary montages;
- explicit non-zero exit codes when pairing, geometry, mask, or split integrity fails;
- synthetic unit tests that require no patient data.

The label is deliberately described as the **ImageCAS binary coronary-artery reference mask** until visual QC resolves its operational annotation semantics.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e ".[dev,excel]"
pytest
```

On Kaggle, clone a pinned commit and install it into the notebook environment. Keep the notebook as a thin command runner.

## Run IMG-CAS-001

First, in Kaggle, print the exact attached input paths and candidate files:

```bash
python scripts/00_environment_check.py
```

Copy its JSON output back into the chat. It reports paths only; it does not copy or modify the dataset.

Discover and pair files:

```bash
python scripts/01_discover_dataset.py /kaggle/input/<attached-imagecas-dataset>
```

Audit every paired case:

```bash
python scripts/02_audit_dataset.py artifacts/data_manifest.csv
```

Import and reconcile official Split-1:

```bash
python scripts/04_create_official_split.py \
  artifacts/data_manifest.csv \
  /kaggle/input/<attached-split-dataset>/ImageCAS_dataset_split.xlsx \
  --split 1
```

Create montages for selected cases:

```bash
python scripts/06_generate_qc_report.py artifacts/data_manifest.csv case0001 case0042
```

Generated CSV and JSON outputs go under `artifacts/`. Large or sensitive data products are ignored by Git.

## Build the engineering smoke dataset

`Dataset599_ImageCAS_SMOKE` uses 20 official Split-1 training cases solely to verify the pipeline. It must never appear in scientific results.

```bash
python scripts/00_inspect_imagecas_inputs.py
python scripts/03_build_smoke_dataset.py \
  /kaggle/input/datasets/xiaoweixumedicalai/imagecas/imageCAS_data_split.xlsx
```

This creates 16 smoke-training cases, 4 smoke-validation cases, `dataset.json`, a hash manifest, and a custom split file. It preserves the original NIfTI geometry.

## Gate A

Do not train until all expected cases are accounted for, pairing and physical geometry are proven, mask values are known, the official split is reproduced, QC overlays are reviewed, and audit outliers are investigated.

## Data policy

Never commit CT volumes, masks, nnU-Net preprocessed arrays, predictions, model checkpoints, or patient-derived QC images.
