#!/usr/bin/env python3
"""Rank with precomputed embeddings as a standalone semantic experiment."""

from __future__ import annotations

import argparse
import csv
import json
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from analysis.common import DEFAULT_DATASET, DEFAULT_OUTPUT_DIR, REPO_ROOT
from analysis.integrity_checks import DEFAULT_KNOWLEDGE_BASE
from solution.candidate_features import DEFAULT_AS_OF
from solution.embedding_features import (
    DEFAULT_EMBEDDINGS,
    DEFAULT_IDS,
    DEFAULT_MODEL_PATH,
    TransformerEmbedder,
)
from solution.jd_parser import parse_jd
from solution.precompute import DEFAULT_FEATURES
from solution.ranker import (
    DEFAULT_JD,
    DEFAULT_OUT,
    EVIDENCE_WEIGHT,
    SEMANTIC_WEIGHT,
    SKILL_WEIGHT,
    ScoreBreakdown,
    behavior_modifier,
    build_reasoning,
    evidence_score,
    integrity_blocks,
    iter_jsonl,
    logistics_modifier,
    seniority_alignment,
    skill_score,
    soft_penalty,
    write_submission,
)
from solution.requirement_spec import RequirementSpec, load_spec


DEFAULT_EXPERIMENT_OUT = DEFAULT_OUTPUT_DIR / "solution_embedding_experiment.csv"
DEFAULT_EXPERIMENT_REPORT = DEFAULT_OUTPUT_DIR / "solution_embedding_experiment_summary.json"


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def load_ids(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(value, str) for value in payload):
        raise ValueError(f"candidate embedding ids must be a JSON list of strings: {path}")
    return payload


def embedding_semantic_scores(
    spec: RequirementSpec,
    embeddings_path: Path,
    ids_path: Path,
    model_path: Path,
    chunk_size: int = 8192,
) -> tuple[list[str], np.ndarray]:
    ids = load_ids(ids_path)
    embeddings = np.load(embeddings_path, mmap_mode="r")
    if embeddings.shape[0] != len(ids):
        raise ValueError(
            f"embedding rows ({embeddings.shape[0]}) != id count ({len(ids)})"
        )
    embedder = TransformerEmbedder(model_path)
    query_vectors = embedder.encode(list(spec.semantic_queries))
    if query_vectors.shape[0] == 0:
        raise ValueError("requirement spec has no semantic queries")
    scores = np.zeros(embeddings.shape[0], dtype=np.float32)
    for start in range(0, embeddings.shape[0], chunk_size):
        end = min(start + chunk_size, embeddings.shape[0])
        candidate_vectors = np.asarray(embeddings[start:end], dtype=np.float32)
        similarities = candidate_vectors @ query_vectors.T
        scores[start:end] = similarities.max(axis=1)
    np.clip(scores, 0.0, 1.0, out=scores)
    return ids, scores


def score_overlay_with_embedding(
    spec: RequirementSpec,
    overlay: dict[str, Any],
    semantic: float,
) -> ScoreBreakdown:
    blocked_reasons = integrity_blocks(spec, overlay)
    evidence = evidence_score(spec, overlay)
    skills = skill_score(spec, overlay)
    behavior = behavior_modifier(overlay)
    logistics = logistics_modifier(overlay)
    seniority = seniority_alignment(spec, overlay)
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


def rank_with_embedding_semantic(
    spec: RequirementSpec,
    features_path: Path,
    embeddings_path: Path,
    ids_path: Path,
    model_path: Path,
    limit: int = 100,
) -> tuple[list[ScoreBreakdown], dict[str, Any]]:
    started = time.perf_counter()
    ids, semantic_scores = embedding_semantic_scores(
        spec,
        embeddings_path,
        ids_path,
        model_path,
    )
    eligible: list[ScoreBreakdown] = []
    candidate_count = 0
    blocked_count = 0
    for index, overlay in enumerate(iter_jsonl(features_path)):
        if index >= len(ids):
            raise ValueError("features contain more rows than embedding ids")
        if str(overlay["candidate_id"]) != ids[index]:
            raise ValueError(
                "feature/embedding id order mismatch: "
                f"{overlay['candidate_id']} != {ids[index]}"
            )
        candidate_count += 1
        row = score_overlay_with_embedding(
            spec,
            overlay,
            float(semantic_scores[index]),
        )
        if row.blocked:
            blocked_count += 1
        else:
            eligible.append(row)
    if candidate_count != len(ids):
        raise ValueError("embedding ids contain more rows than features")
    if len(eligible) < limit:
        raise ValueError(f"need at least {limit} eligible candidates")
    eligible.sort(key=lambda row: (-row.score, row.candidate_id))
    elapsed = time.perf_counter() - started
    summary = {
        "candidate_count": candidate_count,
        "eligible_count": len(eligible),
        "blocked_count": blocked_count,
        "elapsed_seconds": round(elapsed, 3),
        "max_rss_mb": round(peak_rss_mb(), 1),
        "semantic": {
            "method": "mean-pooled MiniLM embeddings",
            "weight": SEMANTIC_WEIGHT,
            "min_score": round(float(semantic_scores.min()), 6),
            "mean_score": round(float(semantic_scores.mean()), 6),
            "max_score": round(float(semantic_scores.max()), 6),
        },
    }
    return eligible[:limit], summary


def read_submission_ids(path: Path, limit: int = 100) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return []
        key = "candidate_id" if "candidate_id" in reader.fieldnames else reader.fieldnames[0]
        return [row[key] for row in reader if row.get(key)][:limit]


def add_overlap_summary(report: dict[str, Any], out_path: Path, baseline_path: Path) -> None:
    if not baseline_path.is_file():
        return
    experiment_ids = set(read_submission_ids(out_path))
    baseline_ids = set(read_submission_ids(baseline_path))
    report["baseline_overlap"] = {
        "baseline": str(baseline_path),
        "top100_common": len(experiment_ids & baseline_ids),
        "experiment_only": len(experiment_ids - baseline_ids),
        "baseline_only": len(baseline_ids - experiment_ids),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jd", type=Path, default=DEFAULT_JD)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--ids", type=Path, default=DEFAULT_IDS)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_EXPERIMENT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_EXPERIMENT_REPORT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=100)
    # Kept for CLI symmetry with the main ranker; not used in feature mode.
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--knowledge-base", type=Path, default=DEFAULT_KNOWLEDGE_BASE)
    parser.add_argument("--analysis-as-of", default=DEFAULT_AS_OF.isoformat())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = load_spec(repo_path(args.spec)) if args.spec else parse_jd(repo_path(args.jd))
    out_path = repo_path(args.out)
    rows, report = rank_with_embedding_semantic(
        spec,
        repo_path(args.features),
        repo_path(args.embeddings),
        repo_path(args.ids),
        repo_path(args.model),
        args.limit,
    )
    write_submission(rows, out_path)
    report.update(
        {
            "experiment": "embedding-semantic-0.1.0",
            "role_title": spec.role_title,
            "outputs": {"submission": str(out_path)},
            "inputs": {
                "features": str(repo_path(args.features)),
                "embeddings": str(repo_path(args.embeddings)),
                "candidate_ids": str(repo_path(args.ids)),
                "model": str(repo_path(args.model)),
            },
        }
    )
    add_overlap_summary(report, out_path, repo_path(args.baseline))
    report_path = repo_path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Embedding experiment ranked {report['candidate_count']:,} candidates "
        f"({report['eligible_count']:,} eligible, {report['blocked_count']:,} blocked) "
        f"in {report['elapsed_seconds']:.3f}s; "
        f"maximum memory used {report['max_rss_mb']:.1f} MB; "
        f"wrote {out_path}"
    )


if __name__ == "__main__":
    main()
