#!/usr/bin/env python3
"""Score a submission against local proxy truth assumptions.

This is a local diagnostic only. It uses Idea 2 proxy tiers and optional
reference top-100 files to estimate the competition composite under several
truth assumptions.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

from analysis.common import DEFAULT_OUTPUT_DIR, REPO_ROOT, markdown_table, write_json


DEFAULT_SUBMISSION = DEFAULT_OUTPUT_DIR / "solution_ranker_submission.csv"
DEFAULT_IDEA1 = REPO_ROOT / "idea1_top100.csv"
DEFAULT_IDEA2_SUBMISSION = DEFAULT_OUTPUT_DIR / "idea2_submission.csv"
DEFAULT_IDEA2_SCORES = DEFAULT_OUTPUT_DIR / "idea2_scores.csv"
DEFAULT_OUT_JSON = DEFAULT_OUTPUT_DIR / "proxy_composite_score.json"
DEFAULT_OUT_MD = DEFAULT_OUTPUT_DIR / "proxy_composite_score.md"
GAIN_SCHEMES = ("exp", "linear")


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def read_submission_ids(path: Path, limit: int = 100) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        key = "candidate_id" if "candidate_id" in reader.fieldnames else reader.fieldnames[0]
        return [row[key] for row in reader if row.get(key)][:limit]


def load_idea2_tiers(path: Path) -> dict[str, float]:
    tiers = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            tiers[row["candidate_id"]] = float(row["mean_base_tier"])
    return tiers


def gain(relevance: float, scheme: str) -> float:
    if scheme == "exp":
        return 2**relevance - 1
    if scheme == "linear":
        return relevance
    raise ValueError(f"unknown gain scheme: {scheme}")


def dcg(prediction: list[str], relevance: dict[str, float], k: int, scheme: str) -> float:
    total = 0.0
    for rank, candidate_id in enumerate(prediction[:k], 1):
        total += gain(relevance.get(candidate_id, 0.0), scheme) / math.log2(rank + 1)
    return total


def ndcg(prediction: list[str], relevance: dict[str, float], k: int, scheme: str) -> float:
    ideal_ids = sorted(relevance, key=lambda item: (-relevance[item], item))[:k]
    ideal = dcg(ideal_ids, relevance, k, scheme)
    return dcg(prediction, relevance, k, scheme) / ideal if ideal else 0.0


def average_precision(prediction: list[str], relevant: set[str], k: int = 100) -> float:
    hits = 0
    total = 0.0
    for rank, candidate_id in enumerate(prediction[:k], 1):
        if candidate_id in relevant:
            hits += 1
            total += hits / rank
    denominator = min(k, len(relevant))
    return total / denominator if denominator else 0.0


def precision_at(prediction: list[str], relevant: set[str], k: int = 10) -> float:
    return sum(candidate_id in relevant for candidate_id in prediction[:k]) / k


def composite(ndcg10: float, ndcg50: float, map100: float, p10: float) -> float:
    return 0.50 * ndcg10 + 0.30 * ndcg50 + 0.15 * map100 + 0.05 * p10


def score_against_truth(
    prediction: list[str],
    relevance: dict[str, float],
    relevant_threshold: float = 3.0,
) -> dict[str, Any]:
    relevant = {
        candidate_id
        for candidate_id, tier in relevance.items()
        if tier >= relevant_threshold
    }
    rows = {}
    for scheme in GAIN_SCHEMES:
        ndcg10 = ndcg(prediction, relevance, 10, scheme)
        ndcg50 = ndcg(prediction, relevance, 50, scheme)
        map100 = average_precision(prediction, relevant, 100)
        p10 = precision_at(prediction, relevant, 10)
        rows[scheme] = {
            "NDCG@10": round(ndcg10, 6),
            "NDCG@50": round(ndcg50, 6),
            "MAP@100": round(map100, 6),
            "P@10": round(p10, 6),
            "composite": round(composite(ndcg10, ndcg50, map100, p10), 6),
        }
    return {
        "label_count": len(relevance),
        "relevant_count": len(relevant),
        "submission_labeled_overlap": len(set(prediction) & set(relevance)),
        "submission_relevant_count": sum(candidate_id in relevant for candidate_id in prediction),
        "scores": rows,
    }


def build_truth_sets(
    idea1_path: Path,
    idea2_submission_path: Path,
    idea2_scores_path: Path,
) -> dict[str, dict[str, float]]:
    tiers = load_idea2_tiers(idea2_scores_path)
    idea1_ids = read_submission_ids(idea1_path)
    idea2_top_ids = read_submission_ids(idea2_submission_path)
    return {
        "idea1_top100_truth__graded_by_idea2_tiers": {
            candidate_id: tiers.get(candidate_id, 0.0)
            for candidate_id in idea1_ids
        },
        "idea2_full_tiers_truth": tiers,
        "idea2_top100_truth__graded_by_idea2_tiers": {
            candidate_id: tiers.get(candidate_id, 0.0)
            for candidate_id in idea2_top_ids
        },
    }


def build_report(
    submission_path: Path,
    idea1_path: Path,
    idea2_submission_path: Path,
    idea2_scores_path: Path,
) -> dict[str, Any]:
    prediction = read_submission_ids(submission_path)
    truth_sets = build_truth_sets(idea1_path, idea2_submission_path, idea2_scores_path)
    return {
        "audit_scope": "local_proxy_only",
        "submission": str(submission_path),
        "formula": (
            "0.50*NDCG@10 + 0.30*NDCG@50 + 0.15*MAP@100 + 0.05*P@10"
        ),
        "relevant_threshold": 3.0,
        "truth_sets": {
            name: score_against_truth(prediction, relevance)
            for name, relevance in truth_sets.items()
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    rows = []
    for truth_name, payload in report["truth_sets"].items():
        for scheme, scores in payload["scores"].items():
            rows.append(
                (
                    truth_name,
                    scheme,
                    f"{scores['NDCG@10']:.3f}",
                    f"{scores['NDCG@50']:.3f}",
                    f"{scores['MAP@100']:.3f}",
                    f"{scores['P@10']:.3f}",
                    f"{scores['composite']:.3f}",
                )
            )
    return "\n".join(
        [
            "# Proxy Composite Score",
            "",
            "Local proxy-only estimate. This is not an official score.",
            "",
            f"- Submission: `{report['submission']}`",
            f"- Formula: `{report['formula']}`",
            "",
            markdown_table(
                (
                    "Truth assumption",
                    "Gain",
                    "NDCG@10",
                    "NDCG@50",
                    "MAP@100",
                    "P@10",
                    "Composite",
                ),
                rows,
            ),
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, default=DEFAULT_SUBMISSION)
    parser.add_argument("--idea1", type=Path, default=DEFAULT_IDEA1)
    parser.add_argument("--idea2-submission", type=Path, default=DEFAULT_IDEA2_SUBMISSION)
    parser.add_argument("--idea2-scores", type=Path, default=DEFAULT_IDEA2_SCORES)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(
        repo_path(args.submission),
        repo_path(args.idea1),
        repo_path(args.idea2_submission),
        repo_path(args.idea2_scores),
    )
    out_json = repo_path(args.out_json)
    out_md = repo_path(args.out_md)
    write_json(out_json, report)
    out_md.write_text(render_markdown(report), encoding="utf-8")
    composites = [
        payload["scores"][scheme]["composite"]
        for payload in report["truth_sets"].values()
        for scheme in GAIN_SCHEMES
    ]
    print(
        "Proxy composite scoring complete: "
        f"min={min(composites):.3f}, max={max(composites):.3f}; "
        f"wrote {out_json} and {out_md}"
    )


if __name__ == "__main__":
    main()
