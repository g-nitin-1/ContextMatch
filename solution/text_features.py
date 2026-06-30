#!/usr/bin/env python3
"""Candidate text extraction and lightweight lexical similarity helpers."""

from __future__ import annotations

import math
import re
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+_.-]*", re.IGNORECASE)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def tokens(text: str) -> set[str]:
    result = set()
    for match in TOKEN_RE.finditer(text):
        token = match.group(0).lower().strip("._-")
        if token and token not in STOPWORDS:
            result.add(token)
    return result


def career_weighted_tokens(candidate: dict[str, Any]) -> list[str]:
    return sorted(tokens(career_weighted_text(candidate)))


def candidate_text_sections(candidate: dict[str, Any]) -> dict[str, str]:
    profile = candidate.get("profile", {})
    career_parts = []
    for role in candidate.get("career_history", []):
        career_parts.extend(
            [
                str(role.get("title", "")),
                str(role.get("company", "")),
                str(role.get("industry", "")),
                str(role.get("description", "")),
            ]
        )
    skill_text = " ".join(str(skill.get("name", "")) for skill in candidate.get("skills", []))
    return {
        "career": " ".join(part for part in career_parts if part),
        "summary": " ".join(
            str(profile.get(key, "")) for key in ("headline", "summary")
        ),
        "skills": skill_text,
    }


def career_weighted_text(candidate: dict[str, Any]) -> str:
    sections = candidate_text_sections(candidate)
    # The repeated career section makes lexical fallback follow the same evidence
    # priority as the future embedding text: career history first, skills last.
    return " ".join(
        [
            sections["career"],
            sections["career"],
            sections["summary"],
            sections["skills"],
        ]
    )


def query_coverage_score(queries: tuple[str, ...], text: str) -> float:
    return query_coverage_score_from_tokens(queries, tokens(text))


def query_coverage_score_from_tokens(
    queries: tuple[str, ...],
    text_tokens: set[str] | list[str] | tuple[str, ...],
) -> float:
    text_tokens = set(text_tokens)
    if not text_tokens:
        return 0.0
    scores = []
    for query in queries:
        query_tokens = tokens(query)
        if not query_tokens:
            continue
        overlap = len(query_tokens & text_tokens)
        coverage = overlap / len(query_tokens)
        density = overlap / math.sqrt(max(len(text_tokens), 1))
        scores.append(min(1.0, 0.8 * coverage + 0.2 * density))
    return max(scores) if scores else 0.0
