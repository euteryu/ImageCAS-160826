# ImageCAS Project Logbook

This is the human-readable record of what we did, what Kaggle showed us, why the plan changed, and what should happen next. Update it after every meaningful Kaggle run or engineering decision.

## Current status

- Phase: IMG-CAS-001 — dataset discovery and audit
- Training status: **EDU100 64-case training and 20-case held-out evaluation passed; official baseline not started**
- GPU required now: **no — Phase 3B evaluation is complete**
- Current checkpoint: Phase 3C automated and independent visual QC passed; EDU100 baseline is complete
- Repository: <https://github.com/euteryu/ImageCAS-160826>
- Kaggle dataset: <https://www.kaggle.com/datasets/xiaoweixumedicalai/imagecas>

## Fixed project decisions

1. Patient data stays on Kaggle. We do not download ImageCAS to the laptop or commit it to Git.
2. Kaggle is the execution environment; GitHub is the source of truth for code.
3. We audit before training.
4. We use the official ImageCAS Split-1 and later isolate its 250 test cases from nnU-Net fingerprinting and preprocessing.
5. The target is called the **ImageCAS binary coronary-artery reference mask** until visual QC establishes its precise annotation semantics.
6. The eventual baseline must include overlap, surface, and topology evaluation—not Dice alone.
7. The project owner explicitly waived the complete 1,000-case audit on 2026-08-16. This is an accepted risk, not evidence that the dataset passed full validation.
8. Kaggle notebook instructions should be one-line commands that run version-controlled scripts under `kaggle/`; avoid asking the user to paste multiline, indentation-sensitive Python.

## Chronological record

### 2026-08-16 — Handover review

**Input**

- `CCTA_Handoff_CodexCli.docx`, a ChatGPT-planned engineering and research handover.

**Conclusion**

The central plan was accepted:

- start with IMG-CAS-001 rather than model training;
- verify image/mask pairing and physical geometry;
- reproduce the official benchmark split;
- prevent held-out test labels from influencing nnU-Net planning;
- evaluate vessel surface and topology in addition to voxel overlap.

**Initial misunderstanding corrected**

The workspace contained only the Word document, not a dataset or an existing codebase. A local Python repository was therefore scaffolded. ImageCAS itself does not need to be downloaded locally because the intended execution environment is Kaggle.

### 2026-08-16 — Local audit package created

Implemented locally:

- Python package and configuration;
- recursive NIfTI discovery;
- case-ID normalization;
- image/mask duplicate and orphan detection;
- SHA-256 manifests;
- shape, spacing, affine, orientation, intensity, foreground-volume, bounding-box, and connected-component auditing;
- official split import and reconciliation foundations;
- axial, coronal, and sagittal QC overlays;
- outlier reporting;
- synthetic NIfTI unit tests.

Verification result: **8 tests passed**. Ruff was unavailable locally, but Python compilation and tests passed.

### 2026-08-16 — GitHub workflow established

The user created the public repository:

`https://github.com/euteryu/ImageCAS-160826`

The local repository was connected and pushed. This corrected the earlier incomplete implication that Kaggle could directly run a local script. Kaggle must first clone the GitHub repository.

Initial Kaggle bootstrap cell:

```python
!git clone https://github.com/euteryu/ImageCAS-160826.git
%cd /kaggle/working/ImageCAS-160826
!pip install -e .
!python scripts/00_environment_check.py --output /kaggle/working/environment_report.json
```

### 2026-08-16 — Kaggle input discovery

**Kaggle configuration**

- Notebook type: Python
- Attached input: official ImageCAS Kaggle dataset
- Accelerator: None
- Internet: On for GitHub cloning/pulling

**Observed paths**

- Dataset root: `/kaggle/input/datasets/xiaoweixumedicalai/imagecas`
- Official workbook: `/kaggle/input/datasets/xiaoweixumedicalai/imagecas/imageCAS_data_split.xlsx`
- Additional split CSV: `Coronary_Segmentation_deep_learning/.../data_list/split_1000.csv`

**Unexpected finding**

The attached dataset exposes no NIfTI files directly. It contains five multipart archives, each represented by one `.change2zip` file and four `.zNN` parts. The environment inspector initially needed an update because it only reported NIfTI and workbook files.

The inspector was adjusted to report multipart archives, then pushed to GitHub.

### 2026-08-16 — Archive and workbook inspection

A safe inspector created symbolic links in `/kaggle/working`:

- each `.change2zip` head was linked as `.zip`;
- each `.zNN` member was linked without copying data;
- total link storage was only 1,580 bytes;
- `7z` successfully opened all five multipart archives.

**Archive findings**

| Archive | NIfTI entries | Interpretation |
|---|---:|---|
| `1-200.zip` | 400 | 200 images + 200 labels |
| `201-400.zip` | 400 | 200 images + 200 labels |
| `401-600.zip` | 400 | 200 images + 200 labels |
| `601-800.zip` | 400 | 200 images + 200 labels |
| `801-1000.zip` | 400 | 200 images + 200 labels |

Confirmed naming convention:

```text
<shard>/<case>.img.nii.gz
<shard>/<case>.label.nii.gz
```

This gives exactly 1,000 apparent image/mask pairs with case numbers 1–1000.

**Workbook findings**

The workbook has two sheets:

- `v1`: old patient-style identifiers such as `10016975`;
- `v2-latest`: archive-compatible identifiers `1` through `1000`.

Decision: use **`v2-latest`**. Its columns encode Split-1 through Split-4, and its first data-like row contains the effective headings.

### 2026-08-16 — Storage constraint and strategy change

Kaggle reported:

```text
/kaggle/working: 20 GB available
all multipart archives: 83 GB total
each 200-case archive group: approximately 17 GB
```

**Why the first extraction idea was rejected**

Extracting a complete 17 GB shard into a 20 GB working disk leaves too little safety margin. The extracted `.nii.gz` files, temporary files, audit outputs, and runtime overhead could exhaust storage.

**Revised approach**

Audit case by case:

1. Read the archive directory.
2. Extract one `<case>.img.nii.gz` and `<case>.label.nii.gz` pair.
3. Calculate geometry, intensity, foreground, component, and hash fields.
4. Append one durable CSV row.
5. Delete that case's temporary directory.
6. Continue from the CSV after interruption.

This keeps peak working storage to approximately one case rather than one 200-case shard.

The resumable implementation is `scripts/02_audit_archives.py`.

## Current next action

Close the EDU100 educational-baseline milestone without tuning from the held-out
results. Preserve notebook versions 1.3, 1.4 version 2, and 1.5 as the durable
Kaggle evidence. Before any new scientific experiment, define a new protocol
and objective rather than iterating on these held-out cases.

## Known open work

- Keep enforcing the rule that all selected official test cases remain absent from fingerprinting, planning, training preprocessing, training, and model selection.
- Define and preregister the objective and data split before starting any follow-up experiment.
- Keep the stronger annotation-semantics question open; the completed screening montages do not resolve it fully.
- Treat Gate A as an accepted-risk waiver, never as passed; reinstate the resumable audit if later failures suggest bad input data.

## Run notes

### 2026-08-17 — EDU100 Phase 3C independent visual review completed

Codex independently inspected the four original-resolution Phase 3C montages.
Red reference and cyan prediction contours were compared in the selected
sagittal, coronal, and axial planes. No gross CT/overlay displacement or other
obvious physical-registration failure was visible in any reviewed case.

Case-level observations:

- `case0752`: broadly concordant principal contours, with small red-only missed
  segments and isolated cyan-only fragments. The visible discrepancy is
  moderate and consistent with Dice 0.736 and HD95 22.1 mm.
- `case0764`: strongest overall visible agreement, particularly along the main
  elongated contours. Some cyan-only peripheral fragments and local boundary
  offsets remain. This is a credible highest-Dice control rather than a perfect
  segmentation.
- `case0768`: visibly weakest case. Although portions of the principal contours
  overlap, multiple cyan-only remote fragments and red-only missed regions are
  visible across planes. This qualitatively supports the worst Dice, HD95,
  clDice, and component-count results and the 45 predicted versus 2 reference
  components.
- `case0770`: good agreement along the dominant visible contours, with several
  small peripheral cyan-only fragments and minor local under/over-segmentation.
  Its qualitative appearance is consistent with Dice 0.787 and low HD95.

Overall interpretation: the model learned meaningful coronary-reference-mask
localization and shape, but predictions remain over-fragmented and contain
scattered distant false positives. The evidence does not establish detailed
annotation semantics beyond the existing term “ImageCAS binary
coronary-artery reference mask.” The three-plane, one-slice-per-plane montages
are useful screening views but cannot fully characterize 3D continuity or all
distal branches.

Decision: accept Phase 3C and close the fixed 64-train/16-validation/20-test
EDU100 educational baseline. Do not alter the accepted model or checkpoint
based on this held-out review. Only textual observations are committed.

At the project owner's explicit request and authorization, local review copies
of the four montage PNGs were placed at
`artifacts/qc/montages/edu100_phase3c/`. This directory is covered by the
repository's `artifacts/qc/montages/` ignore rule; `git check-ignore` confirmed
all four files are excluded. They must never be staged, committed, or pushed.

### 2026-08-17 — EDU100 Phase 3C automated visual-QC generation passed

Notebook `ImageCAS-180626-v2-EDU100-1.5-visual-qc` completed the CPU-only
visual-QC stage with `status: PASS`. It generated four montages in 3.4 MB:

```text
case0752  seeded-random review case
case0764  highest-Dice control (Dice 0.810980, HD95 8.848 mm)
case0768  lowest Dice, highest HD95, lowest clDice, and highest component error
case0770  seeded-random review case
```

The multiple adverse criteria correctly collapsed onto `case0768`: Dice
0.619977, HD95 58.431 mm, clDice 0.683003, and absolute component-count error
43. Its prediction had 45 connected components versus 2 in the reference.
The source checkpoint SHA-256 remained
`780eba53bedcdbd4797801eee88a3924d67785236f62ea1514b447e0ac7ddbb9`.

Decision: accept automated montage generation. The remaining Phase 3C gate is
human review of the four PNGs directly in Kaggle. Do not download or upload the
patient-derived montages; return only non-identifying qualitative observations
for the logbook. This review is descriptive and must not drive model or
checkpoint selection.

### 2026-08-17 — EDU100 Phase 3C visual-QC notebook launched

The project owner created and started the CPU-only Save & Run All notebook
`ImageCAS-180626-v2-EDU100-1.5-visual-qc` after attaching notebook 1.4 saved
version 2. The Phase 3C implementation had already been pushed to GitHub main
as commit `69dca36`. No official ImageCAS dataset attachment or GPU is required
for this stage. Await the final `EDU100_VISUAL_QC_REPORT` and generated montage
names; do not infer a pass merely from successful notebook startup.

### 2026-08-17 — EDU100 Phase 3C visual-QC stage implemented

A separate CPU-only visual-QC stage was added for the persisted notebook 1.4
version 2 output. It requires no official ImageCAS archive attachment and does
not rerun inference or metrics. It discovers exactly one complete
`edu100_test` attachment and rejects any source report other than the accepted
20-case `PASS` result.

The deterministic selection includes the lowest Dice, highest HD95, lowest
clDice, highest absolute component-count error, highest-Dice control, and two
seeded-random held-out cases. Duplicate metric extremes are merged. Each
montage displays the maximum combined reference/prediction foreground slice in
the sagittal, coronal, and axial planes, with the ImageCAS binary
coronary-artery reference boundary in red and the prediction boundary in cyan.
The report preserves selection reasons, source checkpoint SHA-256, and per-case
metrics.

Patient-derived PNGs are written only to
`/kaggle/working/edu100_visual_qc/montages`; none are created locally or added
to Git. The one-line entry point is
`kaggle/13_generate_edu100_visual_qc.sh`. This is review-only: the held-out
images must not be used to tune the accepted model or checkpoint.

Local verification: **28 synthetic tests passed**; Python compilation, shell
syntax, and Git whitespace checks passed. Ruff was unavailable locally.
Decision: push the implementation, then run it in a new Save & Run All notebook
with accelerator None and only notebook 1.4 version 2 attached.

### 2026-08-17 — EDU100 Phase 3B held-out evaluation passed

The isolated T4 evaluation completed as notebook 1.4, saved version 2, for all
20 untouched EDU100 held-out test
cases (`case0751`–`case0770`) using fold 2, configuration `3d_fullres`, trainer
`nnUNetTrainer_50epochs`, and `checkpoint_best.pth`. The checkpoint SHA-256 was
`780eba53bedcdbd4797801eee88a3924d67785236f62ea1514b447e0ac7ddbb9`.

Observed aggregate metrics:

```text
Dice:                         mean 0.7393319414, median 0.7449195543
IoU:                          mean 0.5890245575, median 0.5935469954
surface Dice at 1 mm:         mean 0.8400824923, median 0.8525089656
HD95:                         mean 21.5099630955 mm, median 19.1561040672 mm
mean surface distance:        mean 3.1153813912 mm, median 2.6458581492 mm
clDice:                       mean 0.8142099568, median 0.8206520986
absolute component error:     mean 16.5, median 14.5
predicted largest component:  mean 0.5635069672, median 0.5271636046
reference largest component:  mean 0.6798381297, median 0.6370807542
```

Per-case Dice ranged from 0.619977 (`case0768`) to 0.810980 (`case0764`). All
acceptance checks passed: correct official test cases and counts, predictions
created before references were opened, binary masks, physical geometry,
checkpoint identity, and overlap, surface, and topology metrics. The final
report status was `PASS`.

After completion, `/kaggle/working/edu100_test` occupied 1.7 GB,
`/kaggle/working/nnUNet_results/Dataset598_ImageCAS_EDU100` occupied 4 KB, and
the 20 GB writable filesystem had 18 GB available (9% used).

The successful Save Version run means its output is already persisted as a
read-only Kaggle notebook-version output; no repeat run or additional save is
needed.

Decision: accept Phase 3B as the final held-out result for the educational
64-train/16-validation/20-test experiment. This is not the official 250-case
ImageCAS benchmark and must not be described as one. Proceed to a separate
visual-QC stage; do not tune the model or checkpoint from these test results.

### 2026-08-17 — Phase 3B first launch stopped: official dataset not attached

The fresh T4 evaluation notebook had the saved Phase 3A/1.3 model output
attached, but not the official `xiaoweixumedicalai/imagecas` Kaggle dataset.
Installation, nnU-Net/PyTorch checks, the Tesla T4 check, and an executable CUDA
kernel test passed. Input discovery then stopped with:

```text
RuntimeError: Expected one imageCAS_data_split.xlsx, found 0: []
```

This was an attachment/configuration issue, not a model or evaluation failure.
No held-out inference ran and no test reference masks were extracted. Decision:
keep the 1.3 output attached, additionally attach the official ImageCAS dataset,
restart the session, and rerun `kaggle/10_evaluate_edu100_test.sh`.

### 2026-08-17 — Isolated EDU100 Phase 3B evaluation implemented

The held-out stage is implemented as
`kaggle/10_evaluate_edu100_test.sh` for one fresh T4 Save & Run All notebook.
Its only required attachments are the official ImageCAS dataset and the saved
Phase 3A output containing the accepted fold-2 model. It symlinks the read-only
model result rather than copying it and selects the same deterministic 20 cases
from the official workbook `v2-latest` Split-1 test partition.

The leakage boundary is executable rather than advisory:

1. Extract only the 20 test images and record their source entries and hashes.
2. Run `nnUNetv2_predict` with fold 2 and the already selected
   `checkpoint_best.pth`; nnU-Net uses the frozen training-derived plan bundled
   with the trained model.
3. Refuse to extract any test reference unless predictions for all 20 expected
   case IDs already exist.
4. Extract the 20 ImageCAS binary coronary-artery reference masks and calculate
   final metrics without any retraining, replanning, checkpoint selection, or
   parameter tuning.

The final report includes Dice, IoU, 1 mm surface Dice, HD95, mean symmetric
surface distance, clDice, 26-connected component counts/errors, and largest
component fractions. It verifies binary masks and exact prediction/reference
shape and affine agreement. It also records the selected checkpoint SHA-256,
per-case CSV metrics, and an explicit statement that this is a held-out EDU100
subset result rather than the official 250-case ImageCAS benchmark.

Local verification: **25 synthetic tests passed**; Python compilation, shell
syntax, and Git whitespace checks passed. Ruff was unavailable locally. No
patient data, predictions, references, or patient-derived images were created
locally.

Decision: persist the accepted Phase 3A output, push this implementation, and
run Phase 3B with Save & Run All on one T4. Do not inspect test predictions or
references between inference and the scripted final evaluation.

### 2026-08-17 — EDU100 Phase 3A 64-case training accepted

The one-T4 Phase 3A notebook completed fold 2 using
`nnUNetTrainer_50epochs` and the `3d_fullres` configuration. The existing split
file contained the three auditable nested splits; fold 2 correctly selected 64
training cases and the fixed 16 validation cases. Training completed all 50
epochs, with the final reported epoch taking 220.23 seconds, and nnU-Net then
generated predictions for all 16 validation cases (`case0701`–`case0716`).

Observed acceptance report:

```text
status: PASS
training cases: 64
validation cases: 16
validation predictions: 16
mean validation Dice: 0.7529778036966221
mean validation IoU: 0.6065750250751691
checkpoint_best: 235.01 MB
checkpoint_final: 235.01 MB
results directory: 473 MB
/kaggle/working usage after completion: 474 MB of 20 GB (3%)
```

All five automated checks passed: training-case count, validation-case count,
validation predictions, validation summary, and both required checkpoints.
Validation inference ran from 16:49:42 to 17:34:28, approximately 44 minutes
46 seconds. The validation Dice is a model-selection result for the fixed
EDU100 validation subset, not a held-out test result or an official ImageCAS
benchmark score.

Decision: accept Phase 3A and persist its notebook output. Do not train folds 0
or 1. Next, implement a separate held-out stage for the untouched 20 selected
official Split-1 test cases, reusing the frozen training-derived plan and the
accepted fold-2 checkpoint. Test labels may be opened only for final metric
calculation and must not influence preprocessing fitting, checkpoint choice, or
any other model-selection decision.

### 2026-08-17 — Learning curve simplified to one 64-case model

The project owner chose to skip the separate 16- and 32-case learning-curve
models and train directly on all 64 training cases. This is a scope decision,
not a Kaggle memory or disk workaround. The fixed 16-case validation set remains
unchanged, and the 20 selected test cases remain isolated. Phase 3A now runs
fold 2 with `nnUNetTrainer_50epochs`; the nested split metadata is retained for
auditability, but folds 0 and 1 will not be trained.

### 2026-08-17 — Superseded initial Phase 3A 16-case design

The initially proposed learning-curve training job was packaged as an unattended one-T4
stage. It validates and symlinks the persisted 12 GB Phase 2 output without
copying it, installs the fixed nested splits as nnU-Net folds, rechecks test
isolation and all 80 case payloads, executes a real CUDA kernel, and trains fold
0 with 16 training and the fixed 16 validation cases using
`nnUNetTrainer_50epochs`. Final acceptance requires non-empty final and best
checkpoints, 16 validation predictions, and a validation summary.

This design was superseded before execution by the decision above to train only
the 64-case model. The measured smoke epoch was about five minutes, so a 50-epoch stage is expected to
take roughly 4–5 hours plus setup and final validation. It must use Save & Run
All on one T4. Folds 0 and 1 are no longer planned runs.

### 2026-08-17 — EDU100 Phase 2 preprocessing accepted

The corrected report was run against the persisted 12 GB Phase 2 notebook
output `ImageCAS-180626-v2-EDU100-1.2-preprocess` and passed all acceptance
checks:

```text
training fingerprint cases: 64
development preprocessed cases: 80
test cases in training/development views: 0
configuration: 3d_fullres
target spacing: 0.5 × 0.34765625 × 0.34765625 mm
patch size: 96 × 160 × 160
batch size: 2
status: PASS
```

The installed nnU-Net 2.8.1 output used Blosc2 `.b2nd` arrays; the reporting
code now supports that current format as well as `.npz` and `.npy`. Decision:
accept Phase 2, retain its saved notebook output as the read-only input to
Phase 3, and proceed to the one-T4 learning-curve training design.

### 2026-08-17 — EDU100 Phase 2 preprocessing completed; reporter format bug found

The strict Phase 2 CPU notebook successfully fitted the fingerprint and plans
from 64 training cases, restored the 80-case development view, and completed
`3d_fullres` preprocessing for all 80 cases in 47 minutes 22 seconds. The
training and development view reports both contained zero test cases. The
training-derived plan used target spacing `0.5 × 0.34765625 × 0.34765625` mm,
patch size `96 × 160 × 160`, and batch size 2.

The final custom report nevertheless printed `development_preprocessed_case_count:
0` and `status: FAIL`. This was a reporting defect, not an nnU-Net preprocessing
failure: the reporter counted only legacy `.npz` payloads, while the installed
nnU-Net 2.8.1 workflow stored each data and segmentation array in Blosc2
`.b2nd` files. Kaggle preserved the complete output at 12 GB. The reporter now
recognizes `.npz`, `.npy`, and `.b2nd` data payloads, ignores companion
`_seg` arrays, and deduplicates a case if multiple representations exist.

Decision: do not repeat the 47-minute preprocessing step if the Kaggle working
session still contains the completed output. Pull this fix and rerun only the
reporter; accept Phase 2 only when the corrected report shows 80 preprocessed
cases and `status: PASS`, then persist that notebook output for Phase 3.

### 2026-08-17 — Phase 1 notebook output attachment verified

In the new Phase 2 CPU notebook, Kaggle mounted the successful Phase 1 output at:

```text
/kaggle/input/notebooks/minseokryu5432/imagecas-180626-v2-edu100-1-1/nnUNet_raw/Dataset598_ImageCAS_EDU100/dataset.json
```

Exactly one Dataset598 `dataset.json` was found, confirming that
`ImageCAS-180626-v2-EDU100-1.1` was attached correctly as a read-only notebook
output. Phase 2 is cleared for unattended **Save & Run All** with accelerator
None and Internet On, using `kaggle/05_preprocess_edu100.sh`. Await its final
preprocessing report and disk-usage output before beginning GPU training.

### 2026-08-17 — Strict training-only Phase 2 design implemented

The preprocessing decision is resolved in favour of the methodologically strict
fixed split. Dataset598 fingerprinting, target-spacing selection, and CT
normalization statistics will use only the 64 training cases. The resulting plan
is then frozen and applied unchanged while preprocessing all 80 development
cases. The 16 validation cases do not influence fitted preprocessing statistics,
and all test cases remain absent.

Phase 2 creates a writable raw-dataset view containing file symlinks rather than
copying the 6.9 GB attachment. Its unattended sequence is:

1. Expose and integrity-check all 80 development cases.
2. Rebuild the view with only 64 training cases.
3. Extract the fingerprint with integrity verification and create the plan.
4. Rebuild the view with 64 training plus 16 validation cases.
5. Preprocess all 80 using the already-frozen training-only plan.
6. Emit a report that fails unless fingerprint count is 64, preprocessed count
   is 80, and both views contain zero test cases.

The split nnU-Net commands are an intentional use of its supported separate
fingerprint, planning, and preprocessing entry points. Local verification after
implementation: **16 synthetic tests passed**; Python compilation, shell syntax,
and Git whitespace checks passed.

### 2026-08-17 — EDU100 Phase 1 raw construction passed

The unattended CPU run of `ImageCAS-180626-v2-EDU100-1.1` completed raw
construction for `Dataset598_ImageCAS_EDU100`.

Observed report:

```text
status: PASS
development cases extracted: 80
training pool: 64
validation: 16
held-out test IDs recorded: 20
held-out test cases extracted: 0
test isolation: PASS
raw dataset size: 6.9 GB
/kaggle/working used: 6.9 GB of 20 GB (36%)
/kaggle/working available: 13 GB
```

The measured raw size is 0.3 GB below the provisional 7.2 GB estimate. Counts
match the fixed educational design, and the Phase 1 builder did not extract any
official test image or label. This validates the raw construction and storage
estimate without using a GPU.

Decision: accept EDU100 Phase 1. Persist its successful notebook output and use
it as the read-only input for Phase 2. Do not preprocess yet: first resolve the
documented fixed-validation issue and, if training-only fingerprinting is
selected, update and test the Phase 2 implementation before providing its
one-line command.

### 2026-08-17 — nnU-Net preprocessing terminology documented

Added `docs/IMAGECAS_NNUNET_PREPROCESSING.md` so the project does not rely on
unexplained terms such as target spacing, CT normalization, and label-preserving
resampling. The note explains that the smoke spacing was the 20-case median of
physical voxel spacings, gives the recorded clipping and z-score statistics,
explains why categorical masks must remain in `{0, 1}`, and distinguishes the
smoke plan from the plan Dataset598 will calculate from its own cases.

The note also records a decision point before Dataset598 preprocessing: the
current standard nnU-Net design fingerprints all 80 development cases, so the
16 validation cases—20% of that pool—contribute geometry and foreground-label
intensities to dataset-level planning statistics. They do not update model
weights, and all official test cases remain excluded. A stricter fixed-split
experiment would fit preprocessing statistics on the 64 training cases only and
apply them unchanged to validation and test data; choose explicitly before
running Phase 2.

### 2026-08-17 — Reusable Kaggle ML playbook created

The general lessons from ImageCAS were separated from the project-specific
handover and written to `docs/KAGGLE_ML_PLAYBOOK.md`. The playbook covers goal
selection, inspection, vertical-slice smoke testing, storage measurement,
persistence boundaries, saved-output chaining, thin notebooks, unattended jobs,
hardware verification, leakage prevention, provenance, resumability, and
pre-/post-run checklists. It is intended to be portable to future segmentation
and other machine-learning projects. The repository README links to it.

### 2026-08-17 — Retrospective: why reaching EDU100 staging took so long

The project owner asked for a candid explanation of why the current staged
Kaggle workflow was not obvious from the beginning and whether the preceding
day's work had been wasted. The answer is a mixture of necessary discovery and
avoidable workflow friction.

#### The objective changed materially

The inherited objective was to audit all 1,000 cases and prepare an official
700-case training baseline. The owner later clarified that the actual priority
is learning the complete CCTA modelling workflow with the smallest dataset that
can still demonstrate meaningful training and evaluation. This distinction
matters:

- a 700/50 development set genuinely requires persistent multi-part staging or
  compute with much more writable storage;
- a 64/16 development set can use a substantially simpler three-notebook
  pipeline;
- the 100-case educational objective did not become explicit until after the
  full-scale storage problem had been investigated.

The project should have surfaced this research-scale-versus-learning-scale
choice earlier instead of continuing to optimize around the inherited full
baseline.

#### Discovery that was genuinely necessary

Several facts could not safely be assumed and were established through Kaggle
runs:

1. The official input did not expose ordinary NIfTI files. It contained 83 GB
   of multipart archives with unusual `.change2zip` and `.zNN` names.
2. The archive groups had to be opened without copying them and verified to
   contain 1,000 apparent image/mask pairs.
3. The workbook contained multiple versions. `v2-latest`, not `v1`, was shown
   to match archive IDs 1–1000 and encode the authoritative 700/50/250 Split-1.
4. Kaggle provided only 20 GB of writable `/kaggle/working` storage. Raw and
   preprocessed sizes were unknown until measured.
5. The 20-case smoke run measured 1.8 GB raw and 3.0 GB preprocessed, proving
   that nnU-Net preprocessing materially expands storage and that foreground
   cropping does not reduce these volumes.
6. The installed PyTorch build could detect the P100 but could not execute CUDA
   kernels because its wheel omitted the P100's `sm_60` architecture.
7. Switching to a T4 and strengthening the checker to execute a real CUDA
   operation was necessary; `torch.cuda.is_available()` alone was insufficient.
8. A complete one-epoch run proved preprocessing consumption, GPU
   forward/backward execution, checkpoint creation, inference, and validation
   metric generation before scaling the data workflow.

These findings were valuable. Without them, a larger unattended run could have
failed after hours because of archive handling, disk exhaustion, unsupported
GPU architecture, or an unproven nnU-Net execution path.

#### Workflow friction that was avoidable

The process nevertheless took longer and felt more meandering than necessary:

- Kaggle was initially treated too much like a conventional persistent
  workstation.
- Live `/kaggle/working` state was not distinguished clearly enough from saved,
  attachable notebook-version output.
- Advice about closing an interactively running browser session was initially
  too confident and later corrected to the reliable Save & Run All workflow.
- Exploration remained in an accumulated notebook for too long instead of
  moving promptly to short, version-controlled stage scripts.
- Long pasted commands were unsuitable for the owner's workflow and caused
  paste/indentation failures before the one-line-script policy was adopted.
- Once the 20-case storage measurements existed, the 20 GB arithmetic and
  notebook-output chaining should have been presented more directly.
- The full 700-case inherited objective was allowed to dominate design longer
  than it should have before explicitly asking whether the desired outcome was
  scientific benchmarking or practical learning.

The previous day's work was therefore not pointless: it produced a proven
end-to-end 3D segmentation execution path and exposed the important archive,
storage, persistence, and GPU constraints. However, the owner's sense that the
route was less direct than it should have been is justified.

#### Efficient sequence with current knowledge

If starting again with today's knowledge, the clean route would be:

1. Inspect the multipart archives and validate the official split.
2. Build a 20-case smoke dataset.
3. Measure raw and preprocessed storage.
4. Run one T4 epoch plus inference and validation.
5. Explicitly choose between a research-scale benchmark and an educational
   baseline.
6. Select the fixed 100-case educational design.
7. Execute three unattended stages: CPU raw construction, CPU preprocessing,
   then one-T4 training/inference/evaluation.

The central lesson is to resolve the intended scale and learning objective as
soon as minimum feasibility evidence exists. From this point onward, user
interaction should normally be limited to submitting one background job,
returning later, attaching its saved output, and submitting the next job.

### 2026-08-17 — EDU100 Phase 1 Kaggle notebook created

The project owner named the Phase 1 raw-staging notebook:

```text
ImageCAS-180626-v2-EDU100-1.1
```

This is the notebook whose successfully committed output will contain
`nnUNet_raw/Dataset598_ImageCAS_EDU100`. After it reports PASS and its saved
output is available, select this notebook under **Add Input → Notebook Output
Files → Your Work** in the Phase 2 preprocessing notebook. A separate Kaggle
Dataset is not required unless direct notebook-output attachment fails.

### 2026-08-17 — Kaggle execution policy: unattended stage jobs

The project owner does not want to keep a Kaggle notebook open or execute a
long workflow cell by cell. Future substantial Kaggle work must therefore be
packaged as version-controlled, one-command stage scripts intended for
**Save & Run All**. The browser may be closed after the background run has been
submitted, and the result can be reviewed later.

Yesterday's smoke work was not disposable. It established that nnU-Net installs
correctly, the T4 executes CUDA kernels, preprocessing is consumable, real 3D
forward/backward training completes, checkpoints are written, inference runs,
and validation metrics are produced. It removed the risk of preparing a larger
dataset before proving the execution stack.

Resource policy by stage:

```text
raw extraction         CPU
planning/preprocessing CPU
model training         one T4 GPU
inference              one T4 GPU
metric evaluation      CPU (may run at the end of the GPU job)
```

The smoke command set `CUDA_VISIBLE_DEVICES=0`, so it deliberately used one T4.
nnU-Net does not automatically turn a second exposed T4 into an efficient
multi-GPU run; one T4 is the simpler and more reproducible choice for this
small-data educational experiment.

Decision: use the fewest safe unattended jobs, not interactive checkpointing
after every command. The planned minimum is three submitted notebook runs:

1. CPU raw construction; save its output.
2. CPU planning/preprocessing from the attached raw output; save its output.
3. One-T4 training, inference, and evaluation from the attached preprocessed
   output.

These cannot safely be collapsed into one Kaggle run. Smoke measurements give
the following provisional 80-development-case estimate:

```text
raw dataset:                       approximately 7.2 GB
3d_fullres preprocessed dataset:   approximately 12.0 GB
combined:                          approximately 19.2 GB
Kaggle writable /kaggle/working:   20.0 GB
nominal space left:                approximately 0.8 GB
```

The apparent 0.8 GB remainder is not a usable safety margin. It must also
accommodate per-case extraction directories, preprocessing temporary files,
Python and nnU-Net runtime output, filesystem overhead, plans and fingerprints,
checkpoints, validation predictions, and logs. Disk exhaustion could therefore
occur before preprocessing or training completes. This estimate also comes from
linear extrapolation of the 20-case smoke run and is not a guarantee that every
selected volume has the same size.

Consequently, raw construction must finish and its output must become a
read-only Kaggle input before preprocessing begins in a clean 20 GB workspace.
The preprocessed output should likewise be persisted before training so a
training failure or timeout does not require preprocessing again. The
accelerator boundary is also useful: preparation should not consume GPU quota.
User involvement should be limited to creating the next notebook, attaching the
preceding saved output, submitting Save & Run All, and later returning the final
report. Stop between stages only for material checks: actual disk size, test
isolation, preprocessing completion, and attached-output path.

### 2026-08-17 — Educational-subset staging workflow implemented locally

Implemented deterministic selection and raw construction for
`Dataset598_ImageCAS_EDU100`. Selection takes the lowest normalized case IDs
within each authoritative Split-1 partition: 64 training, 16 validation, and 20
testing. The resulting learning-curve splits are nested at 16, 32, and 64
training cases and reuse the same 16 validation cases.

The raw builder extracts only the 80 development cases into `imagesTr` and
`labelsTr`. It records the 20 held-out test IDs in the subset manifest but has no
test extraction path. Manifests, source checksums, split definitions, and the
test-isolation report are stored inside the raw dataset's `metadata` directory
so they survive Kaggle persistence and reattachment.

Two one-line Kaggle entry points were added:

```text
kaggle/04_build_edu100_raw.sh   CPU raw construction and disk report
kaggle/05_preprocess_edu100.sh  CPU planning/preprocessing from read-only raw attachment
```

The two stages intentionally run in separate Kaggle sessions. First persist the
estimated 7.2 GB raw dataset. Then attach it read-only in a clean session and
write the provisionally estimated 12 GB preprocessed dataset to
`/kaggle/working`. This avoids holding both forms on the 20 GB writable disk.
The preprocessing script searches for exactly one attached Dataset598 raw
dataset, verifies integrity, fingerprints only the 80 development cases, and
preprocesses only `3d_fullres`.

Local verification: **13 synthetic tests passed**. Python compilation and Git
diff whitespace checks passed. Ruff was unavailable locally. No patient data or
patient-derived artifacts were created locally.

Decision: validate raw construction and measured size on Kaggle before
preprocessing or implementing the training schedule.

### 2026-08-17 — Scope reduced to a 100-case educational baseline

The project owner decided not to pursue training over all 1,000 ImageCAS cases
while learning the CCTA segmentation workflow. The priority is now the smallest
experiment that still demonstrates meaningful model learning, validation, and
held-out evaluation within Kaggle's practical storage and runtime limits.

Working design:

```text
64 cases from official Split-1 training: model fitting
16 cases from official Split-1 validation: model selection and monitoring
20 cases from official Split-1 testing: final held-out evaluation only
100 cases total
```

Case selection must be deterministic and recorded in a manifest. Official
partition membership remains authoritative: no case may move between training,
validation, and testing. The 20 selected test labels must remain isolated from
fingerprinting, planning, training preprocessing, training, and model selection;
they are opened only for final metric calculation after predictions exist.

The intended experiment is a learning curve using nested training subsets of
16, 32, and 64 cases, the same 16-case validation set, and the same untouched
20-case test set. This will show whether additional training cases improve
overlap, surface, and topology measures. Results must be described as an
educational small-data baseline, not as the official ImageCAS benchmark or a
full-dataset result.

Clarification: sharding is a storage mechanism, not a plan to train independent
models on separate chunks and combine them. nnU-Net samples small 3D patches
from cases on disk and updates one model continuously. Based on the smoke
measurements, 80 development cases are provisionally estimated at about 7.2 GB
raw and 12 GB preprocessed. The workflow should avoid holding both forms in
`/kaggle/working` simultaneously. Multi-shard staging is deferred unless direct
measurement shows that one persistent preprocessed 80-case dataset cannot fit
safely.

Decision: replace the 750-case persistent-sharding milestone with the fixed
100-case educational experiment. Before implementation, specify the exact case
selection rule, storage lifecycle, training schedule, acceptance checks, and
files to change.

### 2026-08-17 — One-epoch 3d_fullres smoke training passed

The clean Kaggle smoke workflow completed actual GPU training, checkpointing,
validation inference, and metric aggregation for `Dataset599_ImageCAS_SMOKE`.
The installed split contained 16 training and 4 validation cases. The built-in
`nnUNetTrainer_1epoch` trainer used the `3d_fullres` configuration with a
`96 × 160 × 160` patch, batch size 2, and `torch.compile` enabled.

Observed result:

```text
epoch time: 299.21 s
train loss: -0.1679
validation loss: -0.3713
epoch pseudo Dice: 0.4495
validation predictions: case0017–case0020 (4/4)
final mean validation Dice: 0.33587939502312114
final mean validation IoU: 0.2027645833892343
checkpoint_final: 235 MB
checkpoint_best: 235 MB
results directory: 471 MB
/kaggle/working usage after completion: 5.2 GB of 20 GB
status: PASS
```

The PyTorch Inductor messages about insufficient SMs for
`max_autotune_gemm` and dynamically disabling online softmax were warnings,
not failures. Training and all four validation predictions completed.

Interpretation: the end-to-end nnU-Net v2 execution path is proven on Kaggle,
including preprocessing consumption, GPU forward/backward execution,
checkpoint creation, inference, and evaluation. The Dice value is not a
scientific baseline result: it comes from one epoch on a deliberately small,
engineering-only 16/4 split and must not be used to characterize ImageCAS model
performance.

Decision: close the smoke-training checkpoint. Keep the official 700-case
training baseline unstarted. The next engineering milestone is persistent,
manifested raw/preprocessed sharding that fits Kaggle's storage model and keeps
all 250 official Split-1 test cases out of nnU-Net fingerprinting and
preprocessing.

### 2026-08-17 — Why the full 700-case baseline was not launched overnight

The project owner reasonably asked why we were still running a smoke workflow rather than immediately training the intended U-Net baseline on all official training data. The distinction was clarified:

- Tonight's smoke workflow **does train a real 3D U-Net** on ImageCAS: 16 training cases, 4 validation cases, one complete epoch, GPU forward/backward passes, checkpoint creation, and validation predictions.
- It is an engineering pipeline test, not the scientific 700-case baseline.

The complete baseline was not launched because the current Kaggle notebook exposes only **20 GB of writable `/kaggle/working` storage**. The official ImageCAS input is about **83 GB** and is mounted read-only as five multipart archives. nnU-Net cannot train directly from those archive members: it expects a normal raw dataset tree and a preprocessed dataset tree.

Measured smoke storage was:

```text
20 raw image/label pairs: 1.8 GB
20 preprocessed 3d_fullres cases: 3.0 GB
combined before results: 4.8 GB
Kaggle writable capacity: 20 GB
```

Simple linear estimates for the 750-case development set are therefore approximately:

```text
raw 750-case development data: 1.8 / 20 × 750 ≈ 67.5 GB
preprocessed 750-case data: 3.0 / 20 × 750 ≈ 112.5 GB
combined raw + preprocessed: ≈ 180 GB
```

These estimates exclude model checkpoints, validation predictions, logs, temporary extraction files, and filesystem safety margin. Even raw data alone is more than three times the writable capacity; raw plus preprocessing is roughly nine times the capacity. Trusting the dataset owners and waiving the full audit does not remove this physical storage requirement.

Why this affects workflow convenience:

1. We cannot extract all 750 development cases into one ordinary Kaggle notebook.
2. We cannot run standard full-dataset nnU-Net preprocessing into the same 20 GB working disk.
3. Session resets erase `/kaggle/working` unless outputs are saved or persistence succeeds, so hours of preparation cannot be treated as disposable state.
4. The read-only Kaggle input can hold large persistent datasets, but preprocessing cannot write back into it.
5. Full training therefore needs a staged design: create raw/preprocessed shards as persistent Kaggle dataset outputs, attach them read-only in the training notebook, and present a unified directory through symbolic links—or move the run to compute with substantially more writable storage.

Decision: do not launch a knowingly impossible 700-case job merely to appear to be training sooner. First complete the one-epoch smoke run to prove actual GPU training/checkpoint/validation behavior. Then implement and validate persistent sharded storage before scheduling the official baseline. This is a Kaggle infrastructure constraint, not additional model experimentation.

### 2026-08-17 — Corrected advice about closing an interactive Kaggle session

Codex initially stated too confidently that an interactively running cell could be left by closing the browser and checked later. Kaggle documentation says interactive sessions may remain active until their idle timeout, and optional file persistence is best-effort; this is not the reliable mechanism for an unattended run. Kaggle staff recommends **Save & Run All** for background execution that may safely continue after the browser closes.

Decision: use a new clean notebook and `Save & Run All` for unattended smoke training. `kaggle/run_smoke_end_to_end.sh` reproduces bootstrap, smoke-data construction, planning/preprocessing, one-epoch training, validation, and reports from a clean session. Do not use the exploratory notebook's accumulated cells for a background commit.

### 2026-08-17 — Smoke planning and 3d_fullres preprocessing passed

nnU-Net verified the 20-case raw dataset, extracted its fingerprint, created default plans, and preprocessed all cases for `3d_fullres` in 9 minutes 4 seconds. The custom split was installed successfully.

Key plan:

```text
median and target spacing: 0.5 × 0.3525390625 × 0.3525390625 mm
median cropped shape: 275 × 512 × 512 voxels
median relative size after cropping: 1.0
patch size: 96 × 160 × 160
batch size: 2
training/validation: 16/4
raw size: 1.8 GB
preprocessed size: 3.0 GB
remaining writable disk: 15 GB
```

The crop ratio of 1.0 shows that default foreground cropping does not reduce these volumes. Decision: run the official built-in `nnUNetTrainer_1epoch` debugging trainer on fold 0 using one T4. This is a pipeline test only, not a performance experiment.

### 2026-08-17 — T4 stack and executable CUDA kernel passed

The smoke environment was rebuilt on a Tesla T4. Verified versions were nnU-Net 2.8.1, PyTorch 2.10.0+cu128, NumPy 2.5.2, SciPy 1.16.3, and NiBabel 5.4.2. The corrected checker successfully allocated a CUDA tensor, ran an operation, synchronized the device, and reported `CUDA kernel test: PASS`.

Decision: accept T4 as the smoke-training GPU. Proceed to nnU-Net dataset-integrity verification, fingerprint extraction, default experiment planning, and only the `3d_fullres` preprocessing configuration. Use two processes for fingerprinting and preprocessing to limit RAM pressure.

### 2026-08-17 — P100 rejected by installed PyTorch architecture support

The rebuilt smoke dataset passed and the installed stack reported nnU-Net 2.8.1, PyTorch 2.10.0+cu128, NumPy 2.5.2, SciPy 1.16.3, and NiBabel 5.4.2. PyTorch could see the Tesla P100, but warned that the wheel supports CUDA architectures `sm_70` through `sm_120` while the P100 is `sm_60`.

The original stack checker incorrectly printed `STATUS: PASS` because it tested only `torch.cuda.is_available()` and the device name. It did not execute a CUDA kernel. The checker was corrected to allocate a CUDA tensor, perform an operation, and synchronize before passing.

Decision: do not use the P100 with this installed PyTorch build. Switch the Kaggle accelerator to T4 (`sm_75`), which falls within the wheel's reported supported range, and rerun the bootstrap after the inevitable session reset. Avoid downloading and pinning a separate legacy PyTorch/CUDA stack unless T4 is unavailable.

### 2026-08-17 — Kaggle session reset and long-cell paste failure

The Kaggle session reset after a pause, deleting `/kaggle/working/ImageCAS-160826` and the generated smoke dataset. A subsequent attempt to recreate everything with one long shell command was split during copy/paste, causing Python to interpret shell text and raise `SyntaxError: invalid decimal literal`.

Decision: stop sending long compound notebook commands. `kaggle/bootstrap_smoke.sh` now owns cloning/pulling, installation, archive-link inspection, smoke-dataset recreation, and stack verification. The notebook should only download that script and execute it using short cells.

### 2026-08-17 — Kaggle cell delivery changed to committed scripts

The user reported that copying multiline code from chat into Kaggle introduced incorrect indentation from the second line onward. A dedicated `kaggle/` directory was added. Future notebook actions should normally be delivered as one-line commands such as `!python kaggle/01_verify_stack.py`, with the implementation reviewed and versioned in GitHub/local VS Code.

The current P100 session does not need a pull merely to rerun already-cloned code. A pull is required now only because the new Kaggle helper directory and stack-verification script were just added.

### 2026-08-16 — Dataset599 smoke raw build passed on Kaggle P100

`Dataset599_ImageCAS_SMOKE` was built successfully from cases 1–20:

```text
training cases: 16
validation cases: 4
raw dataset size: 1.8 GB
Kaggle writable disk remaining: 18 GB
GPU: Tesla P100-PCIE-16GB (16,384 MiB)
status: PASS
```

The install selected nnU-Net v2.8.1. Pip upgraded NumPy to 2.5.2 and reported compatibility warnings for unrelated preinstalled Kaggle packages including `numba`, `ydata-profiling`, `google-colab`, and others. These warnings are not yet classified as failures. Decision: run focused imports and CUDA checks for the actual smoke pipeline dependencies before planning/preprocessing; only change versions if those checks demonstrate a real incompatibility.

### 2026-08-16 — Smoke dataset builder implemented

A storage-bounded builder was added for `Dataset599_ImageCAS_SMOKE`. It selects the first 20 IDs assigned to training in official Split-1, extracts only those cases, preserves their original NIfTI geometry, renames them into nnU-Net v2 format, and produces:

- 20 raw image/label pairs;
- `dataset.json` for one CT channel and binary coronary labels;
- deterministic source and SHA-256 manifest;
- one engineering-only split with 16 training and 4 validation cases.

The smoke dataset is explicitly non-scientific. Its purpose is to test installation, dataset integrity verification, planning, preprocessing, GPU training, checkpoint creation, inference, and evaluation without requiring the full dataset to fit in Kaggle's 20 GB writable disk.

### 2026-08-16 — Full 1,000-case audit explicitly waived

After the 23-case validation and timing run, the projected full CPU audit time was approximately four hours. An unattended clean Kaggle notebook was proposed to verify all 1,000 pairs overnight.

The project owner explicitly decided **not** to run that full audit and to trust the dataset owners regarding:

- all 1,000 image/mask pairs opening correctly;
- absence of corrupted files;
- matching image/mask physical geometry;
- binary mask values;
- absence of other case-level integrity failures.

This decision advances the project faster but accepts the risk that an undiscovered bad case may later crash preprocessing/training or compromise evaluation. The audit gate is therefore **waived**, not passed. Evidence actually obtained remains limited to:

- all five multipart archives opened successfully;
- their directory listings contained 1,000 apparent image/mask pairs;
- official Split-1 validated as 700/50/250;
- cases 1–23 audited successfully with zero warnings.

If a later pipeline failure suggests bad input data, reinstate the resumable audit rather than silently repairing or excluding cases.

Revised next step: determine how to stage raw and preprocessed nnU-Net data within Kaggle's observed 20 GB writable-disk limit. The original archives total 83 GB, so ordinary full extraction into `/kaggle/working` is not feasible.

### 2026-08-16 — Timed 20-case audit continuation passed

The archive audit resumed after the first three cases and processed cases 4–23:

```text
already completed: 3
newly audited: 20
total completed: 23
warning cases: 0
wall time: 5 minutes 4 seconds
```

Observed throughput was approximately 15.2 seconds per case. At that rate, the remaining 977 cases should require roughly 4 hours 8 minutes on CPU. Decision: resource use and throughput are acceptable for a full resumable audit in the current Kaggle session; GPU remains unnecessary.

### 2026-08-16 — Official Split-1 validation passed

The `v2-latest` workbook parser validated official Split-1 independently of the partial audit CSV:

```text
case_count: 1000
train: 700
validation: 50
test: 250
first ID: case0001
last ID: case1000
status: PASS
manifest SHA-256: 2dfc35bafe67101f04c538c84abc20c34d33412d38ed7bda55d3018eba62cc15
```

There were no missing, duplicate, unexpected, or invalid partition records. Decision: Split-1 integrity is established at workbook level. The next checkpoint is a timed 20-case continuation of the resumable CPU archive audit.

### 2026-08-16 — Three-case archive audit smoke test passed

The resumable archive auditor processed cases 1–3 successfully:

```text
case0001: OK
case0002: OK
case0003: OK
completed_cases: 3
warning_cases: 0
```

All three volumes were `512 × 512 × 275`; z-spacing was `0.5 mm`; in-plane spacing varied by case as expected. All masks contained only `[0, 1]`, foreground occupied roughly 0.13–0.16% of voxels, and each mask had two connected components. Empty warning cells appeared as `NaN` when pandas loaded the CSV using its default missing-value behavior; this meant no warning, not missing audit execution.

Decision: the case-wise extraction, NIfTI loading, geometry audit, hashing, CSV append, and temporary cleanup path passes its smoke test. Next validate official Split-1, then time a further 20 cases before the full audit.

### 2026-08-16 — Audit CSV read attempted before audit execution

After pulling the logbook commit in Kaggle, `pd.read_csv("artifacts/data_audit.csv")` raised `FileNotFoundError`. This was expected because `git pull` retrieves source-controlled files only; the generated audit CSV is deliberately not committed and `scripts/02_audit_archives.py --limit 3` had not yet been run.

Resolution: run the three-case audit command first, then load its generated CSV. This was a command-order issue, not a dataset or code failure.

## How to maintain this logbook

For each meaningful run, append:

1. Date and checkpoint name.
2. Exact command or notebook cell.
3. What we expected to learn.
4. Actual output or summarized evidence.
5. Any failure or surprise.
6. Decision made because of it.
7. Exact next action.

Keep raw patient data, NIfTI files, and patient-derived images out of Git. Summary statistics, code, commands, and non-identifying engineering observations may be recorded here.
