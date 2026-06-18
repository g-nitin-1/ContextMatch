#!/usr/bin/env python3
"""Run all deterministic proxy-analysis stages."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from analysis.behavioral_twins import analyze as analyze_twins
from analysis.build_report import build_report
from analysis.candidate_overlay import build_overlay
from analysis.common import DEFAULT_DATASET, DEFAULT_OUTPUT_DIR
from analysis.generator_reconstruction import analyze as reconstruct_generator
from analysis.integrity_checks import (
    DEFAULT_KNOWLEDGE_BASE,
    analyze as analyze_integrity,
)
from analysis.idea2_scorer import build_scores
from analysis.jd_evidence_catalog import build_catalog as build_jd_catalog
from analysis.profile_archetypes import analyze as analyze_archetypes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--knowledge-base", type=Path, default=DEFAULT_KNOWLEDGE_BASE
    )
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2026, 6, 1))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyze_archetypes(args.candidates, args.output_dir)
    analyze_integrity(
        args.candidates, args.output_dir, args.knowledge_base, args.as_of
    )
    analyze_twins(args.candidates, args.output_dir)
    reconstruct_generator(args.candidates, args.output_dir)
    build_jd_catalog(args.candidates, args.output_dir)
    build_overlay(args.candidates, args.output_dir, args.as_of)
    build_scores(args.output_dir)
    build_report(args.output_dir)
    print(f"All analyses complete. Artifacts: {args.output_dir}")


if __name__ == "__main__":
    main()
