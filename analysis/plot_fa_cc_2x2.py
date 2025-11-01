#!/usr/bin/env python3
"""Compare CC FA slices and summary stats across a 2x2 age × gender design."""
from pathlib import Path
import json

import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

SUBJECTS = [
    {
        "id": "sub-010019",
        "label": "Young Female (sub-010019, 20-25y)",
        "age_group": "Young",
        "gender": "F",
        "fa_path": RESULTS / "sub-010019_ses-01_dti.fib.gz.fa.nii.gz",
    },
    {
        "id": "sub-010005",
        "label": "Young Male (sub-010005, 25-30y)",
        "age_group": "Young",
        "gender": "M",
        "fa_path": RESULTS / "sub-010005_ses-01_dti.fib.gz.fa.nii.gz",
    },
    {
        "id": "sub-010002",
        "label": "Older Female (sub-010002, 65-70y)",
        "age_group": "Older",
        "gender": "F",
        "fa_path": RESULTS / "sub-010002_ses-01_dti.fib.gz.fa.nii.gz",
    },
    {
        "id": "sub-010039",
        "label": "Older Male (sub-010039, 70-75y)",
        "age_group": "Older",
        "gender": "M",
        "fa_path": RESULTS / "sub-010039_ses-01_dti.fib.gz.fa.nii.gz",
    },
]

PLANES = (
    ("Axial", 2),
    ("Coronal", 1),
    ("Sagittal", 0),
)


def central_mask(shape, widths=(48, 48, 32)):
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
        roi_slice = mask[tuple(slicer)]
        if not roi_slice.any():
            continue
        val_slice = volume[tuple(slicer)][roi_slice]
        mean_val = val_slice.mean()
        if mean_val > best_mean:
            best_mean = mean_val
            best_idx = idx
    return best_idx


def extract_slice(volume, axis, index):
    slicer = [slice(None)] * 3
    slicer[axis] = index
    return volume[tuple(slicer)]


def main():
    rows = {"Young": 0, "Older": 1}
    cols = {"F": 0, "M": 1}
    fig, axes = plt.subplots(2 * len(PLANES), 2, figsize=(8, 10))
    stats = []

    for subj in SUBJECTS:
        data = nib.load(subj["fa_path"]).get_fdata()
        mask = central_mask(data.shape)
        roi_mean = data[mask].mean()
        roi_std = data[mask].std()
        stats.append({
            "subject": subj["id"],
            "age_group": subj["age_group"],
            "gender": subj["gender"],
            "roi_mean_fa": float(roi_mean),
            "roi_std_fa": float(roi_std),
        })
        base_row = rows[subj["age_group"]] * len(PLANES)
        col = cols[subj["gender"]]
        for plane_offset, (plane_name, axis) in enumerate(PLANES):
            idx = slice_with_max_roi_mean(data, axis, mask)
            slice_img = extract_slice(data, axis, idx)
            disp = np.rot90(slice_img)
            ax = axes[base_row + plane_offset, col]
            im = ax.imshow(disp, cmap="magma", vmin=0, vmax=1)
            if col == 0:
                ax.set_ylabel(f"{plane_name}\n{ subj['age_group'] }")
            if plane_offset == 0:
                ax.set_title(f"{subj['gender']}\n{subj['id']} idx={idx}")
            ax.set_xticks([])
            ax.set_yticks([])

    plt.tight_layout()
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.6, label="FA")
    out_fig = RESULTS / "fa_cc_comparison_2x2.png"
    fig.savefig(out_fig, dpi=300)

    out_json = RESULTS / "fa_cc_stats.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"Saved figure to {out_fig}")
    print(f"Saved stats to {out_json}")


if __name__ == "__main__":
    main()
