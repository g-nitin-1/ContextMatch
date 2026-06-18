#!/usr/bin/env python3
"""Evaluate a bounded skill-assessment modifier against frozen Idea 2."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from analysis.candidate_overlay import _matches_any, load_skill_signal_patterns
from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    stream_candidates,
    summary_archetype,
    write_json,
)
from analysis.idea2_scorer import (
    SKILL_WEIGHTS,
    WORLD_CONFIGS,
    assign_ranks,
    clamp,
)


EXPERIMENT_VERSION = "assessment-exp-0.1.0"
DEFAULT_BASE_SCORES = "idea2_scores.csv"
DEFAULT_FROZEN_SUBMISSION = "idea2_submission.csv"
DEFAULT_TOP100 = "skill_assessment_top100.csv"
DEFAULT_SUMMARY = "skill_assessment_summary.json"
DEFAULT_REPORT = "skill_assessment_report.md"

# Assessment evidence is stronger than self-declared skill metadata, but only
# for the same JD-relevant signal families already allowed by the frozen scorer.
ASSESSMENT_WEIGHTS = dict(SKILL_WEIGHTS)
ASSESSMENT_MIN = -0.15
ASSESSMENT_MAX = 0.50


def assessment_quality_multiplier(score: float) -> float:
    """Map a 0-100 assessment to bounded confidence around a neutral midpoint."""
    value = clamp(float(score), 0.0, 100.0)
    if value < 40.0:
        return -0.5 + value / 40.0 * 0.5
    if value < 55.0:
        return (value - 40.0) / 15.0 * 0.25
    if value < 70.0:
        return 0.25 + (value - 55.0) / 15.0 * 0.75
    if value < 80.0:
        return 1.0 + (value - 70.0) / 10.0
    return 2.0 + (value - 80.0) / 20.0 * 0.5


def summarize_assessments(
    assessment_scores: dict[str, Any],
    skill_patterns: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    signal_scores: dict[str, float] = {}
    signal_sources: dict[str, list[str]] = {}
    unmapped = []

    for skill_name, raw_score in sorted(assessment_scores.items()):
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        matched = False
        for signal_id, patterns in skill_patterns.items():
            if not _matches_any(skill_name, patterns):
                continue
            matched = True
            signal_sources.setdefault(signal_id, []).append(skill_name)
            signal_scores[signal_id] = max(signal_scores.get(signal_id, 0.0), score)
        if not matched:
            unmapped.append(skill_name)

    contributions = {
        signal_id: ASSESSMENT_WEIGHTS[signal_id]
        * assessment_quality_multiplier(score)
        for signal_id, score in signal_scores.items()
        if signal_id in ASSESSMENT_WEIGHTS
    }
    total = clamp(sum(contributions.values()), ASSESSMENT_MIN, ASSESSMENT_MAX)
    return {
        "assessment_count": len(assessment_scores),
        "mapped_signal_scores": dict(sorted(signal_scores.items())),
        "mapped_signal_sources": {
            signal_id: sorted(names)
            for signal_id, names in sorted(signal_sources.items())
        },
        "scored_signal_contributions": {
            signal_id: round(value, 6)
            for signal_id, value in sorted(contributions.items())
        },
        "unmapped_assessment_names": sorted(unmapped),
        "assessment_score": round(total, 6),
    }


def load_assessment_index(
    dataset: Path,
    skill_patterns: dict[str, tuple[str, ...]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    index = {}
    candidate_count = 0
    candidates_with_assessments = 0
    candidates_with_scored_signals = 0
    assessment_entries = 0
    scored_signal_counts: Counter[str] = Counter()
    mapped_signal_counts: Counter[str] = Counter()
    score_buckets: Counter[str] = Counter()
    candidate_archetypes: Counter[str] = Counter()
    assessment_archetypes: Counter[str] = Counter()
    scored_assessment_archetypes: Counter[str] = Counter()
    assessment_score_sum_by_archetype: Counter[str] = Counter()

    for candidate in stream_candidates(dataset):
        candidate_count += 1
        profile = candidate["profile"]
        archetype = summary_archetype(
            profile.get("summary", ""),
            profile.get("current_title", ""),
        )
        candidate_archetypes[archetype] += 1
        raw = candidate["redrob_signals"].get("skill_assessment_scores") or {}
        if not raw:
            continue
        candidates_with_assessments += 1
        assessment_archetypes[archetype] += 1
        assessment_entries += len(raw)
        evidence = summarize_assessments(raw, skill_patterns)
        index[candidate["candidate_id"]] = evidence
        mapped_signal_counts.update(evidence["mapped_signal_scores"].keys())
        scored_signal_counts.update(
            evidence["scored_signal_contributions"].keys()
        )
        if evidence["scored_signal_contributions"]:
            candidates_with_scored_signals += 1
            scored_assessment_archetypes[archetype] += 1
            assessment_score_sum_by_archetype[archetype] += evidence[
                "assessment_score"
            ]
        score = evidence["assessment_score"]
        if score < 0:
            score_buckets["negative"] += 1
        elif score == 0:
            score_buckets["neutral"] += 1
        elif score < 0.15:
            score_buckets["weak_positive"] += 1
        elif score < 0.30:
            score_buckets["moderate_positive"] += 1
        else:
            score_buckets["strong_positive"] += 1

    return index, {
        "candidate_count": candidate_count,
        "candidates_with_assessments": candidates_with_assessments,
        "assessment_candidate_share": round(
            candidates_with_assessments / candidate_count, 6
        ),
        "assessment_entries": assessment_entries,
        "candidates_with_scored_signals": candidates_with_scored_signals,
        "scored_signal_candidate_counts": dict(scored_signal_counts.most_common()),
        "mapped_signal_candidate_counts": dict(mapped_signal_counts.most_common()),
        "assessment_score_buckets": dict(score_buckets),
        "assessment_coverage_by_archetype": {
            archetype: {
                "candidates": candidate_archetypes[archetype],
                "with_any_assessment": assessment_archetypes[archetype],
                "with_scored_assessment": scored_assessment_archetypes[archetype],
                "any_assessment_share": round(
                    assessment_archetypes[archetype]
                    / candidate_archetypes[archetype],
                    6,
                ),
                "mean_modifier_when_scored": round(
                    assessment_score_sum_by_archetype[archetype]
                    / scored_assessment_archetypes[archetype],
                    6,
                )
                if scored_assessment_archetypes[archetype]
                else 0.0,
            }
            for archetype in sorted(candidate_archetypes)
        },
    }


def load_base_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def apply_assessment_experiment(
    rows: list[dict[str, Any]],
    assessment_index: dict[str, dict[str, Any]],
) -> None:
    for row in rows:
        evidence = assessment_index.get(row["candidate_id"], {})
        raw_assessment = float(evidence.get("assessment_score", 0.0))
        row["assessment_score_raw"] = round(raw_assessment, 6)
        row["assessment_signal_scores"] = ";".join(
            f"{signal}:{score:g}"
            for signal, score in evidence.get("mapped_signal_scores", {}).items()
            if signal in ASSESSMENT_WEIGHTS
        )
        row["assessment_signal_sources"] = ";".join(
            f"{signal}:{'|'.join(names)}"
            for signal, names in evidence.get("mapped_signal_sources", {}).items()
            if signal in ASSESSMENT_WEIGHTS
        )
        for world in WORLD_CONFIGS:
            key = f"score_{world.name}"
            adjustment = raw_assessment * world.skill_weight
            row[key] = round(float(row[key]) + adjustment, 6)
            row[f"assessment_{world.name}"] = round(adjustment, 6)

        world_scores = [float(row[f"score_{world.name}"]) for world in WORLD_CONFIGS]
        row["mean_score"] = round(sum(world_scores) / len(world_scores), 6)

    assign_ranks(rows, WORLD_CONFIGS)


def frozen_ranks(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row["candidate_id"]: int(row["rank"])
            for row in csv.DictReader(handle)
        }


def top_ids(rows: list[dict[str, Any]], k: int) -> set[str]:
    return {row["candidate_id"] for row in rows[:k]}


def write_top100(
    rows: list[dict[str, Any]],
    path: Path,
    baseline_ranks: dict[str, int],
) -> None:
    fields = [
        "final_rank",
        "candidate_id",
        "mean_score",
        "assessment_score_raw",
        "assessment_signal_scores",
        "assessment_signal_sources",
        "frozen_top100_rank",
        "rank_change_vs_frozen_top100",
        "summary_archetype",
        "fine_static_atom",
        "current_title",
        "current_company",
        "career_compounds",
        "skill_names",
        "integrity_risk_level",
        "honeypot_proxy_rules",
    ]
    output = []
    for row in rows[:100]:
        frozen_rank = baseline_ranks.get(row["candidate_id"])
        item = dict(row)
        item["frozen_top100_rank"] = frozen_rank or ""
        item["rank_change_vs_frozen_top100"] = (
            frozen_rank - int(row["final_rank"]) if frozen_rank else ""
        )
        output.append(item)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output)


def build_summary(
    rows: list[dict[str, Any]],
    coverage: dict[str, Any],
    baseline_ranks: dict[str, int],
) -> dict[str, Any]:
    rows_by_id = {row["candidate_id"]: row for row in rows}
    frozen_sets = {
        k: {candidate_id for candidate_id, rank in baseline_ranks.items() if rank <= k}
        for k in (10, 50, 100)
    }
    overlaps = {}
    for k in (10, 50, 100):
        experiment = top_ids(rows, k)
        frozen = frozen_sets[k]
        overlaps[str(k)] = {
            "intersection_count": len(experiment & frozen),
            "entered": sorted(experiment - frozen),
            "exited": sorted(frozen - experiment),
        }

    top100 = rows[:100]
    top100_entrants = [
        row for row in top100 if row["candidate_id"] not in baseline_ranks
    ]
    return {
        "experiment_version": EXPERIMENT_VERSION,
        "baseline_freeze": "idea2-1.0.0",
        "policy": {
            "assessment_weights": ASSESSMENT_WEIGHTS,
            "assessment_score_bounds": [ASSESSMENT_MIN, ASSESSMENT_MAX],
            "missing_assessment": "neutral",
            "career_compounds_unchanged": True,
            "world_scaling": "multiply by each frozen world's skill_weight",
        },
        "coverage": coverage,
        "top_k_overlap_with_frozen": overlaps,
        "top100_assessment_coverage": {
            "with_scored_assessment": sum(
                float(row["assessment_score_raw"]) != 0.0 for row in top100
            ),
            "strong_positive": sum(
                float(row["assessment_score_raw"]) >= 0.30 for row in top100
            ),
            "negative": sum(
                float(row["assessment_score_raw"]) < 0.0 for row in top100
            ),
        },
        "frozen_top100_assessment_coverage": {
            "with_scored_assessment": sum(
                float(rows_by_id[candidate_id]["assessment_score_raw"]) != 0.0
                for candidate_id in baseline_ranks
            ),
        },
        "top100_integrity": {
            "high_risk": sum(
                row["integrity_risk_level"] == "high" for row in top100
            ),
            "honeypot_proxy": sum(bool(row["honeypot_proxy_rules"]) for row in top100),
        },
        "top100_entrant_audit": {
            "count": len(top100_entrants),
            "archetypes": dict(
                Counter(row["summary_archetype"] for row in top100_entrants)
            ),
            "without_career_compounds": sum(
                not row["career_compounds"] for row in top100_entrants
            ),
            "without_scored_assessment": sum(
                float(row["assessment_score_raw"]) == 0.0
                for row in top100_entrants
            ),
        },
        "top20": [
            {
                "rank": row["final_rank"],
                "candidate_id": row["candidate_id"],
                "mean_score": row["mean_score"],
                "assessment_score_raw": row["assessment_score_raw"],
                "assessment_signal_scores": row["assessment_signal_scores"],
                "frozen_top100_rank": baseline_ranks.get(row["candidate_id"]),
            }
            for row in rows[:20]
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    coverage = summary["coverage"]
    overlap = summary["top_k_overlap_with_frozen"]
    lines = [
        "# Skill Assessment Experiment",
        "",
        f"- Experiment: `{summary['experiment_version']}`",
        f"- Baseline: `{summary['baseline_freeze']}`",
        "- Frozen Idea 2 files and manifest were not modified.",
        "",
        "## Policy",
        "",
        "- Missing assessments are neutral.",
        "- Only assessments mapping to existing JD skill signals affect scores.",
        "- Scores of 80+ outweigh the maximum proficiency-and-duration bonus for "
        "one self-declared skill signal.",
        "- Assessment influence is capped and cannot create production career "
        "signals or compounds.",
        "- Assessments are class-conditional in this synthetic dataset. This "
        "experiment therefore tests an informative but potentially "
        "double-counted signal.",
        "",
        "## Coverage",
        "",
        f"- Candidates: {coverage['candidate_count']:,}",
        f"- Candidates with any assessment: "
        f"{coverage['candidates_with_assessments']:,} "
        f"({coverage['assessment_candidate_share']:.2%})",
        f"- Assessment entries: {coverage['assessment_entries']:,}",
        f"- Candidates with at least one scored JD signal: "
        f"{coverage['candidates_with_scored_signals']:,}",
        "",
        "Assessment coverage is class-conditional, so this modifier can change "
        "relative positions even though missing values are individually neutral. "
        "Use the per-archetype coverage in the JSON summary when interpreting "
        "rank changes.",
        "",
        "## Ranking Change",
        "",
    ]
    for k in ("10", "50", "100"):
        values = overlap[k]
        lines.append(
            f"- Top {k}: {values['intersection_count']}/{k} retained; "
            f"{len(values['entered'])} entered and {len(values['exited'])} exited."
        )
    lines.extend(
        [
            "",
            "## Safeguards",
            "",
            f"- Top-100 high-risk candidates: "
            f"{summary['top100_integrity']['high_risk']}",
            f"- Top-100 honeypot proxies: "
            f"{summary['top100_integrity']['honeypot_proxy']}",
            f"- New top-100 candidates without career compounds: "
            f"{summary['top100_entrant_audit']['without_career_compounds']}",
            "",
            "## Interpretation",
            "",
            "This experiment tests whether platform assessments improve the "
            "skill-confidence layer. It does not alter the frozen Idea 2 result "
            "and does not establish hidden-label accuracy. Because assessment "
            "coverage rises sharply with the reconstructed profile family, the "
            "absolute modifier may partially reward class a second time. The "
            "result should be compared with Idea 1 and a class-normalized "
            "assessment variant before adoption.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_experiment(
    dataset: Path,
    output_dir: Path,
    base_scores_path: Path | None = None,
    frozen_submission_path: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    skill_patterns = load_skill_signal_patterns()
    assessment_index, coverage = load_assessment_index(dataset, skill_patterns)
    rows = load_base_rows(base_scores_path or output_dir / DEFAULT_BASE_SCORES)
    apply_assessment_experiment(rows, assessment_index)
    baseline = frozen_ranks(
        frozen_submission_path or output_dir / DEFAULT_FROZEN_SUBMISSION
    )

    top100_path = output_dir / DEFAULT_TOP100
    write_top100(rows, top100_path, baseline)
    summary = build_summary(rows, coverage, baseline)
    summary["top100_path"] = str(top100_path)
    write_json(output_dir / DEFAULT_SUMMARY, summary)
    write_report(output_dir / DEFAULT_REPORT, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-scores", type=Path, default=None)
    parser.add_argument("--frozen-submission", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_experiment(
        args.candidates,
        args.output_dir,
        args.base_scores,
        args.frozen_submission,
    )
    overlap = summary["top_k_overlap_with_frozen"]
    print(
        "Assessment experiment complete: "
        f"top-10 overlap {overlap['10']['intersection_count']}/10, "
        f"top-100 overlap {overlap['100']['intersection_count']}/100"
    )


if __name__ == "__main__":
    main()
