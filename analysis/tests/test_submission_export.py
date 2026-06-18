import csv
import re
import tempfile
import unittest
from pathlib import Path

from analysis.submission_export import submission_rows, write_submission_csv


def scored_row(index: int) -> dict:
    return {
        "candidate_id": f"CAND_{index:07d}",
        "mean_score": 8.0 - index / 1000,
        "current_title": "Machine Learning Engineer",
        "current_company": f"Product Company {index}",
        "years_of_experience": 5.0 + index / 100,
        "career_compounds": (
            "evaluated_ranking_system;production_embeddings_retrieval"
        ),
        "skill_names": "BM25;Python;Unrelated Skill",
        "inactive_days": index % 40,
        "open_to_work": index % 3 != 0,
        "notice_period_days": 30 if index % 2 else 90,
        "location": "Pune, Maharashtra",
        "country": "India",
        "location_bucket": "pune",
    }


class SubmissionExportTests(unittest.TestCase):
    def test_submission_rows_match_required_shape_and_order(self) -> None:
        rows = submission_rows([scored_row(index) for index in range(1, 101)])

        self.assertEqual(len(rows), 100)
        self.assertEqual(list(rows[0]), ["candidate_id", "rank", "score", "reasoning"])
        self.assertEqual([row["rank"] for row in rows], list(range(1, 101)))
        self.assertEqual(len({row["candidate_id"] for row in rows}), 100)
        self.assertTrue(
            all(
                float(rows[index]["score"]) >= float(rows[index + 1]["score"])
                for index in range(99)
            )
        )
        self.assertTrue(all(row["reasoning"] for row in rows))

    def test_reasoning_uses_candidate_specific_facts(self) -> None:
        row = submission_rows([scored_row(index) for index in range(1, 101)])[0]

        self.assertIn("Machine Learning Engineer", row["reasoning"])
        self.assertIn("Product Company 1", row["reasoning"])
        self.assertIn("BM25", row["reasoning"])
        sentence_endings = re.findall(r"[.!?](?:\s|$)", row["reasoning"])
        self.assertLessEqual(len(sentence_endings), 2)

    def test_csv_writer_emits_exact_header_and_100_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "team_test.csv"
            write_submission_csv(
                [scored_row(index) for index in range(1, 101)],
                path,
            )
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

        self.assertEqual(
            rows[0],
            ["candidate_id", "rank", "score", "reasoning"],
        )
        self.assertEqual(len(rows), 101)


if __name__ == "__main__":
    unittest.main()
