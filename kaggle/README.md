# Kaggle notebook commands

This directory contains the code intended for Kaggle notebook execution.

## Copy/paste rule

Do not paste multiline Python implementations into Kaggle cells. Pull the repository, then run a committed script with a one-line cell. This avoids indentation damage during copy/paste and keeps notebook logic version-controlled.

## Current next command: EDU100 held-out test evaluation

Persist the successful Phase 3A training notebook output. In a fresh **T4 GPU**
notebook, attach that output and the official ImageCAS dataset, then run the
repository bootstrap followed by:

```python
!bash /kaggle/working/ImageCAS-160826/kaggle/10_evaluate_edu100_test.sh
```

This verifies a real CUDA kernel, stages only the 20 deterministically selected
official Split-1 test images, and predicts them with the accepted fold-2
`checkpoint_best.pth`. The script refuses to extract the 20 reference masks
until all predictions exist. It then reports overlap (Dice/IoU), physical
surface (1 mm surface Dice, HD95, mean surface distance), and topology (clDice,
component counts, and largest-component fractions) metrics. Submit it with
**Save & Run All**. The final report must be PASS and is an educational held-out
subset result, not the official 250-case ImageCAS benchmark.

## Earlier EDU100 training command

```python
!bash /kaggle/working/ImageCAS-160826/kaggle/08_train_edu100_64.sh
```

This trains fold 2 with 64 training and 16 fixed validation cases for 50 epochs.

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
