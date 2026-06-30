import json
import tempfile
import unittest
from pathlib import Path

from solution.precompute import build_features


def candidate(candidate_id: str = "CAND_0000001") -> dict:
    return {
        "candidate_id": candidate_id,
        "profile": {
            "current_title": "Senior AI Engineer",
            "years_of_experience": 7.0,
            "current_company": "SearchCo",
            "current_industry": "AI/ML",
            "location": "Noida",
            "country": "India",
        },
        "career_history": [
            {
                "company": "SearchCo",
                "title": "Senior AI Engineer",
                "start_date": "2023-01-01",
                "end_date": None,
                "duration_months": 41,
                "is_current": True,
                "industry": "AI/ML",
                "description": (
                    "Owned and shipped production embedding retrieval and "
                    "ranking evaluation systems."
                ),
            }
        ],
        "education": [],
        "skills": [
            {"name": "Python", "proficiency": "advanced", "duration_months": 60}
        ],
        "redrob_signals": {
            "last_active_date": "2026-05-20",
            "signup_date": "2025-01-01",
            "open_to_work_flag": True,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 10,
            "notice_period_days": 30,
            "profile_views_received_30d": 20,
            "search_appearance_30d": 100,
            "saved_by_recruiters_30d": 5,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.8,
            "github_activity_score": 50,
            "willing_to_relocate": False,
            "preferred_work_mode": "hybrid",
            "expected_salary_range_inr_lpa": {"min": 10, "max": 20},
        },
    }


class PrecomputeTests(unittest.TestCase):
    def test_build_features_writes_jsonl_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidates = root / "candidates.jsonl"
            kb = root / "kb.json"
            out = root / "features.jsonl"
            manifest = root / "manifest.json"
            candidates.write_text(json.dumps(candidate()) + "\n", encoding="utf-8")
            kb.write_text('{"companies": {}, "technologies": {}}\n', encoding="utf-8")

            summary = build_features(candidates, kb, out, manifest)
            rows = [json.loads(line) for line in out.read_text().splitlines()]
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(manifest_payload["candidate_count"], 1)
        self.assertEqual(rows[0]["candidate_id"], "CAND_0000001")
        self.assertIn("semantic_tokens", rows[0])
        self.assertIn("retrieval", rows[0]["semantic_tokens"])


if __name__ == "__main__":
    unittest.main()
