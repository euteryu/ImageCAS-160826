# ImageCAS EDU100 Project Summary

## Are we finished?

Yes. The EDU100 educational experiment is complete. The data preparation,
training, held-out evaluation, visual review, documentation, and reproducibility
checks all finished successfully.

No more Kaggle runs are required for this experiment.

## What did we do?

We trained a 3D nnU-Net model to segment the ImageCAS binary coronary-artery
reference mask from CCTA scans.

The fixed experiment used:

- 64 cases for training;
- 16 cases for validation and model selection;
- 20 untouched cases for final testing;
- 50 training epochs;
- one Kaggle Tesla T4 GPU.

The test cases were kept out of preprocessing fitting, training, and model
selection. Their reference masks were opened only after predictions existed for
all 20 cases.

## How well did training go?

Training completed successfully and produced valid checkpoints and predictions.

The main results were:

| Result | Score |
|---|---:|
| Mean validation Dice | 0.753 |
| Mean held-out test Dice | 0.739 |
| Mean held-out test clDice | 0.814 |
| Mean held-out 1 mm surface Dice | 0.840 |

A Dice score of 1.0 would mean perfect overlap. The test Dice of 0.739 shows
that the model learned a meaningful segmentation rather than failing or making
random predictions.

Validation and test Dice were reasonably close. This suggests the model's
validation performance transferred to the untouched test subset without a
large obvious collapse.

## What did the model learn?

The model generally learned:

- where the coronary reference masks are located;
- the main shape and course of the annotated vessels;
- useful vessel continuity, reflected by the clDice score of 0.814;
- boundaries that were often close to the reference, reflected by the 1 mm
  surface Dice of 0.840.

Independent visual review confirmed that the main predicted contours often
followed the reference contours. There was no obvious image/overlay alignment
failure.

## What were the weaknesses?

The main problem was fragmentation. Predictions often contained too many small,
disconnected pieces.

Other visible errors included:

- isolated false-positive vessel fragments;
- distant false positives that increased surface-distance errors;
- missed reference segments;
- small local boundary differences.

The clearest difficult case was `case0768`. It had a Dice score of 0.620 and 45
predicted connected components compared with 2 reference components. Visual
review confirmed scattered false positives, missed regions, and fragmentation.

## What are the limitations?

This was a small educational baseline, not the official ImageCAS benchmark.

- Only 64 cases were used for training.
- Only 20 of the official 250 Split-1 test cases were evaluated.
- The full 1,000-case dataset audit was explicitly waived after cases 1–23
  passed. This was an accepted risk, not a passed full-audit gate.
- The visual-QC montages showed three selected 2D slices per case, so they could
  not prove complete 3D vessel continuity.

The result must therefore be described as a held-out EDU100 subset result, not
as overall ImageCAS benchmark performance.

## What did we learn about the workflow?

The complete ImageCAS archive and conventional full nnU-Net preprocessing do
not fit into Kaggle's 20 GB writable disk. A staged workflow solved this:

1. Build and save the raw development dataset.
2. Attach it read-only and create the preprocessed dataset.
3. Attach preprocessing read-only and train the model.
4. Run held-out inference in a separate notebook.
5. Generate visual QC in a final CPU-only notebook.

This kept each stage reproducible and prevented Kaggle session resets from
destroying completed work.

## What should happen in the future?

Nothing else is required for EDU100. That experiment is closed.

If a new experiment is started:

1. Define its objective and evaluation protocol before training.
2. Use more training cases if storage and compute allow.
3. Develop methods to reduce disconnected false positives using training and
   validation data only.
4. Do not tune against the 20 EDU100 held-out cases.
5. Reserve a new untouched test set for the final evaluation.
6. Continue reporting overlap, surface, and topology metrics rather than Dice
   alone.

## Final conclusion

The project successfully demonstrated an auditable ImageCAS-to-nnU-Net v2
pipeline on Kaggle. The model learned meaningful coronary-mask segmentation,
but topology and fragmentation remain the main opportunities for improvement.

For the full technical record, see
[`docs/EDU100_BASELINE_REPORT.md`](docs/EDU100_BASELINE_REPORT.md) and
[`LOGBOOK.md`](LOGBOOK.md).
