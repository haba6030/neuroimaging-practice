#!/usr/bin/env python3
"""Compute corpus callosum FA using FreeSurfer atlas warped to subject space."""
from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import nibabel as nib
from nibabel.processing import resample_from_to
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

ATLAS_LABELS = [251, 252, 253, 254, 255]

SUBJECTS = [
    {"id": "sub-010019", "age_group": "Young", "gender": "F", "age_bin": "20-25"},
    {"id": "sub-010005", "age_group": "Young", "gender": "M", "age_bin": "25-30"},
    {"id": "sub-010002", "age_group": "Older", "gender": "F", "age_bin": "65-70"},
    {"id": "sub-010039", "age_group": "Older", "gender": "M", "age_bin": "70-75"},
]


def load_pair(subj_id: str):
    fa = nib.load(str(RESULTS / f"{subj_id}_ses-01_dti.fib.gz.fa.nii.gz"))
    atlas = nib.load(str(RESULTS / f"{subj_id}_ses-01_FreeSurferSeg.nii.gz"))
    if fa.shape != atlas.shape:
        atlas = resample_from_to(atlas, fa, order=0)
    return fa.get_fdata(), atlas.get_fdata()


def compute_stats():
    rows = []
    for subj in SUBJECTS:
        fa, atlas = load_pair(subj["id"])
        mask = np.isin(atlas, ATLAS_LABELS)
        roi_vals = fa[mask]
        mean = float(np.mean(roi_vals))
        median = float(np.median(roi_vals))
        std = float(np.std(roi_vals))
        rows.append({
            **subj,
            "mean_fa": mean,
            "median_fa": median,
            "std_fa": std,
            "voxel_count": int(mask.sum()),
        })
    return pd.DataFrame(rows)


def plot_bar(df: pd.DataFrame):
    order = ["Young", "Older"]
    genders = ["F", "M"]
    fig, ax = plt.subplots(figsize=(6, 4))
    width = 0.35
    x = np.arange(len(order))
    for i, gender in enumerate(genders):
        vals = [df[(df.age_group == age) & (df.gender == gender)]["mean_fa"].mean() for age in order]
        ax.bar(x + (i - 0.5) * width, vals, width=width, label=f"{gender}")
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Corpus callosum mean FA")
    ax.set_title("FreeSurfer atlas ROI (labels 251-255)")
    ax.set_ylim(0, 0.5)
    ax.legend(title="Gender")
    fig.tight_layout()
    out_path = RESULTS / "cc_freesurfer_bar.png"
    fig.savefig(out_path, dpi=300)
    return out_path


def main():
    df = compute_stats()
    csv_path = RESULTS / "cc_freesurfer_stats.csv"
    df.to_csv(csv_path, index=False)
    json_path = RESULTS / "cc_freesurfer_stats.json"
    df.to_json(json_path, orient="records", indent=2)
    fig_path = plot_bar(df)
    print(f"Saved stats to {csv_path}")
    print(f"Saved JSON to {json_path}")
    print(f"Saved bar chart to {fig_path}")


if __name__ == "__main__":
    main()
