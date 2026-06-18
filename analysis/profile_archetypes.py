#!/usr/bin/env python3
"""Recover deterministic profile and text-template archetypes."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    career_sequence,
    career_template_id,
    headline_template_id,
    markdown_table,
    stable_id,
    stream_candidates,
    summary_archetype,
    summary_template_id,
    title_family,
    write_json,
)


def analyze(dataset: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assignments_path = output_dir / "archetype_assignments.csv"

    archetypes: Counter[str] = Counter()
    title_families: Counter[str] = Counter()
    summary_templates: Counter[str] = Counter()
    headline_templates: Counter[str] = Counter()
    career_templates: Counter[str] = Counter()
    career_sequences: Counter[str] = Counter()
    titles_by_archetype: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)
    record_count = 0
    career_entry_count = 0

    with assignments_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "summary_archetype",
                "summary_template_id",
                "headline_template_id",
                "title_family",
                "current_title",
                "current_career_template_id",
                "career_sequence_id",
                "career_role_count",
            ],
        )
        writer.writeheader()

        for candidate in stream_candidates(dataset):
            record_count += 1
            profile = candidate["profile"]
            archetype = summary_archetype(
                profile.get("summary", ""), profile.get("current_title", "")
            )
            family = title_family(profile.get("current_title", ""))
            summary_id = summary_template_id(profile.get("summary", ""))
            headline_id = headline_template_id(profile.get("headline", ""))
            sequence = career_sequence(candidate)
            sequence_id = stable_id(sequence, "career_seq")
            current_role = next(
                (
                    role
                    for role in candidate.get("career_history", [])
                    if role.get("is_current")
                ),
                candidate.get("career_history", [{}])[0],
            )
            current_template = career_template_id(
                current_role.get("description", "")
            )

            archetypes[archetype] += 1
            title_families[family] += 1
            summary_templates[summary_id] += 1
            headline_templates[headline_id] += 1
            career_sequences[sequence_id] += 1
            titles_by_archetype[archetype][profile.get("current_title", "")] += 1
            if len(examples[archetype]) < 5:
                examples[archetype].append(candidate["candidate_id"])

            for role in candidate.get("career_history", []):
                career_entry_count += 1
                career_templates[career_template_id(role.get("description", ""))] += 1

            writer.writerow(
                {
                    "candidate_id": candidate["candidate_id"],
                    "summary_archetype": archetype,
                    "summary_template_id": summary_id,
                    "headline_template_id": headline_id,
                    "title_family": family,
                    "current_title": profile.get("current_title", ""),
                    "current_career_template_id": current_template,
                    "career_sequence_id": sequence_id,
                    "career_role_count": len(candidate.get("career_history", [])),
                }
            )

    summary = {
        "dataset": str(dataset),
        "record_count": record_count,
        "career_entry_count": career_entry_count,
        "unique_summary_templates": len(summary_templates),
        "unique_headline_templates": len(headline_templates),
        "unique_career_templates": len(career_templates),
        "unique_career_sequences": len(career_sequences),
        "summary_archetypes": dict(archetypes.most_common()),
        "title_families": dict(title_families.most_common()),
        "top_titles_by_archetype": {
            name: dict(counter.most_common(12))
            for name, counter in sorted(titles_by_archetype.items())
        },
        "example_candidate_ids": dict(sorted(examples.items())),
        "career_template_frequency_distribution": dict(
            sorted(Counter(career_templates.values()).items())
        ),
    }
    write_json(output_dir / "archetype_summary.json", summary)

    report = [
        "# Profile Archetype Analysis",
        "",
        "This report describes deterministic generator patterns. It does not assign",
        "or claim to recover official relevance tiers.",
        "",
        "## Dataset",
        "",
        f"- Candidate records: {record_count:,}",
        f"- Career entries: {career_entry_count:,}",
        f"- Unique normalized summary templates: {len(summary_templates):,}",
        f"- Unique normalized headline templates: {len(headline_templates):,}",
        f"- Unique exact career-description templates: {len(career_templates):,}",
        f"- Unique ordered career-template sequences: {len(career_sequences):,}",
        "",
        "## Summary Archetypes",
        "",
        markdown_table(
            ("Archetype", "Candidates", "Share"),
            (
                (name, f"{count:,}", f"{count / record_count:.2%}")
                for name, count in archetypes.most_common()
            ),
        ),
        "",
        "## Title Families",
        "",
        markdown_table(
            ("Title family", "Candidates", "Share"),
            (
                (name, f"{count:,}", f"{count / record_count:.2%}")
                for name, count in title_families.most_common()
            ),
        ),
        "",
        "## Interpretation",
        "",
        "- The small number of career-description templates confirms that career",
        "  evidence was generated from a compact library.",
        "- Summary archetypes are useful structural hypotheses, not hidden labels.",
        "- Candidate-level assignments are available in `archetype_assignments.csv`.",
        "- Any relevance mapping must be validated against independent semantic and",
        "  factual evidence to avoid overfitting generator artifacts.",
        "",
    ]
    (output_dir / "archetype_report.md").write_text(
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
        "Archetype analysis complete: "
        f"{summary['record_count']:,} candidates, "
        f"{summary['unique_career_templates']} career templates."
    )


if __name__ == "__main__":
    main()
