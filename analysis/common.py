#!/usr/bin/env python3
"""Shared helpers for deterministic candidate analysis."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Iterator


_MODULE_ROOT = Path(__file__).absolute().parents[1]
_WORKING_ROOT = Path.cwd()
_LOWERCASE_WORKING_ALIAS = _WORKING_ROOT.with_name(_WORKING_ROOT.name.lower())
if (
    _LOWERCASE_WORKING_ALIAS.exists()
    and os.path.samefile(_LOWERCASE_WORKING_ALIAS, _WORKING_ROOT)
):
    _WORKING_ROOT = _LOWERCASE_WORKING_ALIAS
REPO_ROOT = (
    _WORKING_ROOT
    if (_WORKING_ROOT / "India_runs_data_and_ai_challenge").is_dir()
    else _MODULE_ROOT
)
_LOCAL_DATASET = (
    _WORKING_ROOT / "India_runs_data_and_ai_challenge" / "candidates.jsonl"
)
DEFAULT_DATASET = (
    _LOCAL_DATASET
    if _LOCAL_DATASET.is_file()
    else REPO_ROOT / "India_runs_data_and_ai_challenge" / "candidates.jsonl"
)
DEFAULT_OUTPUT_DIR = (
    _WORKING_ROOT / "artifacts" / "analysis"
    if _LOCAL_DATASET.is_file()
    else REPO_ROOT / "artifacts" / "analysis"
)

_NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)*(?:%|[KkMmBb]\+?)?")
_WHITESPACE_RE = re.compile(r"\s+")


def stream_candidates(path: Path) -> Iterator[dict[str, Any]]:
    """Yield non-empty JSONL records without loading the dataset into memory."""
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc


def clean_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.strip())


def canonicalize_numbers(text: str) -> str:
    """Normalize variable numeric values while retaining the surrounding wording."""
    return _NUMBER_RE.sub("<num>", clean_text(text).lower())


def stable_id(value: Any, prefix: str, length: int = 12) -> str:
    """Return a deterministic, compact identifier for structured content."""
    if isinstance(value, str):
        payload = value
    else:
        payload = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def summary_archetype(summary: str, current_title: str = "") -> str:
    """Classify the high-level synthetic summary family without assigning relevance."""
    prefix_map = (
        ("Senior engineer who has spent", "senior_plain_language"),
        ("Senior AI engineer with", "senior_explicit_ai"),
        ("Machine learning engineer with", "applied_ml"),
        ("Data scientist / ML engineer with", "generic_ml"),
        ("Software / data professional with", "data_backend_adjacent"),
        ("Software engineer with", "general_software"),
        ("Professional with", "general_professional"),
    )
    for prefix, name in prefix_map:
        if summary.startswith(prefix):
            return name

    first_sentence = clean_text(summary).split(".", 1)[0]
    direct_match = re.match(r"^(.+?) with \d", first_sentence, re.IGNORECASE)
    if direct_match:
        occupation = direct_match.group(1).strip().lower()
        if occupation and (
            not current_title or occupation in current_title.lower()
        ):
            return "direct_occupation"
    return "other"


def title_family(title: str) -> str:
    value = clean_text(title).lower()
    ai_terms = (
        "machine learning",
        "ml engineer",
        "ai engineer",
        "ai research",
        "ai specialist",
        "applied scientist",
        "applied ml",
        "nlp engineer",
        "search engineer",
        "recommendation systems",
        "data scientist",
        "software engineer (ml)",
    )
    senior_terms = ("senior", "staff", "lead", "principal", "head")
    if any(term in value for term in ai_terms):
        if any(term in value for term in senior_terms):
            return "senior_ai_ml"
        return "ai_ml"
    if any(
        term in value
        for term in (
            "data engineer",
            "analytics engineer",
            "data analyst",
            "backend engineer",
        )
    ):
        return "data_backend"
    if any(
        term in value
        for term in (
            "software",
            "developer",
            "devops",
            "cloud engineer",
            "frontend",
            "full stack",
            ".net",
            "java",
            "mobile",
            "qa engineer",
        )
    ):
        return "software"
    return "other"


def career_template_id(description: str) -> str:
    return stable_id(clean_text(description), "career")


def summary_template_id(summary: str) -> str:
    return stable_id(canonicalize_numbers(summary), "summary")


def headline_template_id(headline: str) -> str:
    return stable_id(canonicalize_numbers(headline), "headline")


def career_sequence(candidate: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        career_template_id(role.get("description", ""))
        for role in candidate.get("career_history", [])
    )


def education_signature(candidate: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    entries = []
    for education in candidate.get("education", []):
        entries.append(
            (
                education.get("tier", "unknown"),
                clean_text(education.get("degree", "")).lower(),
                clean_text(education.get("field_of_study", "")).lower(),
            )
        )
    return tuple(sorted(entries))


def experience_bucket(years: float, width: float = 1.0) -> float:
    return round(float(years) / width) * width


def strict_static_signature(candidate: dict[str, Any]) -> tuple[Any, ...]:
    """Signature used for behavioral twins; excludes every behavioral field."""
    profile = candidate["profile"]
    return (
        summary_archetype(profile.get("summary", ""), profile.get("current_title", "")),
        clean_text(profile.get("current_title", "")).lower(),
        experience_bucket(profile.get("years_of_experience", 0.0)),
        career_sequence(candidate),
        education_signature(candidate),
    )


def career_static_signature(candidate: dict[str, Any]) -> tuple[Any, ...]:
    """Near-twin signature that keeps career evidence but excludes education."""
    profile = candidate["profile"]
    return (
        summary_archetype(profile.get("summary", ""), profile.get("current_title", "")),
        clean_text(profile.get("current_title", "")).lower(),
        experience_bucket(profile.get("years_of_experience", 0.0)),
        career_sequence(candidate),
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")


def percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    if fraction <= 0:
        return sorted_values[0]
    if fraction >= 1:
        return sorted_values[-1]
    position = (len(sorted_values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def markdown_table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
    header_list = [str(value) for value in headers]
    lines = [
        "| " + " | ".join(header_list) + " |",
        "| " + " | ".join("---" for _ in header_list) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)
