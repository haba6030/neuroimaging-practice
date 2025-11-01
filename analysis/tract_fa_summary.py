#!/usr/bin/env python3
"""Aggregate tract FA metrics and generate comparison outputs."""
from __future__ import annotations

import glob
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

SUBJECT_METADATA = {
    "sub-010019": {"age_bin": "20-25", "age_group": "Young", "sex": "F"},
    "sub-010005": {"age_bin": "25-30", "age_group": "Young", "sex": "M"},
    "sub-010002": {"age_bin": "65-70", "age_group": "Older", "sex": "F"},
    "sub-010039": {"age_bin": "70-75", "age_group": "Older", "sex": "M"},
}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "analysis", "figures")

os.makedirs(FIGURES_DIR, exist_ok=True)

TRACT_LABEL_MAP = {
    "Commissure_CorpusCallosum": "Corpus_Callosum",
    "Association_SuperiorLongitudinalFasciculusL": "SLF_L",
    "Association_SuperiorLongitudinalFasciculusR": "SLF_R",
    "ProjectionBrainstem_CorticospinalTractL": "CST_L",
    "ProjectionBrainstem_CorticospinalTractR": "CST_R",
    "Association_UncinateFasciculusL": "UF_L",
    "Association_UncinateFasciculusR": "UF_R",
}

TARGET_LABELS = set(TRACT_LABEL_MAP.values())


@dataclass
class TractMetric:
    subject: str
    tract: str
    mean_fa: float


def parse_stat_file(path: str) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if "\t" not in line:
                continue
            key, value = line.strip().split("\t", 1)
            try:
                metrics[key] = float(value)
            except ValueError:
                continue
    return metrics


def identify_subject(path: str) -> str:
    basename = os.path.basename(path)
    parts = basename.split(".")
    for part in parts:
        if part.startswith("sub-"):
            return part.split("_")[0]
    raise ValueError(f"Could not identify subject from {path}")


def identify_tract(path: str) -> Tuple[str, str]:
    for atlas_name, label in TRACT_LABEL_MAP.items():
        if atlas_name in path:
            return atlas_name, label
    return "", ""


def collect_metrics() -> List[TractMetric]:
    metrics: List[TractMetric] = []
    pattern = os.path.join(RESULTS_DIR, "**", "*.stat.txt")
    for stat_path in glob.glob(pattern, recursive=True):
        atlas_name, tract_label = identify_tract(stat_path)
        if not tract_label:
            continue
        stats = parse_stat_file(stat_path)
        if "fa" not in stats:
            continue
        subject = identify_subject(stat_path)
        metrics.append(TractMetric(subject=subject, tract=tract_label, mean_fa=stats["fa"]))
    return metrics


def _subject_sort_key(subject: str) -> Tuple[int, str]:
    meta = SUBJECT_METADATA.get(subject, {})
    group = meta.get("age_group", "")
    group_rank = 0 if group.lower().startswith("young") else 1
    return (group_rank, subject)


def to_wide_table(metrics: List[TractMetric]) -> Tuple[List[str], Dict[str, Dict[str, float]]]:
    subjects = sorted({m.subject for m in metrics}, key=_subject_sort_key)
    table: Dict[str, Dict[str, float]] = defaultdict(dict)
    for metric in metrics:
        table[metric.subject][metric.tract] = metric.mean_fa
    return subjects, table


def write_comparison_csv(path: str, subjects: List[str], table: Dict[str, Dict[str, float]]):
    import csv

    fieldnames = [
        "subject",
        "age_group",
        "age_bin",
        "sex",
    ] + sorted(TARGET_LABELS)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for subject in subjects:
            meta = SUBJECT_METADATA.get(subject, {})
            row = {
                "subject": subject,
                "age_group": meta.get("age_group", ""),
                "age_bin": meta.get("age_bin", ""),
                "sex": meta.get("sex", ""),
            }
            for tract in sorted(TARGET_LABELS):
                row[tract] = table.get(subject, {}).get(tract, "")
            writer.writerow(row)


def compute_change_rates(subjects: List[str], table: Dict[str, Dict[str, float]]):
    import csv

    change_rates: List[Dict[str, object]] = []
    for tract in sorted(TARGET_LABELS):
        values = [table.get(sub, {}).get(tract) for sub in subjects]
        values = [v for v in values if v is not None]
        if not values:
            continue
        mean_val = sum(values) / len(values)
        for subject in subjects:
            val = table.get(subject, {}).get(tract)
            if val is None:
                continue
            percent_change = ((val - mean_val) / mean_val) * 100 if mean_val else 0.0
            meta = SUBJECT_METADATA.get(subject, {})
            change_rates.append(
                {
                    "subject": subject,
                    "age_group": meta.get("age_group", ""),
                    "age_bin": meta.get("age_bin", ""),
                    "sex": meta.get("sex", ""),
                    "tract": tract,
                    "mean_fa": val,
                    "percent_change_from_group_mean": percent_change,
                }
            )

    change_csv = os.path.join(RESULTS_DIR, "tract_fa_change_rates.csv")
    fieldnames = [
        "subject",
        "age_group",
        "age_bin",
        "sex",
        "tract",
        "mean_fa",
        "percent_change_from_group_mean",
    ]
    with open(change_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in change_rates:
            writer.writerow(row)


def plot_bar_chart(subjects: List[str], table: Dict[str, Dict[str, float]]):
    tracts = sorted(TARGET_LABELS)
    x = range(len(subjects))
    bar_width = 0.12

    plt.figure(figsize=(12, 5))
    for idx, tract in enumerate(tracts):
        offsets = [pos + (idx - len(tracts) / 2) * bar_width + bar_width / 2 for pos in x]
        values = [table.get(subject, {}).get(tract, 0.0) for subject in subjects]
        plt.bar(offsets, values, width=bar_width, label=tract)

    xticklabels = []
    for subject in subjects:
        meta = SUBJECT_METADATA.get(subject, {})
        xticklabels.append(
            f"{subject}\n{meta.get('age_group', '')} / {meta.get('sex', '')} / {meta.get('age_bin', '')}"
        )
    plt.xticks(list(x), xticklabels, rotation=20, ha="right")
    plt.ylabel("Mean FA")
    plt.title("Mean FA per Subject and Tract")
    plt.legend(ncol=3, fontsize=8)
    plt.tight_layout()
    plot_path = os.path.join(FIGURES_DIR, "tract_fa_barplot.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()


def main() -> None:
    metrics = collect_metrics()
    if not metrics:
        raise SystemExit("No tract metrics found.")

    subjects, table = to_wide_table(metrics)
    comparison_csv = os.path.join(RESULTS_DIR, "tract_fa_comparison.csv")
    write_comparison_csv(comparison_csv, subjects, table)
    compute_change_rates(subjects, table)
    plot_bar_chart(subjects, table)


if __name__ == "__main__":
    main()
