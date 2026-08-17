# Kaggle notebook commands

This directory contains the code intended for Kaggle notebook execution.

## Copy/paste rule

Do not paste multiline Python implementations into Kaggle cells. Pull the repository, then run a committed script with a one-line cell. This avoids indentation damage during copy/paste and keeps notebook logic version-controlled.

## Current next command: EDU100 64-case training

In a fresh **T4 GPU** notebook, attach the successful Phase 2 notebook output
and run the repository bootstrap followed by:

```python
!bash /kaggle/working/ImageCAS-160826/kaggle/08_train_edu100_64.sh
```

This creates a writable metadata view over the attached 12 GB read-only
preprocessed dataset, installs the fixed nested 16/32/64 splits, verifies a real
CUDA kernel, and trains fold 2 (64 training, 16 fixed validation cases) for 50
epochs. Submit it with **Save & Run All**; it is expected to take roughly 4–5
hours based on the measured one-epoch smoke run. The final report must be PASS
with two checkpoints and 16 validation predictions. The 16- and 32-case
learning-curve models are intentionally skipped; this stage trains the single
largest educational model directly.

## Earlier data-preparation commands

```python
!bash /kaggle/working/ImageCAS-160826/kaggle/04_build_edu100_raw.sh
```

This CPU-only command builds `Dataset598_ImageCAS_EDU100` with 64 training and
16 validation cases. It records 20 official test IDs in the selection manifest
but does not extract their images or labels.

After the raw dataset has been saved as a persistent Kaggle dataset, start a
fresh CPU session, attach that dataset read-only, clone/pull this repository,
and run:

```python
!bash /kaggle/working/ImageCAS-160826/kaggle/05_preprocess_edu100.sh
```

Phase 2 first verifies all 80 development cases. It then fingerprints and plans
using only the 64 training cases, freezes that plan, and preprocesses the 64
training plus 16 validation cases. Both views contain zero test cases. The final
report must show 64 fingerprint cases and 80 preprocessed cases.

Do not run raw construction and preprocessing in the same session: their
estimated combined size is too close to the 20 GB writable-disk limit.

## Standard update command

Run this only when Codex says a new script or code change was pushed:

```python
!git pull
```

`git pull` is not required between cells when the relevant script was already present in the current clone.
