#!/usr/bin/env python3
"""General JD-to-candidate ranker."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import resource
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterator

from analysis.common import DEFAULT_DATASET, DEFAULT_OUTPUT_DIR, REPO_ROOT, stream_candidates
from analysis.integrity_checks import DEFAULT_KNOWLEDGE_BASE, IntegrityChecker
from solution.candidate_features import DEFAULT_AS_OF, build_candidate_overlay
from solution.jd_parser import parse_jd
from solution.precompute import DEFAULT_FEATURES
from solution.requirement_spec import RequirementItem, RequirementSpec, load_spec
from solution.text_features import (
    career_weighted_text,
    query_coverage_score,
    query_coverage_score_from_tokens,
)


DEFAULT_JD = REPO_ROOT / "India_runs_data_and_ai_challenge" / "job_description.docx"
DEFAULT_OVERLAY = DEFAULT_OUTPUT_DIR / "candidate_overlay.jsonl"
DEFAULT_OUT = DEFAULT_OUTPUT_DIR / "solution_ranker_submission.csv"
SUBMISSION_COLUMNS = ("candidate_id", "rank", "score", "reasoning")
EVIDENCE_WEIGHT = 5.0
SEMANTIC_WEIGHT = 0.45
SKILL_WEIGHT = 1.0
SENIORITY_ORDERING_CAP = 0.4
ROLE_TITLE_ORDERING_CAP = 0.4

# Signals that show the candidate has done JD-relevant technical work in a
# role. Generic support signals such as product_context, production_delivery,
# scale, ownership, or leadership are intentionally not enough by themselves.
CAREER_FLOOR_SIGNALS = {
    "embeddings",
    "learning_to_rank",
    "ranking_evaluation",
    "ranking_recommendation_matching",
    "retrieval_search",
    "vector_hybrid_infrastructure",
}
LEVEL_INDEX = {
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "staff": 4,
    "principal": 5,
}
OWNERSHIP_SIGNALS = {
    "meaningful_scale",
    "mentoring_leadership",
    "operational_ownership",
    "zero_to_one_ownership",
}
HANDS_ON_SIGNALS = CAREER_FLOOR_SIGNALS | {"python_engineering"}
MANAGEMENT_TITLE_RE = re.compile(
    r"\b(manager|director|head|vp|chief|people lead)\b",
    re.IGNORECASE,
)
SENIOR_TITLE_RE = re.compile(r"\b(senior|staff|lead|principal)\b", re.IGNORECASE)
TECHNICAL_TITLE_RE = re.compile(
    r"\b(engineer|scientist|developer|architect|ml|ai|data|search|backend|software)\b",
    re.IGNORECASE,
)
COMPOUND_REASON_PHRASES = {
    "production_embeddings_retrieval": (
        "shipped production embedding and retrieval systems",
        "worked on production retrieval infrastructure",
        "has production retrieval-system evidence",
    ),
    "production_vector_or_hybrid_search": (
        "built vector or hybrid search infrastructure",
        "worked with search infrastructure beyond keyword matching",
        "shows vector or hybrid-search delivery",
    ),
    "evaluated_ranking_system": (
        "evaluated ranking quality with relevance metrics",
        "worked on ranking systems with quality evaluation",
        "connected ranking work to measurable relevance outcomes",
    ),
    "shipper_with_evaluation_depth": (
        "shipped systems with evaluation depth",
        "combined delivery ownership with model-quality measurement",
        "has shipping evidence tied to evaluation",
    ),
    "end_to_end_intelligence_ownership": (
        "owned an intelligence system end to end",
        "drove ranking or intelligence work from design into production",
        "shows end-to-end ownership of applied AI systems",
    ),
}
SIGNAL_REASON_PHRASES = {
    "embeddings": "embedding work",
    "retrieval_search": "retrieval/search work",
    "ranking_recommendation_matching": "ranking, recommendation, or matching work",
    "ranking_evaluation": "ranking evaluation",
    "online_experimentation": "online experimentation",
    "learning_to_rank": "learning-to-rank exposure",
    "production_delivery": "production delivery",
    "operational_ownership": "operational ownership",
    "zero_to_one_ownership": "zero-to-one ownership",
    "meaningful_scale": "meaningful scale",
    "mentoring_leadership": "technical mentoring",
    "vector_hybrid_infrastructure": "vector or hybrid-search infrastructure",
    "python_engineering": "Python engineering",
}
REQUIREMENT_REASON_PHRASES = {
    "production_retrieval": (
        "the JD's production-retrieval ask",
        "the role's retrieval and ranking requirement",
        "the core search/matching systems requirement",
    ),
    "evaluated_ranking": (
        "the JD's evaluation-depth requirement",
        "the relevance-quality measurement ask",
        "the ranking-evaluation requirement",
    ),
    "end_to_end_ownership": (
        "the senior IC ownership requirement",
        "the role's end-to-end ownership expectation",
        "the JD's shipped-system ownership bar",
    ),
    "ml_engineering": (
        "the applied ML engineering requirement",
        "the role's AI engineering depth",
        "the ML systems requirement",
    ),
    "vector_hybrid_search": (
        "the vector/hybrid search preference",
        "the search-infrastructure requirement",
        "the retrieval-infrastructure preference",
    ),
    "senior_leadership": (
        "the senior technical-leadership signal",
        "the mentoring and ownership preference",
        "the senior IC scope expectation",
    ),
    "people_leadership": (
        "the management-track requirement",
        "the people-leadership requirement",
        "the team-management ask",
    ),
}
INTERNAL_REASONING_PATTERNS = (
    "evidence=",
    "semantic=",
    "mean_",
    "idea1",
    "idea2",
    "proxy",
    "archetype",
    "_",
)


@dataclass(frozen=True)
class ScoreBreakdown:
    candidate_id: str
    score: float
    evidence: float
    semantic: float
    skills: float
    behavior: float
    logistics: float
    seniority: float
    penalties: float
    blocked: bool
    blocked_reasons: tuple[str, ...]
    reasoning: str


@dataclass(frozen=True)
class RankRun:
    rows: list[ScoreBreakdown]
    candidate_count: int
    eligible_count: int
    blocked_count: int


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc


def _as_set(values: Any) -> set[str]:
    if not values:
        return set()
    return {str(value) for value in values}


def _rule_fired(overlay: dict[str, Any], rule_id: str) -> bool:
    verdict = overlay.get("candidate_overlay_rules", {}).get(rule_id)
    return bool(verdict and verdict.get("fired"))


def _item_score(item: RequirementItem, signals: set[str], compounds: set[str]) -> float:
    signal_hits = len(set(item.evidence_signals) & signals)
    signal_score = signal_hits / len(item.evidence_signals)
    if item.compounds:
        if compounds & set(item.compounds):
            return item.weight
        return item.weight * 0.45 * signal_score
    return item.weight * signal_score


def evidence_score(spec: RequirementSpec, overlay: dict[str, Any]) -> float:
    career = overlay.get("career_evidence", {})
    signals = _as_set(career.get("any_career_signal_ids"))
    compounds = _as_set(career.get("any_career_compound_ids"))

    must_weight = sum(item.weight for item in spec.must_have)
    nice_weight = sum(item.weight for item in spec.nice_to_have) or 1.0
    must = sum(_item_score(item, signals, compounds) for item in spec.must_have)
    nice = sum(_item_score(item, signals, compounds) for item in spec.nice_to_have)
    must_norm = must / must_weight if must_weight else 0.0
    nice_norm = nice / nice_weight
    return 0.82 * must_norm + 0.18 * nice_norm


def skill_score(spec: RequirementSpec, overlay: dict[str, Any]) -> float:
    skills = overlay.get("skill_overlay", {})
    skill_signals = _as_set(skills.get("skill_signal_ids"))
    advanced_counts = skills.get("advanced_or_expert_signal_counts", {})
    overlap = skill_signals & spec.evidence_signal_ids
    if not overlap:
        return 0.0
    advanced_overlap = {
        signal for signal in overlap if int(advanced_counts.get(signal, 0) or 0) > 0
    }
    base = 0.03 * len(overlap) + 0.02 * len(advanced_overlap)
    return min(0.22, base)


def behavior_modifier(overlay: dict[str, Any]) -> float:
    behavior = overlay.get("availability_overlay", {})
    score = 0.0
    inactive_days = behavior.get("inactive_days")
    if isinstance(inactive_days, int):
        if inactive_days <= 30:
            score += 0.08
        elif inactive_days > 120:
            score -= 0.10
        elif inactive_days > 60:
            score -= 0.04
    if behavior.get("open_to_work"):
        score += 0.06
    response_rate = behavior.get("response_rate")
    if isinstance(response_rate, (int, float)):
        score += max(-0.06, min(0.08, (float(response_rate) - 0.5) * 0.16))
    notice = behavior.get("notice_period_days")
    if isinstance(notice, int):
        if notice <= 30:
            score += 0.04
        elif notice >= 90:
            score -= 0.04
    return max(-0.18, min(0.22, score))


def logistics_modifier(overlay: dict[str, Any]) -> float:
    logistics = overlay.get("logistics_overlay", {})
    bucket = logistics.get("location_bucket")
    if bucket in {"pune", "noida", "ncr"}:
        return 0.08
    if bucket == "outside_india":
        return -0.12
    if bucket == "outside_india_relocatable":
        return -0.04
    return 0.0


def seniority_alignment(spec: RequirementSpec, overlay: dict[str, Any]) -> float:
    seniority = spec.seniority
    strength = float(seniority.get("strength", 0.0) or 0.0)
    target_level = str(seniority.get("level", "unspecified"))
    target_track = str(seniority.get("track", "either"))
    if strength <= 0 or (target_level == "unspecified" and target_track == "either"):
        return 0.0
    if not meets_career_evidence_floor(spec, overlay):
        return 0.0

    career = overlay.get("career_evidence", {})
    signals = _as_set(career.get("any_career_signal_ids"))
    compounds = _as_set(career.get("any_career_compound_ids"))
    ownership = ownership_score(signals, compounds)
    raw = (
        0.35 * level_alignment(target_level, overlay)
        + 0.35 * track_alignment(target_track, overlay, signals, compounds)
        + 0.20 * ownership
        + 0.10 * years_alignment(seniority, overlay)
    )

    # For senior IC roles, title/years/hands-on alone should not create a
    # positive modifier. The JD asks for demonstrated scope and ownership.
    if target_level in {"senior", "staff", "principal"} and target_track == "ic":
        if ownership <= 0:
            raw = min(raw, 0.0)

    return max(-strength, min(strength, raw * strength))


def seniority_ordering_modifier(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    alignment: float | None = None,
    cap: float = SENIORITY_ORDERING_CAP,
) -> float:
    """Bounded extra ordering influence for positive JD seniority fit.

    `seniority_alignment` is intentionally conservative because it also handles
    penalties. For senior/staff IC roles, the top of the shortlist needs a small
    extra nudge toward candidates who demonstrate the requested level and track.
    The modifier is normalized by the JD-emitted strength and never applies to
    evidence-poor candidates because `seniority_alignment` itself enforces the
    career-evidence floor.
    """
    if cap <= 0:
        return 0.0
    strength = float(spec.seniority.get("strength", 0.0) or 0.0)
    if strength <= 0:
        return 0.0
    base_alignment = seniority_alignment(spec, overlay) if alignment is None else alignment
    if base_alignment <= 0:
        return 0.0
    fit = min(1.0, base_alignment / strength)
    return cap * fit


def level_alignment(target_level: str, overlay: dict[str, Any]) -> float:
    if target_level == "unspecified":
        return 0.0
    candidate_level = infer_candidate_level(overlay)
    target = LEVEL_INDEX.get(target_level)
    candidate = LEVEL_INDEX.get(candidate_level)
    if target is None or candidate is None:
        return 0.0
    delta = abs(candidate - target)
    if delta == 0:
        return 1.0
    if delta == 1:
        return 0.25
    if delta == 2:
        return -0.35
    return -0.75


def infer_candidate_level(overlay: dict[str, Any]) -> str:
    static = overlay.get("static", {})
    title = str(static.get("current_title") or "").lower()
    if re.search(r"\b(intern|junior|associate|entry[- ]level)\b", title):
        return "junior"
    if re.search(r"\b(principal|director|head|vp|chief)\b", title):
        return "principal"
    if re.search(r"\bstaff\b", title):
        return "staff"
    if re.search(r"\b(senior|lead)\b", title):
        return "senior"
    years = static.get("years_of_experience")
    if isinstance(years, (int, float)):
        if years >= 10:
            return "principal"
        if years >= 8:
            return "senior"
        if years >= 3:
            return "mid"
        return "junior"
    return "mid"


def track_alignment(
    target_track: str,
    overlay: dict[str, Any],
    signals: set[str],
    compounds: set[str],
) -> float:
    if target_track == "either":
        return 0.0
    static = overlay.get("static", {})
    title = str(static.get("current_title") or "")
    hands_on = bool((signals & HANDS_ON_SIGNALS) or compounds)
    leadership = bool("mentoring_leadership" in signals or MANAGEMENT_TITLE_RE.search(title))
    management_title = bool(MANAGEMENT_TITLE_RE.search(title))
    technical_title = bool(TECHNICAL_TITLE_RE.search(title))

    if target_track == "ic":
        if hands_on and not (management_title and not technical_title):
            return 1.0
        if management_title and not hands_on:
            return -1.0
        return -0.25

    if target_track == "management":
        if leadership and management_title:
            return 1.0
        if leadership:
            return 0.6
        if hands_on and not management_title:
            return -0.45
        return -0.2

    return 0.0


def ownership_score(signals: set[str], compounds: set[str]) -> float:
    score = 0.0
    if "end_to_end_intelligence_ownership" in compounds:
        score += 0.7
    if "shipper_with_evaluation_depth" in compounds:
        score += 0.3
    if signals & OWNERSHIP_SIGNALS:
        score += min(0.6, 0.2 * len(signals & OWNERSHIP_SIGNALS))
    return min(1.0, score)


def title_family(role_title: str) -> str:
    normalized = role_title.lower()
    if re.search(r"\b(ai|ml|machine learning|nlp)\b", normalized):
        return "ai_ml"
    if "data" in normalized:
        return "data"
    if "backend" in normalized:
        return "backend"
    if "software" in normalized:
        return "software"
    if "manager" in normalized:
        return "management"
    return "generic"


def title_function(role_title: str) -> str:
    normalized = role_title.lower()
    for term in ("engineer", "scientist", "manager", "analyst", "architect", "developer"):
        if term in normalized:
            return term
    return "generic"


def role_title_alignment_score(role_title: str, candidate_title: str) -> float:
    """Return 0..1 title-family/function fit derived from the JD title."""
    family = title_family(role_title)
    function = title_function(role_title)
    title = candidate_title.lower()

    if family == "ai_ml":
        family_score = (
            1.0
            if re.search(r"\b(ai|ml|machine learning|nlp)\b", title)
            else 0.45
            if re.search(r"\b(data scientist|applied scientist)\b", title)
            else 0.0
        )
    elif family == "data":
        family_score = (
            1.0
            if "data" in title
            else 0.3
            if re.search(r"\b(ai|ml|machine learning)\b", title)
            else 0.0
        )
    elif family == "backend":
        family_score = 1.0 if "backend" in title else 0.4 if "software" in title else 0.0
    elif family == "software":
        family_score = (
            1.0
            if "software" in title
            else 0.6
            if re.search(r"\b(backend|developer|engineer)\b", title)
            else 0.0
        )
    elif family == "management":
        family_score = 1.0 if re.search(r"\b(manager|director|head|lead)\b", title) else 0.0
    else:
        family_score = 0.0

    if function == "engineer":
        function_score = (
            1.0
            if "engineer" in title
            else 0.65
            if "scientist" in title
            else 0.45
            if re.search(r"\b(architect|developer)\b", title)
            else 0.0
        )
    elif function == "scientist":
        function_score = 1.0 if "scientist" in title else 0.65 if "engineer" in title else 0.0
    elif function == "manager":
        function_score = 1.0 if "manager" in title else 0.6 if re.search(r"\b(lead|head|director)\b", title) else 0.0
    elif function == "analyst":
        function_score = 1.0 if "analyst" in title else 0.4 if "data" in title else 0.0
    elif function == "architect":
        function_score = 1.0 if "architect" in title else 0.5 if "engineer" in title else 0.0
    elif function == "developer":
        function_score = 1.0 if "developer" in title else 0.7 if "engineer" in title else 0.0
    else:
        function_score = 0.0

    return max(0.0, min(1.0, 0.6 * family_score + 0.4 * function_score))


def explicit_senior_title_score(spec: RequirementSpec, candidate_title: str) -> float:
    seniority = spec.seniority
    level = str(seniority.get("level", "unspecified"))
    track = str(seniority.get("track", "either"))
    if level not in {"senior", "staff", "principal"} or track == "management":
        return 0.0
    if MANAGEMENT_TITLE_RE.search(candidate_title) and not TECHNICAL_TITLE_RE.search(candidate_title):
        return 0.0
    return 1.0 if SENIOR_TITLE_RE.search(candidate_title) else 0.0


def candidate_ownership_score(overlay: dict[str, Any]) -> float:
    career = overlay.get("career_evidence", {})
    return ownership_score(
        _as_set(career.get("any_career_signal_ids")),
        _as_set(career.get("any_career_compound_ids")),
    )


def role_title_ordering_modifier(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    cap: float = ROLE_TITLE_ORDERING_CAP,
) -> float:
    if cap <= 0 or not meets_career_evidence_floor(spec, overlay):
        return 0.0
    candidate_title = str(overlay.get("static", {}).get("current_title") or "")
    explicit_level = explicit_senior_title_score(spec, candidate_title)
    if explicit_level <= 0:
        return 0.0
    ownership = candidate_ownership_score(overlay)
    if ownership <= 0:
        return 0.0
    role_fit = role_title_alignment_score(spec.role_title, candidate_title)
    return cap * explicit_level * ownership * role_fit


def years_alignment(seniority: dict[str, Any], overlay: dict[str, Any]) -> float:
    static = overlay.get("static", {})
    years = static.get("years_of_experience")
    if not isinstance(years, (int, float)):
        return 0.0
    min_years = seniority.get("min_years")
    max_years = seniority.get("max_years")
    if not min_years and max_years is None:
        return 0.0
    if min_years and years < float(min_years):
        return -min(1.0, (float(min_years) - years) / max(float(min_years), 1.0))
    if max_years is not None and years > float(max_years):
        excess = years - float(max_years)
        return -min(0.8, excess / max(float(max_years), 1.0))
    return 1.0


def integrity_blocks(spec: RequirementSpec, overlay: dict[str, Any]) -> tuple[str, ...]:
    integrity = overlay.get("integrity_overlay", {})
    reasons = []
    if integrity.get("risk_level") in {"high", "critical"}:
        reasons.append("high_integrity_risk")
    reasons.extend(str(rule) for rule in integrity.get("honeypot_proxy_rules", []))
    for rule_id in spec.hard_disqualifiers:
        if _rule_fired(overlay, rule_id):
            reasons.append(rule_id)
    if not meets_career_evidence_floor(spec, overlay):
        reasons.append("career_evidence_floor_not_met")
    return tuple(sorted(set(reasons)))


def meets_career_evidence_floor(
    spec: RequirementSpec,
    overlay: dict[str, Any],
) -> bool:
    career = overlay.get("career_evidence", {})
    signals = _as_set(career.get("any_career_signal_ids"))
    compounds = _as_set(career.get("any_career_compound_ids"))
    if compounds & spec.compound_ids:
        return True
    required_signals = spec.evidence_signal_ids & CAREER_FLOOR_SIGNALS
    if required_signals:
        return bool(signals & required_signals)
    return bool(signals & spec.evidence_signal_ids)


def soft_penalty(spec: RequirementSpec, overlay: dict[str, Any]) -> float:
    penalty = 0.0
    for rule_id in spec.soft_negatives:
        if _rule_fired(overlay, rule_id):
            penalty += 0.20
    risk_contexts = _as_set(
        overlay.get("career_evidence", {}).get("any_career_risk_context_ids")
    )
    if "llm_application_context" in risk_contexts:
        penalty += 0.05
    return min(0.35, penalty)


def semantic_score(
    spec: RequirementSpec,
    overlay: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
) -> float:
    if candidate is None:
        if overlay and overlay.get("semantic_tokens"):
            return query_coverage_score_from_tokens(
                spec.semantic_queries,
                overlay["semantic_tokens"],
            )
        return 0.0
    return query_coverage_score(spec.semantic_queries, career_weighted_text(candidate))


def score_overlay(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    seniority_ordering_cap: float = SENIORITY_ORDERING_CAP,
    role_title_ordering_cap: float = ROLE_TITLE_ORDERING_CAP,
) -> ScoreBreakdown:
    blocked_reasons = integrity_blocks(spec, overlay)
    evidence = evidence_score(spec, overlay)
    semantic = semantic_score(spec, overlay, candidate)
    skills = skill_score(spec, overlay)
    behavior = behavior_modifier(overlay)
    logistics = logistics_modifier(overlay)
    seniority = seniority_alignment(spec, overlay)
    seniority += seniority_ordering_modifier(
        spec,
        overlay,
        alignment=seniority,
        cap=seniority_ordering_cap,
    )
    seniority += role_title_ordering_modifier(
        spec,
        overlay,
        cap=role_title_ordering_cap,
    )
    penalties = soft_penalty(spec, overlay)
    if blocked_reasons:
        score = -999.0
    else:
        score = (
            EVIDENCE_WEIGHT * evidence
            + SEMANTIC_WEIGHT * semantic
            + SKILL_WEIGHT * skills
            + behavior
            + logistics
            + seniority
            - penalties
        )
    return ScoreBreakdown(
        candidate_id=str(overlay["candidate_id"]),
        score=score,
        evidence=evidence,
        semantic=semantic,
        skills=skills,
        behavior=behavior,
        logistics=logistics,
        seniority=seniority,
        penalties=penalties,
        blocked=bool(blocked_reasons),
        blocked_reasons=blocked_reasons,
        reasoning=build_reasoning(spec, overlay, evidence, semantic, blocked_reasons),
    )


def iter_rank_inputs(
    overlay_path: Path,
    candidates_path: Path | None = None,
) -> Iterator[tuple[dict[str, Any], dict[str, Any] | None]]:
    overlay_iter = iter_jsonl(overlay_path)
    if candidates_path is None:
        for overlay in overlay_iter:
            yield overlay, None
        return

    candidate_iter = stream_candidates(candidates_path)
    for overlay, candidate in zip(overlay_iter, candidate_iter):
        if overlay["candidate_id"] != candidate["candidate_id"]:
            raise ValueError(
                "candidate and overlay order mismatch: "
                f"{candidate['candidate_id']} != {overlay['candidate_id']}"
            )
        yield overlay, candidate


def rank_candidates(
    spec: RequirementSpec,
    overlay_path: Path,
    candidates_path: Path | None = None,
    limit: int = 100,
) -> list[ScoreBreakdown]:
    return rank_with_summary(spec, overlay_path, candidates_path, limit).rows


def rank_with_summary(
    spec: RequirementSpec,
    overlay_path: Path,
    candidates_path: Path | None = None,
    limit: int = 100,
) -> RankRun:
    eligible = []
    candidate_count = 0
    blocked_count = 0
    for overlay, candidate in iter_rank_inputs(overlay_path, candidates_path):
        candidate_count += 1
        row = score_overlay(spec, overlay, candidate)
        if row.blocked:
            blocked_count += 1
        else:
            eligible.append(row)

    if len(eligible) < limit:
        raise ValueError(f"need at least {limit} eligible candidates")
    eligible.sort(key=lambda row: (-row.score, row.candidate_id))
    return RankRun(
        rows=eligible[:limit],
        candidate_count=candidate_count,
        eligible_count=len(eligible),
        blocked_count=blocked_count,
    )


def rank_raw_candidates(
    spec: RequirementSpec,
    candidates_path: Path,
    knowledge_base_path: Path,
    as_of: date = DEFAULT_AS_OF,
    limit: int = 100,
) -> list[ScoreBreakdown]:
    return rank_raw_with_summary(
        spec,
        candidates_path,
        knowledge_base_path,
        as_of,
        limit,
    ).rows


def rank_raw_with_summary(
    spec: RequirementSpec,
    candidates_path: Path,
    knowledge_base_path: Path,
    as_of: date = DEFAULT_AS_OF,
    limit: int = 100,
) -> RankRun:
    knowledge_base = json.loads(knowledge_base_path.read_text(encoding="utf-8"))
    checker = IntegrityChecker(knowledge_base, as_of)
    eligible = []
    candidate_count = 0
    blocked_count = 0
    for candidate in stream_candidates(candidates_path):
        candidate_count += 1
        findings = checker.check(candidate)
        overlay = build_candidate_overlay(candidate, findings, as_of)
        row = score_overlay(spec, overlay, candidate)
        if row.blocked:
            blocked_count += 1
        else:
            eligible.append(row)

    if len(eligible) < limit:
        raise ValueError(f"need at least {limit} eligible candidates")
    eligible.sort(key=lambda row: (-row.score, row.candidate_id))
    return RankRun(
        rows=eligible[:limit],
        candidate_count=candidate_count,
        eligible_count=len(eligible),
        blocked_count=blocked_count,
    )


def build_reasoning(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    evidence: float,
    semantic: float,
    blocked_reasons: tuple[str, ...],
) -> str:
    static = overlay.get("static", {})
    candidate_id = str(overlay.get("candidate_id") or "")
    title = str(static.get("current_title") or "Candidate")
    company = str(static.get("current_company") or "current employer")
    years = static.get("years_of_experience")
    career = overlay.get("career_evidence", {})
    compounds = _as_set(career.get("any_career_compound_ids"))
    signals = _as_set(career.get("any_career_signal_ids"))
    if blocked_reasons:
        return (
            f"{title} at {company} is not shortlist-ready because deterministic "
            f"screening found {human_join(blocked_reasons)}."
        )
    try:
        years_text = f"{float(years):.1f} years"
    except (TypeError, ValueError):
        years_text = "undisclosed experience"

    jd_phrase = matched_requirement_phrase(spec, signals, compounds, candidate_id)
    evidence_bits = evidence_reason_phrases(candidate_id, signals, compounds)
    skill_bits = selected_skill_names(overlay)
    availability_bits = availability_facts(overlay)
    concern = strongest_concern(spec, overlay, evidence, semantic, signals, compounds)

    evidence_text = (
        human_join(evidence_bits[:2])
        if evidence_bits
        else "shows relevant technical signals with fewer explicit system details"
    )
    skill_text = (
        f"skills include {human_join(skill_bits[:3])}"
        if skill_bits
        else "career evidence carries the match more than listed skills"
    )
    availability_text = selected_availability_fact(candidate_id, availability_bits, concern)
    availability_clause = f"; {availability_text}" if availability_text else ""
    concern_clause = f"; {concern.rstrip('.')}" if concern else ""
    skeletons = (
        "{lead} — career history {evidence} for {jd}; {skills}{availability}{concern}.",
        "{lead} — {skills}; career history {evidence}, fitting {jd}{availability}{concern}.",
        "{lead} — fits {jd} through career evidence that {evidence}; {skills}{concern}.",
        "{lead} — career evidence {evidence}; {skills} for {jd}{availability}{concern}.",
        "{lead} — {skills}, while career history {evidence} for {jd}{availability}{concern}.",
    )
    lead = f"{title} at {company}, {years_text}"
    skeleton = stable_choice(candidate_id, skeletons)
    reasoning = skeleton.format(
        lead=lead,
        evidence=evidence_text,
        jd=jd_phrase,
        skills=skill_text,
        availability=availability_clause,
        concern=concern_clause,
    )
    return compact_reasoning(reasoning)


def stable_choice(key: str, options: tuple[str, ...]) -> str:
    if not options:
        raise ValueError("stable_choice requires options")
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return options[int(digest[:8], 16) % len(options)]


def human_join(items: Any) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def matched_requirement_phrase(
    spec: RequirementSpec,
    signals: set[str],
    compounds: set[str],
    candidate_id: str,
) -> str:
    matches: list[tuple[float, str, str]] = []
    for item in spec.must_have + spec.nice_to_have:
        compound_hit = bool(compounds & set(item.compounds))
        signal_hit = bool(signals & set(item.evidence_signals))
        if compound_hit or signal_hit:
            phrases = REQUIREMENT_REASON_PHRASES.get(item.id)
            if phrases:
                phrase = stable_choice(f"{candidate_id}:req:{item.id}", phrases)
            else:
                desc = item.desc.strip().rstrip(".")
                phrase = desc[:1].lower() + desc[1:]
            matches.append((float(item.weight), item.id, phrase))
    if not matches:
        return "the parsed JD's adjacent technical requirements"
    matches.sort(key=lambda value: (-value[0], value[1]))
    top_weight = matches[0][0]
    top_matches = tuple(phrase for weight, _, phrase in matches if weight == top_weight)
    return stable_choice(f"{candidate_id}:req-choice", top_matches)


def evidence_reason_phrases(
    candidate_id: str,
    signals: set[str],
    compounds: set[str],
) -> list[str]:
    phrases = []
    for compound in sorted(compounds):
        options = COMPOUND_REASON_PHRASES.get(compound)
        if options:
            phrases.append(stable_choice(f"{candidate_id}:{compound}", options))
    if len(phrases) >= 2:
        return phrases
    for signal in sorted(signals):
        phrase = SIGNAL_REASON_PHRASES.get(signal)
        if phrase and phrase not in phrases:
            phrases.append(f"shows {phrase}")
        if len(phrases) >= 3:
            break
    return phrases


def selected_skill_names(overlay: dict[str, Any], limit: int = 3) -> list[str]:
    names = [
        str(name).strip()
        for name in overlay.get("skill_overlay", {}).get("skill_names", [])
        if str(name).strip()
    ]
    if not names:
        return []
    priority = re.compile(
        r"\b(python|rag|retrieval|ranking|search|bm25|elasticsearch|faiss|"
        r"pinecone|pgvector|mlops|tensorflow|pytorch|hugging face|llm|nlp)\b",
        re.IGNORECASE,
    )
    prioritized = [name for name in names if priority.search(name)]
    fallback = [name for name in names if name not in prioritized]
    selected = []
    for name in prioritized + fallback:
        if name not in selected:
            selected.append(name)
        if len(selected) >= limit:
            break
    return selected


def availability_facts(overlay: dict[str, Any]) -> list[str]:
    availability = overlay.get("availability_overlay", {})
    facts = []
    inactive_days = availability.get("inactive_days")
    if isinstance(inactive_days, int):
        facts.append(f"active {inactive_days} days ago")
    response_rate = availability.get("response_rate")
    if isinstance(response_rate, (int, float)):
        facts.append(f"{float(response_rate):.2f} recruiter response rate")
    notice = availability.get("notice_period_days")
    if isinstance(notice, int):
        facts.append(f"{notice}-day notice")
    if availability.get("open_to_work"):
        facts.append("open to work")
    return facts


def selected_availability_fact(
    candidate_id: str,
    facts: list[str],
    concern: str,
) -> str:
    if not facts:
        return ""
    concern_lower = concern.lower()
    filtered = [
        fact
        for fact in facts
        if not (
            ("notice" in concern_lower and "notice" in fact)
            or ("response" in concern_lower and "response" in fact)
            or ("inactive" in concern_lower and "active" in fact)
        )
    ]
    choices = tuple(filtered or facts)
    return stable_choice(f"{candidate_id}:availability", choices)


def strongest_concern(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    evidence: float,
    semantic: float,
    signals: set[str],
    compounds: set[str],
) -> str:
    availability = overlay.get("availability_overlay", {})
    logistics = overlay.get("logistics_overlay", {})
    risk_contexts = _as_set(
        overlay.get("career_evidence", {}).get("any_career_risk_context_ids")
    )
    unsatisfied = unsatisfied_must_have(spec, signals, compounds)

    notice = availability.get("notice_period_days")
    if isinstance(notice, int) and notice >= 90:
        return f"Concern: {notice}-day notice may slow hiring."
    response_rate = availability.get("response_rate")
    if isinstance(response_rate, (int, float)) and response_rate < 0.35:
        return f"Concern: recruiter response rate is only {float(response_rate):.2f}."
    inactive_days = availability.get("inactive_days")
    if isinstance(inactive_days, int) and inactive_days > 120:
        return f"Concern: profile has been inactive for {inactive_days} days."
    if logistics.get("location_bucket") == "outside_india" and not logistics.get(
        "willing_to_relocate"
    ):
        return "Concern: location is outside India with no relocation signal."
    if "llm_application_context" in risk_contexts:
        return "Concern: some experience is LLM-application context, so production depth matters."
    if unsatisfied:
        return f"Concern: less explicit evidence for {unsatisfied[0]}."
    if evidence < 0.80:
        return "Concern: relevant evidence is present but not as complete as the highest-ranked profiles."
    if semantic < 0.45:
        return "Concern: wording is less directly aligned to the JD than the strongest matches."
    return ""


def unsatisfied_must_have(
    spec: RequirementSpec,
    signals: set[str],
    compounds: set[str],
) -> list[str]:
    missing = []
    for item in spec.must_have:
        compound_hit = bool(compounds & set(item.compounds))
        signal_hits = len(signals & set(item.evidence_signals))
        if not compound_hit and signal_hits < max(1, len(item.evidence_signals) // 2):
            desc = item.desc.strip().rstrip(".")
            missing.append(desc[:1].lower() + desc[1:])
    return missing


def compact_reasoning(reasoning: str) -> str:
    return re.sub(r"\s+", " ", reasoning).strip()


def apply_rank_tone(reasoning: str, rank: int) -> str:
    if rank <= 10:
        tones = (
            "a strong shortlist match",
            "a high-signal fit",
            "one of the stronger matches",
        )
    elif rank <= 50:
        tones = (
            "a solid shortlist fit with trade-offs",
            "a credible shortlist option",
            "a good fit with a few trade-offs",
        )
    else:
        tones = (
            "a viable near-cutoff option",
            "a borderline but relevant fit",
            "a lower-ranked shortlist option",
        )
    tone = stable_choice(f"{rank}:{reasoning}", tones)
    if " — " in reasoning:
        return reasoning.replace(" — ", f" is {tone}: ", 1)
    return f"{reasoning} This is {tone}."


def write_submission(rows: list[ScoreBreakdown], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUBMISSION_COLUMNS)
        writer.writeheader()
        for rank, row in enumerate(rows, 1):
            writer.writerow(
                {
                    "candidate_id": row.candidate_id,
                    "rank": rank,
                    "score": f"{row.score - rank * 1e-9:.9f}",
                    "reasoning": apply_rank_tone(row.reasoning, rank),
                }
            )


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def peak_rss_mb() -> float:
    # Linux reports ru_maxrss in KiB. The challenge runs in a Linux-like
    # environment, and this workspace is WSL/Linux.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jd",
        type=Path,
        default=DEFAULT_JD,
        help="Job description file (.docx, .txt, or .md).",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        help="Optional prebuilt requirement spec. If omitted, --jd is parsed.",
    )
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--knowledge-base",
        type=Path,
        default=DEFAULT_KNOWLEDGE_BASE,
        help="Chronology/integrity knowledge base.",
    )
    parser.add_argument("--analysis-as-of", default=DEFAULT_AS_OF.isoformat())
    parser.add_argument(
        "--features",
        type=Path,
        default=DEFAULT_FEATURES,
        help="Precomputed candidate feature JSONL built by solution.precompute.",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Slow fallback: build candidate features directly from candidates.jsonl.",
    )
    parser.add_argument(
        "--use-overlay",
        action="store_true",
        help="Internal compatibility mode: score precomputed candidate_overlay.jsonl.",
    )
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    parser.add_argument("--no-candidate-text", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    started = time.perf_counter()
    args = parse_args()
    spec = load_spec(repo_path(args.spec)) if args.spec else parse_jd(repo_path(args.jd))
    candidates_path = repo_path(args.candidates)
    out = repo_path(args.out)
    if args.use_overlay:
        candidates = None if args.no_candidate_text else candidates_path
        run = rank_with_summary(spec, repo_path(args.overlay), candidates)
        mode_text = "precomputed overlay mode"
    elif not args.raw:
        features_path = repo_path(args.features)
        if not features_path.is_file():
            raise FileNotFoundError(
                f"precomputed features not found: {features_path}; "
                "run `python3 -m solution.precompute` first or pass --raw"
            )
        run = rank_with_summary(spec, features_path, None)
        mode_text = "precomputed feature mode"
    else:
        run = rank_raw_with_summary(
            spec,
            candidates_path,
            repo_path(args.knowledge_base),
            date.fromisoformat(args.analysis_as_of),
        )
        mode_text = "raw JD + raw candidate mode"
    write_submission(run.rows, out)
    elapsed = time.perf_counter() - started
    max_memory_mb = peak_rss_mb()
    print(
        f"Ranked {run.candidate_count:,} candidates "
        f"({run.eligible_count:,} eligible, {run.blocked_count:,} blocked) "
        f"in {elapsed:.3f}s; maximum memory used {max_memory_mb:.1f} MB; "
        f"wrote {out} using {mode_text}; parsed role: {spec.role_title}"
    )


if __name__ == "__main__":
    main()
