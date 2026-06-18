#!/usr/bin/env python3
"""Build deterministic JD evidence annotations for generator templates and atoms."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    career_template_id,
    stream_candidates,
    summary_template_id,
    write_json,
)


DEFAULT_RUBRIC = Path(__file__).with_name("jd_evidence_rubric.json")

REQUIRED_OVERLAY_FIELDS = {
    "jd_strength": str,
    "evaluation_scope": str,
    "description": str,
    "required_inputs": list,
    "must_not_trigger_from": str,
    "automatic_tier_zero": bool,
}


def load_rubric(path: Path = DEFAULT_RUBRIC) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        rubric = json.load(handle)
    if (
        not rubric.get("signals")
        or not rubric.get("compounds")
        or not rubric.get("candidate_overlay_rules")
        or not rubric.get("skill_signal_patterns")
    ):
        raise ValueError(
            "Rubric is missing signals, compounds, overlay rules, or "
            f"skill patterns: {path}"
        )
    _validate_skill_signal_patterns(rubric["skill_signal_patterns"], path)
    _validate_overlay_rules(rubric["candidate_overlay_rules"], path)
    return rubric


def _validate_skill_signal_patterns(patterns: dict[str, Any], path: Path) -> None:
    if not isinstance(patterns, dict):
        raise ValueError(f"skill_signal_patterns must be an object: {path}")

    for signal_id, entry in patterns.items():
        if not isinstance(entry, dict):
            raise ValueError(f"skill_signal_patterns.{signal_id} must be an object")
        for field in ("label", "description"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise ValueError(
                    f"skill_signal_patterns.{signal_id}.{field} must be a "
                    f"non-empty string: {path}"
                )
        raw_patterns = entry.get("patterns")
        if not isinstance(raw_patterns, list) or not raw_patterns:
            raise ValueError(
                f"skill_signal_patterns.{signal_id}.patterns must be a "
                f"non-empty list: {path}"
            )
        for pattern in raw_patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError(
                    f"skill_signal_patterns.{signal_id}.patterns contains "
                    f"a non-string pattern: {path}"
                )
            re.compile(pattern, flags=re.IGNORECASE)


def _validate_overlay_rules(rules: dict[str, Any], path: Path) -> None:
    if not isinstance(rules, dict):
        raise ValueError(f"candidate_overlay_rules must be an object: {path}")

    for rule_id, rule in rules.items():
        if not isinstance(rule, dict):
            raise ValueError(
                f"candidate_overlay_rules.{rule_id} must be an object: {path}"
            )
        for field, expected_type in REQUIRED_OVERLAY_FIELDS.items():
            if field not in rule:
                raise ValueError(
                    f"candidate_overlay_rules.{rule_id} missing {field}: {path}"
                )
            if not isinstance(rule[field], expected_type):
                raise ValueError(
                    f"candidate_overlay_rules.{rule_id}.{field} must be "
                    f"{expected_type.__name__}: {path}"
                )
        if not rule["required_inputs"]:
            raise ValueError(
                f"candidate_overlay_rules.{rule_id}.required_inputs is empty: "
                f"{path}"
            )


def _snippet(text: str, start: int, end: int, radius: int = 70) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    value = text[left:right].strip()
    if left:
        value = "..." + value
    if right < len(text):
        value += "..."
    return value


def annotate_text(text: str, rubric: dict[str, Any]) -> dict[str, Any]:
    """Return exact atomic and compound evidence observed in one text."""
    observed: dict[str, Any] = {}
    for signal_id, signal in rubric["signals"].items():
        group_evidence = []
        all_groups_match = True
        for alternatives in signal["pattern_groups"]:
            matches = []
            for pattern in alternatives:
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    matches.append(
                        {
                            "pattern": pattern,
                            "match": match.group(0),
                            "snippet": _snippet(text, match.start(), match.end()),
                        }
                    )
            if not matches:
                all_groups_match = False
                break
            group_evidence.append(matches)
        if all_groups_match:
            observed[signal_id] = {
                "category": signal["category"],
                "label": signal["label"],
                "group_evidence": group_evidence,
            }

    compounds = {}
    for compound_id, compound in rubric["compounds"].items():
        required = compound["requires_all"]
        if all(signal_id in observed for signal_id in required):
            compounds[compound_id] = {
                "category": compound["category"],
                "label": compound["label"],
                "requires_all": required,
            }

    return {
        "signals": observed,
        "compounds": compounds,
    }


def _current_role(candidate: dict[str, Any]) -> dict[str, Any]:
    roles = candidate.get("career_history", [])
    return next(
        (role for role in roles if role.get("is_current")),
        roles[0] if roles else {},
    )


def _counter_rows(
    counter: Counter[str],
    total: int,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    rows = []
    values = counter.most_common(limit)
    for value, count in values:
        rows.append(
            {
                "value": value,
                "count": count,
                "prevalence": round(count / total, 6) if total else 0.0,
            }
        )
    return rows


def _category_signal_ids(
    rubric: dict[str, Any], category: str
) -> list[str]:
    return sorted(
        signal_id
        for signal_id, signal in rubric["signals"].items()
        if signal["category"] == category
    )


def _build_atom_catalog(
    dataset: Path,
    manifest: dict[str, Any],
    career_annotations: dict[str, dict[str, Any]],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    atom_by_summary = {
        summary_id: summary["fine_static_atom"]
        for summary_id, summary in manifest["summary_templates"].items()
    }
    atom_manifest = manifest["fine_static_atoms"]
    stats: dict[str, dict[str, Any]] = {}
    for atom_id, atom in atom_manifest.items():
        stats[atom_id] = {
            "candidate_count": 0,
            "years": [],
            "titles": Counter(),
            "current_careers": Counter(),
            "all_careers": Counter(),
            "current_signals": Counter(),
            "any_career_signals": Counter(),
            "current_compounds": Counter(),
            "any_career_compounds": Counter(),
        }

    for candidate in stream_candidates(dataset):
        profile = candidate["profile"]
        summary_id = summary_template_id(profile.get("summary", ""))
        atom_id = atom_by_summary.get(summary_id)
        if atom_id is None:
            raise ValueError(
                f"Summary template {summary_id} is missing from generator manifest"
            )
        atom = stats[atom_id]
        atom["candidate_count"] += 1
        atom["years"].append(float(profile.get("years_of_experience", 0.0)))
        atom["titles"][profile.get("current_title", "")] += 1

        current = _current_role(candidate)
        current_id = career_template_id(current.get("description", ""))
        atom["current_careers"][current_id] += 1
        current_annotation = career_annotations[current_id]
        atom["current_signals"].update(current_annotation["signals"].keys())
        atom["current_compounds"].update(current_annotation["compounds"].keys())

        candidate_signals: set[str] = set()
        candidate_compounds: set[str] = set()
        for role in candidate.get("career_history", []):
            career_id = career_template_id(role.get("description", ""))
            atom["all_careers"][career_id] += 1
            annotation = career_annotations[career_id]
            candidate_signals.update(annotation["signals"])
            candidate_compounds.update(annotation["compounds"])

        atom["any_career_signals"].update(candidate_signals)
        atom["any_career_compounds"].update(candidate_compounds)

    direct_signal_ids = _category_signal_ids(rubric, "direct_requirement")
    risk_signal_ids = _category_signal_ids(rubric, "risk_context")
    result = {}
    for atom_id, atom in sorted(stats.items()):
        count = atom["candidate_count"]
        years = sorted(atom.pop("years"))
        manifest_entry = atom_manifest[atom_id]
        result[atom_id] = {
            "candidate_count": count,
            "dominant_archetype": manifest_entry["dominant_archetype"],
            "archetype_purity": manifest_entry["archetype_purity"],
            "coarse_static_classes": manifest_entry["coarse_static_classes"],
            "experience_years": {
                "median": round(float(median(years)), 3) if years else 0.0,
                "minimum": round(years[0], 3) if years else 0.0,
                "maximum": round(years[-1], 3) if years else 0.0,
            },
            "top_current_titles": _counter_rows(atom["titles"], count, limit=12),
            "current_career_templates": _counter_rows(
                atom["current_careers"], count
            ),
            "all_career_template_occurrences": [
                {"value": value, "count": occurrence_count}
                for value, occurrence_count in atom["all_careers"].most_common()
            ],
            "current_signal_prevalence": _counter_rows(
                atom["current_signals"], count
            ),
            "any_career_signal_prevalence": _counter_rows(
                atom["any_career_signals"], count
            ),
            "current_compound_prevalence": _counter_rows(
                atom["current_compounds"], count
            ),
            "any_career_compound_prevalence": _counter_rows(
                atom["any_career_compounds"], count
            ),
            "direct_requirement_evidence": {
                signal_id: {
                    "current_count": atom["current_signals"].get(signal_id, 0),
                    "current_prevalence": round(
                        atom["current_signals"].get(signal_id, 0) / count, 6
                    ),
                    "any_career_count": atom["any_career_signals"].get(
                        signal_id, 0
                    ),
                    "any_career_prevalence": round(
                        atom["any_career_signals"].get(signal_id, 0) / count,
                        6,
                    ),
                }
                for signal_id in direct_signal_ids
            },
            "risk_context_evidence": {
                signal_id: {
                    "current_count": atom["current_signals"].get(signal_id, 0),
                    "current_prevalence": round(
                        atom["current_signals"].get(signal_id, 0) / count, 6
                    ),
                    "any_career_count": atom["any_career_signals"].get(
                        signal_id, 0
                    ),
                    "any_career_prevalence": round(
                        atom["any_career_signals"].get(signal_id, 0) / count,
                        6,
                    ),
                }
                for signal_id in risk_signal_ids
            },
        }
    return result


def _serialize_career_annotations(
    manifest: dict[str, Any],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    result = {}
    for career_id, career in sorted(manifest["career_templates"].items()):
        annotation = annotate_text(career["text"], rubric)
        signal_ids = sorted(annotation["signals"])
        compound_ids = sorted(annotation["compounds"])
        result[career_id] = {
            "text": career["text"],
            "occurrence_count": career["count"],
            "current_role_count": career["current_count"],
            "dominant_archetype": career["dominant_archetype"],
            "archetype_purity": career["archetype_purity"],
            "signal_ids": signal_ids,
            "compound_ids": compound_ids,
            "signals": annotation["signals"],
            "compounds": annotation["compounds"],
            "signals_by_category": {
                category: sorted(
                    signal_id
                    for signal_id in signal_ids
                    if rubric["signals"][signal_id]["category"] == category
                )
                for category in (
                    "direct_requirement",
                    "core_role",
                    "preferred",
                    "risk_context",
                )
            },
        }
    return result


def build_catalog(
    dataset: Path,
    output_dir: Path,
    rubric_path: Path = DEFAULT_RUBRIC,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "generator_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "generator_manifest.json is required; run "
            "`python3 -m analysis.generator_reconstruction` first"
        )
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    rubric = load_rubric(rubric_path)
    career_catalog = _serialize_career_annotations(manifest, rubric)
    atom_catalog = _build_atom_catalog(
        dataset,
        manifest,
        career_catalog,
        rubric,
    )

    catalog = {
        "method": {
            "rubric_version": rubric["version"],
            "rubric_path": str(rubric_path),
            "source": rubric["source"],
            "purpose": rubric["purpose"],
            "career_template_count": len(career_catalog),
            "fine_atom_count": len(atom_catalog),
            "candidate_count": sum(
                atom["candidate_count"] for atom in atom_catalog.values()
            ),
            "important_limitations": [
                "No relevance tier or combined score is assigned.",
                "A missing text match means not observed, not evidence of absence.",
                "Python and other evidence may appear in candidate skills and "
                "will be added in the candidate-overlay stage.",
                "Risk contexts are review flags, not automatic disqualifiers.",
                "Services-only and research-only conditions require whole-career "
                "evaluation in the candidate-overlay stage.",
                "Fine-atom prevalence is candidate-weighted; career-template "
                "occurrence counts are reported separately."
            ],
        },
        "rubric_summary": {
            "signals": {
                signal_id: {
                    "category": signal["category"],
                    "label": signal["label"],
                    "description": signal["description"],
                }
                for signal_id, signal in rubric["signals"].items()
            },
            "compounds": rubric["compounds"],
            "candidate_overlay_rules": rubric["candidate_overlay_rules"],
            "skill_signal_patterns": rubric["skill_signal_patterns"],
        },
        "career_templates": career_catalog,
        "fine_atoms": atom_catalog,
    }
    catalog_path = output_dir / "jd_evidence_catalog.json"
    report_path = output_dir / "jd_evidence_report.md"
    write_json(catalog_path, catalog)
    _write_report(report_path, catalog)
    return {
        "career_template_count": len(career_catalog),
        "fine_atom_count": len(atom_catalog),
        "candidate_count": catalog["method"]["candidate_count"],
        "catalog_path": str(catalog_path),
        "report_path": str(report_path),
    }


def _signal_prevalence(
    atom: dict[str, Any],
    signal_id: str,
) -> float:
    return atom["direct_requirement_evidence"].get(
        signal_id, {}
    ).get("any_career_prevalence", 0.0)


def _compound_prevalence(
    atom: dict[str, Any],
    compound_id: str,
) -> float:
    for row in atom["any_career_compound_prevalence"]:
        if row["value"] == compound_id:
            return float(row["prevalence"])
    return 0.0


def _write_report(path: Path, catalog: dict[str, Any]) -> None:
    method = catalog["method"]
    lines = [
        "# Deterministic JD Evidence Catalog",
        "",
        "This artifact maps the 44 career templates and 12 fine generator atoms "
        "to explicit, versioned JD evidence rules. It does not assign relevance "
        "tiers or a combined score.",
        "",
        "## Method",
        "",
        f"- Rubric version: `{method['rubric_version']}`",
        f"- Career templates: {method['career_template_count']}",
        f"- Fine atoms: {method['fine_atom_count']}",
        f"- Candidates aggregated for atom prevalence: "
        f"{method['candidate_count']:,}",
        "- Matching method: case-insensitive regular expressions with exact "
        "matched snippets retained in the JSON catalog.",
        "- Candidate-weighted atom evidence is inherited from current and "
        "historical career templates.",
        "",
        "A missing match means **not observed in the career text**, not that the "
        "candidate lacks the capability. Skills and candidate-specific overlays "
        "are intentionally deferred.",
        "",
        "## Atomic Rubric",
        "",
        "| signal | category | meaning |",
        "|---|---|---|",
    ]
    for signal_id, signal in catalog["rubric_summary"]["signals"].items():
        lines.append(
            f"| `{signal_id}` | {signal['category']} | "
            f"{signal['description']} |"
        )

    lines.extend(
        [
            "",
            "## Skill Overlay Patterns",
            "",
            "These patterns are used only for candidate skill overlays. They do not "
            "create career compounds.",
            "",
            "| signal | meaning | pattern count |",
            "|---|---|---:|",
        ]
    )
    for signal_id, entry in catalog["rubric_summary"][
        "skill_signal_patterns"
    ].items():
        lines.append(
            f"| `{signal_id}` | {entry['description']} | "
            f"{len(entry['patterns'])} |"
        )

    lines.extend(
        [
            "",
            "## Required Candidate-Overlay Rules",
            "",
            "| rule | JD strength | scope | required interpretation |",
            "|---|---|---|---|",
        ]
    )
    for rule_id, rule in catalog["rubric_summary"][
        "candidate_overlay_rules"
    ].items():
        lines.append(
            f"| `{rule_id}` | {rule['jd_strength']} | "
            f"{rule['evaluation_scope']} | {rule['description']} |"
        )

    lines.extend(
        [
            "",
            "## Fine Atom Evidence",
            "",
            "| atom | candidates | interpretation | prod. embedding retrieval | "
            "prod. vector/hybrid | evaluated ranking | Python observed | "
            "risk contexts |",
            "|---|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    risk_ids = [
        signal_id
        for signal_id, signal in catalog["rubric_summary"]["signals"].items()
        if signal["category"] == "risk_context"
    ]
    for atom_id, atom in catalog["fine_atoms"].items():
        risks = []
        for risk_id in risk_ids:
            prevalence = atom["risk_context_evidence"][risk_id][
                "any_career_prevalence"
            ]
            if prevalence:
                risks.append(f"{risk_id}={prevalence:.1%}")
        lines.append(
            f"| `{atom_id}` | {atom['candidate_count']:,} | "
            f"{atom['dominant_archetype']} | "
            f"{_compound_prevalence(atom, 'production_embeddings_retrieval'):.1%} | "
            f"{_compound_prevalence(atom, 'production_vector_or_hybrid_search'):.1%} | "
            f"{_compound_prevalence(atom, 'evaluated_ranking_system'):.1%} | "
            f"{_signal_prevalence(atom, 'python_engineering'):.1%} | "
            f"{', '.join(risks) or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Career Template Evidence",
            "",
            "| career template | occurrences | interpretation | direct evidence | "
            "compounds | risks |",
            "|---|---:|---|---|---|---|",
        ]
    )
    for career_id, career in catalog["career_templates"].items():
        categories = career["signals_by_category"]
        lines.append(
            f"| `{career_id}` | {career['occurrence_count']:,} | "
            f"{career['dominant_archetype']} | "
            f"{', '.join(categories['direct_requirement']) or '-'} | "
            f"{', '.join(career['compound_ids']) or '-'} | "
            f"{', '.join(categories['risk_context']) or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "This catalog establishes which JD evidence is explicitly present in "
            "the compact generator library. It does not establish official tier "
            "assignments. The next stage should add candidate-specific overlays "
            "(skills, recency, companies, location, behavior, and integrity) and "
            "then formulate probabilistic tier hypotheses.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_catalog(args.candidates, args.output_dir, args.rubric)
    print(
        "JD evidence catalog complete: "
        f"{result['career_template_count']} career templates, "
        f"{result['fine_atom_count']} fine atoms, "
        f"{result['candidate_count']:,} candidates aggregated."
    )


if __name__ == "__main__":
    main()
