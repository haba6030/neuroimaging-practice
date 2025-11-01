#!/usr/bin/env python3
"""Create SLF tract density projection comparing young vs older groups."""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "analysis" / "figures"

FIGURES.mkdir(parents=True, exist_ok=True)

SUBJECTS = [
    {"id": "sub-010005", "label": "Young • M (25-30)"},
    {"id": "sub-010019", "label": "Young • F (20-25)"},
    {"id": "sub-010002", "label": "Older • F (65-70)"},
    {"id": "sub-010039", "label": "Older • M (70-75)"},
]

TRACTS = {
    "L": "Association_SuperiorLongitudinalFasciculusL",
    "R": "Association_SuperiorLongitudinalFasciculusR",
}


def load_tdi(subject: str, tract: str) -> np.ndarray:
    path = (
        RESULTS
        / f"{subject}_tracts"
        / tract
        / f"{subject}_ses-01_dti.{tract}.tt.gz.tdi.nii.gz"
    )
    img = nib.load(str(path))
    data = img.get_fdata(dtype=np.float32)
    return data


def prepare_projection(volume: np.ndarray) -> np.ndarray:
    # Sum both hemispheres, normalize, and compute coronal max projection.
    if volume.max() > 0:
        volume = volume / volume.max()
    mip = volume.max(axis=0)  # collapse left-right axis -> coronal view
    mip = np.log1p(mip * 20)  # enhance contrast for visualization
    mip = np.flipud(np.rot90(mip))  # orient superior at top
    return mip


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(8, 7))
    for ax, subj in zip(axes.flatten(), SUBJECTS):
        combined = np.zeros((128, 128, 88), dtype=np.float32)
        for tract in TRACTS.values():
            combined += load_tdi(subj["id"], tract)
        projection = prepare_projection(combined)
        im = ax.imshow(projection, cmap="inferno", interpolation="nearest")
        ax.set_title(subj["label"], fontsize=10)
        ax.axis("off")

    fig.suptitle("Superior Longitudinal Fasciculus • Tract Density Projection", fontsize=14)
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    output_path = FIGURES / "slf_group_comparison.png"
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
