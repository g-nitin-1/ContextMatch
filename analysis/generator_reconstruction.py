#!/usr/bin/env python3
"""Reverse-engineer generator structure without assigning relevance scores."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import AgglomerativeClustering, MiniBatchKMeans
from sklearn.metrics import (
    adjusted_mutual_info_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler, normalize

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    career_template_id,
    headline_template_id,
    stream_candidates,
    summary_archetype,
    summary_template_id,
    title_family,
    write_json,
)


REFERENCE_DATE = date(2026, 6, 1)
BEHAVIOR_FEATURES = [
    "profile_completeness",
    "inactive_days",
    "open_to_work",
    "response_rate",
    "response_time_hours",
    "profile_views_log",
    "applications_log",
    "notice_period_days",
    "willing_to_relocate",
    "github_score",
    "github_missing",
    "search_appearances_log",
    "recruiter_saves_log",
    "interview_completion",
    "offer_acceptance",
    "offer_history_missing",
    "verification_count",
]
MUTATION_RULES = {
    "company_pre_founding": "company_chronology",
    "technology_before_release": "technology_chronology",
    "expert_zero_duration_3plus": "zero_duration_expert",
    "role_duration_large_mismatch": "duration_corruption",
    "career_duration_exceeds_experience": "duration_corruption",
}


@dataclass
class TemplateStats:
    count: int = 0
    canonical_summary: str = ""
    archetypes: Counter[str] = field(default_factory=Counter)
    headlines: Counter[str] = field(default_factory=Counter)
    title_families: Counter[str] = field(default_factory=Counter)
    current_titles: Counter[str] = field(default_factory=Counter)
    current_careers: Counter[str] = field(default_factory=Counter)
    all_careers: Counter[str] = field(default_factory=Counter)
    industries: Counter[str] = field(default_factory=Counter)
    companies: Counter[str] = field(default_factory=Counter)
    skills: Counter[str] = field(default_factory=Counter)
    role_counts: Counter[int] = field(default_factory=Counter)
    mutation_families: Counter[str] = field(default_factory=Counter)
    behavior_sums: np.ndarray = field(
        default_factory=lambda: np.zeros(len(BEHAVIOR_FEATURES), dtype=float)
    )


def conditional_mode_accuracy(x: Iterable[str], y: Iterable[str]) -> float:
    """Accuracy from predicting the modal Y value associated with each X."""
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    total = 0
    for x_value, y_value in zip(x, y):
        groups[x_value][y_value] += 1
        total += 1
    if not total:
        return 0.0
    correct = sum(group.most_common(1)[0][1] for group in groups.values())
    return correct / total


def correlation_ratio(categories: Iterable[str], measurements: Iterable[float]) -> float:
    """Eta-squared: the numeric variance explained by categorical groups."""
    category_array = np.asarray(list(categories))
    values = np.asarray(list(measurements), dtype=float)
    if values.size == 0 or float(np.var(values)) == 0.0:
        return 0.0
    grand_mean = float(np.mean(values))
    between = 0.0
    for category in np.unique(category_array):
        group = values[category_array == category]
        between += len(group) * float((np.mean(group) - grand_mean) ** 2)
    total = float(np.sum((values - grand_mean) ** 2))
    return between / total if total else 0.0


def _top(counter: Counter[Any], limit: int = 10) -> list[dict[str, Any]]:
    return [
        {"value": str(value), "count": count}
        for value, count in counter.most_common(limit)
    ]


def _dominant(counter: Counter[str]) -> tuple[str, float]:
    total = sum(counter.values())
    if not total:
        return "", 0.0
    value, count = counter.most_common(1)[0]
    return value, count / total


def _entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 1:
        return 0.0
    return -sum(
        (count / total) * math.log2(count / total)
        for count in counter.values()
        if count
    )


def _distribution(counter: Counter[str], categories: list[str]) -> np.ndarray:
    total = sum(counter.values())
    if not total:
        return np.zeros(len(categories), dtype=float)
    return np.array([counter.get(value, 0) / total for value in categories])


def _behavior_vector(candidate: dict[str, Any]) -> list[float]:
    signals = candidate["redrob_signals"]
    inactive_days = (REFERENCE_DATE - date.fromisoformat(signals["last_active_date"])).days
    github_score = float(signals["github_activity_score"])
    offer_acceptance = float(signals["offer_acceptance_rate"])
    return [
        float(signals["profile_completeness_score"]),
        float(inactive_days),
        float(bool(signals["open_to_work_flag"])),
        float(signals["recruiter_response_rate"]),
        float(signals["avg_response_time_hours"]),
        math.log1p(max(0, int(signals["profile_views_received_30d"]))),
        math.log1p(max(0, int(signals["applications_submitted_30d"]))),
        float(signals["notice_period_days"]),
        float(bool(signals["willing_to_relocate"])),
        max(0.0, github_score),
        float(github_score < 0),
        math.log1p(max(0, int(signals["search_appearance_30d"]))),
        math.log1p(max(0, int(signals["saved_by_recruiters_30d"]))),
        float(signals["interview_completion_rate"]),
        max(0.0, offer_acceptance),
        float(offer_acceptance < 0),
        float(
            bool(signals["verified_email"])
            + bool(signals["verified_phone"])
            + bool(signals["linkedin_connected"])
        ),
    ]


def _current_role(candidate: dict[str, Any]) -> dict[str, Any]:
    roles = candidate.get("career_history", [])
    return next(
        (role for role in roles if role.get("is_current")),
        roles[0] if roles else {},
    )


def _load_mutations(
    path: Path,
) -> tuple[dict[str, set[str]], dict[str, list[dict[str, Any]]]]:
    by_candidate: dict[str, set[str]] = defaultdict(set)
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if not path.exists():
        return by_candidate, evidence
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            candidate_id = payload["candidate_id"]
            for issue in payload.get("issues", []):
                family = MUTATION_RULES.get(issue.get("rule", ""))
                if not family:
                    continue
                by_candidate[candidate_id].add(family)
                evidence[family].append(issue)
    return by_candidate, evidence


def _mutation_label(families: set[str]) -> str:
    return "+".join(sorted(families)) if families else "none"


def _build_template_matrix(
    templates: dict[str, TemplateStats],
    top_skills: list[str],
) -> tuple[list[str], np.ndarray, dict[str, float]]:
    template_ids = sorted(templates)
    title_categories = sorted(
        {value for stats in templates.values() for value in stats.title_families}
    )
    career_categories = sorted(
        {value for stats in templates.values() for value in stats.all_careers}
    )
    industry_categories = sorted(
        {value for stats in templates.values() for value in stats.industries}
    )
    weights = {
        "title_family_distribution": 2.0,
        "current_career_template_distribution": 3.0,
        "all_career_template_distribution": 2.0,
        "industry_distribution": 0.75,
        "skill_distribution": 0.5,
        "mean_role_count": 0.5,
    }
    blocks: list[np.ndarray] = []

    def add_distribution_block(
        attribute: str, categories: list[str], weight_name: str
    ) -> None:
        values = np.vstack(
            [
                _distribution(getattr(templates[template_id], attribute), categories)
                for template_id in template_ids
            ]
        )
        blocks.append(normalize(values, norm="l2") * weights[weight_name])

    add_distribution_block(
        "title_families", title_categories, "title_family_distribution"
    )
    add_distribution_block(
        "current_careers",
        career_categories,
        "current_career_template_distribution",
    )
    add_distribution_block(
        "all_careers", career_categories, "all_career_template_distribution"
    )
    add_distribution_block(
        "industries", industry_categories, "industry_distribution"
    )
    add_distribution_block("skills", top_skills, "skill_distribution")

    role_means = np.array(
        [
            [
                sum(roles * count for roles, count in templates[template_id].role_counts.items())
                / templates[template_id].count
            ]
            for template_id in template_ids
        ],
        dtype=float,
    )
    blocks.append(StandardScaler().fit_transform(role_means) * weights["mean_role_count"])
    return template_ids, np.hstack(blocks), weights


def _select_static_clusters(
    matrix: np.ndarray,
    template_ids: list[str],
    templates: dict[str, TemplateStats],
) -> tuple[
    np.ndarray,
    np.ndarray,
    list[dict[str, Any]],
    int,
    int,
    dict[str, dict[str, str]],
]:
    matrix = normalize(matrix, norm="l2")
    labels_by_k: dict[int, np.ndarray] = {}
    evaluations: list[dict[str, Any]] = []
    previous_score: float | None = None
    for k in range(4, min(12, len(matrix) - 1) + 1):
        labels = AgglomerativeClustering(
            n_clusters=k,
            metric="cosine",
            linkage="average",
        ).fit_predict(matrix)
        score = float(silhouette_score(matrix, labels, metric="cosine"))
        labels_by_k[k] = labels
        template_sizes = Counter(labels)
        candidate_sizes: Counter[int] = Counter()
        for template_id, label in zip(template_ids, labels):
            candidate_sizes[int(label)] += templates[template_id].count
        evaluations.append(
            {
                "k": k,
                "silhouette_cosine": round(score, 6),
                "silhouette_gain_from_previous_k": (
                    round(score - previous_score, 6)
                    if previous_score is not None
                    else None
                ),
                "smallest_class_templates": min(template_sizes.values()),
                "smallest_class_candidates": min(candidate_sizes.values()),
            }
        )
        previous_score = score

    fine = max(
        evaluations, key=lambda row: (row["silhouette_cosine"], -row["k"])
    )
    fine_k = int(fine["k"])
    coarse = max(
        evaluations[1:],
        key=lambda row: (
            float(row["silhouette_gain_from_previous_k"]),
            -int(row["k"]),
        ),
    )
    coarse_k = int(coarse["k"])
    hierarchy = {
        str(k): {
            template_id: f"k{k}_class_{int(label):02d}"
            for template_id, label in zip(template_ids, labels)
        }
        for k, labels in labels_by_k.items()
    }
    return (
        labels_by_k[coarse_k],
        labels_by_k[fine_k],
        evaluations,
        coarse_k,
        fine_k,
        hierarchy,
    )


def _select_behavior_clusters(
    matrix: np.ndarray,
    random_state: int,
) -> tuple[np.ndarray, list[dict[str, Any]], int]:
    scaled = StandardScaler().fit_transform(matrix)
    rng = np.random.default_rng(random_state)
    sample_indices = rng.choice(
        len(scaled), size=min(10_000, len(scaled)), replace=False
    )
    labels_by_k: dict[int, np.ndarray] = {}
    evaluations: list[dict[str, Any]] = []
    for k in range(2, 7):
        labels = MiniBatchKMeans(
            n_clusters=k,
            random_state=random_state,
            batch_size=4096,
            n_init=10,
        ).fit_predict(scaled)
        score = float(
            silhouette_score(
                scaled[sample_indices],
                labels[sample_indices],
                metric="euclidean",
            )
        )
        labels_by_k[k] = labels
        evaluations.append({"k": k, "silhouette_euclidean": round(score, 6)})
    best = max(evaluations, key=lambda row: (row["silhouette_euclidean"], -row["k"]))
    selected_k = int(best["k"])
    return labels_by_k[selected_k], evaluations, selected_k


def _dependency(
    source_name: str,
    source: list[str],
    target_name: str,
    target: list[str],
) -> dict[str, Any]:
    return {
        "source": source_name,
        "target": target_name,
        "nmi": round(float(normalized_mutual_info_score(source, target)), 6),
        "ami": round(float(adjusted_mutual_info_score(source, target)), 6),
        "target_mode_accuracy_given_source": round(
            conditional_mode_accuracy(source, target), 6
        ),
        "source_cardinality": len(set(source)),
        "target_cardinality": len(set(target)),
    }


def analyze(
    dataset: Path,
    output_dir: Path,
    random_state: int = 42,
) -> dict[str, Any]:
    """Build a generator manifest, dependencies, and candidate assignments."""
    output_dir.mkdir(parents=True, exist_ok=True)
    mutations_by_candidate, mutation_evidence = _load_mutations(
        output_dir / "integrity_issues.jsonl"
    )

    templates: dict[str, TemplateStats] = defaultdict(TemplateStats)
    careers: dict[str, dict[str, Any]] = {}
    headline_archetypes: dict[str, Counter[str]] = defaultdict(Counter)
    headline_texts: dict[str, str] = {}
    global_skills: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    behavior_rows: list[list[float]] = []

    for candidate in stream_candidates(dataset):
        profile = candidate["profile"]
        candidate_id = candidate["candidate_id"]
        summary = profile.get("summary", "")
        summary_id = summary_template_id(summary)
        archetype = summary_archetype(summary, profile.get("current_title", ""))
        headline = profile.get("headline", "")
        headline_id = headline_template_id(headline)
        current_role = _current_role(candidate)
        current_title = profile.get("current_title", "")
        current_family = title_family(current_title)
        behavior = _behavior_vector(candidate)
        mutation_label = _mutation_label(
            mutations_by_candidate.get(candidate_id, set())
        )

        stats = templates[summary_id]
        stats.count += 1
        stats.canonical_summary = stats.canonical_summary or summary
        stats.archetypes[archetype] += 1
        stats.headlines[headline_id] += 1
        stats.title_families[current_family] += 1
        stats.current_titles[current_title] += 1
        stats.industries[profile.get("current_industry", "")] += 1
        stats.companies[profile.get("current_company", "")] += 1
        stats.role_counts[len(candidate.get("career_history", []))] += 1
        stats.mutation_families[mutation_label] += 1
        stats.behavior_sums += np.asarray(behavior)

        headline_archetypes[headline_id][archetype] += 1
        headline_texts.setdefault(headline_id, headline)

        current_career_id = ""
        for role_index, role in enumerate(candidate.get("career_history", [])):
            description = role.get("description", "")
            career_id = career_template_id(description)
            stats.all_careers[career_id] += 1
            entry = careers.setdefault(
                career_id,
                {
                    "text": description,
                    "count": 0,
                    "current_count": 0,
                    "archetypes": Counter(),
                    "titles": Counter(),
                    "companies": Counter(),
                    "positions": Counter(),
                },
            )
            entry["count"] += 1
            entry["archetypes"][archetype] += 1
            entry["titles"][role.get("title", "")] += 1
            entry["companies"][role.get("company", "")] += 1
            entry["positions"][str(role_index)] += 1
            if role.get("is_current"):
                current_career_id = career_id
                stats.current_careers[career_id] += 1
                entry["current_count"] += 1

        for skill in candidate.get("skills", []):
            skill_name = skill.get("name", "")
            if skill_name:
                stats.skills[skill_name] += 1
                global_skills[skill_name] += 1

        rows.append(
            {
                "candidate_id": candidate_id,
                "summary_template_id": summary_id,
                "summary_archetype": archetype,
                "headline_template_id": headline_id,
                "title_family": current_family,
                "current_title": current_title,
                "current_career_template_id": current_career_id,
                "current_industry": profile.get("current_industry", ""),
                "mutation_family": mutation_label,
            }
        )
        behavior_rows.append(behavior)

    top_skills = [name for name, _ in global_skills.most_common(80)]
    template_ids, static_matrix, static_weights = _build_template_matrix(
        templates, top_skills
    )
    (
        static_labels,
        fine_static_labels,
        static_evaluations,
        static_k,
        fine_static_k,
        static_hierarchy,
    ) = _select_static_clusters(
        static_matrix,
        template_ids,
        templates,
    )
    static_by_template = {
        template_id: f"static_class_{label:02d}"
        for template_id, label in zip(template_ids, static_labels)
    }
    fine_static_by_template = {
        template_id: f"fine_atom_{label:02d}"
        for template_id, label in zip(template_ids, fine_static_labels)
    }

    behavior_matrix = np.asarray(behavior_rows, dtype=float)
    behavior_labels, behavior_evaluations, behavior_k = _select_behavior_clusters(
        behavior_matrix, random_state
    )
    for row, behavior_label in zip(rows, behavior_labels):
        row["static_class"] = static_by_template[row["summary_template_id"]]
        row["fine_static_atom"] = fine_static_by_template[
            row["summary_template_id"]
        ]
        row["behavior_cluster"] = f"behavior_cluster_{behavior_label:02d}"

    categorical = {
        "summary_template": [row["summary_template_id"] for row in rows],
        "summary_archetype": [row["summary_archetype"] for row in rows],
        "headline_template": [row["headline_template_id"] for row in rows],
        "static_class": [row["static_class"] for row in rows],
        "fine_static_atom": [row["fine_static_atom"] for row in rows],
        "title_family": [row["title_family"] for row in rows],
        "current_career_template": [
            row["current_career_template_id"] for row in rows
        ],
        "current_industry": [row["current_industry"] for row in rows],
        "behavior_cluster": [row["behavior_cluster"] for row in rows],
        "mutation_family": [row["mutation_family"] for row in rows],
    }
    dependency_pairs = [
        ("summary_template", "summary_archetype"),
        ("summary_template", "headline_template"),
        ("summary_template", "current_career_template"),
        ("summary_template", "title_family"),
        ("static_class", "summary_archetype"),
        ("fine_static_atom", "summary_archetype"),
        ("static_class", "title_family"),
        ("static_class", "current_career_template"),
        ("static_class", "current_industry"),
        ("static_class", "behavior_cluster"),
        ("summary_archetype", "behavior_cluster"),
        ("static_class", "mutation_family"),
        ("summary_archetype", "mutation_family"),
        ("current_career_template", "summary_archetype"),
        ("headline_template", "summary_archetype"),
    ]
    dependencies = [
        _dependency(source, categorical[source], target, categorical[target])
        for source, target in dependency_pairs
    ]
    dependencies.sort(key=lambda row: row["nmi"], reverse=True)

    static_classes: dict[str, dict[str, Any]] = {}
    for class_name in sorted(set(categorical["static_class"])):
        indices = [
            index for index, row in enumerate(rows) if row["static_class"] == class_name
        ]
        archetypes = Counter(rows[index]["summary_archetype"] for index in indices)
        template_counts = Counter(
            rows[index]["summary_template_id"] for index in indices
        )
        dominant_archetype, purity = _dominant(archetypes)
        class_behavior = behavior_matrix[indices]
        static_classes[class_name] = {
            "candidate_count": len(indices),
            "summary_template_count": len(template_counts),
            "dominant_archetype": dominant_archetype,
            "archetype_purity": round(purity, 6),
            "archetypes": _top(archetypes),
            "summary_templates": _top(template_counts),
            "current_career_templates": _top(
                Counter(
                    rows[index]["current_career_template_id"] for index in indices
                )
            ),
            "current_titles": _top(
                Counter(rows[index]["current_title"] for index in indices)
            ),
            "behavior_clusters": _top(
                Counter(rows[index]["behavior_cluster"] for index in indices)
            ),
            "mutation_families": _top(
                Counter(rows[index]["mutation_family"] for index in indices)
            ),
            "behavior_medians": {
                feature: round(
                    float(np.median(class_behavior[:, feature_index])), 6
                )
                for feature_index, feature in enumerate(BEHAVIOR_FEATURES)
            },
        }

    behavior_clusters: dict[str, dict[str, Any]] = {}
    for cluster_name in sorted(set(categorical["behavior_cluster"])):
        indices = [
            index
            for index, row in enumerate(rows)
            if row["behavior_cluster"] == cluster_name
        ]
        cluster_behavior = behavior_matrix[indices]
        behavior_clusters[cluster_name] = {
            "candidate_count": len(indices),
            "static_classes": _top(
                Counter(rows[index]["static_class"] for index in indices)
            ),
            "archetypes": _top(
                Counter(rows[index]["summary_archetype"] for index in indices)
            ),
            "medians": {
                feature: round(
                    float(np.median(cluster_behavior[:, feature_index])), 6
                )
                for feature_index, feature in enumerate(BEHAVIOR_FEATURES)
            },
        }

    behavior_separation = []
    behavior_cluster_names = sorted(set(categorical["behavior_cluster"]))
    for feature_index, feature in enumerate(BEHAVIOR_FEATURES):
        cluster_means = []
        for cluster_name in behavior_cluster_names:
            indices = [
                index
                for index, row in enumerate(rows)
                if row["behavior_cluster"] == cluster_name
            ]
            cluster_means.append(
                float(np.mean(behavior_matrix[indices, feature_index]))
            )
        standard_deviation = float(np.std(behavior_matrix[:, feature_index]))
        standardized_range = (
            (max(cluster_means) - min(cluster_means)) / standard_deviation
            if standard_deviation
            else 0.0
        )
        behavior_separation.append(
            {
                "feature": feature,
                "standardized_cluster_mean_range": round(
                    standardized_range, 6
                ),
                "cluster_means": [
                    round(cluster_mean, 6) for cluster_mean in cluster_means
                ],
            }
        )
    behavior_separation.sort(
        key=lambda row: row["standardized_cluster_mean_range"], reverse=True
    )

    fine_static_classes: dict[str, dict[str, Any]] = {}
    for class_name in sorted(set(categorical["fine_static_atom"])):
        indices = [
            index
            for index, row in enumerate(rows)
            if row["fine_static_atom"] == class_name
        ]
        archetypes = Counter(rows[index]["summary_archetype"] for index in indices)
        dominant_archetype, purity = _dominant(archetypes)
        fine_static_classes[class_name] = {
            "candidate_count": len(indices),
            "summary_template_count": len(
                {rows[index]["summary_template_id"] for index in indices}
            ),
            "dominant_archetype": dominant_archetype,
            "archetype_purity": round(purity, 6),
            "archetypes": _top(archetypes),
            "coarse_static_classes": _top(
                Counter(rows[index]["static_class"] for index in indices)
            ),
        }

    mutation_manifest: dict[str, Any] = {}
    for family in sorted(set(MUTATION_RULES.values())):
        indices = [
            index
            for index, row in enumerate(rows)
            if family in row["mutation_family"].split("+")
        ]
        companies: Counter[str] = Counter()
        technologies: Counter[str] = Counter()
        for issue in mutation_evidence.get(family, []):
            evidence = issue.get("evidence", {})
            if evidence.get("company"):
                companies[evidence["company"]] += 1
            if evidence.get("technology"):
                technologies[evidence["technology"]] += 1
        mutation_manifest[family] = {
            "candidate_count": len(indices),
            "issue_count": len(mutation_evidence.get(family, [])),
            "static_classes": _top(
                Counter(rows[index]["static_class"] for index in indices)
            ),
            "archetypes": _top(
                Counter(rows[index]["summary_archetype"] for index in indices)
            ),
            "summary_templates": _top(
                Counter(rows[index]["summary_template_id"] for index in indices)
            ),
            "companies_from_evidence": _top(companies),
            "technologies_from_evidence": _top(technologies),
        }

    summary_manifest: dict[str, Any] = {}
    for template_id in template_ids:
        stats = templates[template_id]
        dominant_archetype, purity = _dominant(stats.archetypes)
        summary_manifest[template_id] = {
            "count": stats.count,
            "static_class": static_by_template[template_id],
            "fine_static_atom": fine_static_by_template[template_id],
            "canonical_text": stats.canonical_summary,
            "dominant_archetype": dominant_archetype,
            "archetype_purity": round(purity, 6),
            "archetypes": _top(stats.archetypes),
            "headline_templates": _top(stats.headlines),
            "title_families": _top(stats.title_families),
            "current_titles": _top(stats.current_titles),
            "current_career_templates": _top(stats.current_careers),
            "all_career_templates": _top(stats.all_careers),
            "industries": _top(stats.industries),
            "companies": _top(stats.companies),
            "skills": _top(stats.skills, 20),
            "role_counts": _top(stats.role_counts),
            "mutation_families": _top(stats.mutation_families),
            "title_entropy_bits": round(_entropy(stats.current_titles), 6),
            "career_entropy_bits": round(_entropy(stats.current_careers), 6),
            "behavior_means": {
                feature: round(
                    float(stats.behavior_sums[feature_index] / stats.count), 6
                )
                for feature_index, feature in enumerate(BEHAVIOR_FEATURES)
            },
        }

    career_manifest: dict[str, Any] = {}
    for career_id, entry in sorted(careers.items()):
        dominant_archetype, purity = _dominant(entry["archetypes"])
        career_manifest[career_id] = {
            "text": entry["text"],
            "count": entry["count"],
            "current_count": entry["current_count"],
            "dominant_archetype": dominant_archetype,
            "archetype_purity": round(purity, 6),
            "archetypes": _top(entry["archetypes"]),
            "titles": _top(entry["titles"]),
            "companies": _top(entry["companies"]),
            "positions": _top(entry["positions"]),
        }

    headline_manifest: dict[str, Any] = {}
    for headline_id, archetypes in sorted(headline_archetypes.items()):
        dominant_archetype, purity = _dominant(archetypes)
        headline_manifest[headline_id] = {
            "text": headline_texts[headline_id],
            "count": sum(archetypes.values()),
            "dominant_archetype": dominant_archetype,
            "archetype_purity": round(purity, 6),
            "archetypes": _top(archetypes),
        }

    eta_by_static_class = {
        feature: round(
            correlation_ratio(
                categorical["static_class"], behavior_matrix[:, feature_index]
            ),
            6,
        )
        for feature_index, feature in enumerate(BEHAVIOR_FEATURES)
    }
    eta_by_archetype = {
        feature: round(
            correlation_ratio(
                categorical["summary_archetype"], behavior_matrix[:, feature_index]
            ),
            6,
        )
        for feature_index, feature in enumerate(BEHAVIOR_FEATURES)
    }

    manifest = {
        "method": {
            "purpose": "Reconstruct generator structure; no relevance scoring.",
            "candidate_count": len(rows),
            "summary_template_count": len(summary_manifest),
            "career_template_count": len(career_manifest),
            "headline_template_count": len(headline_manifest),
            "static_inputs": list(static_weights),
            "static_feature_weights": static_weights,
            "static_cluster_selection": static_evaluations,
            "selected_static_k": static_k,
            "selected_fine_static_k": fine_static_k,
            "coarse_selection_rule": (
                "Largest positive silhouette gain over the previous k (the "
                "strongest structural elbow). The maximum-silhouette solution "
                "is retained as fine atoms."
            ),
            "behavior_cluster_selection": behavior_evaluations,
            "selected_behavior_k": behavior_k,
            "behavior_structure_assessment": (
                "weak_discrete_structure"
                if max(
                    row["silhouette_euclidean"]
                    for row in behavior_evaluations
                )
                < 0.20
                else "discrete_structure"
            ),
            "behavior_cluster_separating_features": behavior_separation,
            "random_state": random_state,
        },
        "static_classes": static_classes,
        "fine_static_atoms": fine_static_classes,
        "static_hierarchy_by_summary_template": static_hierarchy,
        "behavior_clusters": behavior_clusters,
        "mutation_families": mutation_manifest,
        "summary_templates": summary_manifest,
        "career_templates": career_manifest,
        "headline_templates": headline_manifest,
    }
    dependency_payload = {
        "categorical_dependencies": dependencies,
        "behavior_eta_squared_by_static_class": eta_by_static_class,
        "behavior_eta_squared_by_summary_archetype": eta_by_archetype,
        "manual_archetype_agreement_for_interpretation_only": {
            "nmi": round(
                float(
                    normalized_mutual_info_score(
                        categorical["static_class"],
                        categorical["summary_archetype"],
                    )
                ),
                6,
            ),
            "ami": round(
                float(
                    adjusted_mutual_info_score(
                        categorical["static_class"],
                        categorical["summary_archetype"],
                    )
                ),
                6,
            ),
            "note": (
                "Manual archetypes interpret discovered classes; they are not "
                "clustering inputs."
            ),
        },
    }

    write_json(output_dir / "generator_manifest.json", manifest)
    write_json(output_dir / "generator_dependencies.json", dependency_payload)
    with (output_dir / "generator_assignments.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        fieldnames = [
            "candidate_id",
            "static_class",
            "fine_static_atom",
            "behavior_cluster",
            "mutation_family",
            "summary_template_id",
            "summary_archetype",
            "headline_template_id",
            "title_family",
            "current_title",
            "current_career_template_id",
            "current_industry",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    _write_report(output_dir / "generator_reconstruction_report.md", manifest, dependency_payload)
    return {
        "candidate_count": len(rows),
        "static_class_count": static_k,
        "fine_static_atom_count": fine_static_k,
        "behavior_cluster_count": behavior_k,
        "manual_archetype_nmi": dependency_payload[
            "manual_archetype_agreement_for_interpretation_only"
        ]["nmi"],
    }


def _write_report(
    path: Path,
    manifest: dict[str, Any],
    dependencies: dict[str, Any],
) -> None:
    method = manifest["method"]
    agreement = dependencies[
        "manual_archetype_agreement_for_interpretation_only"
    ]
    best_behavior_silhouette = max(
        row["silhouette_euclidean"]
        for row in method["behavior_cluster_selection"]
    )
    lines = [
        "# Generator Reconstruction Report",
        "",
        "This report reverse-engineers the synthetic data-generation structure. "
        "It does not assign relevance scores and does not use an LLM, embedding "
        "model, or teacher output.",
        "",
        "## Method",
        "",
        f"- Candidates: {method['candidate_count']:,}",
        f"- Exact summary templates: {method['summary_template_count']}",
        f"- Exact career-description templates: {method['career_template_count']}",
        f"- Exact headline templates: {method['headline_template_count']}",
        f"- Coarse static classes: {method['selected_static_k']}",
        f"- Fine static atoms: {method['selected_fine_static_k']}",
        f"- Mathematical behavior-cluster optimum: "
        f"{method['selected_behavior_k']}",
        "",
        "Static classes are learned from what each summary template emits: title "
        "families, current and historical career templates, industries, skills, "
        "and role counts. Summary wording and hand-written archetype labels are "
        "not clustering inputs.",
        "",
        method["coarse_selection_rule"],
        "",
        "## Static cluster selection",
        "",
        "| k | cosine silhouette | gain | smallest templates | "
        "smallest candidates |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in method["static_cluster_selection"]:
        gain = row["silhouette_gain_from_previous_k"]
        gain_text = gain if gain is not None else "-"
        lines.append(
            f"| {row['k']} | {row['silhouette_cosine']:.4f} | "
            f"{gain_text} | "
            f"{row['smallest_class_templates']} | "
            f"{row['smallest_class_candidates']} |"
        )

    lines.extend(
        [
            "",
            "## Discovered static classes",
            "",
            "| class | candidates | templates | interpretation | purity |",
            "|---|---:|---:|---|---:|",
        ]
    )
    for class_name, info in manifest["static_classes"].items():
        lines.append(
            f"| {class_name} | {info['candidate_count']:,} | "
            f"{info['summary_template_count']} | {info['dominant_archetype']} | "
            f"{info['archetype_purity']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Interpretations are attached after clustering. Agreement with the "
            f"manual archetype map is NMI={agreement['nmi']:.3f}, "
            f"AMI={agreement['ami']:.3f}.",
            "",
            "## Strongest dependencies",
            "",
            "| source | target | NMI | AMI | modal target accuracy |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in dependencies["categorical_dependencies"][:12]:
        lines.append(
            f"| {row['source']} | {row['target']} | {row['nmi']:.3f} | "
            f"{row['ami']:.3f} | "
            f"{row['target_mode_accuracy_given_source']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Behavior structure",
            "",
            "The best k among 2-6 is shown below, but its silhouette is only "
            f"{best_behavior_silhouette:.3f}. "
            "This is weak evidence for discrete behavioral classes. Treat behavior "
            "as mostly continuous plus missing-data patterns.",
            "",
            "| cluster | candidates | dominant static class | inactive days | "
            "response rate |",
            "|---|---:|---|---:|---:|",
        ]
    )
    for cluster_name, info in manifest["behavior_clusters"].items():
        dominant_class = (
            info["static_classes"][0]["value"] if info["static_classes"] else ""
        )
        lines.append(
            f"| {cluster_name} | {info['candidate_count']:,} | {dominant_class} | "
            f"{info['medians']['inactive_days']:.1f} | "
            f"{info['medians']['response_rate']:.3f} |"
        )

    lines.extend(
        [
            "",
            "Strongest cluster separators:",
            "",
        ]
    )
    for row in method["behavior_cluster_separating_features"][:5]:
        lines.append(
            f"- `{row['feature']}`: standardized mean range "
            f"{row['standardized_cluster_mean_range']:.3f}"
        )

    strongest_eta = sorted(
        dependencies["behavior_eta_squared_by_static_class"].items(),
        key=lambda item: item[1],
        reverse=True,
    )[:8]
    lines.extend(
        [
            "",
            "Behavior variance explained by static class (eta-squared):",
            "",
        ]
    )
    lines.extend(f"- `{name}`: {value:.3f}" for name, value in strongest_eta)

    lines.extend(
        [
            "",
            "## Mutation reconstruction",
            "",
            "| mutation | candidates | dominant class | interpreted archetype | "
            "concentrated evidence |",
            "|---|---:|---|---|---|",
        ]
    )
    for family, info in manifest["mutation_families"].items():
        top_class = info["static_classes"][0]["value"] if info["static_classes"] else ""
        top_archetype = info["archetypes"][0]["value"] if info["archetypes"] else ""
        concentration_rows = (
            info["companies_from_evidence"][:3]
            or info["technologies_from_evidence"][:3]
        )
        concentration = ", ".join(
            f"{row['value']} ({row['count']})" for row in concentration_rows
        ) or "-"
        lines.append(
            f"| {family} | {info['candidate_count']:,} | {top_class} | "
            f"{top_archetype} | {concentration} |"
        )

    lines.extend(
        [
            "",
            "## Reconstructed generator graph",
            "",
            "The evidence supports a generator with static profile families that emit "
            "summary, headline, title, career, industry, and skill atoms; a mostly "
            "continuous behavior generator whose distribution depends partly on "
            "profile family; and "
            "rare targeted contradiction mutations applied to selected records.",
            "",
            "This is evidence about data production, not proof of an official "
            "relevance grade. The next Idea 2 stage is to infer and freeze an ordinal "
            "mapping from the job description to these reconstructed classes before "
            "any Idea 1 comparison.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze(args.candidates, args.output_dir, args.random_state)
    print(
        "Generator reconstruction complete: "
        f"{result['candidate_count']:,} candidates, "
        f"{result['static_class_count']} coarse static classes, "
        f"{result['fine_static_atom_count']} fine atoms, "
        f"{result['behavior_cluster_count']} behavior clusters."
    )


if __name__ == "__main__":
    main()
