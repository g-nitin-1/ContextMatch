#!/usr/bin/env python3
"""Build the first multi-world Idea 2 proxy scorer from candidate overlays."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analysis.common import DEFAULT_OUTPUT_DIR, markdown_table, percentile, write_json
from analysis.submission_export import write_submission_csv


SCORER_VERSION = "0.2.0"
DEFAULT_OVERLAY_JSONL = "candidate_overlay.jsonl"
DEFAULT_SCORE_CSV = "idea2_scores.csv"
DEFAULT_TOP100_CSV = "idea2_top100.csv"
DEFAULT_SUBMISSION_CSV = "idea2_submission.csv"
DEFAULT_SCORE_SUMMARY = "idea2_score_summary.json"
DEFAULT_SCORE_REPORT = "idea2_score_report.md"

TOP_KS = (10, 50, 100)

BASE_TIER_BY_ATOM = {
    "fine_atom_01": 4.9,
    "fine_atom_03": 4.45,
    "fine_atom_04": 4.7,
    "fine_atom_05": 4.9,
    "fine_atom_08": 4.8,
    "fine_atom_10": 4.8,
    "fine_atom_11": 4.75,
    "fine_atom_00": 3.4,
    "fine_atom_02": 1.8,
    "fine_atom_07": 0.75,
    "fine_atom_09": 0.45,
    "fine_atom_06": 0.08,
}

BASE_TIER_BY_ARCHETYPE = {
    "senior_plain_language": 4.85,
    "senior_explicit_ai": 4.75,
    "applied_ml": 3.4,
    "generic_ml": 1.8,
    "data_backend_adjacent": 0.75,
    "general_software": 0.45,
    "direct_occupation": 0.25,
    "general_professional": 0.08,
}

COMPOUND_WEIGHTS = {
    "end_to_end_intelligence_ownership": 0.45,
    "production_embeddings_retrieval": 0.42,
    "production_vector_or_hybrid_search": 0.38,
    "shipper_with_evaluation_depth": 0.36,
    "evaluated_ranking_system": 0.30,
}

SIGNAL_WEIGHTS = {
    "ranking_evaluation": 0.24,
    "retrieval_search": 0.22,
    "vector_hybrid_infrastructure": 0.20,
    "embeddings": 0.18,
    "ranking_recommendation_matching": 0.18,
    "production_delivery": 0.16,
    "operational_ownership": 0.12,
    "learning_to_rank": 0.14,
    "online_experimentation": 0.10,
    "meaningful_scale": 0.08,
    "product_context": 0.06,
    "recruiting_marketplace": 0.06,
    "distributed_inference": 0.05,
    "mentoring_leadership": 0.04,
    "zero_to_one_ownership": 0.08,
}

SKILL_WEIGHTS = {
    "ranking_evaluation": 0.10,
    "retrieval_search": 0.10,
    "vector_hybrid_infrastructure": 0.10,
    "embeddings": 0.09,
    "ranking_recommendation_matching": 0.09,
    "python_engineering": 0.07,
    "llm_finetuning": 0.06,
    "ml_depth": 0.06,
}

OVERLAY_RULE_PENALTIES = {
    "services_only_entire_career": -0.75,
    "research_only_without_production": -2.0,
    "recent_shallow_llm_only": -0.65,
    "senior_not_coding_recently": -0.25,
}

DIRECT_RELEVANCE_SIGNALS = {
    "embeddings",
    "ranking_evaluation",
    "ranking_recommendation_matching",
    "retrieval_search",
    "vector_hybrid_infrastructure",
}

PRODUCTION_COMPOUNDS = {
    "end_to_end_intelligence_ownership",
    "production_embeddings_retrieval",
    "production_vector_or_hybrid_search",
    "shipper_with_evaluation_depth",
}

DIRECT_TITLE_RE = re.compile(
    r"\b("
    r"machine learning|ml engineer|ai engineer|applied scientist|"
    r"data scientist|search engineer|recommendation systems?|"
    r"nlp engineer|ai research|applied ml"
    r")\b",
    re.IGNORECASE,
)
ADJACENT_TITLE_RE = re.compile(
    r"\b("
    r"software engineer|data engineer|analytics engineer|backend engineer|"
    r"platform engineer|research engineer"
    r")\b",
    re.IGNORECASE,
)
SENIOR_TITLE_RE = re.compile(
    r"\b(senior|staff|principal|lead|head|director|architect)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class WorldConfig:
    name: str
    description: str
    atom_tiers: dict[str, float]
    title_weight: float = 1.0
    evidence_weight: float = 1.0
    skill_weight: float = 1.0
    behavior_weight: float = 0.35
    logistics_weight: float = 0.5
    overlay_penalty_scale: float = 1.0
    integrity_policy: str = "hard"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "atom_tiers": self.atom_tiers,
            "title_weight": self.title_weight,
            "evidence_weight": self.evidence_weight,
            "skill_weight": self.skill_weight,
            "behavior_weight": self.behavior_weight,
            "logistics_weight": self.logistics_weight,
            "overlay_penalty_scale": self.overlay_penalty_scale,
            "integrity_policy": self.integrity_policy,
        }


def atom_tiers(**overrides: float) -> dict[str, float]:
    values = dict(BASE_TIER_BY_ATOM)
    values.update(overrides)
    return values


WORLD_CONFIGS = (
    WorldConfig(
        name="conservative",
        description=(
            "Prioritizes audited senior/applied evidence, keeps generic ML "
            "borderline, hard-excludes strongest honeypot proxies."
        ),
        atom_tiers=atom_tiers(fine_atom_00=3.25, fine_atom_02=1.45),
        evidence_weight=0.95,
        skill_weight=0.65,
        behavior_weight=0.25,
        logistics_weight=0.45,
        integrity_policy="hard",
    ),
    WorldConfig(
        name="senior_heavy",
        description=(
            "Gives the plain-language and explicit senior cohorts the strongest "
            "Tier-5 prior, matching the JD's senior-system-builder anchor."
        ),
        atom_tiers=atom_tiers(
            fine_atom_01=5.0,
            fine_atom_03=4.65,
            fine_atom_04=4.9,
            fine_atom_05=5.0,
            fine_atom_08=4.95,
            fine_atom_10=4.95,
            fine_atom_11=4.9,
            fine_atom_00=3.15,
            fine_atom_02=1.35,
        ),
        evidence_weight=1.05,
        skill_weight=0.55,
        behavior_weight=0.20,
        logistics_weight=0.35,
        integrity_policy="hard",
    ),
    WorldConfig(
        name="applied_ml_friendly",
        description=(
            "Raises applied-ML candidates when their career templates show "
            "ranking/evaluation depth, while keeping senior cohorts high."
        ),
        atom_tiers=atom_tiers(fine_atom_00=3.95, fine_atom_02=1.65),
        evidence_weight=1.05,
        skill_weight=0.75,
        behavior_weight=0.25,
        logistics_weight=0.45,
        integrity_policy="hard",
    ),
    WorldConfig(
        name="generic_tail_friendly",
        description=(
            "Stress-tests whether generic-ML or data/backend tail exceptions "
            "can enter the shortlist when skill overlays are useful."
        ),
        atom_tiers=atom_tiers(fine_atom_00=3.55, fine_atom_02=4.6, fine_atom_07=1.0),
        evidence_weight=1.05,
        skill_weight=1.1,
        behavior_weight=0.25,
        logistics_weight=0.4,
        integrity_policy="hard",
    ),
    WorldConfig(
        name="behavior_medium",
        description=(
            "Uses the same static structure as the conservative world but gives "
            "bounded behavior and availability the largest allowed influence."
        ),
        atom_tiers=atom_tiers(fine_atom_00=3.25, fine_atom_02=1.45),
        evidence_weight=0.95,
        skill_weight=0.65,
        behavior_weight=0.55,
        logistics_weight=0.65,
        integrity_policy="hard",
    ),
    WorldConfig(
        name="mutation_uncertain",
        description=(
            "Treats detected honeypot proxies as very strong penalties rather "
            "than absolute truth, to measure mutation-policy sensitivity."
        ),
        atom_tiers=atom_tiers(fine_atom_00=3.35, fine_atom_02=1.65),
        evidence_weight=0.95,
        skill_weight=0.65,
        behavior_weight=0.25,
        logistics_weight=0.45,
        integrity_policy="strong",
    ),
)


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def values(values_or_none: Any) -> set[str]:
    if not values_or_none:
        return set()
    return {str(value) for value in values_or_none}


def base_tier(record: dict[str, Any], world: WorldConfig) -> float:
    static = record.get("static", {})
    atom = static.get("fine_static_atom")
    if atom in world.atom_tiers:
        return world.atom_tiers[atom]
    archetype = static.get("summary_archetype", "general_professional")
    return BASE_TIER_BY_ARCHETYPE.get(archetype, 0.08)


def career_evidence_score(record: dict[str, Any]) -> float:
    evidence = record.get("career_evidence", {})
    any_compounds = values(evidence.get("any_career_compound_ids"))
    current_compounds = values(evidence.get("current_compound_ids"))
    any_signals = values(evidence.get("any_career_signal_ids"))
    current_signals = values(evidence.get("current_signal_ids"))

    score = sum(COMPOUND_WEIGHTS.get(compound, 0.0) for compound in any_compounds)
    score += sum(
        COMPOUND_WEIGHTS.get(compound, 0.0) * 0.25
        for compound in current_compounds
    )
    score += sum(SIGNAL_WEIGHTS.get(signal, 0.0) for signal in any_signals)
    score += sum(
        SIGNAL_WEIGHTS.get(signal, 0.0) * 0.25
        for signal in current_signals
    )
    return clamp(score, 0.0, 1.9)


def title_alignment_score(record: dict[str, Any]) -> float:
    title = str(record.get("static", {}).get("current_title", ""))
    if DIRECT_TITLE_RE.search(title):
        return 0.25 if SENIOR_TITLE_RE.search(title) else 0.20
    if ADJACENT_TITLE_RE.search(title):
        return 0.05
    return -0.08


def skill_score(record: dict[str, Any]) -> float:
    skill_overlay = record.get("skill_overlay", {})
    skill_signals = values(skill_overlay.get("skill_signal_ids"))
    advanced_counts = skill_overlay.get("advanced_or_expert_signal_counts", {})
    durations = skill_overlay.get("max_duration_months_by_signal", {})

    score = 0.0
    for signal in skill_signals:
        score += SKILL_WEIGHTS.get(signal, 0.0)
        if int(advanced_counts.get(signal, 0) or 0) > 0:
            score += SKILL_WEIGHTS.get(signal, 0.0) * 0.5
        if as_float(durations.get(signal)) >= 24:
            score += SKILL_WEIGHTS.get(signal, 0.0) * 0.25
    return clamp(score, 0.0, 0.8)


def behavior_score(record: dict[str, Any]) -> float:
    overlay = record.get("availability_overlay", {})
    score = 0.0

    inactive_days = overlay.get("inactive_days")
    if inactive_days is None:
        score -= 0.08
    elif inactive_days <= 14:
        score += 0.24
    elif inactive_days <= 45:
        score += 0.15
    elif inactive_days <= 90:
        score += 0.05
    elif inactive_days > 180:
        score -= 0.22
    else:
        score -= 0.06

    if overlay.get("open_to_work"):
        score += 0.14

    notice = overlay.get("notice_period_days")
    if notice is not None:
        if notice <= 30:
            score += 0.14
        elif notice <= 60:
            score += 0.05
        elif notice > 90:
            score -= 0.10

    response_rate = as_float(overlay.get("response_rate"), 0.5)
    score += clamp((response_rate - 0.5) * 0.35, -0.18, 0.18)

    response_time = overlay.get("response_time_hours")
    if response_time is not None:
        if response_time <= 24:
            score += 0.08
        elif response_time > 168:
            score -= 0.10

    saved = as_float(overlay.get("saved_by_recruiters_30d"))
    search = as_float(overlay.get("search_appearance_30d"))
    views = as_float(overlay.get("profile_views_30d"))
    if saved >= 20:
        score += 0.12
    elif saved >= 10:
        score += 0.08
    if search >= 250:
        score += 0.08
    elif search >= 100:
        score += 0.04
    if views >= 50:
        score += 0.05

    score += clamp((as_float(overlay.get("interview_completion_rate"), 0.7) - 0.7) * 0.18, -0.08, 0.08)
    score += clamp((as_float(overlay.get("offer_acceptance_rate"), 0.6) - 0.6) * 0.14, -0.06, 0.06)
    score += min(int(overlay.get("verification_count", 0) or 0), 3) * 0.025

    github = overlay.get("github_activity_score")
    if github is not None:
        score += clamp((as_float(github) - 50.0) / 100.0 * 0.12, -0.06, 0.08)

    return clamp(score, -0.8, 1.0)


def logistics_score(record: dict[str, Any]) -> float:
    bucket = record.get("logistics_overlay", {}).get("location_bucket")
    return {
        "pune": 0.22,
        "noida": 0.22,
        "ncr": 0.15,
        "india_other": 0.04,
        "outside_india_relocatable": -0.05,
        "outside_india": -0.25,
    }.get(bucket, -0.05)


def risk_context_penalty(record: dict[str, Any]) -> float:
    evidence = record.get("career_evidence", {})
    risks = values(evidence.get("any_career_risk_context_ids"))
    signals = values(evidence.get("any_career_signal_ids"))
    compounds = values(evidence.get("any_career_compound_ids"))
    skill_signals = values(record.get("skill_overlay", {}).get("skill_signal_ids"))

    penalty = 0.0
    has_direct_relevance = bool((signals | skill_signals) & DIRECT_RELEVANCE_SIGNALS)
    has_production_depth = bool(compounds & PRODUCTION_COMPOUNDS)
    if "computer_vision_primary" in risks or "computer_vision_primary" in skill_signals:
        if not has_direct_relevance:
            penalty -= 0.35
        else:
            penalty -= 0.10
    if "llm_application_context" in risks and not has_production_depth:
        penalty -= 0.15
    return penalty


def overlay_rule_penalty(record: dict[str, Any]) -> float:
    penalty = 0.0
    for rule_id, verdict in record.get("candidate_overlay_rules", {}).items():
        if verdict.get("fired"):
            penalty += OVERLAY_RULE_PENALTIES.get(rule_id, 0.0)
    return penalty


def integrity_penalty(record: dict[str, Any], world: WorldConfig) -> float:
    integrity = record.get("integrity_overlay", {})
    high_confidence = values(integrity.get("high_confidence_rules"))
    honeypot_proxy = values(integrity.get("honeypot_proxy_rules"))
    risk_level = integrity.get("risk_level", "none")

    if world.integrity_policy == "hard" and honeypot_proxy:
        return -100.0

    penalty = 0.0
    if honeypot_proxy:
        penalty -= 8.0
    if "technology_before_release" in high_confidence:
        penalty -= 4.0
    if "role_duration_large_mismatch" in high_confidence:
        penalty -= 1.25
    if "career_duration_exceeds_experience" in high_confidence:
        penalty -= 1.0
    if risk_level == "high":
        penalty -= 1.5
    elif risk_level == "medium":
        penalty -= 0.4
    return penalty


def fired_overlay_rules(record: dict[str, Any]) -> list[str]:
    return sorted(
        rule_id
        for rule_id, verdict in record.get("candidate_overlay_rules", {}).items()
        if verdict.get("fired")
    )


def score_candidate(record: dict[str, Any], world: WorldConfig) -> dict[str, float]:
    components = {
        "base_tier": base_tier(record, world),
        "title_alignment": title_alignment_score(record) * world.title_weight,
        "career_evidence": career_evidence_score(record) * world.evidence_weight,
        "skill_overlay": skill_score(record) * world.skill_weight,
        "behavior": behavior_score(record) * world.behavior_weight,
        "logistics": logistics_score(record) * world.logistics_weight,
        "risk_context": risk_context_penalty(record),
        "overlay_rules": overlay_rule_penalty(record) * world.overlay_penalty_scale,
        "integrity": integrity_penalty(record, world),
    }
    score = sum(components.values())
    components["score"] = score
    return {key: round(value, 6) for key, value in components.items()}


def score_record(record: dict[str, Any], worlds: tuple[WorldConfig, ...]) -> dict[str, Any]:
    static = record.get("static", {})
    evidence = record.get("career_evidence", {})
    integrity = record.get("integrity_overlay", {})
    skill = record.get("skill_overlay", {})
    rules = fired_overlay_rules(record)
    world_scores = {world.name: score_candidate(record, world) for world in worlds}
    score_values = [payload["score"] for payload in world_scores.values()]

    row: dict[str, Any] = {
        "candidate_id": record["candidate_id"],
        "summary_archetype": static.get("summary_archetype"),
        "fine_static_atom": static.get("fine_static_atom"),
        "static_class": static.get("static_class"),
        "current_title": static.get("current_title"),
        "current_company": static.get("current_company"),
        "current_industry": static.get("current_industry"),
        "years_of_experience": static.get("years_of_experience"),
        "location_bucket": record.get("logistics_overlay", {}).get("location_bucket"),
        "location": record.get("logistics_overlay", {}).get("location"),
        "country": record.get("logistics_overlay", {}).get("country"),
        "inactive_days": record.get("availability_overlay", {}).get("inactive_days"),
        "open_to_work": record.get("availability_overlay", {}).get("open_to_work"),
        "notice_period_days": record.get("availability_overlay", {}).get(
            "notice_period_days"
        ),
        "integrity_risk_level": integrity.get("risk_level", "none"),
        "high_confidence_rules": ";".join(integrity.get("high_confidence_rules", [])),
        "honeypot_proxy_rules": ";".join(integrity.get("honeypot_proxy_rules", [])),
        "overlay_rules_fired": ";".join(rules),
        "career_compounds": ";".join(evidence.get("any_career_compound_ids", [])),
        "career_signals": ";".join(evidence.get("any_career_signal_ids", [])),
        "skill_names": ";".join(skill.get("skill_names", [])),
        "skill_signals": ";".join(skill.get("skill_signal_ids", [])),
        "mean_score": round(sum(score_values) / len(score_values), 6),
        "min_score": round(min(score_values), 6),
        "max_score": round(max(score_values), 6),
        "score_range": round(max(score_values) - min(score_values), 6),
    }
    for component in (
        "base_tier",
        "title_alignment",
        "career_evidence",
        "skill_overlay",
        "behavior",
        "logistics",
        "risk_context",
        "overlay_rules",
        "integrity",
    ):
        row[f"mean_{component}"] = round(
            sum(payload[component] for payload in world_scores.values())
            / len(world_scores),
            6,
        )
    for world in worlds:
        row[f"score_{world.name}"] = world_scores[world.name]["score"]
    return row


def assign_ranks(rows: list[dict[str, Any]], worlds: tuple[WorldConfig, ...]) -> None:
    for world in worlds:
        score_key = f"score_{world.name}"
        rank_key = f"rank_{world.name}"
        ordered = sorted(rows, key=lambda row: (-float(row[score_key]), row["candidate_id"]))
        for rank, row in enumerate(ordered, 1):
            row[rank_key] = rank

    for row in rows:
        ranks = [int(row[f"rank_{world.name}"]) for world in worlds]
        row["mean_rank"] = round(sum(ranks) / len(ranks), 3)
        row["best_rank"] = min(ranks)
        row["worst_rank"] = max(ranks)
        row["rank_range"] = max(ranks) - min(ranks)

    rows.sort(
        key=lambda row: (
            -float(row["mean_score"]),
            float(row["mean_rank"]),
            row["candidate_id"],
        )
    )
    for rank, row in enumerate(rows, 1):
        row["final_rank"] = rank


def compact_candidate(row: dict[str, Any], worlds: tuple[WorldConfig, ...]) -> dict[str, Any]:
    payload = {
        "candidate_id": row["candidate_id"],
        "final_rank": row["final_rank"],
        "mean_score": row["mean_score"],
        "score_range": row["score_range"],
        "best_rank": row["best_rank"],
        "worst_rank": row["worst_rank"],
        "rank_range": row["rank_range"],
        "summary_archetype": row["summary_archetype"],
        "fine_static_atom": row["fine_static_atom"],
        "current_title": row["current_title"],
        "current_company": row["current_company"],
        "integrity_risk_level": row["integrity_risk_level"],
        "honeypot_proxy_rules": row["honeypot_proxy_rules"],
        "overlay_rules_fired": row["overlay_rules_fired"],
        "career_compounds": row["career_compounds"],
        "skill_signals": row["skill_signals"],
    }
    for world in worlds:
        payload[f"rank_{world.name}"] = row[f"rank_{world.name}"]
    return payload


def top_set(rows: list[dict[str, Any]], world: WorldConfig, k: int) -> set[str]:
    return {
        row["candidate_id"]
        for row in sorted(rows, key=lambda item: item[f"rank_{world.name}"])[:k]
    }


def summarize_world_top(
    rows: list[dict[str, Any]],
    world: WorldConfig,
    k: int,
) -> dict[str, Any]:
    top_rows = sorted(rows, key=lambda item: item[f"rank_{world.name}"])[:k]
    return {
        "archetypes": dict(Counter(row["summary_archetype"] for row in top_rows)),
        "fine_atoms": dict(Counter(row["fine_static_atom"] for row in top_rows)),
        "high_risk_count": sum(
            row["integrity_risk_level"] == "high" for row in top_rows
        ),
        "honeypot_proxy_count": sum(
            bool(row["honeypot_proxy_rules"]) for row in top_rows
        ),
        "overlay_rule_counts": dict(
            Counter(
                rule
                for row in top_rows
                for rule in str(row["overlay_rules_fired"]).split(";")
                if rule
            )
        ),
    }


def build_summary(
    rows: list[dict[str, Any]],
    worlds: tuple[WorldConfig, ...],
    overlay_path: Path,
    score_path: Path,
    top100_path: Path,
    submission_path: Path,
) -> dict[str, Any]:
    mean_scores = sorted(float(row["mean_score"]) for row in rows)
    stability = {}
    for k in TOP_KS:
        sets = [top_set(rows, world, k) for world in worlds]
        intersection = set.intersection(*sets)
        union = set.union(*sets)
        stability[str(k)] = {
            "intersection_count": len(intersection),
            "union_count": len(union),
            "intersection_over_union": round(len(intersection) / len(union), 6)
            if union
            else 0.0,
            "always_top_k": [
                compact_candidate(row, worlds)
                for row in rows
                if row["candidate_id"] in intersection
            ][: min(k, 25)],
        }

    world_top = {
        world.name: {
            str(k): summarize_world_top(rows, world, k)
            for k in TOP_KS
        }
        for world in worlds
    }
    union_top50 = set.union(*(top_set(rows, world, 50) for world in worlds))
    fragile = sorted(
        (row for row in rows if row["candidate_id"] in union_top50),
        key=lambda row: (-int(row["rank_range"]), float(row["mean_rank"])),
    )[:25]

    return {
        "scorer_version": SCORER_VERSION,
        "overlay_path": str(overlay_path),
        "score_csv": str(score_path),
        "top100_csv": str(top100_path),
        "submission_csv": str(submission_path),
        "candidate_count": len(rows),
        "worlds": [world.as_dict() for world in worlds],
        "score_percentiles": {
            "p01": round(percentile(mean_scores, 0.01), 6),
            "p10": round(percentile(mean_scores, 0.10), 6),
            "p50": round(percentile(mean_scores, 0.50), 6),
            "p90": round(percentile(mean_scores, 0.90), 6),
            "p99": round(percentile(mean_scores, 0.99), 6),
        },
        "stability": stability,
        "world_top_summaries": world_top,
        "top_by_mean": [compact_candidate(row, worlds) for row in rows[:50]],
        "fragile_top50_union": [compact_candidate(row, worlds) for row in fragile],
    }


def write_scores_csv(
    rows: list[dict[str, Any]],
    path: Path,
    worlds: tuple[WorldConfig, ...],
) -> None:
    fieldnames = [
        "final_rank",
        "candidate_id",
        "mean_score",
        "min_score",
        "max_score",
        "score_range",
        "mean_rank",
        "best_rank",
        "worst_rank",
        "rank_range",
        "summary_archetype",
        "fine_static_atom",
        "static_class",
        "current_title",
        "current_company",
        "current_industry",
        "years_of_experience",
        "location",
        "country",
        "location_bucket",
        "inactive_days",
        "open_to_work",
        "notice_period_days",
        "integrity_risk_level",
        "high_confidence_rules",
        "honeypot_proxy_rules",
        "overlay_rules_fired",
        "career_compounds",
        "career_signals",
        "skill_names",
        "skill_signals",
        "mean_base_tier",
        "mean_title_alignment",
        "mean_career_evidence",
        "mean_skill_overlay",
        "mean_behavior",
        "mean_logistics",
        "mean_risk_context",
        "mean_overlay_rules",
        "mean_integrity",
    ]
    for world in worlds:
        fieldnames.append(f"score_{world.name}")
        fieldnames.append(f"rank_{world.name}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_top100_csv(
    rows: list[dict[str, Any]],
    path: Path,
    worlds: tuple[WorldConfig, ...],
) -> None:
    compact_rows = [compact_candidate(row, worlds) for row in rows[:100]]
    fieldnames = list(compact_rows[0]) if compact_rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(compact_rows)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    worlds = summary["worlds"]
    stability = summary["stability"]
    top100 = summary["world_top_summaries"]
    lines = [
        "# Idea 2 Proxy Scorer",
        "",
        "This is a deterministic proxy ranker built on the candidate overlay. It "
        "does not claim to recover hidden labels; it reports stability across "
        "plausible scoring worlds.",
        "",
        "## Coverage",
        "",
        f"- Scorer version: `{summary['scorer_version']}`",
        f"- Candidates scored: {summary['candidate_count']:,}",
        f"- Full score CSV: `{summary['score_csv']}`",
        f"- Top-100 CSV: `{summary['top100_csv']}`",
        f"- Validator-ready CSV: `{summary['submission_csv']}`",
        "",
        "## Worlds",
        "",
        markdown_table(
            (
                "World",
                "Integrity policy",
                "Title weight",
                "Evidence weight",
                "Skill weight",
                "Behavior weight",
                "Description",
            ),
            (
                (
                    world["name"],
                    world["integrity_policy"],
                    world["title_weight"],
                    world["evidence_weight"],
                    world["skill_weight"],
                    world["behavior_weight"],
                    world["description"],
                )
                for world in worlds
            ),
        ),
        "",
        "## Stability",
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
                for k, values in sorted(stability.items(), key=lambda item: int(item[0]))
            ),
        ),
        "",
        "## Top Candidates By Mean Score",
        "",
        markdown_table(
            (
                "Rank",
                "Candidate",
                "Archetype",
                "Atom",
                "Mean score",
                "Rank range",
                "Integrity",
                "Overlay rules",
            ),
            (
                (
                    row["final_rank"],
                    row["candidate_id"],
                    row["summary_archetype"],
                    row["fine_static_atom"],
                    row["mean_score"],
                    row["rank_range"],
                    row["integrity_risk_level"],
                    row["overlay_rules_fired"] or "-",
                )
                for row in summary["top_by_mean"][:20]
            ),
        ),
        "",
        "## Top-100 Safeguards",
        "",
        markdown_table(
            ("World", "High-risk", "Honeypot proxy", "Overlay rules"),
            (
                (
                    world,
                    values["100"]["high_risk_count"],
                    values["100"]["honeypot_proxy_count"],
                    ", ".join(
                        f"{rule}={count}"
                        for rule, count in sorted(
                            values["100"]["overlay_rule_counts"].items()
                        )
                    )
                    or "-",
                )
                for world, values in top100.items()
            ),
        ),
        "",
        "## Fragile Top-50 Union",
        "",
        "These candidates appear in at least one world's top 50 and have the "
        "largest rank range across worlds.",
        "",
        markdown_table(
            (
                "Candidate",
                "Archetype",
                "Atom",
                "Mean score",
                "Best rank",
                "Worst rank",
                "Rank range",
            ),
            (
                (
                    row["candidate_id"],
                    row["summary_archetype"],
                    row["fine_static_atom"],
                    row["mean_score"],
                    row["best_rank"],
                    row["worst_rank"],
                    row["rank_range"],
                )
                for row in summary["fragile_top50_union"][:20]
            ),
        ),
        "",
        "## Interpretation Boundary",
        "",
        "Use this output to inspect shortlist stability and obvious failure modes. "
        "It is still an Idea 2 proxy, not a validated local score.",
        "",
        "All current worlds keep two fixed points: senior system-builder cohorts "
        "remain above applied/generic cohorts, and high-confidence honeypot "
        "proxies are suppressed. That is defensible from the JD and challenge "
        "documentation, but it means stability here tests weighting, behavior, "
        "mutation policy, and boundary sensitivity rather than a fundamentally "
        "different tier ordering.",
        "",
        "`BASE_TIER_BY_ATOM` is therefore the core unvalidated hypothesis in "
        "this scorer. It needs deliberate sign-off before Idea 2 is frozen; "
        "stable rankings across these worlds do not prove the tier mapping is "
        "officially correct.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def build_scores(
    output_dir: Path,
    overlay_jsonl: Path | None = None,
    worlds: tuple[WorldConfig, ...] = WORLD_CONFIGS,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = overlay_jsonl or output_dir / DEFAULT_OVERLAY_JSONL
    if not overlay_path.exists():
        raise FileNotFoundError(f"candidate overlay not found: {overlay_path}")

    rows = []
    with overlay_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(score_record(json.loads(line), worlds))

    assign_ranks(rows, worlds)
    score_path = output_dir / DEFAULT_SCORE_CSV
    top100_path = output_dir / DEFAULT_TOP100_CSV
    submission_path = output_dir / DEFAULT_SUBMISSION_CSV
    write_scores_csv(rows, score_path, worlds)
    write_top100_csv(rows, top100_path, worlds)
    write_submission_csv(rows, submission_path)

    summary = build_summary(
        rows,
        worlds,
        overlay_path,
        score_path,
        top100_path,
        submission_path,
    )
    write_json(output_dir / DEFAULT_SCORE_SUMMARY, summary)
    write_report(output_dir / DEFAULT_SCORE_REPORT, summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--overlay-jsonl",
        type=Path,
        default=None,
        help="Defaults to candidate_overlay.jsonl inside --output-dir.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_scores(args.output_dir, args.overlay_jsonl)
    print(
        "Idea 2 scoring complete: "
        f"{summary['candidate_count']:,} candidates written to "
        f"{summary['score_csv']}"
    )


if __name__ == "__main__":
    main()
