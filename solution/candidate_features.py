#!/usr/bin/env python3
"""Build JD-agnostic candidate evidence from raw candidate profiles."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from analysis.integrity_checks import HIGH_CONFIDENCE_RULES, risk_level


DEFAULT_AS_OF = date(2026, 6, 1)
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

CORE_TECHNICAL_SIGNALS = {
    "embeddings",
    "learning_to_rank",
    "online_experimentation",
    "python_engineering",
    "ranking_evaluation",
    "ranking_recommendation_matching",
    "retrieval_search",
    "vector_hybrid_infrastructure",
}

TECHNICAL_TITLE_RE = re.compile(
    r"\b("
    r"ai|ml|machine learning|data scientist|applied scientist|"
    r"engineer|developer|architect|backend|software|platform|"
    r"search|recommendation|nlp|mlops"
    r")\b",
    re.IGNORECASE,
)
STRONG_TECHNICAL_WORK_RE = re.compile(
    r"\b("
    r"embedding model|embeddings|vector search|hybrid search|"
    r"retrieval system|ranking system|recommendation system|matching system|"
    r"search relevance|learning to rank|ndcg|mrr|bm25|faiss|pinecone|"
    r"milvus|weaviate|qdrant|pgvector|pytorch|tensorflow|mlops|"
    r"production ml|model serving|feature pipeline"
    r")\b",
    re.IGNORECASE,
)

SIGNAL_PATTERNS: dict[str, tuple[str, ...]] = {
    "embeddings": (r"\bembedding(s)?\b", r"\btext encoder(s)?\b", r"\bvector representation(s)?\b"),
    "retrieval_search": (
        r"\bretriev",
        r"\binformation retrieval\b",
        r"\brag\b",
        r"\bbm25\b",
        r"\bsearch and discovery\b",
        r"\b(vector|hybrid|semantic|neural|keyword|candidate|document)\s+search\b",
        r"\bsearch\s+(system|engine|backend|infrastructure|relevance|ranking)\b",
    ),
    "ranking_recommendation_matching": (
        r"\branking\b",
        r"\branking layer\b",
        r"\branker\b",
        r"\blearning to rank\b",
        r"\brecommendation(s)?\b",
        r"\brecommender\b",
        r"\bpersonalization infrastructure\b",
        r"\bsearch and discovery\b",
        r"\bmatching\s+(system|engine|algorithm|pipeline|model)\b",
        r"\bmatching layer\b",
        r"\b(candidate|job|document|content)\s+matching\b",
        r"\brelevant matches\b",
        r"\bsurface\s+(the\s+)?(right|relevant)\s+(thing|content|items?|results?)\b",
        r"\bsearch relevance\b",
        r"\bltr\b",
    ),
    "ranking_evaluation": (
        r"\bndcg\b",
        r"\bmrr\b",
        r"\bmean average precision\b",
        r"\bprecision@",
        r"\brecall@",
        r"\branking evaluation\b",
        r"\bretrieval evaluation\b",
        r"\brelevance evaluation\b",
        r"\boffline evaluation\b",
        r"\bonline evaluation\b",
        r"\bevaluation framework\b",
        r"\bevaluation methodology\b",
        r"\bmodeling and evaluation\b",
        r"\beval side\b",
        r"\boffline metrics?\b",
        r"\bmetrics?\s+that\s+.*\bonline\b",
        r"\bonline engagement\b",
    ),
    "online_experimentation": (r"\ba/b\b", r"\bab test", r"\bonline experiment", r"\bexperimentation\b"),
    "learning_to_rank": (r"\blearning to rank\b", r"\blearn-to-rank\b", r"\bltr\b"),
    "meaningful_scale": (r"\b\d+\s*(m|million|k|thousand)\+?\b", r"\bscale\b", r"\bhigh[- ]traffic\b", r"\bqueries\b"),
    "production_delivery": (
        r"\bproduction\s+(ml|model|system|service|pipeline|retrieval|ranking|search)\b",
        r"\bship(ped|ping)?\b",
        r"\bdeploy(ed|ment)?\b",
        r"\bserved\b",
        r"\blaunched\b",
    ),
    "operational_ownership": (r"\bowned\b", r"\bownership\b", r"\bon-call\b", r"\boperational\b", r"\bmaintained\b"),
    "zero_to_one_ownership": (r"\bfrom scratch\b", r"\bfirst\b", r"\bzero[- ]to[- ]one\b", r"\bgreenfield\b"),
    "product_context": (r"\bproduct\b", r"\bsaas\b", r"\bmarketplace\b", r"\bconsumer\b", r"\buser\b"),
    "vector_hybrid_infrastructure": (
        r"\bvector\s+(search|database|db|index|store|retrieval|similarity|infrastructure)\b",
        r"\b(search|retrieval|similarity)\s+vector(s)?\b",
        r"\bhybrid\s+(search|retrieval|ranking|relevance)\b",
        r"\b(search|retrieval)\s+hybrid\b",
        r"\bfaiss\b",
        r"\bpinecone\b",
        r"\bmilvus\b",
        r"\bweaviate\b",
        r"\bqdrant\b",
        r"\belasticsearch\b",
        r"\bopensearch\b",
        r"\bpgvector\b",
    ),
    "python_engineering": (r"\bpython\b", r"\bpytorch\b", r"\btensorflow\b", r"\bfastapi\b", r"\bflask\b", r"\bmlops\b"),
    "mentoring_leadership": (r"\bmentor", r"\bled\b", r"\blead\b", r"\bstaff\b", r"\bprincipal\b", r"\barchitecture\b"),
    "llm_application_context": (r"\bchatgpt\b", r"\bprompt", r"\bllm\b", r"\bgenerative ai\b", r"\bcontent generation\b"),
    "research_only_context": (r"\bresearch[- ]only\b", r"\bacademic lab\b", r"\bresearch lab\b"),
    "consulting_services_context": (r"\bconsulting\b", r"\bclient\b", r"\badvisory\b", r"\bit services\b", r"\bservices\b"),
}


def build_candidate_overlay(
    candidate: dict[str, Any],
    integrity_findings: list[dict[str, Any]] | None = None,
    as_of: date = DEFAULT_AS_OF,
) -> dict[str, Any]:
    profile = candidate["profile"]
    roles = [role_evidence(role) for role in candidate.get("career_history", [])]
    career = career_evidence(roles)
    skills = skill_overlay(candidate.get("skills", []))
    rules = overlay_rules(candidate, roles, career, skills)
    return {
        "candidate_id": candidate["candidate_id"],
        "static": {
            "current_title": profile.get("current_title"),
            "years_of_experience": profile.get("years_of_experience"),
            "current_company": profile.get("current_company"),
            "current_industry": profile.get("current_industry"),
        },
        "career_evidence": career,
        "skill_overlay": skills,
        "availability_overlay": behavior_overlay(candidate["redrob_signals"], as_of),
        "logistics_overlay": logistics_overlay(profile, candidate["redrob_signals"]),
        "integrity_overlay": integrity_overlay(integrity_findings or []),
        "candidate_overlay_rules": rules,
    }


def role_evidence(role: dict[str, Any]) -> dict[str, Any]:
    text = role_text(role)
    signals = sorted(signal_id for signal_id, patterns in SIGNAL_PATTERNS.items() if matches_any(text, patterns))
    if not has_technical_role_context(role, text):
        signals = [
            signal
            for signal in signals
            if signal not in CORE_TECHNICAL_SIGNALS
        ]
    compounds = role_compounds(set(signals))
    risk_contexts = sorted(
        signal for signal in signals if signal in {"llm_application_context", "research_only_context", "consulting_services_context"}
    )
    if role.get("industry") in PRODUCT_INDUSTRIES and "product_context" not in signals:
        signals.append("product_context")
        signals.sort()
    if role.get("industry") in SERVICE_INDUSTRIES and "consulting_services_context" not in signals:
        risk_contexts.append("consulting_services_context")
        risk_contexts.sort()
    return {
        "company": role.get("company"),
        "title": role.get("title"),
        "industry": role.get("industry"),
        "duration_months": role.get("duration_months"),
        "is_current": role.get("is_current"),
        "signals": signals,
        "compounds": compounds,
        "risk_contexts": sorted(set(risk_contexts)),
    }


def role_text(role: dict[str, Any]) -> str:
    return " ".join(str(role.get(field, "")) for field in ("company", "title", "industry", "description"))


def matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def has_technical_role_context(role: dict[str, Any], text: str) -> bool:
    title = str(role.get("title", ""))
    industry = str(role.get("industry", ""))
    if TECHNICAL_TITLE_RE.search(title):
        return True
    if industry in {"AI/ML", "Software", "Internet", "SaaS", "HR Tech"} and TECHNICAL_TITLE_RE.search(text):
        return True
    return bool(STRONG_TECHNICAL_WORK_RE.search(text))


def role_compounds(signals: set[str]) -> list[str]:
    compounds = []
    if "production_delivery" in signals and signals & {"embeddings", "retrieval_search"}:
        compounds.append("production_embeddings_retrieval")
    if (
        "production_delivery" in signals
        and signals & {"vector_hybrid_infrastructure", "retrieval_search"}
    ):
        compounds.append("production_vector_or_hybrid_search")
    if "ranking_recommendation_matching" in signals and signals & {"ranking_evaluation", "online_experimentation", "learning_to_rank"}:
        compounds.append("evaluated_ranking_system")
    if (
        "production_delivery" in signals
        and "operational_ownership" in signals
        and signals & {"embeddings", "retrieval_search", "ranking_recommendation_matching"}
    ):
        compounds.append("end_to_end_intelligence_ownership")
    if (
        "operational_ownership" in signals
        and "product_context" in signals
        and "ranking_recommendation_matching" in signals
        and signals & {"ranking_evaluation", "online_experimentation", "learning_to_rank"}
    ):
        compounds.append("end_to_end_intelligence_ownership")
    if "production_delivery" in signals and signals & {"ranking_evaluation", "online_experimentation"}:
        compounds.append("shipper_with_evaluation_depth")
    return sorted(set(compounds))


def career_evidence(roles: list[dict[str, Any]]) -> dict[str, Any]:
    signals = sorted({signal for role in roles for signal in role["signals"]})
    compounds = sorted({compound for role in roles for compound in role["compounds"]})
    risk_contexts = sorted({context for role in roles for context in role["risk_contexts"]})
    current = next((role for role in roles if role.get("is_current")), roles[0] if roles else {})
    return {
        "any_career_signal_ids": signals,
        "any_career_compound_ids": compounds,
        "any_career_risk_context_ids": risk_contexts,
        "current_signal_ids": current.get("signals", []),
        "current_compound_ids": current.get("compounds", []),
        "role_evidence": roles,
    }


def skill_overlay(skills: list[dict[str, Any]]) -> dict[str, Any]:
    signal_counts: dict[str, int] = {}
    advanced_counts: dict[str, int] = {}
    names = []
    for skill in skills:
        name = str(skill.get("name", "")).strip()
        if not name:
            continue
        names.append(name)
        for signal_id, patterns in SIGNAL_PATTERNS.items():
            if signal_id in {"research_only_context", "consulting_services_context"}:
                continue
            if matches_any(name, patterns):
                signal_counts[signal_id] = signal_counts.get(signal_id, 0) + 1
                if str(skill.get("proficiency", "")).lower() in {"advanced", "expert"}:
                    advanced_counts[signal_id] = advanced_counts.get(signal_id, 0) + 1
    return {
        "skill_names": sorted(names),
        "skill_signal_ids": sorted(signal_counts),
        "skill_signal_counts": dict(sorted(signal_counts.items())),
        "advanced_or_expert_signal_counts": dict(sorted(advanced_counts.items())),
    }


def behavior_overlay(signals: dict[str, Any], as_of: date) -> dict[str, Any]:
    last_active = parse_date(signals.get("last_active_date"))
    inactive_days = (as_of - last_active).days if last_active else None
    return {
        "inactive_days": inactive_days,
        "open_to_work": bool(signals.get("open_to_work_flag")),
        "response_rate": signals.get("recruiter_response_rate"),
        "response_time_hours": signals.get("avg_response_time_hours"),
        "notice_period_days": signals.get("notice_period_days"),
        "profile_views_30d": signals.get("profile_views_received_30d"),
        "search_appearance_30d": signals.get("search_appearance_30d"),
        "saved_by_recruiters_30d": signals.get("saved_by_recruiters_30d"),
        "interview_completion_rate": signals.get("interview_completion_rate"),
        "offer_acceptance_rate": signals.get("offer_acceptance_rate"),
        "github_activity_score": signals.get("github_activity_score"),
        "willing_to_relocate": bool(signals.get("willing_to_relocate")),
    }


def logistics_overlay(profile: dict[str, Any], signals: dict[str, Any]) -> dict[str, Any]:
    return {
        "location": profile.get("location"),
        "country": profile.get("country"),
        "location_bucket": location_bucket(profile, signals),
        "preferred_work_mode": signals.get("preferred_work_mode"),
        "willing_to_relocate": bool(signals.get("willing_to_relocate")),
        "notice_period_days": signals.get("notice_period_days"),
    }


def location_bucket(profile: dict[str, Any], signals: dict[str, Any]) -> str:
    location = str(profile.get("location", ""))
    country = str(profile.get("country", ""))
    if re.search(r"\bpune\b", location, re.I):
        return "pune"
    if re.search(r"\bnoida\b", location, re.I):
        return "noida"
    if re.search(r"\b(gurgaon|gurugram|delhi|ncr)\b", location, re.I):
        return "ncr"
    if country.lower() != "india":
        return "outside_india_relocatable" if signals.get("willing_to_relocate") else "outside_india"
    return "india_other"


def integrity_overlay(findings: list[dict[str, Any]]) -> dict[str, Any]:
    rules = sorted({finding["rule"] for finding in findings})
    high_confidence = sorted(set(rules) & HIGH_CONFIDENCE_RULES)
    honeypot_proxy = sorted(
        set(rules) & {"company_pre_founding", "expert_zero_duration_3plus"}
    )
    return {
        "risk_level": risk_level(findings),
        "issue_rules": rules,
        "high_confidence_rules": high_confidence,
        "honeypot_proxy_rules": honeypot_proxy,
        "issue_count": len(findings),
    }


def overlay_rules(
    candidate: dict[str, Any],
    roles: list[dict[str, Any]],
    career: dict[str, Any],
    skills: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    services = services_only(roles)
    research = research_only_without_production(roles, career)
    shallow = recent_shallow_llm_only(roles, career, skills)
    not_coding = senior_not_coding_recently(candidate, roles)
    return {
        "services_only_entire_career": {
            "fired": services,
            "reason": "career appears services-only" if services else "not services-only",
        },
        "research_only_without_production": {
            "fired": research,
            "reason": "research context without production delivery" if research else "not research-only",
        },
        "recent_shallow_llm_only": {
            "fired": shallow,
            "reason": "recent shallow LLM context without production ML" if shallow else "no shallow-only pattern",
        },
        "senior_not_coding_recently": {
            "fired": not_coding,
            "reason": "senior title without recent hands-on signals" if not_coding else "recent hands-on evidence present or not senior",
        },
    }


def services_only(roles: list[dict[str, Any]]) -> bool:
    if not roles:
        return False
    service_roles = [
        role for role in roles
        if "consulting_services_context" in role["risk_contexts"]
        or role.get("industry") in SERVICE_INDUSTRIES
    ]
    product_roles = [
        role for role in roles
        if "product_context" in role["signals"]
        or role.get("industry") in PRODUCT_INDUSTRIES
    ]
    return len(service_roles) == len(roles) and not product_roles


def research_only_without_production(
    roles: list[dict[str, Any]],
    career: dict[str, Any],
) -> bool:
    if "production_delivery" in career["any_career_signal_ids"]:
        return False
    research_roles = [
        role for role in roles if "research_only_context" in role["risk_contexts"]
    ]
    return bool(research_roles) and len(research_roles) == len(roles)


def recent_shallow_llm_only(
    roles: list[dict[str, Any]],
    career: dict[str, Any],
    skills: dict[str, Any],
) -> bool:
    if career["any_career_compound_ids"]:
        return False
    has_llm = (
        "llm_application_context" in career["any_career_risk_context_ids"]
        or "llm_application_context" in skills.get("skill_signal_ids", [])
    )
    has_deep_ml = bool(
        set(career["any_career_signal_ids"])
        & {"embeddings", "retrieval_search", "ranking_recommendation_matching", "ranking_evaluation"}
    )
    return has_llm and not has_deep_ml


def senior_not_coding_recently(candidate: dict[str, Any], roles: list[dict[str, Any]]) -> bool:
    title = str(candidate.get("profile", {}).get("current_title", ""))
    if not re.search(r"\b(senior|staff|principal|lead|architect|head)\b", title, re.I):
        return False
    current = next((role for role in roles if role.get("is_current")), roles[0] if roles else {})
    hands_on = {
        "embeddings",
        "python_engineering",
        "ranking_recommendation_matching",
        "retrieval_search",
        "vector_hybrid_infrastructure",
        "production_delivery",
    }
    return not bool(set(current.get("signals", [])) & hands_on)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)
