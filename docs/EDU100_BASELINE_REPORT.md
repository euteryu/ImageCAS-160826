# ImageCAS EDU100 Educational Baseline Report

## Status

**Completed and accepted on 2026-08-17.**

This report describes a fixed 64-training/16-validation/20-held-out-test
educational experiment using the ImageCAS binary coronary-artery reference
mask. It is not the official ImageCAS benchmark, does not evaluate the full
250-case official Split-1 test partition, and must not be presented as a
full-dataset result.

## Objective

The experiment tested whether a small, storage-bounded nnU-Net v2 workflow
could reproducibly learn a meaningful coronary segmentation model on Kaggle
while maintaining a strict separation between development data and held-out
test labels.

The experiment was designed as an educational baseline, not as a claim of
state-of-the-art performance.

## Dataset and fixed split

The official workbook sheet `v2-latest` and official Split-1 partition
assignments were authoritative. Cases were selected deterministically by taking
the lowest normalized case IDs within each official partition:

| Role | Cases | Use |
|---|---:|---|
| Training | 64 | Fingerprinting, planning, preprocessing fitting, and model fitting |
| Validation | 16 | Fixed model selection and monitoring |
| Held-out test | 20 | Final inference and evaluation only |

No case moved between official partitions. The 20 selected test cases were
`case0751` through `case0770`.

The original nested 16-, 32-, and 64-case learning-curve splits remained in
the metadata for auditability, but only the 64-case model was trained. This was
an explicit scope decision.

## Data-integrity evidence and limitation

All five multipart archives opened successfully and their listings contained
1,000 apparent image/reference pairs. Official Split-1 independently validated
as 700 training, 50 validation, and 250 test cases. Cases 1–23 passed the
case-wise audit with zero warnings.

The project owner explicitly waived the remaining full 1,000-case audit. Gate A
was therefore waived with accepted risk; it did not pass. This limitation
applies to the project as a whole even though all 100 selected EDU100 cases
successfully completed their relevant pipeline stages.

## Leakage controls

The experiment used the following executable controls:

1. Raw construction extracted only the 64 training and 16 validation cases.
2. Fingerprinting, target-spacing selection, and normalization-statistic fitting
   used only the 64 training cases.
3. The fitted plan was frozen before preprocessing the 16 validation cases.
4. No selected test image or reference participated in fingerprinting,
   planning, development preprocessing, training, checkpoint selection, or
   model selection.
5. Held-out inference staged the 20 test images first.
6. The evaluation stage refused to extract references until predictions for
   all 20 expected test cases existed.
7. Evaluation used the already selected `checkpoint_best.pth` without
   retraining, replanning, or parameter tuning.

## Preprocessing and model

| Item | Value |
|---|---|
| Dataset | `Dataset598_ImageCAS_EDU100` |
| Framework | nnU-Net v2.8.1 |
| Configuration | `3d_fullres` |
| Trainer | `nnUNetTrainer_50epochs` |
| Fold | 2 |
| Epochs | 50 |
| Target spacing | 0.5 × 0.34765625 × 0.34765625 mm |
| Patch size | 96 × 160 × 160 voxels |
| Batch size | 2 |
| Selected checkpoint | `checkpoint_best.pth` |
| Checkpoint SHA-256 | `780eba53bedcdbd4797801eee88a3924d67785236f62ea1514b447e0ac7ddbb9` |

Image/reference physical geometry was preserved. Geometry mismatches were not
silently resized or repaired.

## Validation result

The fixed 16-case validation evaluation completed after training:

| Metric | Mean |
|---|---:|
| Dice | 0.752978 |
| IoU | 0.606575 |

This result was available for model selection. It is not a held-out test score.

## Held-out test result

All 20 selected test cases were predicted and evaluated. Every automated gate
passed: expected official test IDs, prediction and reference counts, prediction
before reference extraction, checkpoint identity, binary masks, physical
geometry, and overlap, surface, and topology metric availability.

| Metric | Mean | Median |
|---|---:|---:|
| Dice | 0.739332 | 0.744920 |
| IoU | 0.589025 | 0.593547 |
| Surface Dice at 1 mm | 0.840082 | 0.852509 |
| HD95 (mm) | 21.509963 | 19.156104 |
| Mean surface distance (mm) | 3.115381 | 2.645858 |
| clDice | 0.814210 | 0.820652 |
| Absolute component-count error | 16.5 | 14.5 |
| Predicted largest-component fraction | 0.563507 | 0.527164 |
| Reference largest-component fraction | 0.679838 | 0.637081 |

Per-case Dice ranged from 0.619977 for `case0768` to 0.810980 for
`case0764`.

### Per-case Dice

| Case | Dice | Case | Dice |
|---|---:|---|---:|
| `case0751` | 0.684806 | `case0761` | 0.749754 |
| `case0752` | 0.735547 | `case0762` | 0.684367 |
| `case0753` | 0.774963 | `case0763` | 0.740085 |
| `case0754` | 0.792116 | `case0764` | 0.810980 |
| `case0755` | 0.707285 | `case0765` | 0.683059 |
| `case0756` | 0.750978 | `case0766` | 0.761050 |
| `case0757` | 0.783641 | `case0767` | 0.670647 |
| `case0758` | 0.806478 | `case0768` | 0.619977 |
| `case0759` | 0.729190 | `case0769` | 0.799753 |
| `case0760` | 0.714745 | `case0770` | 0.787218 |

## Visual QC

The deterministic screening set merged metric extremes with two seeded-random
cases:

| Case | Selection reason | Independent review |
|---|---|---|
| `case0752` | Seeded random | Broad principal-contour agreement; small missed reference segments and isolated prediction fragments |
| `case0764` | Highest-Dice control | Strongest visible agreement; residual peripheral fragments and local offsets |
| `case0768` | Worst Dice, HD95, clDice, and component error | Clearly weakest; remote false positives, missed regions, and marked fragmentation |
| `case0770` | Seeded random | Good dominant-contour agreement with minor local errors and small peripheral fragments |

No gross CT/overlay registration failure was visible. The qualitative evidence
supports the quantitative conclusion: the model learned meaningful localization
and shape, but its predictions remain over-fragmented and contain scattered
distant false positives. In `case0768`, the prediction contained 45 connected
components versus 2 in the reference.

The montages show one selected slice in each orthogonal plane. They are
screening views and cannot fully characterize 3D continuity or every distal
branch. They also do not establish stronger annotation semantics than the term
“ImageCAS binary coronary-artery reference mask.”

Patient-derived montage files are excluded from Git. Authorized local review
copies, when present, reside under the ignored path
`artifacts/qc/montages/edu100_phase3c/`.

## Storage and execution evidence

The workflow respected Kaggle's 20 GB writable-storage constraint by separating
raw construction, preprocessing, training, held-out inference, and QC into
persistent notebook stages.

Key measurements were:

- raw 80-case development dataset: 6.9 GB;
- preprocessed 80-case dataset: 12 GB;
- training results: 473 MB;
- held-out test stage: 1.7 GB;
- visual-QC output: 3.4 MB.

The 50-epoch training and held-out inference used one Tesla T4. Raw
construction, preprocessing, and visual-QC generation were CPU-only.

## Reproducibility trail

The version-controlled Kaggle entry points were:

```text
kaggle/04_build_edu100_raw.sh
kaggle/05_preprocess_edu100.sh
kaggle/08_train_edu100_64.sh
kaggle/10_evaluate_edu100_test.sh
kaggle/13_generate_edu100_visual_qc.sh
```

Durable Kaggle evidence includes:

- notebook 1.1: raw construction;
- notebook 1.2: strict preprocessing;
- notebook 1.3: 64-case, 50-epoch training;
- notebook 1.4, saved Version 2: held-out inference and evaluation;
- notebook 1.5: visual-QC generation.

The repository's `LOGBOOK.md` is the detailed chronological audit trail.

## Conclusion

The EDU100 experiment demonstrated a reproducible end-to-end ImageCAS-to-nnU-Net
v2 educational workflow under Kaggle's storage limits. The held-out mean Dice
of 0.739332, mean clDice of 0.814210, and mean 1 mm surface Dice of 0.840082
show meaningful learning on this fixed small-data experiment. The high mean
component-count error and visual false-positive fragments show that topology
and continuity remain important weaknesses.

This milestone is closed. The held-out cases must not be reused to tune this
model. Any follow-up experiment requires a newly defined objective and protocol
before additional model development begins.
