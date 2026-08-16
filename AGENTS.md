# Codex project instructions

Read `LOGBOOK.md` before changing this repository. Treat its **Current status**, **Fixed project decisions**, and latest **Run notes** as the durable project handover.

## Purpose

Build a reproducible and auditable ImageCAS-to-nnU-Net v2 coronary segmentation baseline. Current work is IMG-CAS-001 dataset discovery and audit—not training.

## Non-negotiable rules

- Keep ImageCAS patient data on Kaggle. Never request or create a local laptop copy.
- Never commit NIfTI data, extracted cases, patient-derived QC images, nnU-Net arrays, predictions, or checkpoints.
- GitHub is the source of truth for code; Kaggle notebooks are thin execution environments.
- Keep the Kaggle GPU disabled until CPU-only preparation is complete and training is ready.
- Use official workbook sheet `v2-latest`; archive case IDs are 1–1000.
- Preserve image/mask physical geometry. Do not silently resize or repair mismatches.
- Isolate official Split-1 test labels from nnU-Net fingerprinting/preprocessing in the later builder.
- Refer to labels as the “ImageCAS binary coronary-artery reference mask” until visual QC establishes stronger semantics.
- Prefer resumable, case-wise archive processing because Kaggle working storage is 20 GB and each shard is about 17 GB.
- Do not attempt a conventional full Dataset501 extraction/preprocessing in one Kaggle session. Smoke measurements extrapolate to about 67.5 GB raw plus 112.5 GB preprocessed for 750 development cases, far beyond the 20 GB writable disk. Use persistent shards/symlinks or larger-storage compute.
- The project owner waived the full 1,000-case audit after cases 1–23 passed. Never describe Gate A or the full dataset audit as passed; describe it as an explicit accepted-risk waiver.
- Update `LOGBOOK.md` after each meaningful Kaggle result, unexpected issue, strategy change, or completed milestone.
- Put Kaggle-executed implementation code in numbered scripts under `kaggle/`. Give the user one-line notebook commands instead of multiline Python cells because pasted indentation is unreliable in their workflow.

## Current task

Design and validate a Kaggle-feasible raw/preprocessed data staging strategy. The attached archives total 83 GB while `/kaggle/working` has 20 GB, so a conventional full extraction is impossible.

## Verification

Run `python -m pytest` after code changes. Use synthetic data for tests; do not add patient fixtures.
