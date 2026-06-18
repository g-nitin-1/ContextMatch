#!/usr/bin/env python3
"""Find strict static-profile matches with contrasting behavioral signals."""

from __future__ import annotations

import argparse
import csv
import itertools
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    career_static_signature,
    education_signature,
    markdown_table,
    percentile,
    stable_id,
    stream_candidates,
    summary_archetype,
    write_json,
)


REFERENCE_DATE = date(2026, 6, 1)
FEATURE_RANGES = {
    "inactive_days": 240.0,
    "open_to_work": 1.0,
    "response_rate": 1.0,
    "response_time_hours": 280.0,
    "notice_period_days": 180.0,
    "willing_to_relocate": 1.0,
    "saved_by_recruiters": 80.0,
    "interview_completion": 1.0,
}


def behavior_vector(candidate: dict[str, Any]) -> dict[str, float]:
    signals = candidate["redrob_signals"]
    last_active = date.fromisoformat(signals["last_active_date"])
    return {
        "inactive_days": float((REFERENCE_DATE - last_active).days),
        "open_to_work": float(bool(signals["open_to_work_flag"])),
        "response_rate": float(signals["recruiter_response_rate"]),
        "response_time_hours": float(signals["avg_response_time_hours"]),
        "notice_period_days": float(signals["notice_period_days"]),
        "willing_to_relocate": float(bool(signals["willing_to_relocate"])),
        "saved_by_recruiters": float(signals["saved_by_recruiters_30d"]),
        "interview_completion": float(signals["interview_completion_rate"]),
    }


def behavior_distance(left: dict[str, float], right: dict[str, float]) -> float:
    distances = []
    for feature, scale in FEATURE_RANGES.items():
        distances.append(min(abs(left[feature] - right[feature]) / scale, 1.0))
    return sum(distances) / len(distances)


def contrast_flags(left: dict[str, float], right: dict[str, float]) -> list[str]:
    flags = []
    inactive_low = min(left["inactive_days"], right["inactive_days"])
    inactive_high = max(left["inactive_days"], right["inactive_days"])
    if inactive_low <= 60 and inactive_high >= 120:
        flags.append("recent_vs_inactive")
    if left["open_to_work"] != right["open_to_work"]:
        flags.append("open_to_work")
    if abs(left["response_rate"] - right["response_rate"]) >= 0.35:
        flags.append("response_rate")
    if abs(left["response_time_hours"] - right["response_time_hours"]) >= 96:
        flags.append("response_time")
    if abs(left["notice_period_days"] - right["notice_period_days"]) >= 60:
        flags.append("notice_period")
    if left["willing_to_relocate"] != right["willing_to_relocate"]:
        flags.append("relocation")
    if abs(left["saved_by_recruiters"] - right["saved_by_recruiters"]) >= 20:
        flags.append("recruiter_saves")
    if abs(left["interview_completion"] - right["interview_completion"]) >= 0.25:
        flags.append("interview_completion")
    return flags


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    profile = candidate["profile"]
    return {
        "candidate_id": candidate["candidate_id"],
        "summary_archetype": summary_archetype(
            profile.get("summary", ""), profile.get("current_title", "")
        ),
        "current_title": profile.get("current_title", ""),
        "years_of_experience": profile.get("years_of_experience", 0.0),
        "career_signature": career_static_signature(candidate),
        "education_signature": education_signature(candidate),
        "behavior": behavior_vector(candidate),
    }


def analyze(dataset: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    archetype_behavior: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    record_count = 0
    for candidate in stream_candidates(dataset):
        record_count += 1
        compact = compact_candidate(candidate)
        groups[compact["career_signature"]].append(compact)
        for feature, value in compact["behavior"].items():
            archetype_behavior[compact["summary_archetype"]][feature].append(value)

    career_matched_groups = {
        signature: candidates
        for signature, candidates in groups.items()
        if len(candidates) >= 2
    }
    group_size_distribution = Counter(
        len(candidates) for candidates in career_matched_groups.values()
    )
    strict_group_count = 0
    strict_candidate_count = 0
    relevant_archetypes = {
        "generic_ml",
        "applied_ml",
        "senior_explicit_ai",
        "senior_plain_language",
    }
    archetype_group_counts: Counter[str] = Counter()
    relevant_group_counts: Counter[str] = Counter()
    pair_rows = []
    signal_differences: dict[str, list[float]] = defaultdict(list)
    contrast_counts: Counter[str] = Counter()

    for signature, candidates in career_matched_groups.items():
        archetype = candidates[0]["summary_archetype"]
        archetype_group_counts[archetype] += 1
        if archetype in relevant_archetypes:
            relevant_group_counts[archetype] += 1

        education_groups: dict[tuple[Any, ...], int] = Counter(
            candidate["education_signature"] for candidate in candidates
        )
        strict_sizes = [size for size in education_groups.values() if size >= 2]
        strict_group_count += len(strict_sizes)
        strict_candidate_count += sum(strict_sizes)

        best_pair = None
        best_distance = -1.0
        for left, right in itertools.combinations(candidates, 2):
            distance = behavior_distance(left["behavior"], right["behavior"])
            if distance > best_distance:
                best_pair = (left, right)
                best_distance = distance
        if best_pair is None:
            continue
        left, right = best_pair
        flags = contrast_flags(left["behavior"], right["behavior"])
        for flag in flags:
            contrast_counts[flag] += 1
        differences = {
            feature: abs(left["behavior"][feature] - right["behavior"][feature])
            for feature in FEATURE_RANGES
        }
        for feature, difference in differences.items():
            signal_differences[feature].append(difference)
        pair_rows.append(
            {
                "static_signature_id": stable_id(signature, "static"),
                "group_size": len(candidates),
                "education_match": (
                    left["education_signature"] == right["education_signature"]
                ),
                "summary_archetype": left["summary_archetype"],
                "current_title": left["current_title"],
                "experience_bucket": signature[2],
                "candidate_a": left["candidate_id"],
                "candidate_b": right["candidate_id"],
                "behavior_distance": best_distance,
                "contrast_flags": ";".join(flags),
                **{f"a_{key}": value for key, value in left["behavior"].items()},
                **{f"b_{key}": value for key, value in right["behavior"].items()},
                **{f"delta_{key}": value for key, value in differences.items()},
            }
        )

    pair_rows.sort(
        key=lambda row: (
            -float(row["behavior_distance"]),
            row["candidate_a"],
            row["candidate_b"],
        )
    )
    csv_path = output_dir / "behavioral_twins.csv"
    if pair_rows:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
            writer.writeheader()
            writer.writerows(pair_rows)

    difference_summary = {}
    for feature, values in sorted(signal_differences.items()):
        ordered = sorted(values)
        difference_summary[feature] = {
            "median": median(ordered),
            "p90": percentile(ordered, 0.90),
            "max": ordered[-1],
        }
    high_contrast_pairs = sum(
        bool(row["contrast_flags"]) for row in pair_rows
    )
    relevant_pair_rows = [
        row for row in pair_rows if row["summary_archetype"] in relevant_archetypes
    ]
    relevant_contrast_counts: Counter[str] = Counter()
    relevant_signal_differences: dict[str, list[float]] = defaultdict(list)
    for row in relevant_pair_rows:
        for flag in str(row["contrast_flags"]).split(";"):
            if flag:
                relevant_contrast_counts[flag] += 1
        for feature in FEATURE_RANGES:
            relevant_signal_differences[feature].append(
                float(row[f"delta_{feature}"])
            )
    relevant_difference_summary = {}
    for feature, values in sorted(relevant_signal_differences.items()):
        ordered = sorted(values)
        relevant_difference_summary[feature] = {
            "median": median(ordered),
            "p90": percentile(ordered, 0.90),
            "max": ordered[-1],
        }

    behavior_by_archetype = {}
    for archetype, features in sorted(archetype_behavior.items()):
        feature_summary = {}
        for feature, values in sorted(features.items()):
            ordered = sorted(values)
            feature_summary[feature] = {
                "mean": sum(ordered) / len(ordered),
                "median": median(ordered),
                "p10": percentile(ordered, 0.10),
                "p90": percentile(ordered, 0.90),
            }
        behavior_by_archetype[archetype] = {
            "candidate_count": len(next(iter(features.values()))),
            "features": feature_summary,
        }

    summary = {
        "dataset": str(dataset),
        "reference_date": REFERENCE_DATE.isoformat(),
        "record_count": record_count,
        "career_matched_groups": len(career_matched_groups),
        "candidates_in_career_matched_groups": sum(
            len(candidates) for candidates in career_matched_groups.values()
        ),
        "strict_education_matched_subgroups": strict_group_count,
        "candidates_in_strict_education_subgroups": strict_candidate_count,
        "archetype_group_counts": dict(archetype_group_counts.most_common()),
        "relevant_archetype_group_counts": dict(relevant_group_counts.most_common()),
        "group_size_distribution": dict(sorted(group_size_distribution.items())),
        "representative_pairs": len(pair_rows),
        "pairs_with_at_least_one_large_contrast": high_contrast_pairs,
        "contrast_counts": dict(contrast_counts.most_common()),
        "signal_difference_summary": difference_summary,
        "relevant_representative_pairs": len(relevant_pair_rows),
        "relevant_contrast_counts": dict(relevant_contrast_counts.most_common()),
        "relevant_signal_difference_summary": relevant_difference_summary,
        "behavior_by_archetype": behavior_by_archetype,
        "career_matching_definition": {
            "same_summary_archetype": True,
            "same_normalized_current_title": True,
            "same_one_year_experience_bucket": True,
            "same_ordered_career_template_sequence": True,
            "education_excluded_from_primary_signature": True,
            "behavior_excluded_from_signature": True,
            "skills_excluded_from_signature": (
                "Skills are deliberately noisy in this synthetic dataset."
            ),
        },
    }
    write_json(output_dir / "behavioral_twins_summary.json", summary)

    top_pairs = pair_rows[:15]
    top_relevant_pairs = sorted(
        relevant_pair_rows,
        key=lambda row: (
            -float(row["behavior_distance"]),
            row["candidate_a"],
            row["candidate_b"],
        ),
    )[:15]
    archetype_behavior_rows = []
    for archetype, values in behavior_by_archetype.items():
        features = values["features"]
        archetype_behavior_rows.append(
            (
                archetype,
                values["candidate_count"],
                f"{features['inactive_days']['median']:.1f}",
                f"{features['response_rate']['median']:.2f}",
                f"{features['notice_period_days']['median']:.0f}",
                f"{features['open_to_work']['mean']:.1%}",
                f"{features['saved_by_recruiters']['median']:.1f}",
            )
        )
    archetype_behavior_rows.sort(key=lambda row: -int(row[1]))
    report = [
        "# Behavioral Twin Analysis",
        "",
        "A career-matched twin group shares summary archetype, normalized current",
        "title, one-year experience bucket, and ordered career-description",
        "templates. Behavioral fields, skills, and education are excluded from",
        "the primary signature. A stricter education-matched subset is also counted.",
        "",
        "This analysis demonstrates controlled behavioral variation. Without hidden",
        "relevance labels, it cannot estimate the official causal weight of a signal.",
        "",
        "## Coverage",
        "",
        f"- Candidates scanned: {record_count:,}",
        f"- Career-matched groups: {len(career_matched_groups):,}",
        (
            "- Candidates represented in career-matched groups: "
            f"{sum(len(candidates) for candidates in career_matched_groups.values()):,}"
        ),
        f"- Strict education-matched subgroups: {strict_group_count:,}",
        f"- Candidates in strict education-matched subgroups: {strict_candidate_count:,}",
        (
            "- ML-relevant career-matched groups: "
            f"{sum(relevant_group_counts.values()):,}"
        ),
        f"- Representative maximum-distance pairs: {len(pair_rows):,}",
        f"- Pairs with at least one large contrast: {high_contrast_pairs:,}",
        "",
        "## Large Contrast Counts",
        "",
        markdown_table(
            ("Contrast", "Representative pairs"),
            ((name, count) for name, count in contrast_counts.most_common()),
        ),
        "",
        "## Behavioral Distribution by Archetype",
        "",
        markdown_table(
            (
                "Archetype",
                "Candidates",
                "Median inactive days",
                "Median response rate",
                "Median notice days",
                "Open-to-work rate",
                "Median recruiter saves",
            ),
            archetype_behavior_rows,
        ),
        "",
        "Behavioral signals are not identically distributed across static profile",
        "archetypes. This means a model can accidentally use behavior as a proxy for",
        "the generator's candidate class unless static relevance and behavior are",
        "modeled separately.",
        "",
        "## Highest-Distance Pairs",
        "",
        markdown_table(
            (
                "Candidate A",
                "Candidate B",
                "Archetype",
                "Title",
                "Distance",
                "Contrasts",
            ),
            (
                (
                    row["candidate_a"],
                    row["candidate_b"],
                    row["summary_archetype"],
                    row["current_title"],
                    f"{float(row['behavior_distance']):.3f}",
                    row["contrast_flags"] or "none",
                )
                for row in top_pairs
            ),
        ),
        "",
        "## Highest-Distance ML-Relevant Pairs",
        "",
        markdown_table(
            (
                "Candidate A",
                "Candidate B",
                "Archetype",
                "Title",
                "Distance",
                "Contrasts",
            ),
            (
                (
                    row["candidate_a"],
                    row["candidate_b"],
                    row["summary_archetype"],
                    row["current_title"],
                    f"{float(row['behavior_distance']):.3f}",
                    row["contrast_flags"] or "none",
                )
                for row in top_relevant_pairs
            ),
        ),
        "",
        "## Interpretation",
        "",
        "- The matched set is useful for counterfactual and sensitivity tests.",
        "- Large behavioral variation among otherwise matched profiles supports",
        "  modeling behavior separately from static relevance.",
        "- The direction of desirable changes comes from the JD and signal",
        "  documentation; their exact hidden-label weights remain unknown.",
        "- `behavioral_twins.csv` contains one maximum-distance pair per group.",
        "",
    ]
    (output_dir / "behavioral_twins_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = analyze(args.candidates, args.output_dir)
    print(
        "Behavioral twin analysis complete: "
        f"{summary['career_matched_groups']:,} career-matched groups."
    )


if __name__ == "__main__":
    main()
