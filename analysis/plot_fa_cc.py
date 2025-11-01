#!/usr/bin/env python3
"""Visualize FA slices highlighting the corpus callosum for young vs older subjects."""
from pathlib import Path
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

SUBJECTS = [
    {
        "id": "sub-010005",
        "label": "Young (sub-010005, 25-30y)",
        "fa_path": RESULTS / "sub-010005_ses-01_dti.fib.gz.fa.nii.gz",
    },
    {
        "id": "sub-010002",
        "label": "Older (sub-010002, 65-70y)",
        "fa_path": RESULTS / "sub-010002_ses-01_dti.fib.gz.fa.nii.gz",
    },
]

PLANES = (
    ("Axial", 2),
    ("Coronal", 1),
    ("Sagittal", 0),
)


def central_mask(shape, widths=(48, 48, 32)):
    """Boolean mask covering the central cerebrum where the corpus callosum resides."""
    hx, hy, hz = (w // 2 for w in widths)
    cx, cy, cz = (s // 2 for s in shape)
    mask = np.zeros(shape, dtype=bool)
    mask[cx - hx : cx + hx, cy - hy : cy + hy, cz - hz : cz + hz] = True
    return mask


def slice_with_max_roi_mean(volume, axis, mask):
    best_idx, best_mean = 0, -np.inf
    for idx in range(volume.shape[axis]):
        slicer = [slice(None)] * 3
        slicer[axis] = idx
        data_slice = volume[tuple(slicer)]
        mask_slice = mask[tuple(slicer)]
        roi_vals = data_slice[mask_slice]
        if roi_vals.size == 0:
            continue
        mean_val = roi_vals.mean()
        if mean_val > best_mean:
            best_mean = mean_val
            best_idx = idx
    return best_idx


def extract_slice(volume, axis, index):
    slicer = [slice(None)] * 3
    slicer[axis] = index
    return volume[tuple(slicer)]


def main():
    fig, axes = plt.subplots(len(SUBJECTS), len(PLANES), figsize=(12, 6))
    cmap = "magma"

    for row, subj in enumerate(SUBJECTS):
        data = nib.load(subj["fa_path"]).get_fdata()
        mask = central_mask(data.shape)
        for col, (plane_name, axis) in enumerate(PLANES):
            idx = slice_with_max_roi_mean(data, axis, mask)
            img = extract_slice(data, axis, idx)
            disp = np.rot90(img)
            ax = axes[row, col]
            im = ax.imshow(disp, cmap=cmap, vmin=0, vmax=1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{subj['label']}\n{plane_name} idx={idx}")

    fig.suptitle("Corpus Callosum FA comparison (young vs older)")
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.6, label="FA")
    cbar.set_ticks([0.2, 0.4, 0.6, 0.8])
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path = RESULTS / "fa_cc_comparison.png"
    fig.savefig(out_path, dpi=300)
    print(f"Saved figure to {out_path}")


if __name__ == "__main__":
    main()
