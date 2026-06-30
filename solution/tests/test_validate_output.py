import csv

from solution.validate_output import validate_submission_rows


def write_submission(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["candidate_id", "rank", "score", "reasoning"],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_validate_output_accepts_valid_ranked_rows(tmp_path):
    submission = tmp_path / "submission.csv"
    write_submission(
        submission,
        [
            {
                "candidate_id": "CAND_0000001",
                "rank": "1",
                "score": "2.0",
                "reasoning": "Strong career evidence.",
            },
            {
                "candidate_id": "CAND_0000002",
                "rank": "2",
                "score": "1.5",
                "reasoning": "Relevant adjacent evidence.",
            },
        ],
    )

    rows, errors = validate_submission_rows(
        submission,
        {"CAND_0000001", "CAND_0000002"},
        2,
    )

    assert len(rows) == 2
    assert errors == []


def test_validate_output_rejects_unknown_candidate_and_bad_score(tmp_path):
    submission = tmp_path / "submission.csv"
    write_submission(
        submission,
        [
            {
                "candidate_id": "CAND_9999999",
                "rank": "1",
                "score": "nan",
                "reasoning": "",
            }
        ],
    )

    _, errors = validate_submission_rows(submission, {"CAND_0000001"}, 1)

    assert any("unknown candidate_id" in error for error in errors)
    assert any("score must be finite" in error for error in errors)
    assert any("reasoning is required" in error for error in errors)


def test_validate_output_rejects_rank_and_score_order_errors(tmp_path):
    submission = tmp_path / "submission.csv"
    write_submission(
        submission,
        [
            {
                "candidate_id": "CAND_0000001",
                "rank": "1",
                "score": "1.0",
                "reasoning": "First.",
            },
            {
                "candidate_id": "CAND_0000002",
                "rank": "1",
                "score": "2.0",
                "reasoning": "Second.",
            },
        ],
    )

    _, errors = validate_submission_rows(
        submission,
        {"CAND_0000001", "CAND_0000002"},
        2,
    )

    assert any("duplicate rank" in error for error in errors)
    assert any("missing ranks" in error for error in errors)
