#!/usr/bin/env python3
"""Build a consolidated interpretation from generated analysis artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from analysis.common import DEFAULT_OUTPUT_DIR, markdown_table


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return read_json(path)


def build_report(output_dir: Path) -> Path:
    archetypes = read_json(output_dir / "archetype_summary.json")
    integrity = read_json(output_dir / "integrity_summary.json")
    twins = read_json(output_dir / "behavioral_twins_summary.json")
    overlay = read_json_if_exists(output_dir / "candidate_overlay_summary.json")
    scores = read_json_if_exists(output_dir / "idea2_score_summary.json")

    documented_pattern_ids = set()
    chronology_ids = set()
    duration_ids = set()
    high_risk_archetypes: Counter[str] = Counter()
    with (output_dir / "integrity_issues.jsonl").open(
        "r", encoding="utf-8"
    ) as handle:
        for line in handle:
            record = json.loads(line)
            rules = {item["rule"] for item in record["issues"]}
            candidate_id = record["candidate_id"]
            if rules & {"company_pre_founding", "expert_zero_duration_3plus"}:
                documented_pattern_ids.add(candidate_id)
            if "technology_before_release" in rules:
                chronology_ids.add(candidate_id)
            if rules & {
                "role_duration_large_mismatch",
                "career_duration_exceeds_experience",
            }:
                duration_ids.add(candidate_id)
            if record["risk_level"] == "high":
                high_risk_archetypes[record["summary_archetype"]] += 1

    relevant_archetypes = {
        "senior_plain_language",
        "senior_explicit_ai",
        "applied_ml",
        "generic_ml",
    }
    relevant_high_risk = sum(
        count
        for name, count in high_risk_archetypes.items()
        if name in relevant_archetypes
    )
    high_risk_total = integrity["risk_levels"].get("high", 0)

    report = [
        "# Consolidated Analysis: Archetypes, Integrity, Behavior, and Overlay",
        "",
        "## Executive Findings",
        "",
        (
            f"1. The dataset contains {archetypes['unique_career_templates']} exact "
            "career-description templates across "
            f"{archetypes['career_entry_count']:,} career entries. Generator "
            "structure is therefore strong and measurable."
        ),
        (
            "2. The rarest summary cohorts contain 8 plain-language senior profiles, "
            "21 explicit senior AI profiles, 150 applied-ML profiles, and 1,000 "
            "generic-ML profiles. These are structural cohorts, not proven official "
            "relevance tiers."
        ),
        (
            f"3. The integrity engine found {high_risk_total:,} candidates with at "
            "least one strong contradiction. "
            f"{relevant_high_risk:,} ({relevant_high_risk / high_risk_total:.1%}) "
            "are in ML-relevant-looking cohorts, so anomaly filtering matters most "
            "exactly where keyword and semantic rankers are likely to focus."
        ),
        (
            f"4. {len(documented_pattern_ids):,} candidates match a proxy rule based "
            "on one of the challenge's documented honeypot pattern families: "
            "employment before company founding or multiple expert skills with zero "
            "duration. This is not the hidden official set."
        ),
        (
            f"5. Career-matched analysis produced "
            f"{twins['career_matched_groups']:,} groups covering "
            f"{twins['candidates_in_career_matched_groups']:,} candidates, including "
            f"{sum(twins['relevant_archetype_group_counts'].values()):,} ML-relevant "
            "groups. Behavior varies substantially inside these groups."
        ),
        "",
        "## Archetype Structure",
        "",
        markdown_table(
            ("Archetype", "Candidates", "Share"),
            (
                (
                    name,
                    f"{count:,}",
                    f"{count / archetypes['record_count']:.2%}",
                )
                for name, count in archetypes["summary_archetypes"].items()
            ),
        ),
        "",
        "The exact cohort sizes strongly suggest deliberate generator classes.",
        "However, assigning them directly to hidden relevance tiers would be an",
        "unsupported leap. They should become probabilistic prior features.",
        "",
        "## Integrity Findings",
        "",
        markdown_table(
            ("Evidence family", "Unique candidates"),
            (
                ("Documented-pattern proxy", len(documented_pattern_ids)),
                ("Additional technology chronology", len(chronology_ids)),
                ("Large duration contradictions", len(duration_ids)),
                ("Union of strong contradiction rules", high_risk_total),
            ),
        ),
        "",
        markdown_table(
            ("Archetype", "High-risk candidates"),
            high_risk_archetypes.most_common(),
        ),
        "",
        "The 24,895 behavioral data-quality records are intentionally kept separate.",
        "Their frequency makes them unsuitable as automatic honeypot exclusions.",
        "",
        "The company-founding rule alone flags 83 unique candidates, which is close",
        "to the challenge's approximate honeypot count. This is notable but not",
        "proof: technology and duration checks identify additional non-overlapping",
        "contradictions.",
        "",
        "## Behavioral Twin Findings",
        "",
        markdown_table(
            ("Archetype", "Career-matched groups"),
            twins["archetype_group_counts"].items(),
        ),
        "",
        "Within the 169 ML-relevant matched groups:",
        "",
        markdown_table(
            ("Signal contrast", "Representative pairs"),
            twins["relevant_contrast_counts"].items(),
        ),
        "",
        "No senior-profile twin groups were found under the career-matched",
        "definition because the senior cohorts are small and structurally unique.",
        "Behavioral weights for the top cohort therefore cannot be inferred from",
        "twins alone.",
        "",
        "Behavior is also conditioned on archetype. For example, ML-relevant groups",
        "have narrower inactivity ranges and larger recruiter-save variation than",
        "the broad population. A model should compute static relevance first and",
        "apply a bounded behavioral modifier second.",
        "",
        "## Implications for the Proxy Ranker",
        "",
        "1. Use archetype as a prior, never as a final relevance label.",
        "2. Give career templates and demonstrated work more weight than skills.",
        "3. Treat company-founding and zero-duration-expert checks as the strongest",
        "   honeypot signals; keep chronology and duration checks as strong but",
        "   independently auditable evidence.",
        "4. Do not let common salary/signup inconsistencies disqualify candidates.",
        "5. Cap behavioral adjustments so they reorder similarly qualified",
        "   candidates without promoting irrelevant but active candidates.",
        "6. Use the 169 ML-relevant matched groups for behavioral sensitivity tests.",
        "7. Cross-check rare senior candidates individually with the teacher system",
        "   from Idea 1 because twin-based estimation has no coverage there.",
        "",
        "## What Remains Unknown",
        "",
        "- The official relevance tier definitions and gains.",
        "- Which detected contradictions are included in the hidden honeypot list.",
        "- The exact behavioral modifier used in hidden labels.",
        "- Whether hidden labels were generated entirely by rules or manually",
        "  adjusted.",
        "",
    ]
    if overlay:
        fired = overlay["overlay_rule_fired_counts"]
        report.insert(
            report.index("## Archetype Structure") - 1,
            (
                "6. The candidate overlay joins template evidence to skills, "
                "recency, logistics, behavior, and integrity for all "
                f"{overlay['candidate_count']:,} candidates. Current rule "
                f"firings: services-only="
                f"{fired.get('services_only_entire_career', 0):,}, "
                f"recent-shallow-LLM={fired.get('recent_shallow_llm_only', 0):,}, "
                f"research-only="
                f"{fired.get('research_only_without_production', 0):,}, "
                f"senior-not-coding="
                f"{fired.get('senior_not_coding_recently', 0):,}."
            ),
        )
        unknown_index = report.index("## What Remains Unknown")
        report[unknown_index:unknown_index] = [
            "## Candidate Overlay Findings",
            "",
            "The overlay is the candidate-level feature table for Idea 2. It does",
            "not assign tiers or scores.",
            "",
            markdown_table(
                ("Overlay rule", "Candidates"),
                overlay["overlay_rule_fired_counts"].items(),
            ),
            "",
            "Career compounds inherited by candidates:",
            "",
            markdown_table(
                ("Compound", "Candidates"),
                overlay["career_compound_candidate_counts"].items(),
            ),
            "",
        ]
    if scores:
        report.insert(
            report.index("## Archetype Structure") - 1,
            (
                "7. The first Idea 2 scorer evaluates candidates across "
                f"{len(scores['worlds'])} plausible worlds. Top-10 consensus "
                "intersection/union is "
                f"{scores['stability']['10']['intersection_count']}/"
                f"{scores['stability']['10']['union_count']}; top-100 is "
                f"{scores['stability']['100']['intersection_count']}/"
                f"{scores['stability']['100']['union_count']}."
            ),
        )
        unknown_index = report.index("## What Remains Unknown")
        report[unknown_index:unknown_index] = [
            "## Idea 2 Score Findings",
            "",
            "The scorer is a multi-world proxy model, not a local leaderboard.",
            "All current worlds preserve the senior-above-applied/generic tier "
            "ordering, so stability here tests weighting and boundary choices, "
            "not a fundamentally different JD-to-tier mapping.",
            "",
            markdown_table(
                ("Top K", "Intersection", "Union", "Intersection / Union"),
                (
                    (
                        k,
                        values["intersection_count"],
                        values["union_count"],
                        values["intersection_over_union"],
                    )
                    for k, values in sorted(
                        scores["stability"].items(),
                        key=lambda item: int(item[0]),
                    )
                ),
            ),
            "",
            "Top candidates by mean score:",
            "",
            markdown_table(
                ("Rank", "Candidate", "Archetype", "Atom", "Mean score"),
                (
                    (
                        row["final_rank"],
                        row["candidate_id"],
                        row["summary_archetype"],
                        row["fine_static_atom"],
                        row["mean_score"],
                    )
                    for row in scores["top_by_mean"][:10]
                ),
            ),
            "",
        ]
    path = output_dir / "analysis_report.md"
    path.write_text("\n".join(report), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = build_report(args.output_dir)
    print(f"Consolidated report written to {path}")


if __name__ == "__main__":
    main()
