#!/usr/bin/env python3
"""General output validator for the JD-to-candidate ranker.

This validator intentionally checks only submission mechanics and candidate
universe membership. It does not inspect benchmark-specific archetypes,
generator cohorts, or proxy labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import resource
import time
from pathlib import Path
from typing import Any, Iterable

from analysis.common import DEFAULT_DATASET, REPO_ROOT, stream_candidates
from solution.precompute import DEFAULT_FEATURES
from solution.ranker import DEFAULT_OUT, SUBMISSION_COLUMNS


DEFAULT_REPORT = REPO_ROOT / "artifacts" / "solution" / "output_validation.json"


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def candidate_ids_from_features(path: Path) -> set[str]:
    ids = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            candidate_id = record.get("candidate_id")
            if not candidate_id:
                raise ValueError(f"missing candidate_id at {path}:{line_number}")
            ids.add(str(candidate_id))
    return ids


def candidate_ids_from_raw(path: Path) -> set[str]:
    return {str(candidate["candidate_id"]) for candidate in stream_candidates(path)}


def load_candidate_ids(features: Path | None, candidates: Path | None) -> set[str]:
    if features and features.is_file():
        return candidate_ids_from_features(features)
    if candidates and candidates.is_file():
        return candidate_ids_from_raw(candidates)
    raise FileNotFoundError("provide an existing --features or --candidates file")


def validate_submission_rows(
    submission: Path,
    known_candidate_ids: set[str],
    expected_rows: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    errors = []
    rows = []
    with submission.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(SUBMISSION_COLUMNS):
            errors.append(
                "header must be exactly "
                + ",".join(SUBMISSION_COLUMNS)
                + f"; found {reader.fieldnames}"
            )
            return rows, errors
        for row_number, row in enumerate(reader, 2):
            row_errors = validate_row(row, row_number, known_candidate_ids)
            errors.extend(row_errors)
            rows.append(row)

    if len(rows) != expected_rows:
        errors.append(f"expected {expected_rows} rows; found {len(rows)}")

    errors.extend(validate_global_constraints(rows, expected_rows))
    return rows, errors


def validate_row(
    row: dict[str, str],
    row_number: int,
    known_candidate_ids: set[str],
) -> list[str]:
    errors = []
    candidate_id = row.get("candidate_id", "").strip()
    if not candidate_id:
        errors.append(f"row {row_number}: candidate_id is required")
    elif candidate_id not in known_candidate_ids:
        errors.append(f"row {row_number}: unknown candidate_id {candidate_id!r}")

    rank_text = row.get("rank", "").strip()
    try:
        rank = int(rank_text)
    except ValueError:
        errors.append(f"row {row_number}: rank must be an integer")
    else:
        if str(rank) != rank_text:
            errors.append(f"row {row_number}: rank must not contain formatting")

    score_text = row.get("score", "").strip()
    try:
        score = float(score_text)
    except ValueError:
        errors.append(f"row {row_number}: score must be numeric")
    else:
        if not math.isfinite(score):
            errors.append(f"row {row_number}: score must be finite")

    if not row.get("reasoning", "").strip():
        errors.append(f"row {row_number}: reasoning is required")

    return errors


def validate_global_constraints(
    rows: list[dict[str, str]],
    expected_rows: int,
) -> list[str]:
    errors = []
    candidate_ids = [row.get("candidate_id", "").strip() for row in rows]
    duplicate_ids = sorted(duplicates(candidate_ids))
    for candidate_id in duplicate_ids:
        errors.append(f"duplicate candidate_id {candidate_id!r}")

    ranks = []
    for row in rows:
        try:
            ranks.append(int(row.get("rank", "").strip()))
        except ValueError:
            continue
    duplicate_ranks = sorted(duplicates(str(rank) for rank in ranks))
    for rank in duplicate_ranks:
        errors.append(f"duplicate rank {rank}")
    expected_rank_set = set(range(1, expected_rows + 1))
    actual_rank_set = set(ranks)
    missing = sorted(expected_rank_set - actual_rank_set)
    extra = sorted(rank for rank in actual_rank_set if rank not in expected_rank_set)
    if missing:
        errors.append(f"missing ranks: {missing}")
    if extra:
        errors.append(f"out-of-range ranks: {extra}")

    scored = []
    for row in rows:
        try:
            scored.append(
                (
                    int(row.get("rank", "").strip()),
                    float(row.get("score", "").strip()),
                    row.get("candidate_id", "").strip(),
                )
            )
        except ValueError:
            continue
    scored.sort(key=lambda item: item[0])
    for (rank_a, score_a, id_a), (rank_b, score_b, id_b) in zip(scored, scored[1:]):
        if score_a < score_b:
            errors.append(
                f"score must be non-increasing: rank {rank_a} "
                f"({score_a}) < rank {rank_b} ({score_b})"
            )
        if score_a == score_b and id_a > id_b:
            errors.append(
                f"tie at ranks {rank_a}/{rank_b} must sort candidate_id ascending"
            )
    return errors


def duplicates(values: Iterable[str]) -> set[str]:
    seen = set()
    repeated = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return repeated


def build_report(
    submission: Path,
    candidate_source: Path,
    rows: list[dict[str, Any]],
    errors: list[str],
    elapsed: float,
) -> dict[str, Any]:
    return {
        "validator": "solution.validate_output",
        "submission": str(submission),
        "candidate_source": str(candidate_source),
        "row_count": len(rows),
        "passed": not errors,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 3),
        "max_rss_mb": round(peak_rss_mb(), 1),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--features",
        type=Path,
        default=DEFAULT_FEATURES,
        help="Preferred candidate universe source.",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_DATASET,
        help="Raw candidate JSONL fallback if --features is unavailable.",
    )
    parser.add_argument("--expected-rows", type=int, default=100)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    started = time.perf_counter()
    args = parse_args()
    submission = repo_path(args.submission)
    features = repo_path(args.features) if args.features else None
    candidates = repo_path(args.candidates) if args.candidates else None
    candidate_source = features if features and features.is_file() else candidates
    if candidate_source is None:
        raise FileNotFoundError("candidate source is required")

    known_candidate_ids = load_candidate_ids(features, candidates)
    rows, errors = validate_submission_rows(
        submission,
        known_candidate_ids,
        args.expected_rows,
    )
    elapsed = time.perf_counter() - started
    report = build_report(submission, candidate_source, rows, errors, elapsed)
    report_path = repo_path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    if errors:
        print(
            f"Validation failed with {len(errors)} issue(s) in {elapsed:.3f}s; "
            f"maximum memory used {peak_rss_mb():.1f} MB; wrote {report_path}"
        )
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(
        f"Validation passed for {len(rows):,} rows against "
        f"{len(known_candidate_ids):,} candidates in {elapsed:.3f}s; "
        f"maximum memory used {peak_rss_mb():.1f} MB; wrote {report_path}"
    )


if __name__ == "__main__":
    main()
