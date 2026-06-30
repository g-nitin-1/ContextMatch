#!/usr/bin/env python3
"""Read a job description and turn it into a structured requirement spec."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from solution.requirement_spec import (
    SPEC_VERSION,
    RequirementItem,
    RequirementSpec,
    write_spec,
)


WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


CONCEPTS: dict[str, dict[str, Any]] = {
    "production_retrieval": {
        "desc": "Production retrieval, search, ranking, matching, or recommendation systems",
        "weight": 1.0,
        "terms": (
            "retrieval",
            "search",
            "ranking",
            "matching",
            "recommendation",
            "recommender",
            "embedding",
            "vector",
            "rag",
        ),
        "signals": (
            "embeddings",
            "retrieval_search",
            "ranking_recommendation_matching",
            "production_delivery",
        ),
        "compound": "production_embeddings_retrieval",
        "compounds": (
            "production_embeddings_retrieval",
            "production_vector_or_hybrid_search",
            "end_to_end_intelligence_ownership",
            "evaluated_ranking_system",
        ),
    },
    "evaluated_ranking": {
        "desc": "Evaluation depth for relevance, ranking, matching, or model quality",
        "weight": 0.9,
        "terms": (
            "ndcg",
            "mrr",
            "precision",
            "recall",
            "a/b",
            "ab test",
            "experiment",
            "evaluation",
            "metrics",
            "relevance",
        ),
        "signals": (
            "ranking_evaluation",
            "online_experimentation",
            "learning_to_rank",
            "meaningful_scale",
        ),
        "compound": "evaluated_ranking_system",
        "compounds": (
            "evaluated_ranking_system",
            "shipper_with_evaluation_depth",
            "end_to_end_intelligence_ownership",
        ),
    },
    "end_to_end_ownership": {
        "desc": "End-to-end ownership of shipped technical systems",
        "weight": 0.8,
        "terms": (
            "own",
            "ownership",
            "end-to-end",
            "end to end",
            "ship",
            "shipped",
            "production",
            "deploy",
            "scale",
        ),
        "signals": (
            "operational_ownership",
            "zero_to_one_ownership",
            "production_delivery",
            "product_context",
        ),
        "compound": "end_to_end_intelligence_ownership",
        "compounds": (
            "end_to_end_intelligence_ownership",
            "shipper_with_evaluation_depth",
        ),
    },
    "ml_engineering": {
        "desc": "Machine learning or AI engineering depth",
        "weight": 0.7,
        "terms": (
            "machine learning",
            "ml",
            "ai",
            "llm",
            "nlp",
            "model",
            "models",
            "deep learning",
        ),
        "signals": (
            "python_engineering",
            "production_delivery",
            "operational_ownership",
        ),
        "compound": None,
        "compounds": (),
    },
    "vector_hybrid_search": {
        "desc": "Vector, hybrid, or search infrastructure depth",
        "weight": 0.5,
        "terms": (
            "vector",
            "hybrid",
            "faiss",
            "pinecone",
            "milvus",
            "weaviate",
            "qdrant",
            "elasticsearch",
            "opensearch",
            "bm25",
        ),
        "signals": (
            "vector_hybrid_infrastructure",
            "retrieval_search",
            "embeddings",
        ),
        "compound": "production_vector_or_hybrid_search",
        "compounds": (
            "production_vector_or_hybrid_search",
            "production_embeddings_retrieval",
        ),
    },
    "senior_leadership": {
        "desc": "Senior IC, technical leadership, or mentoring responsibility",
        "weight": 0.25,
        "terms": (
            "senior",
            "staff",
            "principal",
            "lead",
            "mentor",
            "architecture",
            "technical leadership",
        ),
        "signals": (
            "mentoring_leadership",
            "operational_ownership",
        ),
        "compound": None,
        "compounds": (),
    },
    "people_leadership": {
        "desc": "People leadership, team management, hiring, mentoring, or delivery ownership",
        "weight": 0.8,
        "terms": (
            "engineering manager",
            "manager",
            "manage a team",
            "managed a team",
            "people management",
            "team management",
            "hiring",
            "performance review",
            "mentor",
            "delivery ownership",
        ),
        "signals": (
            "mentoring_leadership",
            "operational_ownership",
        ),
        "compound": None,
        "compounds": (),
    },
}


def read_jd_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return read_docx_text(path)
    return path.read_text(encoding="utf-8")


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml")
    root = ElementTree.fromstring(document)
    paragraphs = []
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        parts = [
            node.text or ""
            for node in paragraph.iter(f"{WORD_NAMESPACE}t")
            if node.text
        ]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def parse_jd(path: Path) -> RequirementSpec:
    return spec_from_jd_text(read_jd_text(path))


def spec_from_jd_text(text: str) -> RequirementSpec:
    normalized = normalize(text)
    role_title = infer_role_title(text)
    matched = [
        (concept_id, payload)
        for concept_id, payload in CONCEPTS.items()
        if any(term in normalized for term in payload["terms"])
    ]
    if not matched:
        matched = [("ml_engineering", CONCEPTS["ml_engineering"])]

    must_payloads = matched[:3]
    nice_payloads = matched[3:]
    if not nice_payloads and "senior" in normalized:
        nice_payloads = [("senior_leadership", CONCEPTS["senior_leadership"])]

    return RequirementSpec(
        schema_version=SPEC_VERSION,
        role_title=role_title,
        seniority=infer_seniority(normalized),
        must_have=tuple(item_from_concept(concept_id, payload) for concept_id, payload in must_payloads),
        nice_to_have=tuple(item_from_concept(concept_id, payload) for concept_id, payload in nice_payloads),
        hard_disqualifiers=(
            "services_only_entire_career",
            "research_only_without_production",
        ),
        soft_negatives=(
            "recent_shallow_llm_only",
            "senior_not_coding_recently",
        ),
        location=infer_location(text),
        semantic_queries=semantic_queries(text, role_title),
    )


def item_from_concept(concept_id: str, payload: dict[str, Any]) -> RequirementItem:
    return RequirementItem(
        id=concept_id,
        desc=str(payload["desc"]),
        weight=float(payload["weight"]),
        evidence_signals=tuple(payload["signals"]),
        compound=payload.get("compound"),
        compounds=tuple(payload.get("compounds", ())),
    )


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def infer_role_title(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip(" #:\t")
        if not cleaned:
            continue
        if len(cleaned) <= 80 and re.search(r"\b(engineer|scientist|developer|manager|analyst|architect)\b", cleaned, re.I):
            return cleaned
    match = re.search(
        r"\b(senior|staff|lead|principal)?\s*(ai|ml|machine learning|data|software)\s+"
        r"(engineer|scientist|architect|developer)\b",
        text,
        re.I,
    )
    if match:
        return re.sub(r"\s+", " ", match.group(0)).strip().title()
    return "Target Role"


def infer_seniority(normalized_text: str) -> dict[str, Any]:
    min_years, max_years = infer_year_band(normalized_text)
    hard = bool(
        re.search(
            r"\b(must|required|minimum|at least|no exceptions|mandatory)\b",
            normalized_text,
        )
    )
    if re.search(r"\b(not a requirement|range,? not a requirement|outside the band|outside the range|will seriously consider)\b", normalized_text):
        hard = False

    level = infer_seniority_level(normalized_text, min_years)
    track = infer_seniority_track(normalized_text)
    strength = seniority_strength(level, track, hard, normalized_text)

    senior_terms = (
        "junior",
        "entry",
        "associate",
        "mid",
        "senior",
        "staff",
        "lead",
        "principal",
        "founding",
        "architect",
        "manager",
    )
    track_terms = (
        "hands-on",
        "hands on",
        "writes code",
        "write code",
        "individual contributor",
        "ic",
        "manager",
        "people management",
        "team management",
        "architecture",
        "tech lead",
    )
    return {
        "level": level,
        "track": track,
        "min_years": min_years,
        "max_years": max_years,
        "hard": hard,
        "strength": strength,
        "seniority_terms": [term for term in senior_terms if term in normalized_text],
        "track_terms": [term for term in track_terms if term in normalized_text],
    }


def infer_year_band(normalized_text: str) -> tuple[int, int | None]:
    range_match = re.search(
        r"(\d+)\s*(?:-|to|–|—)\s*(\d+)\+?\s*(?:years|yrs)",
        normalized_text,
    )
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))
    plus_match = re.search(r"(\d+)\+?\s*(?:years|yrs)", normalized_text)
    if plus_match:
        value = int(plus_match.group(1))
        return value, None
    return 0, None


def infer_seniority_level(normalized_text: str, min_years: int) -> str:
    opening = normalized_text[:100]
    if re.search(r"\b(intern|entry[- ]level|entry level|junior|associate)\b", normalized_text):
        return "junior"
    if re.search(r"\bprincipal\b", opening):
        return "principal"
    if re.search(r"\bstaff\b", opening):
        return "staff"
    if re.search(r"\b(senior|lead|founding)\b", opening):
        return "senior"
    if re.search(r"\b(principal|distinguished|director|head of)\b", normalized_text):
        return "principal"
    if re.search(r"\bstaff\b", normalized_text):
        return "staff"
    if re.search(r"\b(senior|lead|founding)\b", normalized_text):
        return "senior"
    if re.search(r"\b(mid[- ]level|mid level)\b", normalized_text):
        return "mid"
    if min_years >= 10:
        return "principal"
    if min_years >= 7:
        return "senior"
    if min_years >= 3:
        return "mid"
    if min_years > 0:
        return "junior"
    return "unspecified"


def infer_seniority_track(normalized_text: str) -> str:
    management = bool(
        re.search(
            r"\b(engineering manager|people manager|people management|"
            r"team management|manage a team|managed a team|performance reviews|"
            r"hiring manager|manager)\b",
            normalized_text,
        )
    )
    ic = bool(
        re.search(
            r"\b(hands[- ]on|writes code|write code|individual contributor|"
            r"\bic\b|founding team|own end[- ]to[- ]end|own .*end[- ]to[- ]end|"
            r"coding)\b",
            normalized_text,
        )
    )
    if management and not ic:
        return "management"
    if ic:
        return "ic"
    return "either"


def seniority_strength(
    level: str,
    track: str,
    hard: bool,
    normalized_text: str,
) -> float:
    if level == "unspecified" and track == "either":
        return 0.0
    if hard:
        return 0.55
    if re.search(r"\b(not a requirement|outside the band|outside the range|will seriously consider)\b", normalized_text):
        return 0.25
    if level in {"senior", "staff", "principal"} and track == "ic":
        return 0.35
    if level == "junior":
        return 0.4
    return 0.25


def infer_location(text: str) -> dict[str, Any]:
    preferred = []
    for city in ("Pune", "Noida", "NCR", "Gurgaon", "Gurugram", "Delhi", "Bangalore", "Bengaluru", "Hyderabad"):
        if re.search(rf"\b{re.escape(city)}\b", text, re.I):
            preferred.append(city)
    return {
        "preferred": preferred,
        "relocate_ok": bool(re.search(r"\b(relocat|hybrid|remote|flexible)\b", text, re.I)),
    }


def semantic_queries(text: str, role_title: str) -> tuple[str, ...]:
    sentences = [
        sentence.strip(" \n\t-*")
        for sentence in SENTENCE_RE.split(re.sub(r"\s+", " ", text))
        if len(sentence.strip()) >= 30
    ]
    scored = []
    for sentence in sentences:
        lowered = sentence.lower()
        score = sum(
            lowered.count(term)
            for payload in CONCEPTS.values()
            for term in payload["terms"]
        )
        if score:
            scored.append((score, sentence))
    selected = [sentence for _, sentence in sorted(scored, reverse=True)[:6]]
    selected.append(role_title)
    return tuple(dict.fromkeys(selected))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jd", type=Path)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = parse_jd(args.jd)
    if args.out:
        write_spec(spec, args.out)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(spec.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
