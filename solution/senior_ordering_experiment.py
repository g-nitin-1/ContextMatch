#!/usr/bin/env python3
"""Standalone senior-ordering experiment.

This keeps the same eligibility, evidence floor, integrity gates, and feature
artifact as the main ranker. It only adds a bounded JD-derived ordering modifier
for candidates whose existing seniority alignment is already positive.
"""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path
from typing import Any

from analysis.common import DEFAULT_DATASET, DEFAULT_OUTPUT_DIR, REPO_ROOT
from analysis.integrity_checks import DEFAULT_KNOWLEDGE_BASE
from solution.candidate_features import DEFAULT_AS_OF
from solution.jd_parser import parse_jd
from solution.precompute import DEFAULT_FEATURES
from solution.ranker import (
    DEFAULT_JD,
    DEFAULT_OUT,
    RankRun,
    ScoreBreakdown,
    iter_jsonl,
    score_overlay,
    seniority_ordering_modifier as senior_ordering_modifier,
    write_submission,
)
from solution.requirement_spec import RequirementSpec, load_spec


DEFAULT_EXPERIMENT_OUT = DEFAULT_OUTPUT_DIR / "solution_senior_ordering_experiment.csv"
DEFAULT_EXPERIMENT_REPORT = (
    DEFAULT_OUTPUT_DIR / "solution_senior_ordering_experiment_summary.json"
)
DEFAULT_ORDERING_CAP = 0.4


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def score_with_senior_ordering(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    cap: float = DEFAULT_ORDERING_CAP,
) -> ScoreBreakdown:
    return score_overlay(
        spec,
        overlay,
        seniority_ordering_cap=cap,
        role_title_ordering_cap=0.0,
    )


def rank_with_senior_ordering(
    spec: RequirementSpec,
    features_path: Path,
    cap: float = DEFAULT_ORDERING_CAP,
    limit: int = 100,
) -> tuple[list[ScoreBreakdown], dict[str, Any]]:
    started = time.perf_counter()
    eligible: list[ScoreBreakdown] = []
    candidate_count = 0
    blocked_count = 0
    boosted_count = 0
    modifier_sum = 0.0
    modifier_max = 0.0
    for overlay in iter_jsonl(features_path):
        candidate_count += 1
        row = score_with_senior_ordering(spec, overlay, cap)
        if row.blocked:
            blocked_count += 1
            continue
        modifier = senior_ordering_modifier(spec, overlay, cap)
        if modifier > 0:
            boosted_count += 1
            modifier_sum += modifier
            modifier_max = max(modifier_max, modifier)
        eligible.append(row)
    if len(eligible) < limit:
        raise ValueError(f"need at least {limit} eligible candidates")
    eligible.sort(key=lambda row: (-row.score, row.candidate_id))
    elapsed = time.perf_counter() - started
    report = {
        "experiment": "senior-ordering-0.1.0",
        "candidate_count": candidate_count,
        "eligible_count": len(eligible),
        "blocked_count": blocked_count,
        "ordering_cap": cap,
        "boosted_eligible_count": boosted_count,
        "mean_positive_modifier": (
            round(modifier_sum / boosted_count, 6) if boosted_count else 0.0
        ),
        "max_modifier": round(modifier_max, 6),
        "elapsed_seconds": round(elapsed, 3),
        "max_rss_mb": round(peak_rss_mb(), 1),
    }
    return eligible[:limit], report


def add_baseline_overlap(
    report: dict[str, Any],
    rows: list[ScoreBreakdown],
    baseline_path: Path,
) -> None:
    if not baseline_path.is_file():
        return
    import csv

    with baseline_path.open("r", encoding="utf-8", newline="") as handle:
        baseline_ids = {
            row["candidate_id"] for row in csv.DictReader(handle) if row.get("candidate_id")
        }
    experiment_ids = {row.candidate_id for row in rows}
    report["baseline_overlap"] = {
        "baseline": str(baseline_path),
        "top100_common": len(experiment_ids & baseline_ids),
        "experiment_only": len(experiment_ids - baseline_ids),
        "baseline_only": len(baseline_ids - experiment_ids),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jd", type=Path, default=DEFAULT_JD)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--out", type=Path, default=DEFAULT_EXPERIMENT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_EXPERIMENT_REPORT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--ordering-cap", type=float, default=DEFAULT_ORDERING_CAP)
    parser.add_argument("--limit", type=int, default=100)
    # Kept for CLI symmetry with the main ranker; not used in feature mode.
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--knowledge-base", type=Path, default=DEFAULT_KNOWLEDGE_BASE)
    parser.add_argument("--analysis-as-of", default=DEFAULT_AS_OF.isoformat())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_spec(repo_path(args.spec)) if args.spec else parse_jd(repo_path(args.jd))
    out_path = repo_path(args.out)
    rows, report = rank_with_senior_ordering(
        spec,
        repo_path(args.features),
        args.ordering_cap,
        args.limit,
    )
    write_submission(rows, out_path)
    report.update(
        {
            "role_title": spec.role_title,
            "inputs": {"features": str(repo_path(args.features))},
            "outputs": {"submission": str(out_path)},
        }
    )
    add_baseline_overlap(report, rows, repo_path(args.baseline))
    report_path = repo_path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Senior-ordering experiment ranked {report['candidate_count']:,} candidates "
        f"({report['eligible_count']:,} eligible, {report['blocked_count']:,} blocked) "
        f"in {report['elapsed_seconds']:.3f}s; "
        f"maximum memory used {report['max_rss_mb']:.1f} MB; "
        f"cap={args.ordering_cap}; wrote {out_path}"
    )


if __name__ == "__main__":
    main()
