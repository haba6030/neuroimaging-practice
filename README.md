# Neuroimaging Practice

Diffusion MRI self-study workspace for experimenting with preprocessing, tractography, and result reporting workflows. This repository accompanies the dmri-lab8 exercises and keeps lightweight documentation alongside code, notebooks, and derived outputs.

## Repository Layout
- `analysis/`: scripts, notebooks, and configuration for preprocessing and modeling pipelines.
- `data/`: local storage for raw and intermediate diffusion datasets (kept out of version control via `.gitignore`).
- `results/`: generated tables, QC reports, tractography figures, and write-ups.

## Getting Started
1. Place acquisition outputs (e.g., `*.nii.gz`, `.bval`, `.bvec`) under `data/raw/`.
2. Use your preferred preprocessing stack (QSIPrep, MRtrix, DSI Studio, etc.) referencing scripts in `analysis/`.
3. Export figures/tables to `results/` for sharing or manuscript inclusion.

## Data Handling Notes
- Large neuroimaging files and vendor exports are intentionally ignored to avoid bloating the repo.
- DSI Studio-friendly exports (`*.src.gz`, `*.fib.gz`) should stay local; only metadata or notebooks describing how to regenerate them should be tracked.

## Contributions
Issues and pull requests are welcome under the `haba6030/neuroimaging-practice` GitHub repository. Please avoid committing identifiable subject data.
