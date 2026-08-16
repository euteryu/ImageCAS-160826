from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np


def create_montage(case_id: str, image_path: str, mask_path: str, output_path: Path) -> None:
    image = np.asarray(nib.load(image_path).dataobj)
    mask = np.asarray(nib.load(mask_path).dataobj) != 0
    center = np.argwhere(mask).mean(axis=0).astype(int) if mask.any() else np.array(image.shape) // 2
    p01, p99 = np.percentile(image[np.isfinite(image)], [1, 99])
    views = [(0, "sagittal"), (1, "coronal"), (2, "axial")]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), constrained_layout=True)
    for col, (axis, label) in enumerate(views):
        ct = np.take(image, center[axis], axis=axis)
        gt = np.take(mask, center[axis], axis=axis)
        ct, gt = np.rot90(ct), np.rot90(gt)
        axes[0, col].imshow(ct, cmap="gray", vmin=p01, vmax=p99)
        axes[0, col].set_title(f"{label}: CT")
        axes[1, col].imshow(ct, cmap="gray", vmin=p01, vmax=p99)
        axes[1, col].contour(gt, levels=[0.5], colors=["#ff3b30"], linewidths=0.8)
        axes[1, col].set_title(f"{label}: CT + reference boundary")
        for row in range(2):
            axes[row, col].axis("off")
    fig.suptitle(case_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

