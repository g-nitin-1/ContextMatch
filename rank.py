#!/usr/bin/env python3
"""Produce the deterministic Idea 2 top-100 submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import time
from datetime import date
from pathlib import Path
from typing import Any

from analysis.candidate_overlay import (
    load_skill_signal_patterns,
    overlay_candidate,
)
from analysis.common import REPO_ROOT, stream_candidates
from analysis.idea2_scorer import (
    SCORER_VERSION,
    WORLD_CONFIGS,
    assign_ranks,
    score_record,
)
from analysis.integrity_checks import IntegrityChecker, risk_level
from analysis.submission_export import write_submission_csv


DEFAULT_CANDIDATES = (
    REPO_ROOT / "India_runs_data_and_ai_challenge" / "candidates.jsonl"
)
DEFAULT_OUT = REPO_ROOT / "submission.csv"
DEFAULT_FREEZE_MANIFEST = (
    REPO_ROOT / "artifacts" / "analysis" / "idea2_freeze_manifest.json"
)
RUNTIME_ASSETS = (
    "generator_manifest",
    "jd_evidence_catalog",
    "knowledge_base",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_freeze_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"freeze manifest not found: {path}; run the documented freeze build"
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen_pre_teacher":
        raise ValueError("Idea 2 freeze manifest is not marked frozen_pre_teacher")
    if manifest.get("scorer_version") != SCORER_VERSION:
        raise ValueError(
            "scorer version does not match freeze manifest: "
            f"{SCORER_VERSION} != {manifest.get('scorer_version')}"
        )
    return manifest


def resolve_runtime_assets(
    manifest: dict[str, Any],
    repo_root: Path = REPO_ROOT,
) -> dict[str, Path]:
    resolved = {}
    assets = manifest.get("assets", {})
    for asset_id in RUNTIME_ASSETS:
        entry = assets.get(asset_id)
        if not entry:
            raise ValueError(f"freeze manifest is missing runtime asset {asset_id}")
        path = repo_root / entry["path"]
        if not path.is_file():
            raise FileNotFoundError(f"runtime asset not found: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != entry["sha256"]:
            raise ValueError(
                f"runtime asset hash mismatch for {asset_id}: "
                f"{actual_hash} != {entry['sha256']}"
            )
        resolved[asset_id] = path
    return resolved


def integrity_record(
    checker: IntegrityChecker,
    candidate: dict[str, Any],
) -> dict[str, Any] | None:
    findings = checker.check(candidate)
    if not findings:
        return None
    return {
        "risk_level": risk_level(findings),
        "issues": findings,
    }


def rank_candidates(
    candidates_path: Path,
    out_path: Path,
    freeze_manifest_path: Path = DEFAULT_FREEZE_MANIFEST,
) -> dict[str, Any]:
    started = time.monotonic()
    manifest = load_freeze_manifest(freeze_manifest_path)
    assets = resolve_runtime_assets(manifest)
    analysis_as_of = date.fromisoformat(manifest["analysis_as_of"])

    generator_manifest = json.loads(
        assets["generator_manifest"].read_text(encoding="utf-8")
    )
    catalog = json.loads(
        assets["jd_evidence_catalog"].read_text(encoding="utf-8")
    )
    knowledge_base = json.loads(
        assets["knowledge_base"].read_text(encoding="utf-8")
    )
    skill_patterns = load_skill_signal_patterns(catalog["rubric_summary"])
    checker = IntegrityChecker(knowledge_base, analysis_as_of)

    rows = []
    for candidate in stream_candidates(candidates_path):
        overlay = overlay_candidate(
            candidate,
            generator_manifest,
            catalog["career_templates"],
            skill_patterns,
            integrity_record(checker, candidate),
            analysis_as_of,
        )
        rows.append(score_record(overlay, WORLD_CONFIGS))

    if len(rows) < 100:
        raise ValueError(
            f"ranking requires at least 100 candidates; found {len(rows)}"
        )

    assign_ranks(rows, WORLD_CONFIGS)
    top100 = rows[:100]
    unsafe = [
        row["candidate_id"]
        for row in top100
        if row["integrity_risk_level"] == "high"
        or row["honeypot_proxy_rules"]
    ]
    if unsafe:
        raise RuntimeError(
            "integrity gate failed for top 100: " + ", ".join(unsafe)
        )

    write_submission_csv(rows, out_path)
    elapsed = time.monotonic() - started
    max_rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "candidate_count": len(rows),
        "output": str(out_path),
        "elapsed_seconds": round(elapsed, 3),
        "max_rss_mb": round(max_rss_kb / 1024, 1),
        "freeze_version": manifest["freeze_version"],
        "source_commit": manifest["source_commit"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--freeze-manifest",
        type=Path,
        default=DEFAULT_FREEZE_MANIFEST,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = rank_candidates(
        args.candidates,
        args.out,
        args.freeze_manifest,
    )
    print(
        "Ranked "
        f"{summary['candidate_count']:,} candidates in "
        f"{summary['elapsed_seconds']:.3f}s; "
        f"peak RSS {summary['max_rss_mb']:.1f} MB; "
        f"wrote {summary['output']}"
    )


if __name__ == "__main__":
    main()
