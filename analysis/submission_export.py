#!/usr/bin/env python3
"""Export scored Idea 2 rows in the challenge submission format."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


SUBMISSION_COLUMNS = ("candidate_id", "rank", "score", "reasoning")
RELEVANT_SKILL_RE = re.compile(
    r"\b("
    r"bm25|elasticsearch|faiss|pinecone|milvus|weaviate|qdrant|"
    r"retriev|search|rank|recommend|embedding|vector|python"
    r")\b",
    re.IGNORECASE,
)

COMPOUND_PHRASES = {
    "end_to_end_intelligence_ownership": "end-to-end intelligent-system ownership",
    "production_embeddings_retrieval": "production embeddings and retrieval",
    "production_vector_or_hybrid_search": "production vector or hybrid search",
    "shipper_with_evaluation_depth": "shipping work with evaluation depth",
    "evaluated_ranking_system": "evaluated ranking or recommendation systems",
}


def _split(value: Any) -> list[str]:
    return [part for part in str(value or "").split(";") if part]


def _join_phrases(values: list[str], limit: int = 2) -> str:
    selected = values[:limit]
    if not selected:
        return ""
    if len(selected) == 1:
        return selected[0]
    return f"{selected[0]} and {selected[1]}"


def _experience_text(value: Any) -> str:
    try:
        return f"{float(value):.1f} years"
    except (TypeError, ValueError):
        return "undisclosed experience"


def _relevant_skill_names(row: dict[str, Any]) -> list[str]:
    return [
        skill
        for skill in _split(row.get("skill_names"))
        if RELEVANT_SKILL_RE.search(skill)
    ]


def _career_phrases(row: dict[str, Any]) -> list[str]:
    return [
        COMPOUND_PHRASES[compound]
        for compound in _split(row.get("career_compounds"))
        if compound in COMPOUND_PHRASES
    ]


def _availability_sentence(row: dict[str, Any], rank: int) -> str:
    facts = []
    concerns = []
    inactive_days = row.get("inactive_days")
    notice = row.get("notice_period_days")
    location = str(row.get("location") or "").strip()
    country = str(row.get("country") or "").strip()

    if inactive_days is not None:
        inactive_days = int(inactive_days)
        if inactive_days <= 45:
            facts.append(f"active {inactive_days} days ago")
        elif inactive_days > 90:
            concerns.append(f"last active {inactive_days} days ago")

    if row.get("open_to_work") in (True, "True", "true", 1, "1"):
        facts.append("open to work")
    else:
        concerns.append("not marked open to work")

    if notice is not None:
        notice = int(notice)
        if notice <= 30:
            facts.append(f"{notice}-day notice")
        elif notice >= 90:
            concerns.append(f"{notice}-day notice")

    if row.get("location_bucket") in {"pune", "noida", "ncr"} and location:
        facts.append(f"based in {location}")
    elif row.get("location_bucket") == "outside_india":
        concerns.append(f"based in {location or country} without relocation intent")
    elif row.get("location_bucket") == "outside_india_relocatable":
        concerns.append(f"currently in {location or country}, but willing to relocate")

    if concerns:
        lead = "Concerns" if rank <= 50 else "Trade-offs"
        return f"{lead}: {_join_phrases(concerns, 2)}."
    if facts:
        return f"Availability is favorable: {_join_phrases(facts, 3)}."
    return "Availability signals are neutral rather than a major ranking factor."


def build_reasoning(row: dict[str, Any], rank: int) -> str:
    title = str(row.get("current_title") or "Candidate")
    company = str(row.get("current_company") or "an undisclosed employer")
    experience = _experience_text(row.get("years_of_experience"))
    career_phrases = _career_phrases(row)
    skills = _relevant_skill_names(row)

    evidence_parts = []
    if career_phrases:
        evidence_parts.append(f"career evidence shows {_join_phrases(career_phrases)}")
    if skills:
        evidence_parts.append(f"listed skills include {_join_phrases(skills)}")
    if not evidence_parts:
        evidence_parts.append("career evidence is adjacent to the JD")

    first = (
        f"{title} at {company} with {experience}; "
        f"{'; '.join(evidence_parts)}."
    )
    return f"{first} {_availability_sentence(row, rank)}"


def _submission_score(row: dict[str, Any], rank: int) -> str:
    raw_score = float(row["mean_score"])
    # Keep model scores interpretable while making displayed ties deterministic.
    return f"{raw_score - rank * 1e-9:.9f}"


def submission_rows(
    scored_rows: list[dict[str, Any]],
    limit: int = 100,
) -> list[dict[str, Any]]:
    if len(scored_rows) < limit:
        raise ValueError(f"need at least {limit} scored candidates")

    selected = scored_rows[:limit]
    candidate_ids = [str(row["candidate_id"]) for row in selected]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("submission candidates must be unique")

    return [
        {
            "candidate_id": row["candidate_id"],
            "rank": rank,
            "score": _submission_score(row, rank),
            "reasoning": build_reasoning(row, rank),
        }
        for rank, row in enumerate(selected, 1)
    ]


def write_submission_csv(
    scored_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    rows = submission_rows(scored_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUBMISSION_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
