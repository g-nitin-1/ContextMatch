#!/usr/bin/env python3
"""Build candidate-level evidence overlays from template and profile facts."""

from __future__ import annotations

import argparse
import re
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    career_template_id,
    markdown_table,
    stream_candidates,
    summary_archetype,
    summary_template_id,
    write_json,
)
from analysis.integrity_checks import HIGH_CONFIDENCE_RULES, parse_date
from analysis.jd_evidence_catalog import DEFAULT_RUBRIC, load_rubric


DEFAULT_AS_OF = date(2026, 6, 1)
DEFAULT_OVERLAY_JSONL = "candidate_overlay.jsonl"
DEFAULT_OVERLAY_SUMMARY = "candidate_overlay_summary.json"
DEFAULT_OVERLAY_REPORT = "candidate_overlay_report.md"

PRODUCT_INDUSTRIES = {
    "AI/ML",
    "Consumer App",
    "E-commerce",
    "EdTech",
    "Food Delivery",
    "Gaming",
    "HR Tech",
    "Internet",
    "SaaS",
    "Software",
    "Voice AI",
}
SERVICE_INDUSTRIES = {"Consulting", "IT Services", "Services"}
TARGET_LOCATION_PATTERNS = (
    ("pune", re.compile(r"\bpune\b", re.IGNORECASE)),
    ("noida", re.compile(r"\bnoida\b", re.IGNORECASE)),
    ("ncr", re.compile(r"\b(gurgaon|gurugram|delhi|ncr)\b", re.IGNORECASE)),
)
SENIOR_TITLE_RE = re.compile(
    r"\b(senior|staff|principal|lead|head|director|architect)\b",
    re.IGNORECASE,
)
MANAGER_TITLE_RE = re.compile(r"\bmanager\b", re.IGNORECASE)
TECHNICAL_MANAGER_TITLE_RE = re.compile(
    r"\b(engineering|software|data|ml|ai|platform|backend|infrastructure)\b",
    re.IGNORECASE,
)

HANDS_ON_SIGNALS = {
    "embeddings",
    "python_engineering",
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


def _as_set(values: Any) -> set[str]:
    if not values:
        return set()
    if isinstance(values, set):
        return {str(value) for value in values}
    return {str(value) for value in values}


def _months_between(start: date | None, end: date | None, as_of: date) -> int:
    if start is None:
        return 0
    actual_end = end or as_of
    return max(0, (actual_end.year - start.year) * 12 + actual_end.month - start.month)


def _role_duration_months(role: dict[str, Any], as_of: date) -> int:
    declared = role.get("duration_months")
    if isinstance(declared, int):
        return max(0, declared)
    return _months_between(
        parse_date(role.get("start_date")),
        parse_date(role.get("end_date")),
        as_of,
    )


def _role_overlaps_recent_window(
    role: dict[str, Any],
    as_of: date,
    months: int,
) -> bool:
    start = parse_date(role.get("start_date"))
    end = parse_date(role.get("end_date")) or as_of
    if start is None:
        return bool(role.get("is_current"))
    boundary_year = as_of.year
    boundary_month = as_of.month - months
    while boundary_month <= 0:
        boundary_month += 12
        boundary_year -= 1
    boundary = date(boundary_year, boundary_month, 1)
    return end >= boundary


def _matches_any(value: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in patterns)


def load_skill_signal_patterns(
    source: dict[str, Any] | None = None,
) -> dict[str, tuple[str, ...]]:
    if source is None:
        source = load_rubric(DEFAULT_RUBRIC)
    raw = source.get("skill_signal_patterns")
    if raw is None:
        raw = source.get("rubric_summary", {}).get("skill_signal_patterns")
    if not raw:
        raise ValueError("skill_signal_patterns are missing from the rubric source")
    return {
        signal_id: tuple(entry["patterns"])
        for signal_id, entry in sorted(raw.items())
    }


def summarize_skills(
    skills: list[dict[str, Any]],
    skill_patterns: dict[str, tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    if skill_patterns is None:
        skill_patterns = load_skill_signal_patterns()
    signal_counts: Counter[str] = Counter()
    advanced_counts: Counter[str] = Counter()
    max_duration_by_signal: Counter[str] = Counter()
    expert_zero_duration = []
    names = []

    for skill in skills:
        name = str(skill.get("name", "")).strip()
        if not name:
            continue
        names.append(name)
        proficiency = str(skill.get("proficiency", "")).lower()
        duration = int(skill.get("duration_months", 0) or 0)
        if proficiency == "expert" and duration == 0:
            expert_zero_duration.append(name)
        for signal_id, patterns in skill_patterns.items():
            if _matches_any(name, patterns):
                signal_counts[signal_id] += 1
                max_duration_by_signal[signal_id] = max(
                    max_duration_by_signal[signal_id], duration
                )
                if proficiency in {"advanced", "expert"}:
                    advanced_counts[signal_id] += 1

    return {
        "skill_names": sorted(names),
        "skill_signal_ids": sorted(signal_counts),
        "skill_signal_counts": dict(sorted(signal_counts.items())),
        "advanced_or_expert_signal_counts": dict(sorted(advanced_counts.items())),
        "max_duration_months_by_signal": dict(sorted(max_duration_by_signal.items())),
        "expert_zero_duration_skills": sorted(expert_zero_duration),
        "expert_zero_duration_count": len(expert_zero_duration),
    }


def _role_has_product_context(role: dict[str, Any]) -> bool:
    signals = _as_set(role.get("signals"))
    industry = str(role.get("industry", ""))
    return "product_context" in signals or industry in PRODUCT_INDUSTRIES


def _role_has_service_context(role: dict[str, Any]) -> bool:
    signals = _as_set(role.get("signals"))
    text = " ".join(
        str(role.get(name, ""))
        for name in ("company", "title", "industry", "description")
    )
    return (
        "consulting_services_context" in signals
        or str(role.get("industry", "")) in SERVICE_INDUSTRIES
        or bool(re.search(r"\b(consulting|client|advisory|services)\b", text, re.I))
    )


def _role_has_research_context(role: dict[str, Any]) -> bool:
    signals = _as_set(role.get("signals"))
    if "research_only_context" in signals:
        return True
    title = str(role.get("title", ""))
    industry = str(role.get("industry", ""))
    text = " ".join(
        str(role.get(name, ""))
        for name in ("company", "title", "industry", "description")
    )
    return bool(
        re.search(r"\bresearch\s+(scientist|engineer|fellow|intern)\b", title, re.I)
        or re.search(r"\b(academic lab|research lab)\b", industry, re.I)
        or re.search(r"\b(research-only|pure research|academic lab)\b", text, re.I)
    )


def _role_has_production_delivery(role: dict[str, Any]) -> bool:
    return "production_delivery" in _as_set(role.get("signals"))


def _role_has_substantial_production_ml(role: dict[str, Any]) -> bool:
    signals = _as_set(role.get("signals"))
    compounds = _as_set(role.get("compounds"))
    if compounds & (PRODUCTION_COMPOUNDS | {"evaluated_ranking_system"}):
        return True
    if _role_has_production_delivery(role) and signals & (
        HANDS_ON_SIGNALS | {"ranking_evaluation"}
    ):
        return True
    return False


def _role_has_shallow_llm_context(role: dict[str, Any]) -> bool:
    signals = _as_set(role.get("signals"))
    return "llm_application_context" in signals and not _role_has_substantial_production_ml(
        role
    )


def _role_has_recent_hands_on_engineering(role: dict[str, Any]) -> bool:
    signals = _as_set(role.get("signals"))
    return bool(
        signals & HANDS_ON_SIGNALS
        or _role_has_production_delivery(role)
    )


def _verdict(fired: bool, reason: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "fired": fired,
        "reason": reason,
        "evidence": evidence,
    }


def evaluate_services_only_entire_career(
    roles: list[dict[str, Any]],
) -> dict[str, Any]:
    if not roles:
        return _verdict(False, "no career roles", {})

    product_roles = [
        role.get("template_id") or role.get("company")
        for role in roles
        if _role_has_product_context(role)
    ]
    if product_roles:
        return _verdict(
            False,
            "guarded by product-company/product-context evidence",
            {"product_roles": product_roles},
        )

    service_roles = [
        role.get("template_id") or role.get("company")
        for role in roles
        if _role_has_service_context(role)
    ]
    non_service_roles = len(roles) - len(service_roles)
    return _verdict(
        bool(service_roles and non_service_roles == 0),
        "entire career is services/consulting"
        if service_roles and non_service_roles == 0
        else "career is not services-only",
        {
            "service_role_count": len(service_roles),
            "non_service_role_count": non_service_roles,
            "service_roles": service_roles,
        },
    )


def evaluate_research_only_without_production(
    roles: list[dict[str, Any]],
) -> dict[str, Any]:
    if not roles:
        return _verdict(False, "no career roles", {})

    production_roles = [
        role.get("template_id") or role.get("company")
        for role in roles
        if _role_has_production_delivery(role)
    ]
    if production_roles:
        return _verdict(
            False,
            "guarded by production-delivery evidence",
            {"production_roles": production_roles},
        )

    research_roles = [
        role.get("template_id") or role.get("company")
        for role in roles
        if _role_has_research_context(role)
    ]
    non_research_roles = len(roles) - len(research_roles)
    return _verdict(
        bool(research_roles and non_research_roles == 0),
        "entire career is research-only without production"
        if research_roles and non_research_roles == 0
        else "career is not research-only",
        {
            "research_role_count": len(research_roles),
            "non_research_role_count": non_research_roles,
            "research_roles": research_roles,
        },
    )


def evaluate_recent_shallow_llm_only(
    roles: list[dict[str, Any]],
    skill_summary: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    substantial_roles = [
        role.get("template_id") or role.get("company")
        for role in roles
        if _role_has_substantial_production_ml(role)
    ]
    if substantial_roles:
        return _verdict(
            False,
            "guarded by substantial production ML/retrieval/ranking evidence",
            {"substantial_roles": substantial_roles},
        )

    shallow_roles = [
        role
        for role in roles
        if _role_has_shallow_llm_context(role)
        and _role_overlaps_recent_window(role, as_of, 12)
    ]
    shallow_role_months = sum(_role_duration_months(role, as_of) for role in shallow_roles)
    llm_skill_months = int(
        skill_summary.get("max_duration_months_by_signal", {}).get(
            "llm_application_context", 0
        )
        or 0
    )
    has_recent_skill_only_llm = (
        "llm_application_context" in skill_summary.get("skill_signal_ids", [])
        and llm_skill_months <= 12
    )
    fired = bool(
        (shallow_roles and shallow_role_months <= 12) or has_recent_skill_only_llm
    )
    return _verdict(
        fired,
        "recent shallow LLM evidence without deeper production ML"
        if fired
        else "no recent shallow-LLM-only pattern",
        {
            "shallow_role_count": len(shallow_roles),
            "shallow_role_months": shallow_role_months,
            "llm_skill_months": llm_skill_months,
        },
    )


def evaluate_senior_not_coding_recently(
    roles: list[dict[str, Any]],
    profile: dict[str, Any],
    as_of: date,
) -> dict[str, Any]:
    title = str(profile.get("current_title", ""))
    is_technical_manager = bool(
        MANAGER_TITLE_RE.search(title) and TECHNICAL_MANAGER_TITLE_RE.search(title)
    )
    if not (SENIOR_TITLE_RE.search(title) or is_technical_manager):
        return _verdict(False, "current title is not senior technical leadership", {})

    recent_roles = [
        role for role in roles if _role_overlaps_recent_window(role, as_of, 18)
    ]
    hands_on_roles = [
        role.get("template_id") or role.get("company")
        for role in recent_roles
        if _role_has_recent_hands_on_engineering(role)
    ]
    if hands_on_roles:
        return _verdict(
            False,
            "guarded by recent hands-on engineering evidence",
            {"hands_on_roles": hands_on_roles},
        )

    leadership_roles = [
        role.get("template_id") or role.get("company")
        for role in recent_roles
        if "mentoring_leadership" in _as_set(role.get("signals"))
        or SENIOR_TITLE_RE.search(str(role.get("title", "")))
        or (
            MANAGER_TITLE_RE.search(str(role.get("title", "")))
            and TECHNICAL_MANAGER_TITLE_RE.search(str(role.get("title", "")))
        )
    ]
    return _verdict(
        bool(recent_roles and leadership_roles),
        "senior recent evidence lacks hands-on engineering"
        if recent_roles and leadership_roles
        else "insufficient senior-without-coding evidence",
        {
            "recent_role_count": len(recent_roles),
            "leadership_role_count": len(leadership_roles),
            "leadership_roles": leadership_roles,
        },
    )


def evaluate_overlay_rules(
    roles: list[dict[str, Any]],
    skill_summary: dict[str, Any],
    profile: dict[str, Any],
    as_of: date,
) -> dict[str, dict[str, Any]]:
    return {
        "services_only_entire_career": evaluate_services_only_entire_career(roles),
        "research_only_without_production": evaluate_research_only_without_production(
            roles
        ),
        "recent_shallow_llm_only": evaluate_recent_shallow_llm_only(
            roles, skill_summary, as_of
        ),
        "senior_not_coding_recently": evaluate_senior_not_coding_recently(
            roles, profile, as_of
        ),
    }


def load_integrity_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    index = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            index[record["candidate_id"]] = record
    return index


def _location_bucket(profile: dict[str, Any], signals: dict[str, Any]) -> str:
    location = str(profile.get("location", ""))
    for bucket, pattern in TARGET_LOCATION_PATTERNS:
        if pattern.search(location):
            return bucket
    if str(profile.get("country", "")).lower() == "india":
        return "india_other"
    if signals.get("willing_to_relocate"):
        return "outside_india_relocatable"
    return "outside_india"


def _behavior_overlay(signals: dict[str, Any], as_of: date) -> dict[str, Any]:
    last_active = parse_date(signals.get("last_active_date"))
    inactive_days = (as_of - last_active).days if last_active else None
    return {
        "inactive_days": inactive_days,
        "open_to_work": bool(signals.get("open_to_work_flag")),
        "notice_period_days": signals.get("notice_period_days"),
        "willing_to_relocate": bool(signals.get("willing_to_relocate")),
        "response_rate": signals.get("recruiter_response_rate"),
        "response_time_hours": signals.get("avg_response_time_hours"),
        "profile_views_30d": signals.get("profile_views_received_30d"),
        "search_appearance_30d": signals.get("search_appearance_30d"),
        "saved_by_recruiters_30d": signals.get("saved_by_recruiters_30d"),
        "interview_completion_rate": signals.get("interview_completion_rate"),
        "offer_acceptance_rate": signals.get("offer_acceptance_rate"),
        "github_activity_score": signals.get("github_activity_score"),
        "verification_count": sum(
            bool(signals.get(name))
            for name in ("verified_email", "verified_phone", "linkedin_connected")
        ),
    }


def _enrich_roles(
    candidate: dict[str, Any],
    career_catalog: dict[str, Any],
    as_of: date,
) -> list[dict[str, Any]]:
    enriched = []
    for role in candidate.get("career_history", []):
        template_id = career_template_id(role.get("description", ""))
        annotation = career_catalog.get(template_id, {})
        signal_ids = sorted(annotation.get("signal_ids", []))
        compound_ids = sorted(annotation.get("compound_ids", []))
        enriched.append(
            {
                "template_id": template_id,
                "company": role.get("company"),
                "title": role.get("title"),
                "industry": role.get("industry"),
                "start_date": role.get("start_date"),
                "end_date": role.get("end_date"),
                "duration_months": _role_duration_months(role, as_of),
                "is_current": bool(role.get("is_current")),
                "signals": signal_ids,
                "compounds": compound_ids,
                "risk_contexts": annotation.get("signals_by_category", {}).get(
                    "risk_context", []
                ),
                "description": role.get("description", ""),
            }
        )
    return enriched


def _career_evidence(roles: list[dict[str, Any]]) -> dict[str, Any]:
    current_roles = [role for role in roles if role.get("is_current")]
    current = current_roles[0] if current_roles else (roles[0] if roles else {})
    current_signals = _as_set(current.get("signals"))
    current_compounds = _as_set(current.get("compounds"))
    any_signals: set[str] = set()
    any_compounds: set[str] = set()
    current_risks = _as_set(current.get("risk_contexts"))
    any_risks: set[str] = set()
    for role in roles:
        any_signals.update(_as_set(role.get("signals")))
        any_compounds.update(_as_set(role.get("compounds")))
        any_risks.update(_as_set(role.get("risk_contexts")))

    return {
        "current_template_id": current.get("template_id"),
        "career_template_ids": [role["template_id"] for role in roles],
        "current_signal_ids": sorted(current_signals),
        "any_career_signal_ids": sorted(any_signals),
        "current_compound_ids": sorted(current_compounds),
        "any_career_compound_ids": sorted(any_compounds),
        "current_risk_context_ids": sorted(current_risks),
        "any_career_risk_context_ids": sorted(any_risks),
        "role_evidence": [
            {
                key: role[key]
                for key in (
                    "template_id",
                    "company",
                    "title",
                    "industry",
                    "duration_months",
                    "is_current",
                    "signals",
                    "compounds",
                    "risk_contexts",
                )
            }
            for role in roles
        ],
    }


def _integrity_overlay(record: dict[str, Any] | None) -> dict[str, Any]:
    if not record:
        return {
            "risk_level": "none",
            "issue_rules": [],
            "high_confidence_rules": [],
            "honeypot_proxy_rules": [],
            "issue_count": 0,
        }
    rules = sorted({issue["rule"] for issue in record.get("issues", [])})
    high_confidence = sorted(set(rules) & HIGH_CONFIDENCE_RULES)
    honeypot_proxy = sorted(
        set(rules) & {"company_pre_founding", "expert_zero_duration_3plus"}
    )
    return {
        "risk_level": record.get("risk_level", "none"),
        "issue_rules": rules,
        "high_confidence_rules": high_confidence,
        "honeypot_proxy_rules": honeypot_proxy,
        "issue_count": len(record.get("issues", [])),
    }


def overlay_candidate(
    candidate: dict[str, Any],
    manifest: dict[str, Any],
    career_catalog: dict[str, Any],
    skill_patterns: dict[str, tuple[str, ...]],
    integrity_record: dict[str, Any] | None,
    as_of: date,
) -> dict[str, Any]:
    profile = candidate["profile"]
    signals = candidate["redrob_signals"]
    summary_id = summary_template_id(profile.get("summary", ""))
    summary_manifest = manifest["summary_templates"].get(summary_id, {})
    roles = _enrich_roles(candidate, career_catalog, as_of)
    skill_summary = summarize_skills(candidate.get("skills", []), skill_patterns)
    rule_verdicts = evaluate_overlay_rules(roles, skill_summary, profile, as_of)
    integrity = _integrity_overlay(integrity_record)

    return {
        "candidate_id": candidate["candidate_id"],
        "static": {
            "summary_archetype": summary_archetype(
                profile.get("summary", ""), profile.get("current_title", "")
            ),
            "summary_template_id": summary_id,
            "static_class": summary_manifest.get("static_class", "unknown"),
            "fine_static_atom": summary_manifest.get("fine_static_atom", "unknown"),
            "current_title": profile.get("current_title"),
            "years_of_experience": profile.get("years_of_experience"),
            "current_company": profile.get("current_company"),
            "current_industry": profile.get("current_industry"),
        },
        "career_evidence": _career_evidence(roles),
        "skill_overlay": skill_summary,
        "availability_overlay": _behavior_overlay(signals, as_of),
        "logistics_overlay": {
            "location": profile.get("location"),
            "country": profile.get("country"),
            "location_bucket": _location_bucket(profile, signals),
            "preferred_work_mode": signals.get("preferred_work_mode"),
            "willing_to_relocate": bool(signals.get("willing_to_relocate")),
            "notice_period_days": signals.get("notice_period_days"),
        },
        "integrity_overlay": integrity,
        "candidate_overlay_rules": rule_verdicts,
    }


def _load_required_json(path: Path, description: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_overlay(
    dataset: Path,
    output_dir: Path,
    as_of: date = DEFAULT_AS_OF,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_required_json(
        output_dir / "generator_manifest.json",
        "generator manifest",
    )
    catalog = _load_required_json(
        output_dir / "jd_evidence_catalog.json",
        "JD evidence catalog",
    )
    career_catalog = catalog["career_templates"]
    skill_patterns = load_skill_signal_patterns(catalog["rubric_summary"])
    integrity_index = load_integrity_index(output_dir / "integrity_issues.jsonl")

    summary = {
        "dataset": str(dataset),
        "analysis_as_of": as_of.isoformat(),
        "candidate_count": 0,
        "rubric_version": catalog["method"]["rubric_version"],
        "static_class_counts": Counter(),
        "fine_atom_counts": Counter(),
        "summary_archetype_counts": Counter(),
        "career_compound_candidate_counts": Counter(),
        "skill_signal_candidate_counts": Counter(),
        "overlay_rule_fired_counts": Counter(),
        "overlay_rule_fired_by_archetype": defaultdict(Counter),
        "integrity_risk_counts": Counter(),
        "high_confidence_integrity_rule_counts": Counter(),
        "honeypot_proxy_rule_counts": Counter(),
        "location_bucket_counts": Counter(),
    }

    overlay_path = output_dir / DEFAULT_OVERLAY_JSONL
    with overlay_path.open("w", encoding="utf-8") as handle:
        for candidate in stream_candidates(dataset):
            overlay = overlay_candidate(
                candidate,
                manifest,
                career_catalog,
                skill_patterns,
                integrity_index.get(candidate["candidate_id"]),
                as_of,
            )
            handle.write(json.dumps(overlay, sort_keys=True, ensure_ascii=True))
            handle.write("\n")

            summary["candidate_count"] += 1
            static = overlay["static"]
            summary["static_class_counts"][static["static_class"]] += 1
            summary["fine_atom_counts"][static["fine_static_atom"]] += 1
            summary["summary_archetype_counts"][static["summary_archetype"]] += 1
            summary["career_compound_candidate_counts"].update(
                overlay["career_evidence"]["any_career_compound_ids"]
            )
            summary["skill_signal_candidate_counts"].update(
                overlay["skill_overlay"]["skill_signal_ids"]
            )
            for rule_id, verdict in overlay["candidate_overlay_rules"].items():
                if verdict["fired"]:
                    summary["overlay_rule_fired_counts"][rule_id] += 1
                    summary["overlay_rule_fired_by_archetype"][rule_id][
                        static["summary_archetype"]
                    ] += 1
            integrity = overlay["integrity_overlay"]
            summary["integrity_risk_counts"][integrity["risk_level"]] += 1
            summary["high_confidence_integrity_rule_counts"].update(
                integrity["high_confidence_rules"]
            )
            summary["honeypot_proxy_rule_counts"].update(
                integrity["honeypot_proxy_rules"]
            )
            summary["location_bucket_counts"][
                overlay["logistics_overlay"]["location_bucket"]
            ] += 1

    for rule_id in (
        "services_only_entire_career",
        "research_only_without_production",
        "recent_shallow_llm_only",
        "senior_not_coding_recently",
    ):
        summary["overlay_rule_fired_counts"].setdefault(rule_id, 0)

    serializable_summary = {}
    for key, value in summary.items():
        if isinstance(value, Counter):
            serializable_summary[key] = dict(value.most_common())
        elif key == "overlay_rule_fired_by_archetype":
            serializable_summary[key] = {
                rule_id: dict(counter.most_common())
                for rule_id, counter in sorted(value.items())
            }
        else:
            serializable_summary[key] = value
    serializable_summary["overlay_path"] = str(overlay_path)
    write_json(output_dir / DEFAULT_OVERLAY_SUMMARY, serializable_summary)
    _write_report(output_dir / DEFAULT_OVERLAY_REPORT, serializable_summary)
    return serializable_summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    total = int(summary["candidate_count"])
    lines = [
        "# Candidate Evidence Overlay",
        "",
        "This stage joins frozen template evidence to candidate-specific facts. It "
        "does not assign relevance tiers or a score.",
        "",
        "## Coverage",
        "",
        f"- Candidates processed: {total:,}",
        f"- Rubric version: `{summary['rubric_version']}`",
        f"- JSONL output: `{summary['overlay_path']}`",
        "",
        "## Overlay Rule Firings",
        "",
        markdown_table(
            ("Rule", "Candidates", "Share"),
            (
                (rule, f"{count:,}", f"{count / total:.2%}")
                for rule, count in summary["overlay_rule_fired_counts"].items()
            ),
        )
        if summary["overlay_rule_fired_counts"]
        else "No candidate-level overlay rules fired.",
        "",
        "## Overlay Rule Firings By Archetype",
        "",
    ]
    for rule_id, counts in summary["overlay_rule_fired_by_archetype"].items():
        lines.extend(
            [
                f"### `{rule_id}`",
                "",
                markdown_table(("Archetype", "Candidates"), counts.items()),
                "",
            ]
        )
    lines.extend(
        [
        "## Integrity Join",
        "",
        markdown_table(
            ("Risk level", "Candidates", "Share"),
            (
                (level, f"{count:,}", f"{count / total:.2%}")
                for level, count in summary["integrity_risk_counts"].items()
            ),
        ),
        "",
        "High-confidence integrity rules:",
        "",
        markdown_table(
            ("Rule", "Candidates"),
            (
                (rule, f"{count:,}")
                for rule, count in summary[
                    "high_confidence_integrity_rule_counts"
                ].items()
            ),
        ),
        "",
        "## Skill Evidence",
        "",
        markdown_table(
            ("Skill signal", "Candidates", "Share"),
            (
                (signal, f"{count:,}", f"{count / total:.2%}")
                for signal, count in summary["skill_signal_candidate_counts"].items()
            ),
        ),
        "",
        "## Career Compounds",
        "",
        markdown_table(
            ("Career compound", "Candidates", "Share"),
            (
                (compound, f"{count:,}", f"{count / total:.2%}")
                for compound, count in summary[
                    "career_compound_candidate_counts"
                ].items()
            ),
        ),
        "",
        "## Interpretation Boundary",
        "",
        "This overlay creates the candidate-level feature table needed for Idea 2 "
        "tier hypotheses. Template evidence is inherited from the versioned "
        "rubric; its manual audit and freeze status are recorded separately. "
        "Behavior remains a bounded modifier rather than a base relevance signal.",
        "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--as-of", type=date.fromisoformat, default=DEFAULT_AS_OF)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_overlay(args.candidates, args.output_dir, args.as_of)
    print(
        "Candidate overlay complete: "
        f"{summary['candidate_count']:,} candidates written to "
        f"{summary['overlay_path']}"
    )


if __name__ == "__main__":
    main()
