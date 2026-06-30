#!/usr/bin/env python3
"""Local-only benchmark audit for the current solution output.

This script may use synthetic-dataset structure, proxy files, and internal
analysis artifacts. It is not part of the general JD ranking system and should
not be presented as a submission-facing validation step.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from analysis.common import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    REPO_ROOT,
    stream_candidates,
    summary_archetype,
    write_json,
)
from solution.precompute import DEFAULT_FEATURES
from solution.ranker import DEFAULT_OUT


DEFAULT_IDEA1 = REPO_ROOT / "idea1_top100.csv"
DEFAULT_IDEA2 = DEFAULT_OUTPUT_DIR / "idea2_submission.csv"
DEFAULT_REPORT_JSON = DEFAULT_OUTPUT_DIR / "solution_dataset_audit.json"
DEFAULT_REPORT_MD = DEFAULT_OUTPUT_DIR / "solution_dataset_audit.md"


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def read_submission_ids(path: Path, limit: int = 100) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"missing CSV header: {path}")
        key = "candidate_id" if "candidate_id" in reader.fieldnames else reader.fieldnames[0]
        return [row[key] for row in reader if row.get(key)][:limit]


def load_selected_candidates(
    candidates_path: Path,
    candidate_ids: set[str],
) -> dict[str, dict[str, Any]]:
    selected = {}
    for candidate in stream_candidates(candidates_path):
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in candidate_ids:
            selected[candidate_id] = candidate
            if len(selected) == len(candidate_ids):
                break
    missing = sorted(candidate_ids - set(selected))
    if missing:
        raise ValueError(f"candidate IDs not found in raw dataset: {missing[:10]}")
    return selected


def load_selected_features(
    features_path: Path,
    candidate_ids: set[str],
) -> dict[str, dict[str, Any]]:
    selected = {}
    with features_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                feature = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid feature JSON at {features_path}:{line_number}: {exc}"
                ) from exc
            candidate_id = str(feature.get("candidate_id"))
            if candidate_id in candidate_ids:
                selected[candidate_id] = feature
                if len(selected) == len(candidate_ids):
                    break
    missing = sorted(candidate_ids - set(selected))
    if missing:
        raise ValueError(f"candidate IDs not found in features: {missing[:10]}")
    return selected


def archetype_counts(candidates_by_id: dict[str, dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for candidate in candidates_by_id.values():
        profile = candidate["profile"]
        archetype = summary_archetype(
            str(profile.get("summary", "")),
            str(profile.get("current_title", "")),
        )
        counts[archetype] += 1
    return counts


def integrity_summary(features_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    risk_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    unsafe_ids = []
    for candidate_id, feature in features_by_id.items():
        integrity = feature.get("integrity_overlay", {})
        risk = str(integrity.get("risk_level", "unknown"))
        risk_counts[risk] += 1
        issue_counts.update(str(rule) for rule in integrity.get("issue_rules", []))
        honeypot_rules = list(integrity.get("honeypot_proxy_rules", []))
        if risk in {"high", "critical"} or honeypot_rules:
            unsafe_ids.append(
                {
                    "candidate_id": candidate_id,
                    "risk_level": risk,
                    "honeypot_proxy_rules": honeypot_rules,
                    "issue_rules": integrity.get("issue_rules", []),
                }
            )
    return {
        "risk_counts": dict(sorted(risk_counts.items())),
        "issue_rule_counts": dict(issue_counts.most_common()),
        "unsafe_top100_count": len(unsafe_ids),
        "unsafe_top100": sorted(unsafe_ids, key=lambda item: item["candidate_id"]),
    }


def optional_overlap(path: Path, solution_ids: set[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    ids = set(read_submission_ids(path, 100))
    return {
        "path": str(path),
        "top100_count": len(ids),
        "common_count": len(solution_ids & ids),
        "solution_only_count": len(solution_ids - ids),
        "reference_only_count": len(ids - solution_ids),
    }


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Solution Dataset Audit",
        "",
        "Local-only benchmark audit. This report may use synthetic-dataset",
        "structure and proxy artifacts; it is not part of the general solution.",
        "",
        f"- Submission: `{summary['submission']}`",
        f"- Top-100 rows: {summary['top100_count']}",
        f"- Unsafe top-100 candidates: {summary['integrity']['unsafe_top100_count']}",
        "",
        "## Archetype Counts",
        "",
    ]
    for name, count in summary["archetype_counts"].items():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Proxy Overlaps", ""])
    for name, payload in summary["proxy_overlaps"].items():
        if payload is None:
            lines.append(f"- {name}: unavailable")
        else:
            lines.append(f"- {name}: {payload['common_count']} common top-100 candidates")
    lines.append("")
    return "\n".join(lines)


def build_audit(
    submission_path: Path,
    candidates_path: Path,
    features_path: Path,
    idea1_path: Path,
    idea2_path: Path,
) -> dict[str, Any]:
    solution_ids = read_submission_ids(submission_path, 100)
    solution_id_set = set(solution_ids)
    candidates_by_id = load_selected_candidates(candidates_path, solution_id_set)
    features_by_id = load_selected_features(features_path, solution_id_set)
    archetypes = archetype_counts(candidates_by_id)
    return {
        "audit_scope": "local_benchmark_only",
        "submission": str(submission_path),
        "top100_count": len(solution_ids),
        "archetype_counts": dict(archetypes.most_common()),
        "direct_occupation_top100_count": archetypes.get("direct_occupation", 0),
        "integrity": integrity_summary(features_by_id),
        "proxy_overlaps": {
            "idea1_top100": optional_overlap(idea1_path, solution_id_set),
            "idea2_top100": optional_overlap(idea2_path, solution_id_set),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--idea1", type=Path, default=DEFAULT_IDEA1)
    parser.add_argument("--idea2", type=Path, default=DEFAULT_IDEA2)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_audit(
        repo_path(args.submission),
        repo_path(args.candidates),
        repo_path(args.features),
        repo_path(args.idea1),
        repo_path(args.idea2),
    )
    out_json = repo_path(args.out_json)
    out_md = repo_path(args.out_md)
    write_json(out_json, summary)
    out_md.write_text(markdown_report(summary), encoding="utf-8")
    print(
        "Dataset audit complete: "
        f"{summary['top100_count']} rows, "
        f"{summary['integrity']['unsafe_top100_count']} unsafe, "
        f"{summary['direct_occupation_top100_count']} direct_occupation; "
        f"wrote {out_json} and {out_md}"
    )


if __name__ == "__main__":
    main()
