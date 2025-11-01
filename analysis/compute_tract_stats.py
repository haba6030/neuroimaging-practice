#!/usr/bin/env python3
"""Aggregate DSI Studio tract statistics into CSV summaries."""
from __future__ import annotations

import csv
import glob
import math
import os
from collections import defaultdict
from statistics import mean, stdev
from typing import Dict, Iterable, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

SUBJECTS = [
    "sub-010002",
    "sub-010005",
    "sub-010019",
    "sub-010039",
]

TRACT_GROUPS = {
    "CorpusCallosum": ["Commissure_CorpusCallosum"],
    "SLF": [
        "Association_SuperiorLongitudinalFasciculusL",
        "Association_SuperiorLongitudinalFasciculusR",
    ],
    "CST": [
        "ProjectionBrainstem_CorticospinalTractL",
        "ProjectionBrainstem_CorticospinalTractR",
    ],
    "Uncinate": [
        "Association_UncinateFasciculusL",
        "Association_UncinateFasciculusR",
    ],
}

STAT_KEYS = {
    "streamlines": "number of tracts",
    "volume_mm3": "total volume(mm^3)",
    "mean_fa": "fa",
}


def _parse_stat_file(path: str) -> Dict[str, float]:
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


def _find_stat_files(subject: str, tract_name: str) -> List[str]:
    base = os.path.join(RESULTS_DIR, f"{subject}_tracts", tract_name)
    patterns = [
        os.path.join(base, "*.stat.txt"),
        os.path.join(base, "**", "*.stat.txt"),
    ]
    for pattern in patterns:
        hits = glob.glob(pattern, recursive="**" in pattern)
        if hits:
            return sorted(hits)
    raise FileNotFoundError(f"No stat files for {subject} {tract_name}")


def _combine_metrics(stat_paths: Iterable[str]) -> Dict[str, float]:
    total_streamlines = 0.0
    total_volume = 0.0
    weighted_fa = 0.0

    for stat_path in stat_paths:
        stats = _parse_stat_file(stat_path)
        streamlines = stats.get(STAT_KEYS["streamlines"], 0.0)
        volume = stats.get(STAT_KEYS["volume_mm3"], 0.0)
        fa = stats.get(STAT_KEYS["mean_fa"], math.nan)

        total_streamlines += streamlines
        total_volume += volume

        if not math.isnan(fa) and streamlines > 0:
            weighted_fa += fa * streamlines

    mean_fa = weighted_fa / total_streamlines if total_streamlines > 0 else math.nan

    return {
        "streamlines": total_streamlines,
        "volume_mm3": total_volume,
        "mean_fa": mean_fa,
    }


def _collect_subject_metrics() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for subject in SUBJECTS:
        # Whole brain summary
        wholebrain_stat = os.path.join(
            RESULTS_DIR, f"{subject}_wholebrain.tt.gz.stat.txt"
        )
        if not os.path.exists(wholebrain_stat):
            raise FileNotFoundError(f"Missing wholebrain stat for {subject}")
        wholebrain_metrics = _parse_stat_file(wholebrain_stat)
        rows.append(
            {
                "subject": subject,
                "tract": "WholeBrain",
                "streamlines": wholebrain_metrics.get(STAT_KEYS["streamlines"], 0.0),
                "mean_fa": wholebrain_metrics.get(STAT_KEYS["mean_fa"], math.nan),
                "volume_mm3": wholebrain_metrics.get(STAT_KEYS["volume_mm3"], 0.0),
            }
        )

        # Individual tract groups
        for group, tract_list in TRACT_GROUPS.items():
            stat_files: List[str] = []
            for tract_name in tract_list:
                stat_files.extend(_find_stat_files(subject, tract_name))
            metrics = _combine_metrics(stat_files)
            rows.append(
                {
                    "subject": subject,
                    "tract": group,
                    **metrics,
                }
            )
    return rows


def _write_csv(path: str, rows: Iterable[Dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        return
    fieldnames = ["subject", "tract", "streamlines", "mean_fa", "volume_mm3"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _summarise_by_tract(rows: Iterable[Dict[str, object]]) -> List[Dict[str, object]]:
    grouped: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        tract = str(row["tract"])
        grouped[tract]["streamlines"].append(float(row["streamlines"]))
        grouped[tract]["mean_fa"].append(float(row["mean_fa"]))
        grouped[tract]["volume_mm3"].append(float(row["volume_mm3"]))

    summary_rows: List[Dict[str, object]] = []
    for tract, metrics in grouped.items():
        summary_rows.append(
            {
                "tract": tract,
                "mean_streamlines": mean(metrics["streamlines"]),
                "std_streamlines": stdev(metrics["streamlines"]) if len(metrics["streamlines"]) > 1 else 0.0,
                "mean_fa": mean(metrics["mean_fa"]),
                "std_fa": stdev(metrics["mean_fa"]) if len(metrics["mean_fa"]) > 1 else 0.0,
                "mean_volume_mm3": mean(metrics["volume_mm3"]),
                "std_volume_mm3": stdev(metrics["volume_mm3"]) if len(metrics["volume_mm3"]) > 1 else 0.0,
            }
        )
    return summary_rows


def main() -> None:
    rows = _collect_subject_metrics()
    per_subject_csv = os.path.join(RESULTS_DIR, "tract_metrics.csv")
    _write_csv(per_subject_csv, rows)

    summary = _summarise_by_tract(rows)
    summary_csv = os.path.join(RESULTS_DIR, "tract_metrics_summary.csv")
    fieldnames = [
        "tract",
        "mean_streamlines",
        "std_streamlines",
        "mean_fa",
        "std_fa",
        "mean_volume_mm3",
        "std_volume_mm3",
    ]
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary:
            writer.writerow(row)


if __name__ == "__main__":
    main()
