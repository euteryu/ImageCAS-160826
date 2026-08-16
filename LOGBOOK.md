# ImageCAS Project Logbook

This is the human-readable record of what we did, what Kaggle showed us, why the plan changed, and what should happen next. Update it after every meaningful Kaggle run or engineering decision.

## Current status

- Phase: IMG-CAS-001 — dataset discovery and audit
- Training status: **not started**
- GPU required now: **no**
- Current checkpoint: run a three-case archive audit smoke test
- Repository: <https://github.com/euteryu/ImageCAS-160826>
- Kaggle dataset: <https://www.kaggle.com/datasets/xiaoweixumedicalai/imagecas>

## Fixed project decisions

1. Patient data stays on Kaggle. We do not download ImageCAS to the laptop or commit it to Git.
2. Kaggle is the execution environment; GitHub is the source of truth for code.
3. We audit before training.
4. We use the official ImageCAS Split-1 and later isolate its 250 test cases from nnU-Net fingerprinting and preprocessing.
5. The target is called the **ImageCAS binary coronary-artery reference mask** until visual QC establishes its precise annotation semantics.
6. The eventual baseline must include overlap, surface, and topology evaluation—not Dice alone.

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
