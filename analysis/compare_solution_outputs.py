#!/usr/bin/env python3
"""Local-only comparison of two solution CSV outputs.

This is an analysis helper for experiments. It may use benchmark archetypes and
reference CSVs; it is not part of the submission-facing ranker.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    REPO_ROOT,
    markdown_table,
    stream_candidates,
    summary_archetype,
    write_json,
)


DEFAULT_BASELINE = DEFAULT_OUTPUT_DIR / "solution_ranker_submission.csv"
DEFAULT_EXPERIMENT = DEFAULT_OUTPUT_DIR / "solution_embedding_experiment.csv"
DEFAULT_REFERENCE_A = REPO_ROOT / "idea1_top100.csv"
DEFAULT_REFERENCE_B = DEFAULT_OUTPUT_DIR / "idea2_submission.csv"
DEFAULT_OUT_JSON = DEFAULT_OUTPUT_DIR / "solution_output_comparison.json"
DEFAULT_OUT_MD = DEFAULT_OUTPUT_DIR / "solution_output_comparison.md"
TOPK = (10, 20, 30, 50, 100)
SENIOR_ARCHETYPES = {"senior_plain_language", "senior_explicit_ai"}


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def read_submission_ids(path: Path, limit: int = 100) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        key = "candidate_id" if "candidate_id" in reader.fieldnames else reader.fieldnames[0]
        return [row[key] for row in reader if row.get(key)][:limit]


def candidate_lookup(candidates_path: Path, candidate_ids: set[str]) -> dict[str, dict[str, Any]]:
    selected = {}
    for candidate in stream_candidates(candidates_path):
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in candidate_ids:
            profile = candidate["profile"]
            selected[candidate_id] = {
                "archetype": summary_archetype(
                    str(profile.get("summary", "")),
                    str(profile.get("current_title", "")),
                ),
                "title": profile.get("current_title"),
                "company": profile.get("current_company"),
            }
            if len(selected) == len(candidate_ids):
                break
    return selected


def topk_overlap(a: list[str], b: list[str]) -> dict[str, int]:
    return {str(k): len(set(a[:k]) & set(b[:k])) for k in TOPK}


def rank_delta_summary(a: list[str], b: list[str]) -> dict[str, Any]:
    rank_a = {candidate_id: rank for rank, candidate_id in enumerate(a, 1)}
    rank_b = {candidate_id: rank for rank, candidate_id in enumerate(b, 1)}
    common = sorted(set(rank_a) & set(rank_b))
    if not common:
        return {
            "common_count": 0,
            "spearman": None,
            "mean_abs_rank_delta": None,
            "max_abs_rank_delta": None,
        }
    n = len(common)
    deltas = [abs(rank_a[candidate_id] - rank_b[candidate_id]) for candidate_id in common]
    d2 = sum(delta * delta for delta in deltas)
    spearman = 1 - (6 * d2) / (n * (n * n - 1)) if n > 1 else 1.0
    return {
        "common_count": n,
        "spearman": round(spearman, 4),
        "mean_abs_rank_delta": round(sum(deltas) / n, 2),
        "max_abs_rank_delta": max(deltas),
    }


def archetype_counts(ids: list[str], lookup: dict[str, dict[str, Any]]) -> dict[str, dict[str, int]]:
    result = {}
    for k in TOPK:
        counts: Counter[str] = Counter(
            lookup[candidate_id]["archetype"] for candidate_id in ids[:k]
        )
        result[str(k)] = dict(counts.most_common())
    return result


def senior_ranks(ids: list[str], lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for rank, candidate_id in enumerate(ids, 1):
        meta = lookup[candidate_id]
        if meta["archetype"] in SENIOR_ARCHETYPES:
            rows.append(
                {
                    "rank": rank,
                    "candidate_id": candidate_id,
                    "archetype": meta["archetype"],
                    "title": meta["title"],
                    "company": meta["company"],
                }
            )
    return rows


def optional_reference_overlap(path: Path, ids: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    reference_ids = read_submission_ids(path)
    return {
        "path": str(path),
        "top100_common": len(set(ids) & set(reference_ids)),
        "topk_overlap": topk_overlap(ids, reference_ids),
    }


def build_comparison(
    baseline_path: Path,
    experiment_path: Path,
    candidates_path: Path,
    reference_a_path: Path,
    reference_b_path: Path,
) -> dict[str, Any]:
    baseline_ids = read_submission_ids(baseline_path)
    experiment_ids = read_submission_ids(experiment_path)
    all_ids = set(baseline_ids) | set(experiment_ids)
    for path in (reference_a_path, reference_b_path):
        if path.is_file():
            all_ids.update(read_submission_ids(path))
    lookup = candidate_lookup(candidates_path, all_ids)
    return {
        "audit_scope": "local_benchmark_only",
        "baseline": str(baseline_path),
        "experiment": str(experiment_path),
        "baseline_vs_experiment": {
            "top100_common": len(set(baseline_ids) & set(experiment_ids)),
            "topk_overlap": topk_overlap(baseline_ids, experiment_ids),
            "rank_delta": rank_delta_summary(baseline_ids, experiment_ids),
        },
        "baseline_archetype_counts": archetype_counts(baseline_ids, lookup),
        "experiment_archetype_counts": archetype_counts(experiment_ids, lookup),
        "baseline_senior_ranks": senior_ranks(baseline_ids, lookup),
        "experiment_senior_ranks": senior_ranks(experiment_ids, lookup),
        "reference_overlaps": {
            "reference_a": optional_reference_overlap(reference_a_path, experiment_ids),
            "reference_b": optional_reference_overlap(reference_b_path, experiment_ids),
        },
    }


def render_markdown(summary: dict[str, Any]) -> str:
    comparison = summary["baseline_vs_experiment"]
    lines = [
        "# Solution Output Comparison",
        "",
        "Local-only benchmark comparison. This is not part of the general ranker.",
        "",
        f"- Baseline: `{summary['baseline']}`",
        f"- Experiment: `{summary['experiment']}`",
        f"- Top-100 common: {comparison['top100_common']}",
        f"- Spearman on common top-100: {comparison['rank_delta']['spearman']}",
        f"- Mean absolute rank delta: {comparison['rank_delta']['mean_abs_rank_delta']}",
        f"- Max absolute rank delta: {comparison['rank_delta']['max_abs_rank_delta']}",
        "",
        "## Top-K Overlap",
        "",
        markdown_table(
            ("K", "Common"),
            ((k, value) for k, value in comparison["topk_overlap"].items()),
        ),
        "",
        "## Experiment Archetypes",
        "",
    ]
    for k, counts in summary["experiment_archetype_counts"].items():
        lines.append(f"- Top {k}: {counts}")
    lines.extend(["", "## Reference Overlaps", ""])
    for name, overlap in summary["reference_overlaps"].items():
        if overlap is None:
            lines.append(f"- {name}: unavailable")
        else:
            lines.append(
                f"- {name}: {overlap['top100_common']} common top-100 candidates"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--experiment", type=Path, default=DEFAULT_EXPERIMENT)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--reference-a", type=Path, default=DEFAULT_REFERENCE_A)
    parser.add_argument("--reference-b", type=Path, default=DEFAULT_REFERENCE_B)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_comparison(
        repo_path(args.baseline),
        repo_path(args.experiment),
        repo_path(args.candidates),
        repo_path(args.reference_a),
        repo_path(args.reference_b),
    )
    out_json = repo_path(args.out_json)
    out_md = repo_path(args.out_md)
    write_json(out_json, summary)
    out_md.write_text(render_markdown(summary), encoding="utf-8")
    comparison = summary["baseline_vs_experiment"]
    print(
        "Comparison complete: "
        f"top100_common={comparison['top100_common']}, "
        f"spearman={comparison['rank_delta']['spearman']}, "
        f"mean_abs_delta={comparison['rank_delta']['mean_abs_rank_delta']}; "
        f"wrote {out_json} and {out_md}"
    )


if __name__ == "__main__":
    main()
