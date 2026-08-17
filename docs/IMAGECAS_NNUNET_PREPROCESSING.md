# ImageCAS nnU-Net Preprocessing Explained

This note explains the important preprocessing terms and values observed during
the 20-case `Dataset599_ImageCAS_SMOKE` run. These are measured plan outputs,
not universal CCTA constants.

## Where did `0.5 × 0.3525390625 × 0.3525390625 mm` come from?

Every NIfTI header describes the physical size of a voxel. A CCTA volume may,
for example, have approximately `0.5 mm` spacing between reconstructed slices
and approximately `0.35 mm` in-plane pixel spacing.

During fingerprinting, nnU-Net reads the spacing of every case available to the
planner and chooses a representative target spacing. For the 20-case smoke
dataset, the median spacing was:

```text
0.5 × 0.3525390625 × 0.3525390625 mm
```

In the nnU-Net array/plan ordering used here, this corresponds to the
through-plane direction followed by the two in-plane directions. The long
decimal is simply the exact median value inherited from scanner reconstruction
metadata; it was not manually invented or selected because it is intrinsically
optimal.

Cases can start with different voxel spacings. Resampling them to the plan's
common physical spacing makes a voxel represent approximately the same real
distance across cases, allowing one convolutional network to learn at a
consistent spatial scale.

Important: this value belongs to `Dataset599` and its 20 cases. When nnU-Net
fingerprints the 80-case `Dataset598_ImageCAS_EDU100` development dataset, it
will calculate a new plan from those cases. Its target spacing may be identical
or may differ slightly. The Dataset598 value must be read from its generated
`nnUNetPlans.json`, not copied from the smoke plan.

## How does nnU-Net CT intensity normalization work?

CT voxel values represent a physical attenuation scale, commonly expressed in
Hounsfield units (HU). The same tissue has broadly comparable values across CT
scans, so nnU-Net uses one dataset-level CT normalization rather than separately
forcing every patient to have mean zero and standard deviation one.

For the cases included in fingerprinting, nnU-Net collects CT intensities at
voxels belonging to foreground reference labels. It calculates:

- the 0.5th intensity percentile;
- the 99.5th intensity percentile;
- the mean;
- the standard deviation.

It then applies the same transformation to every case:

```text
1. clip values below the 0.5th percentile to that lower limit
2. clip values above the 99.5th percentile to that upper limit
3. normalized value = (clipped value - dataset mean) / dataset standard deviation
```

This is commonly called **z-score standardization**. Machine-learning software
often uses "normalization" as the broader name. It gives values an intuitive
scale:

```text
value equal to the mean                    →  0
value one standard deviation above mean   → +1
value one standard deviation below mean   → -1
```

Using the smoke statistics:

```text
(148.56 - 148.56) / 189.42 =  0
(337.98 - 148.56) / 189.42 = +1
(-40.86 - 148.56) / 189.42 = -1
```

Centering values near zero and putting them on a consistent scale generally
makes neural-network optimization easier than learning directly from a wide HU
range. Because clipping changes the extremes, the final clipped volume is not
guaranteed to have mathematically exact mean zero and standard deviation one;
the practical goal is a stable, reproducible, approximately centred scale.

The smoke plan recorded:

```text
lower clipping limit:  -166 HU
upper clipping limit:   790 HU
foreground mean:        148.5611 HU
foreground std:         189.4168 HU
```

Examples using those smoke statistics:

```text
-500 HU is first clipped to -166 HU, then normalized
 100 HU remains 100 HU, then normalized
1200 HU is first clipped to 790 HU, then normalized
```

Clipping limits the influence of unusually extreme values. Subtracting the mean
and dividing by the standard deviation places typical values on a scale that is
easier for neural-network optimization. It does not change the original NIfTI
files; it creates model-ready arrays.

These statistics are dataset-specific. Dataset598 will calculate its own values
during fingerprinting.

### Validation-statistics caveat

The current Dataset598 design places 64 training and 16 validation cases in the
80-case development dataset before nnU-Net fingerprinting. Standard nnU-Net
planning will therefore derive spacing and CT normalization statistics from all
80 development cases, including the validation cases, while excluding every
official test case.

Validation data are necessary for monitoring training and choosing a model, but
strict methodology normally fits preprocessing rules using training data only.
The 16 validation cases would be 20% of the 80 cases contributing to the
Dataset598 fingerprint, so their numerical contribution is not necessarily
small. What is limited is the *type* of information used: they would not update
model weights, but their geometry and foreground-label intensity distribution
would influence shared spacing and normalization statistics.

This matches nnU-Net's conventional cross-validation workflow, where cases act
as validation in one fold and training in others, and it does not expose test
data. Our fixed 64/16 split is different.

Decision: Dataset598 Phase 2 will fit the fingerprint, spacing, and normalization
statistics using the 64 training cases only. It will then freeze that plan and
apply it unchanged while preprocessing the 16 validation cases. Test cases
remain absent. This preserves the intended fixed-holdout interpretation.

## What does preserving discrete mask labels mean?

The CT image is continuous-valued. Interpolation during resampling may safely
create an intensity between neighboring CT voxels.

The reference mask is categorical:

```text
0 = background
1 = coronary-artery reference label
```

A value such as `0.37` is not a valid anatomical class. Fractions are not
present in the original mask; they can arise temporarily during interpolation.
A new grid point between an original `0` voxel and an original `1` voxel might,
for example, receive 24% or 71% contribution from the foreground voxel. Naive
continuous-image resizing would then produce `0.24` or `0.71`.

nnU-Net therefore tells its resampler that the input is a segmentation
(`is_seg=True`). Its segmentation-aware resampling treats label membership
separately and converts the result back to valid classes. Conceptually, a basic
binary implementation might choose `0` below a `0.5` membership threshold and
`1` at or above it; multiclass handling selects among class memberships. nnU-Net
handles this internally instead of leaving fractions in the saved target. Thus,
the saved mask remains an integer label map rather than a grey-scale blend.

For ImageCAS, the required invariant after preprocessing is:

```text
allowed reference-mask labels: {0, 1}
```

Preserving labels does not mean that the resampled boundary is guaranteed to be
identical voxel for voxel. Moving to a different grid necessarily changes which
new voxels best represent the boundary. It means the transformation preserves
the categorical meaning and physical geometry instead of manufacturing invalid
label values.

## Why preprocessing is necessary

After preprocessing, nnU-Net can sample fixed-size `96 × 160 × 160` patches in
the smoke configuration where:

- physical scale is consistent across cases;
- CT values have a consistent numerical scale;
- target masks contain valid integer classes;
- metadata records how predictions can be mapped back to original geometry.

The original NIfTI data remain the source of truth. Preprocessed arrays are a
derived representation for model computation, not a repaired or overwritten
version of the patient data.
