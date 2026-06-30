#!/usr/bin/env python3
"""Precompute JD-agnostic candidate features for fast JD-time ranking."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Iterator

from analysis.common import DEFAULT_DATASET, REPO_ROOT
from analysis.integrity_checks import DEFAULT_KNOWLEDGE_BASE, IntegrityChecker
from solution.candidate_features import DEFAULT_AS_OF, build_candidate_overlay
from solution.text_features import career_weighted_tokens


FEATURE_VERSION = "candidate-features-0.1.0"
DEFAULT_SOLUTION_ARTIFACT_DIR = REPO_ROOT / "artifacts" / "solution"
DEFAULT_FEATURES = DEFAULT_SOLUTION_ARTIFACT_DIR / "candidate_features.jsonl"
DEFAULT_MANIFEST = DEFAULT_SOLUTION_ARTIFACT_DIR / "candidate_features_manifest.json"


def iter_candidates_with_hash(path: Path) -> Iterator[tuple[dict[str, Any], bytes]]:
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            if not raw_line.strip():
                continue
            try:
                yield json.loads(raw_line), raw_line
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def build_features(
    candidates_path: Path,
    knowledge_base_path: Path,
    out_path: Path = DEFAULT_FEATURES,
    manifest_path: Path = DEFAULT_MANIFEST,
    as_of: date = DEFAULT_AS_OF,
) -> dict[str, Any]:
    started = time.perf_counter()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    knowledge_base_bytes = knowledge_base_path.read_bytes()
    knowledge_base = json.loads(knowledge_base_bytes)
    checker = IntegrityChecker(knowledge_base, as_of)

    candidate_digest = hashlib.sha256()
    feature_digest = hashlib.sha256()
    risk_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    candidate_count = 0

    with out_path.open("wb") as handle:
        for candidate, raw_line in iter_candidates_with_hash(candidates_path):
            candidate_digest.update(raw_line)
            candidate_count += 1
            findings = checker.check(candidate)
            feature = build_candidate_overlay(candidate, findings, as_of)
            feature["semantic_tokens"] = career_weighted_tokens(candidate)
            encoded = (
                json.dumps(feature, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                + "\n"
            ).encode("utf-8")
            feature_digest.update(encoded)
            handle.write(encoded)
            risk_counts[feature["integrity_overlay"]["risk_level"]] += 1
            rule_counts.update(feature["integrity_overlay"]["issue_rules"])

    elapsed = time.perf_counter() - started
    manifest = {
        "feature_version": FEATURE_VERSION,
        "analysis_as_of": as_of.isoformat(),
        "candidate_count": candidate_count,
        "inputs": {
            "candidates": {
                "path": str(candidates_path),
                "sha256": candidate_digest.hexdigest(),
            },
            "knowledge_base": {
                "path": str(knowledge_base_path),
                "sha256": sha256_bytes(knowledge_base_bytes),
            },
        },
        "outputs": {
            "features": {
                "path": str(out_path),
                "sha256": feature_digest.hexdigest(),
                "bytes": out_path.stat().st_size,
            }
        },
        "integrity_risk_counts": dict(sorted(risk_counts.items())),
        "integrity_rule_counts": dict(rule_counts.most_common()),
        "elapsed_seconds": round(elapsed, 3),
        "max_rss_mb": round(peak_rss_mb(), 1),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--knowledge-base", type=Path, default=DEFAULT_KNOWLEDGE_BASE)
    parser.add_argument("--analysis-as-of", default=DEFAULT_AS_OF.isoformat())
    parser.add_argument("--out", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_features(
        repo_path(args.candidates),
        repo_path(args.knowledge_base),
        repo_path(args.out),
        repo_path(args.manifest),
        date.fromisoformat(args.analysis_as_of),
    )
    print(
        f"Precomputed {manifest['candidate_count']:,} candidates "
        f"in {manifest['elapsed_seconds']:.3f}s; "
        f"maximum memory used {manifest['max_rss_mb']:.1f} MB; "
        f"wrote {manifest['outputs']['features']['path']}"
    )


if __name__ == "__main__":
    main()
