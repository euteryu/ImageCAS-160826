# ImageCAS Project Logbook

This is the human-readable record of what we did, what Kaggle showed us, why the plan changed, and what should happen next. Update it after every meaningful Kaggle run or engineering decision.

## Current status

- Phase: IMG-CAS-001 — dataset discovery and audit
- Training status: **not started**
- GPU required now: **no**
- Current checkpoint: build `Dataset599_ImageCAS_SMOKE` from 20 official Split-1 training cases
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

In the existing Kaggle notebook, with the GPU still disabled:

```python
%cd /kaggle/working/ImageCAS-160826
!git pull
!python scripts/02_audit_archives.py --limit 3
```

Then inspect:

```python
import pandas as pd

audit = pd.read_csv("artifacts/data_audit.csv")
display(audit[[
    "case_id",
    "image_shape_x", "image_shape_y", "image_shape_z",
    "spacing_x_mm", "spacing_y_mm", "spacing_z_mm",
    "mask_unique_values",
    "foreground_fraction",
    "connected_component_count",
    "warning_codes",
]])
```

Report the command output and displayed three-row table back to Codex.

## Known open work

- Validate the three-case smoke run.
- Fix any real archive, memory, geometry, or CSV issue found by that run.
- Parse `v2-latest` deterministically and verify Split-1 counts: 700 training, 50 validation, 250 testing.
- Run the resumable audit across all 1,000 cases on CPU.
- Select random and statistical-outlier cases for visual QC.
- Re-extract only selected cases to generate montages.
- Review annotation semantics and outliers manually.
- Pass Gate A before enabling model training.

## Run notes

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
