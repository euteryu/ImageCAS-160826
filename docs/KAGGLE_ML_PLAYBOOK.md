# Kaggle Machine-Learning Playbook

This reusable guide was distilled from large medical-imaging work, but applies
to segmentation, classification, tabular data, NLP, audio, and video.

## Core mental model

Treat Kaggle as disposable compute jobs connected by persistent, read-only
outputs—not as one long-lived computer.

```text
prepare → saved output → preprocess → saved output → train → evaluate
```

Each expensive successful stage should be reusable without rerunning earlier
work.

## 1. Define the objective first

Choose explicitly between a learning exercise, credible small-data experiment,
competition entry, and publication-quality benchmark. Dataset size, validation,
compute cost, and storage architecture depend on this decision.

## 2. Inspect before extracting

Establish the mounted filesystem structure, real formats and archive layout,
sample/label pairings, official splits, compressed and extracted sizes,
writable-disk capacity, preprocessing expansion, and runtime limits. Never
assume the dataset webpage describes the notebook filesystem exactly.

## 3. Prove a tiny end-to-end vertical slice

Use a representative subset to prove:

```text
read → validate → preprocess → train → checkpoint → infer → evaluate
```

- **Read:** Open the original data and label files.
- **Validate:** Check that inputs and labels are readable, correctly paired,
  internally valid, and geometrically compatible where applicable.
- **Preprocess:** Convert the validated data into the representation expected by
  the model, such as resampling, normalization, encoding, or array generation.
- **Train:** Repeatedly show training examples to the model and update its
  parameters to reduce its errors.
- **Checkpoint:** Save the learned model weights and training state so the model
  can be reused or training can resume without starting again.
- **Infer:** Apply the saved model to unseen inputs to generate predictions.
- **Evaluate:** Compare predictions with held-out reference labels using metrics
  chosen for the task.

A complete smoke test is more informative than processing a large dataset while
downstream stages remain untested.

## 4. Measure storage instead of guessing

Record source, extracted, preprocessed, temporary, checkpoint, prediction, and
log sizes. Extrapolate with a meaningful safety margin. An estimated 19.2 GB
workflow does not fit safely on a 20 GB writable disk: temporary files,
filesystem overhead, and sample-size variation still need space.

## 5. Split work at persistence boundaries

A common safe design is:

1. CPU raw preparation.
2. CPU preprocessing from attached raw output.
3. GPU training from attached preprocessed output.
4. Inference and evaluation, combined with training only when runtime and disk
   permit.

Do not combine stages merely to reduce notebook count if failure would repeat
hours of successful work.

## 6. Reuse saved notebook outputs

Live session files are temporary. A successful **Save & Run All** version can
make `/kaggle/working` outputs available as read-only inputs to another
notebook. Use a dedicated Kaggle Dataset when independent versioning or sharing
is useful; direct notebook-output attachment is often simpler for private,
linear experiments.

## 7. Keep notebooks thin

Put implementation in version control and launch it with short commands:

```python
!bash /kaggle/working/project/kaggle/01_prepare.sh
```

This provides reviewable code, reproducible execution, safer copy/paste, useful
diffs, and easier recovery.

## 8. Design jobs to run unattended

Before **Save & Run All**, ensure the stage:

- installs or verifies dependencies;
- validates inputs and disk space;
- fails immediately on real errors;
- prints clear progress;
- writes required artifacts under `/kaggle/working`;
- produces a machine-readable PASS/FAIL report;
- can resume or restart safely where practical.

The user should be able to submit the job, close the browser, and inspect one
final report later.

## 9. Match hardware to the stage

```text
inspection, extraction, hashing      CPU
validation and preprocessing         CPU unless measured otherwise
training and inference               GPU
metric aggregation                   CPU
```

Do not spend GPU quota on CPU-bound work. Multiple visible GPUs are not used
automatically or necessarily efficiently.

## 10. Test hardware with real computation

Device discovery is insufficient. Allocate a framework tensor on the device,
execute an operation, and synchronize. Verify framework/driver compatibility,
supported compute architecture, successful kernel execution, and which devices
the process actually uses.

## 11. Prevent leakage structurally

- Use an authoritative partition manifest.
- Preserve source partition membership.
- Select subsets deterministically.
- Exclude test labels from normalization, fingerprinting, training
  preprocessing, model selection, and threshold selection.
- Open test labels only for final evaluation after the model is fixed.
- Reuse the same validation and test sets across learning-curve experiments.

## 12. Preserve provenance

For every generated dataset or model, record source identifiers, partition
roles, selection rule, source location, checksums where practical, software
versions, configuration, seeds, sizes, completion status, and the exact command.
A result is hard to trust if its input population cannot be reconstructed.

## 13. Make processing resumable and idempotent

A safe rerun recognizes valid completed outputs, avoids duplicate work, and
fails clearly on partial or inconsistent state. Prefer case-wise or shard-wise
progress for large datasets. Session failure and timeout recovery are part of
the design, not emergency additions.

## 14. Validate assumptions before scaling

Open a real archive member, validate a real sample/label pair, execute a real
accelerator kernel, preprocess representative samples, attach a saved output,
and prove downstream tools can consume the read-only attachment. The cheapest
time to invalidate an assumption is before the large run.

## 15. Maintain an operational logbook

For each meaningful run, record:

1. what ran and what it was intended to prove;
2. actual output and measurements;
3. failures, warnings, or surprises;
4. the decision that followed;
5. the exact next action.

Record corrections to earlier advice as well. The reasoning behind a decision
is often more valuable than the decision alone.

## Pre-flight checklist

- [ ] The learning or research objective is explicit.
- [ ] Train, validation, and test roles are fixed.
- [ ] Mounted inputs and archive structure were inspected.
- [ ] Writable disk and runtime limits are recorded.
- [ ] A representative end-to-end smoke test passed.
- [ ] Raw and preprocessed sizes were measured.
- [ ] Accelerator compatibility was tested with real computation.
- [ ] Expensive stages have persistence boundaries.
- [ ] Commands live in version-controlled scripts.
- [ ] The job runs unattended and produces a final report.
- [ ] Failure recovery is understood.
- [ ] Test leakage is prevented structurally.

## Post-run checklist

- [ ] The committed run completed successfully.
- [ ] Expected output files are present.
- [ ] The final report says PASS and counts are correct.
- [ ] Actual runtime and disk usage were recorded.
- [ ] Warnings were classified rather than ignored.
- [ ] Saved output can be attached and read downstream.
- [ ] The logbook was updated before the next stage.

## Condensed rule

```text
Clarify the goal.
Inspect the environment.
Prove a tiny end-to-end run.
Measure actual resources.
Split work into persistent stages.
Automate each stage.
Scale only after validation.
```
