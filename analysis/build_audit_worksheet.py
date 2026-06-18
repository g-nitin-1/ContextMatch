#!/usr/bin/env python3
"""Lay out the 44 career-template evidence annotations for one-time human audit.

This tool does not change any annotation. It reads the frozen JD evidence
catalog and emits a single reviewable worksheet, ordered by ranking
decisiveness, so a human can verify every assigned signal (false positives) and
look for missing evidence (false negatives) before the rubric is version-locked.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from analysis.common import DEFAULT_OUTPUT_DIR


# Decisiveness tiers. Audit priority follows the share of the composite score a
# template can move, not how many candidates carry it.
TIER_A_ARCHETYPES = {
    "senior_plain_language",
    "senior_explicit_ai",
    "applied_ml",
}
TIER_C_ARCHETYPES = {"generic_ml"}

CATEGORY_ORDER = ("direct_requirement", "core_role", "preferred", "risk_context")
CATEGORY_LABELS = {
    "direct_requirement": "Direct requirement",
    "core_role": "Core role",
    "preferred": "Preferred",
    "risk_context": "Risk context",
}


def _tier(archetype: str) -> str:
    if archetype in TIER_A_ARCHETYPES:
        return "A"
    if archetype in TIER_C_ARCHETYPES:
        return "C"
    return "B"


def _archetype_rank(archetype: str) -> int:
    order = [
        "senior_plain_language",
        "senior_explicit_ai",
        "applied_ml",
        "generic_ml",
        "data_backend_adjacent",
        "general_software",
        "general_professional",
    ]
    return order.index(archetype) if archetype in order else len(order)


def _sort_key(item: tuple[str, dict[str, Any]]) -> tuple[Any, ...]:
    _, career = item
    tier = _tier(career["dominant_archetype"])
    tier_order = {"A": 0, "C": 1, "B": 2}[tier]
    # Tier A: most decisive cohorts first, rarest template first (each rare
    # template maps to few but high-impact candidates). Tier B/C: largest
    # populations first, where a false positive injects the most noise.
    if tier == "A":
        secondary = (_archetype_rank(career["dominant_archetype"]), career["occurrence_count"])
    else:
        secondary = (_archetype_rank(career["dominant_archetype"]), -career["occurrence_count"])
    return (tier_order, *secondary)


def _matched_terms(signal: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for group in signal.get("group_evidence", []):
        for match in group:
            term = match.get("match", "")
            if term and term not in seen:
                seen.append(term)
    return seen


def _first_snippet(signal: dict[str, Any]) -> str:
    for group in signal.get("group_evidence", []):
        for match in group:
            snippet = match.get("snippet", "")
            if snippet:
                return snippet
    return ""


def _signal_lines(
    career: dict[str, Any],
    rubric_signals: dict[str, Any],
) -> list[str]:
    lines: list[str] = []
    for category in CATEGORY_ORDER:
        ids = career["signals_by_category"].get(category, [])
        if not ids:
            continue
        lines.append(f"- **{CATEGORY_LABELS[category]}**")
        for signal_id in ids:
            signal = career["signals"][signal_id]
            terms = ", ".join(f"`{term}`" for term in _matched_terms(signal))
            label = rubric_signals.get(signal_id, {}).get("label", signal_id)
            lines.append(f"  - `{signal_id}` ({label}) — matched: {terms}")
            snippet = _first_snippet(signal)
            if snippet:
                lines.append(f"    - snippet: \"{snippet}\"")
    return lines


def build_worksheet(catalog: dict[str, Any]) -> str:
    rubric_signals = catalog["rubric_summary"]["signals"]
    careers = catalog["career_templates"]
    ordered = sorted(careers.items(), key=_sort_key)

    tier_counts = {"A": 0, "B": 0, "C": 0}
    for _, career in ordered:
        tier_counts[_tier(career["dominant_archetype"])] += 1

    method = catalog["method"]
    out: list[str] = [
        "# JD Evidence Catalog — Manual Audit Worksheet",
        "",
        f"Rubric version: `{method['rubric_version']}` | "
        f"Career templates: {method['career_template_count']} | "
        f"Source: `{method['source']}`",
        "",
        "Purpose: verify every assigned signal and look for missing evidence in "
        "the complete, finite career-template library before the rubric is "
        "version-locked. Because all 300k career entries are copies of these 44 "
        "templates, a clean audit makes extraction errors enumerable and "
        "correctable across the visible career-template library. It is still "
        "subject to human and rubric judgment. This tool changes nothing; edit "
        "`jd_evidence_rubric.json` and re-run the catalog if a fix is needed.",
        "",
        "How to review each template:",
        "",
        "1. Read the full text.",
        "2. False positives — does any listed signal NOT actually hold in the "
        "text? (e.g. \"SaaS product\" firing product context for a support lead.)",
        "3. False negatives — is there JD-relevant evidence the rubric missed?",
        "4. Mark the verdict line.",
        "",
        "Audit priority (by share of composite score a template can move):",
        "",
        f"- **Tier A — highest scrutiny ({tier_counts['A']} templates):** senior "
        "and applied-ML templates. These can decide NDCG@10/@50. Verify every "
        "signal AND every absence; one error can materially change a top-cohort "
        "candidate.",
        f"- **Tier C — check both directions ({tier_counts['C']} templates):** "
        "generic-ML, the borderline Tier-3 region (MAP / P@10).",
        f"- **Tier B — confirm no false positives ({tier_counts['B']} templates):** "
        "high-population non-ML templates. False negatives are lower priority "
        "but should still be noted for tail-exception audits; a false "
        "direct-requirement match injects noise into the top 100.",
        "",
        "---",
        "",
    ]

    current_tier: str | None = None
    for career_id, career in ordered:
        tier = _tier(career["dominant_archetype"])
        if tier != current_tier:
            current_tier = tier
            out.append(f"## Tier {tier}")
            out.append("")

        purity = career["archetype_purity"]
        out.append(f"### `{career_id}` — {career['dominant_archetype']} (Tier {tier})")
        out.append("")
        out.append(
            f"- Occurrences: {career['occurrence_count']:,} "
            f"(current role: {career['current_role_count']:,}) | "
            f"archetype purity: {purity:.3f}"
        )
        compounds = career.get("compound_ids", [])
        out.append(
            "- Compounds: "
            + (", ".join(f"`{c}`" for c in compounds) if compounds else "none")
        )
        out.append("")
        out.append("Text:")
        out.append("")
        out.append("> " + career["text"].replace("\n", " ").strip())
        out.append("")
        out.append("Assigned evidence:")
        out.append("")
        signal_lines = _signal_lines(career, rubric_signals)
        out.extend(signal_lines if signal_lines else ["- (no signals assigned)"])
        out.append("")
        out.append("Review:")
        out.append("")
        out.append("- False positives to remove: ")
        out.append("- Missing evidence (false negatives): ")
        out.append("- Verdict: [ ] correct  [ ] fix rubric")
        out.append("")
        out.append("---")
        out.append("")

    return "\n".join(out)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "jd_evidence_catalog.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "jd_evidence_audit_worksheet.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.catalog.exists():
        raise FileNotFoundError(
            f"{args.catalog} not found; run "
            "`python3 -m analysis.jd_evidence_catalog` first"
        )
    with args.catalog.open("r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    worksheet = build_worksheet(catalog)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(worksheet, encoding="utf-8")
    print(f"Audit worksheet written: {args.out}")


if __name__ == "__main__":
    main()
