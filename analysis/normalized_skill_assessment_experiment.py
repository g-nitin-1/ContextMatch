#!/usr/bin/env python3
"""Compare class-normalized skill assessments with frozen and absolute variants."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any

from analysis.candidate_overlay import load_skill_signal_patterns
from analysis.common import DEFAULT_DATASET, DEFAULT_OUTPUT_DIR, write_json
from analysis.idea2_scorer import WORLD_CONFIGS, assign_ranks, clamp
from analysis.skill_assessment_experiment import (
    ASSESSMENT_WEIGHTS,
    DEFAULT_BASE_SCORES,
    DEFAULT_FROZEN_SUBMISSION,
    frozen_ranks,
    load_assessment_index,
    load_base_rows,
)


EXPERIMENT_VERSION = "assessment-normalized-exp-0.2.0"
DEFAULT_ABSOLUTE_TOP100 = "skill_assessment_top100.csv"
DEFAULT_TOP100 = "skill_assessment_normalized_top100.csv"
DEFAULT_SUMMARY = "skill_assessment_normalized_summary.json"
DEFAULT_REPORT = "skill_assessment_normalized_report.md"

NORMALIZED_MIN = -0.15
NORMALIZED_MAX = 0.30
MIN_GROUP_SIZE = 20
ASSESSMENT_Z_WEIGHT = 1.75
SIGNAL_Z_MIN = -1.5
SIGNAL_Z_MAX = 2.0


def normalization_group(archetype: str) -> str:
    if archetype in {"senior_explicit_ai", "senior_plain_language"}:
        return "senior_pooled"
    if archetype in {"general_professional", "direct_occupation"}:
        return "tail_pooled"
    return archetype


def build_normalization_stats(
    rows: list[dict[str, Any]],
    assessment_index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, float | int]]:
    values_by_group: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        evidence = assessment_index.get(row["candidate_id"])
        if not evidence:
            continue
        group = normalization_group(str(row["summary_archetype"]))
        values_by_group[group].extend(
            float(score)
            for signal, score in evidence.get("mapped_signal_scores", {}).items()
            if signal in ASSESSMENT_WEIGHTS
        )

    stats = {}
    for group, values in sorted(values_by_group.items()):
        if len(values) < MIN_GROUP_SIZE:
            raise ValueError(
                f"normalization group {group} has only {len(values)} observations"
            )
        deviation = pstdev(values)
        if deviation <= 0:
            raise ValueError(f"normalization group {group} has zero variance")
        stats[group] = {
            "count": len(values),
            "mean": round(fmean(values), 9),
            "stddev": round(deviation, 9),
            "minimum": round(min(values), 6),
            "maximum": round(max(values), 6),
        }
    return stats


def normalized_signal_assessment_score(
    score: float,
    signal_weight: float,
    group_stats: dict[str, float | int],
) -> float:
    centered = float(score) - float(group_stats["mean"])
    z_score = centered / float(group_stats["stddev"])
    return signal_weight * clamp(z_score, SIGNAL_Z_MIN, SIGNAL_Z_MAX) * (
        ASSESSMENT_Z_WEIGHT
    )


def normalized_assessment_score(
    signal_scores: dict[str, Any],
    group_stats: dict[str, float | int],
) -> float:
    total = sum(
        normalized_signal_assessment_score(
            float(score),
            ASSESSMENT_WEIGHTS[signal],
            group_stats,
        )
        for signal, score in signal_scores.items()
        if signal in ASSESSMENT_WEIGHTS
    )
    return round(clamp(total, NORMALIZED_MIN, NORMALIZED_MAX), 6)


def apply_normalized_experiment(
    rows: list[dict[str, Any]],
    assessment_index: dict[str, dict[str, Any]],
    stats: dict[str, dict[str, float | int]],
) -> None:
    for row in rows:
        evidence = assessment_index.get(row["candidate_id"], {})
        group = normalization_group(str(row["summary_archetype"]))
        signal_scores = evidence.get("mapped_signal_scores", {})
        has_scored_assessment = any(
            signal in ASSESSMENT_WEIGHTS for signal in signal_scores
        )
        raw_score = float(evidence.get("assessment_score", 0.0))
        normalized = (
            normalized_assessment_score(signal_scores, stats[group])
            if has_scored_assessment
            else 0.0
        )

        row["assessment_group"] = group
        row["assessment_score_raw"] = round(raw_score, 6)
        row["assessment_score_normalized"] = normalized
        row["assessment_signal_scores"] = ";".join(
            f"{signal}:{score:g}"
            for signal, score in evidence.get("mapped_signal_scores", {}).items()
            if signal in ASSESSMENT_WEIGHTS
        )
        for world in WORLD_CONFIGS:
            adjustment = normalized * world.skill_weight
            row[f"score_{world.name}"] = round(
                float(row[f"score_{world.name}"]) + adjustment,
                6,
            )
            row[f"assessment_normalized_{world.name}"] = round(adjustment, 6)

        world_scores = [float(row[f"score_{world.name}"]) for world in WORLD_CONFIGS]
        row["mean_score"] = round(sum(world_scores) / len(world_scores), 6)

    assign_ranks(rows, WORLD_CONFIGS)


def load_ranked_top(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rank_field = "final_rank" if "final_rank" in rows[0] else "rank"
    return {row["candidate_id"]: int(row[rank_field]) for row in rows}


def top_set(ranks: dict[str, int], k: int) -> set[str]:
    return {candidate_id for candidate_id, rank in ranks.items() if rank <= k}


def overlap_summary(
    left: dict[str, int],
    right: dict[str, int],
    k: int,
) -> dict[str, Any]:
    left_set = top_set(left, k)
    right_set = top_set(right, k)
    return {
        "intersection_count": len(left_set & right_set),
        "entered": sorted(left_set - right_set),
        "exited": sorted(right_set - left_set),
    }


def write_top100(
    rows: list[dict[str, Any]],
    path: Path,
    frozen: dict[str, int],
    absolute: dict[str, int],
) -> None:
    fields = [
        "final_rank",
        "candidate_id",
        "mean_score",
        "assessment_group",
        "assessment_score_raw",
        "assessment_score_normalized",
        "assessment_signal_scores",
        "frozen_top100_rank",
        "absolute_top100_rank",
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
        item = dict(row)
        item["frozen_top100_rank"] = frozen.get(row["candidate_id"], "")
        item["absolute_top100_rank"] = absolute.get(row["candidate_id"], "")
        output.append(item)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output)


def build_summary(
    rows: list[dict[str, Any]],
    stats: dict[str, dict[str, float | int]],
    coverage: dict[str, Any],
    frozen: dict[str, int],
    absolute: dict[str, int],
) -> dict[str, Any]:
    normalized = {row["candidate_id"]: int(row["final_rank"]) for row in rows[:100]}
    top100 = rows[:100]
    frozen_entrants = [
        row for row in top100 if row["candidate_id"] not in frozen
    ]
    absolute_entrants = [
        row for row in top100 if row["candidate_id"] not in absolute
    ]

    return {
        "experiment_version": EXPERIMENT_VERSION,
        "baselines": {
            "frozen": "idea2-1.0.0",
            "absolute_assessment": "assessment-exp-0.1.0",
        },
        "policy": {
            "normalization": (
                "each numeric assessment score is normalized within reconstructed "
                "archetype before signal-weighted aggregation; senior cohorts "
                "pooled and general/direct occupations pooled"
            ),
            "missing_assessment": "neutral",
            "weight_per_standard_deviation": ASSESSMENT_Z_WEIGHT,
            "signal_z_bounds": [SIGNAL_Z_MIN, SIGNAL_Z_MAX],
            "score_bounds": [NORMALIZED_MIN, NORMALIZED_MAX],
            "minimum_group_size": MIN_GROUP_SIZE,
            "career_compounds_unchanged": True,
        },
        "normalization_stats": stats,
        "coverage": coverage,
        "overlap": {
            "normalized_vs_frozen": {
                str(k): overlap_summary(normalized, frozen, k)
                for k in (10, 50, 100)
            },
            "normalized_vs_absolute": {
                str(k): overlap_summary(normalized, absolute, k)
                for k in (10, 50, 100)
            },
            "three_way_intersection": {
                str(k): len(
                    top_set(normalized, k)
                    & top_set(frozen, k)
                    & top_set(absolute, k)
                )
                for k in (10, 50, 100)
            },
        },
        "top100_integrity": {
            "high_risk": sum(
                row["integrity_risk_level"] == "high" for row in top100
            ),
            "honeypot_proxy": sum(bool(row["honeypot_proxy_rules"]) for row in top100),
        },
        "top100_modifier_counts": {
            "positive": sum(
                float(row["assessment_score_normalized"]) > 0 for row in top100
            ),
            "negative": sum(
                float(row["assessment_score_normalized"]) < 0 for row in top100
            ),
            "neutral": sum(
                float(row["assessment_score_normalized"]) == 0 for row in top100
            ),
        },
        "entrant_audit": {
            "versus_frozen": {
                "count": len(frozen_entrants),
                "archetypes": dict(
                    Counter(row["summary_archetype"] for row in frozen_entrants)
                ),
                "without_career_compounds": sum(
                    not row["career_compounds"] for row in frozen_entrants
                ),
            },
            "versus_absolute": {
                "count": len(absolute_entrants),
                "archetypes": dict(
                    Counter(row["summary_archetype"] for row in absolute_entrants)
                ),
                "without_career_compounds": sum(
                    not row["career_compounds"] for row in absolute_entrants
                ),
            },
        },
        "top20": [
            {
                "rank": row["final_rank"],
                "candidate_id": row["candidate_id"],
                "assessment_group": row["assessment_group"],
                "assessment_score_raw": row["assessment_score_raw"],
                "assessment_score_normalized": row[
                    "assessment_score_normalized"
                ],
                "frozen_rank": frozen.get(row["candidate_id"]),
                "absolute_rank": absolute.get(row["candidate_id"]),
            }
            for row in rows[:20]
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    overlaps = summary["overlap"]
    lines = [
        "# Class-Normalized Skill Assessment Experiment",
        "",
        f"- Experiment: `{summary['experiment_version']}`",
        "- Frozen Idea 2 and the absolute assessment experiment remain unchanged.",
        "",
        "## Policy",
        "",
        "- Each relevant numeric assessment score is centered and scaled within "
        "peer archetype before signal-weighted aggregation.",
        "- The two senior archetypes share one pooled baseline; general "
        "professional and direct occupations share a tail baseline.",
        "- Candidates without a relevant assessment remain exactly neutral.",
        f"- A one-standard-deviation result contributes the signal's frozen "
        f"skill weight times `{summary['policy']['weight_per_standard_deviation']}` "
        "before world scaling.",
        f"- The raw normalized modifier is capped at "
        f"`{summary['policy']['score_bounds']}`.",
        "",
        "## Ranking Comparison",
        "",
    ]
    for k in ("10", "50", "100"):
        frozen = overlaps["normalized_vs_frozen"][k]
        absolute = overlaps["normalized_vs_absolute"][k]
        lines.append(
            f"- Top {k}: {frozen['intersection_count']}/{k} overlap with frozen; "
            f"{absolute['intersection_count']}/{k} overlap with absolute "
            "assessment."
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
            f"- New candidates versus frozen without career compounds: "
            f"{summary['entrant_audit']['versus_frozen']['without_career_compounds']}",
            "",
            "## Interpretation",
            "",
            "This variant removes the average assessment-score advantage "
            "associated with each reconstructed profile family. It normalizes "
            "numeric scores rather than the aggregate modifier, so one excellent "
            "assessment is not penalized merely because the candidate completed "
            "fewer assessments. It remains a post-freeze proxy experiment rather "
            "than hidden-label validation.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_experiment(
    dataset: Path,
    output_dir: Path,
    base_scores_path: Path | None = None,
    frozen_submission_path: Path | None = None,
    absolute_top100_path: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assessment_index, coverage = load_assessment_index(
        dataset,
        load_skill_signal_patterns(),
    )
    rows = load_base_rows(base_scores_path or output_dir / DEFAULT_BASE_SCORES)
    stats = build_normalization_stats(rows, assessment_index)
    apply_normalized_experiment(rows, assessment_index, stats)
    frozen = frozen_ranks(
        frozen_submission_path or output_dir / DEFAULT_FROZEN_SUBMISSION
    )
    absolute = load_ranked_top(
        absolute_top100_path or output_dir / DEFAULT_ABSOLUTE_TOP100
    )

    top100_path = output_dir / DEFAULT_TOP100
    write_top100(rows, top100_path, frozen, absolute)
    summary = build_summary(rows, stats, coverage, frozen, absolute)
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
    parser.add_argument("--absolute-top100", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_experiment(
        args.candidates,
        args.output_dir,
        args.base_scores,
        args.frozen_submission,
        args.absolute_top100,
    )
    overlap = summary["overlap"]
    print(
        "Normalized assessment experiment complete: "
        f"top-10 overlap frozen "
        f"{overlap['normalized_vs_frozen']['10']['intersection_count']}/10, "
        f"absolute "
        f"{overlap['normalized_vs_absolute']['10']['intersection_count']}/10"
    )


if __name__ == "__main__":
    main()
