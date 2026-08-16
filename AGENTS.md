# Codex project instructions

Read `LOGBOOK.md` before changing this repository. Treat its **Current status**, **Fixed project decisions**, and **Current next action** as the durable project handover.

## Purpose

Build a reproducible and auditable ImageCAS-to-nnU-Net v2 coronary segmentation baseline. Current work is IMG-CAS-001 dataset discovery and audit—not training.

## Non-negotiable rules

- Keep ImageCAS patient data on Kaggle. Never request or create a local laptop copy.
- Never commit NIfTI data, extracted cases, patient-derived QC images, nnU-Net arrays, predictions, or checkpoints.
- GitHub is the source of truth for code; Kaggle notebooks are thin execution environments.
- Keep the Kaggle GPU disabled until CPU-only data and pipeline gates require training.
- Use official workbook sheet `v2-latest`; archive case IDs are 1–1000.
- Preserve image/mask physical geometry. Do not silently resize or repair mismatches.
- Isolate official Split-1 test labels from nnU-Net fingerprinting/preprocessing in the later builder.
- Refer to labels as the “ImageCAS binary coronary-artery reference mask” until visual QC establishes stronger semantics.
- Prefer resumable, case-wise archive processing because Kaggle working storage is 20 GB and each shard is about 17 GB.
- Update `LOGBOOK.md` after each meaningful Kaggle result, unexpected issue, strategy change, or completed milestone.

## Current command to validate

```bash
python scripts/02_audit_archives.py --limit 3
```

Do not start a full 1,000-case audit until the three-case result has been reviewed.

## Verification

Run `python -m pytest` after code changes. Use synthetic data for tests; do not add patient fixtures.
