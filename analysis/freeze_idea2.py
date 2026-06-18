#!/usr/bin/env python3
"""Write the versioned pre-teacher Idea 2 freeze manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from analysis.common import REPO_ROOT, write_json
from analysis.idea2_scorer import (
    BASE_TIER_BY_ATOM,
    SCORER_VERSION,
    WORLD_CONFIGS,
)


FREEZE_VERSION = "idea2-1.0.0"
DEFAULT_OUTPUT = (
    REPO_ROOT / "artifacts" / "analysis" / "idea2_freeze_manifest.json"
)
FROZEN_FILES = {
    "generator_manifest": "artifacts/analysis/generator_manifest.json",
    "jd_evidence_catalog": "artifacts/analysis/jd_evidence_catalog.json",
    "knowledge_base": "analysis/knowledge_base.json",
    "rubric": "analysis/jd_evidence_rubric.json",
    "scorer_source": "analysis/idea2_scorer.py",
    "overlay_source": "analysis/candidate_overlay.py",
    "integrity_source": "analysis/integrity_checks.py",
    "submission_export_source": "analysis/submission_export.py",
    "rank_entrypoint": "rank.py",
    "score_summary": "artifacts/analysis/idea2_score_summary.json",
    "top100": "artifacts/analysis/idea2_top100.csv",
    "submission": "artifacts/analysis/idea2_submission.csv",
}

ATOM_RATIONALES = {
    "fine_atom_01": "Senior explicit-AI cohort with complete retrieval, ranking-evaluation, production, and ownership evidence.",
    "fine_atom_03": "Senior explicit-AI cohort with evaluated ranking but only partial production embedding/vector coverage.",
    "fine_atom_04": "Senior explicit-AI cohort with complete production retrieval evidence; LLM context is deep rather than shallow.",
    "fine_atom_05": "JD-anchored plain-language senior system builders; evaluated ranking is universal despite sparse tool keywords.",
    "fine_atom_08": "Senior explicit-AI cohort with complete production retrieval and evaluation evidence.",
    "fine_atom_10": "Senior explicit-AI cohort with complete production retrieval and evaluation evidence.",
    "fine_atom_11": "Single senior explicit-AI profile with complete evidence but maximum small-cohort uncertainty.",
    "fine_atom_00": "Applied-ML cohort with strong evaluated-ranking prevalence and mixed production retrieval depth.",
    "fine_atom_02": "Generic-ML cohort with no career-side ranking evaluation or production retrieval compounds.",
    "fine_atom_07": "Data/backend-adjacent cohort with Python and systems evidence but no direct retrieval/ranking compounds.",
    "fine_atom_09": "General-software cohort with product engineering evidence but no direct retrieval/ranking compounds.",
    "fine_atom_06": "General-professional catch-all with no direct technical JD evidence.",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def build_manifest(source_commit: str | None = None) -> dict[str, Any]:
    assets = {}
    for asset_id, relative_path in FROZEN_FILES.items():
        path = REPO_ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"freeze input not found: {path}")
        assets[asset_id] = {
            "path": relative_path,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }

    rubric = json.loads(
        (REPO_ROOT / FROZEN_FILES["rubric"]).read_text(encoding="utf-8")
    )
    score_summary = json.loads(
        (REPO_ROOT / FROZEN_FILES["score_summary"]).read_text(encoding="utf-8")
    )
    return {
        "freeze_version": FREEZE_VERSION,
        "status": "frozen_pre_teacher",
        "frozen_on": date.today().isoformat(),
        "source_commit": source_commit or git_commit(),
        "analysis_as_of": "2026-06-01",
        "rubric_version": rubric["version"],
        "scorer_version": SCORER_VERSION,
        "candidate_count": score_summary["candidate_count"],
        "base_tier_by_atom": BASE_TIER_BY_ATOM,
        "base_tier_rationales": ATOM_RATIONALES,
        "worlds": [world.as_dict() for world in WORLD_CONFIGS],
        "audit_sign_off": {
            "tier_a": "accepted after full template review and rubric 1.0.3 fixes",
            "tier_b": "accepted after false-positive review; no direct-requirement leakage found",
            "tier_c": "accepted after bidirectional review of all six generic-ML templates",
            "production_delivery_judgments": {
                "career_2e516f229493": "accepted: explicitly shipped small predictive features",
                "career_8f5eedb01688": "accepted: explicit Docker/Kubernetes deployment of the described SaaS application",
                "career_9ab513003702": "rejected: integration of another team's model-serving service is not delivery ownership",
            },
            "additional_correction": {
                "career_03ab1210df1d": "removed operational ownership inferred from a sentence that denied productionization ownership"
            },
        },
        "interpretation_boundary": (
            "This freezes an independent deterministic proxy ranking, not hidden "
            "ground truth. The atom-to-tier ordering remains a JD-supported "
            "hypothesis and must not be changed after viewing Idea 1 without a "
            "new explicitly versioned post-comparison freeze."
        ),
        "assets": assets,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--source-commit",
        help="Commit containing all frozen source and artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args.source_commit)
    write_json(args.out, manifest)
    print(
        f"Frozen {manifest['freeze_version']} at {args.out} "
        f"from commit {manifest['source_commit']}"
    )


if __name__ == "__main__":
    main()
